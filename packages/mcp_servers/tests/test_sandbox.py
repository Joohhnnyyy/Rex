"""Unit tests for Sandbox MCP Server (T-40)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rex_mcp_servers.sandbox import SandboxRunner, build_server


@pytest.fixture
def temp_sandbox(tmp_path: Path):
    sbx = SandboxRunner(workspace_path=tmp_path, use_docker=False, allow_host=True)
    yield sbx
    sbx.close()


@pytest.mark.asyncio
async def test_sandbox_tools_listing(temp_sandbox):
    server = build_server(runner=temp_sandbox)
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert {"execute", "read_file", "write_file", "git_clone", "run_tests"} <= tool_names


@pytest.mark.asyncio
async def test_sandbox_write_and_read_file(temp_sandbox):
    server = build_server(runner=temp_sandbox)

    # Write a file
    res_w = await server.call_tool("write_file", {"path": "src/hello.py", "content": "print('hello from sandbox')\n"})
    assert not res_w.is_error
    data_w = json.loads(res_w.content[0].text)
    assert data_w["ok"] is True

    # Read it back
    res_r = await server.call_tool("read_file", {"path": "src/hello.py"})
    assert not res_r.is_error
    data_r = json.loads(res_r.content[0].text)
    assert data_r["ok"] is True
    assert "hello from sandbox" in data_r["content"]


@pytest.mark.asyncio
async def test_sandbox_security_traversal_blocked(temp_sandbox):
    server = build_server(runner=temp_sandbox)

    res_r = await server.call_tool("read_file", {"path": "../../etc/passwd"})
    data = json.loads(res_r.content[0].text)
    assert data["ok"] is False
    assert "escapes the sandbox" in data["error"]


@pytest.mark.asyncio
async def test_sandbox_execute_command(temp_sandbox):
    server = build_server(runner=temp_sandbox)

    res = await server.call_tool("execute", {"command": "echo 'sandbox execution ok'"})
    assert not res.is_error
    data = json.loads(res.content[0].text)
    assert data["ok"] is True
    assert data["exit_code"] == 0
    assert "sandbox execution ok" in data["stdout"]


@pytest.mark.asyncio
async def test_sandbox_run_tests_success(temp_sandbox):
    server = build_server(runner=temp_sandbox)

    # Write a passing pytest file
    test_code = """
def test_addition():
    assert 1 + 1 == 2
"""
    await server.call_tool("write_file", {"path": "test_sample.py", "content": test_code})

    res = await server.call_tool("run_tests", {"command": "python -m pytest test_sample.py -q", "workdir": "."})
    assert not res.is_error
    data = json.loads(res.content[0].text)
    assert data["ok"] is True
    assert data["exit_code"] == 0
    assert "1 passed" in data["stdout"]


@pytest.mark.asyncio
async def test_sandbox_timeout_handling(temp_sandbox):
    server = build_server(runner=temp_sandbox)

    res = await server.call_tool("execute", {"command": "sleep 5", "timeout_s": 1})
    data = json.loads(res.content[0].text)
    assert data["ok"] is False
    assert data["timed_out"] is True
    assert "timed out" in data["stderr"]


@pytest.mark.asyncio
async def test_git_clone_rejects_injection(temp_sandbox):
    server = build_server(runner=temp_sandbox)
    for args in (
        {"repo_url": "https://github.com/a/b; touch pwned", "branch": "main"},
        {"repo_url": "https://github.com/a/b", "branch": "main; touch pwned"},
        {"repo_url": "file:///etc", "branch": "main"},
        {"repo_url": "https://github.com/a/b", "target_dir": "../../x"},
    ):
        res = await server.call_tool("git_clone", args)
        assert json.loads(res.content[0].text)["ok"] is False
    assert not (temp_sandbox.workspace / "pwned").exists()


@pytest.mark.asyncio
async def test_host_execution_disabled_and_env_scrubbed(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY_X", "leak")
    off = SandboxRunner(workspace_path=tmp_path, use_docker=False, allow_host=False)
    assert (await off.run_command("echo hi"))["ok"] is False
    on = SandboxRunner(workspace_path=tmp_path, use_docker=False, allow_host=True)
    assert "leak" not in (await on.run_command("env"))["stdout"]
