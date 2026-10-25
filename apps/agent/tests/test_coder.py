"""Unit tests for Coder specialist (T-41)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from rex_agent.brain.coder import CoderSpecialist
from rex_llm_router.client import Attempt, Completion, LLMClient
from rex_llm_router.models import ModelSpec
from rex_mcp_servers.sandbox import SandboxRunner


@pytest.fixture
def sandbox_with_failing_test(tmp_path: Path):
    sbx = SandboxRunner(workspace_path=tmp_path, use_docker=False, allow_host=True)
    # Seed a buggy implementation
    buggy_code = """
def calculate_discount(price: float, percent: float) -> float:
    # Bug: adds discount instead of subtracting
    return price + (price * percent / 100)
"""
    test_code = """
from math_utils import calculate_discount

def test_discount():
    assert calculate_discount(100.0, 20.0) == 80.0
"""
    (tmp_path / "math_utils.py").write_text(buggy_code, encoding="utf-8")
    (tmp_path / "test_discount.py").write_text(test_code, encoding="utf-8")
    yield sbx
    sbx.close()


@pytest.mark.asyncio
async def test_coder_specialist_locates_patches_and_passes_tests(sandbox_with_failing_test):
    dummy_model = ModelSpec(
        alias="codestral",
        provider="mistral",
        name="codestral-latest",
        vision=False,
    )
    fixed_code = """
def calculate_discount(price: float, percent: float) -> float:
    return price - (price * percent / 100)
"""
    patch_payload = {
        "explanation": "Fixed calculate_discount to subtract the percentage rather than add.",
        "files": [
            {
                "path": "math_utils.py",
                "content": fixed_code,
            }
        ],
    }
    mock_completion = Completion(
        text=f"```json\n{json.dumps(patch_payload)}\n```",
        model=dummy_model,
        attempts=[Attempt(dummy_model, "ok")],
    )

    fake_client = AsyncMock(spec=LLMClient)
    fake_client.complete.return_value = mock_completion

    coder = CoderSpecialist(llm_client=fake_client, runner=sandbox_with_failing_test)
    res = await coder.run("Fix the calculate_discount function in math_utils.py")

    assert res.ok is True
    assert "verified tests pass in the sandbox" in res.summary
    assert res.data["tests_passed"] is True
    assert "math_utils.py" in res.data["files"]

    # Verify file was actually overwritten on disk
    updated_content = (sandbox_with_failing_test.workspace / "math_utils.py").read_text()
    assert "return price - (price * percent / 100)" in updated_content
