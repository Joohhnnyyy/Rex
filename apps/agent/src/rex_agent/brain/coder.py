"""Coder specialist executor (T-41).

Uses Codestral / Gemini Flash via LLMClient to:
1. Locate relevant code in the sandbox repository.
2. Formulate and apply code patches.
3. Run the test suite in the isolated sandbox runner.
4. Iteratively self-heal if tests fail (up to 3 retries).
5. Produce a concise spoken outcome for the user.
"""

from __future__ import annotations

import json
import logging

from rex_agent.brain.specialists import ExecResult
from rex_llm_router.client import LLMClient
from rex_mcp_servers.sandbox import SandboxRunner

logger = logging.getLogger("rex.coder")

CODER_PROMPT = """You are Rex's autonomous Coder specialist.
You fix bugs, write features, and verify test suites in isolated sandboxes.

You are given:
- User task description: {task}
- Existing code context:
{context}
- Previous test error (if any):
{error}

Return JSON with this exact schema:
{{
  "explanation": "Brief explanation of the root cause and fix",
  "files": [
    {{
      "path": "relative/path/to/file.py",
      "content": "Full replacement file content"
    }}
  ]
}}

Rules:
- Output ONLY valid JSON, no markdown code fences or other text.
- Provide the complete new file content for each modified file.
"""


class CoderSpecialist:
    """Autonomous coding agent loop."""

    def __init__(self, llm_client: LLMClient | None = None, runner: SandboxRunner | None = None) -> None:
        self.llm = llm_client or LLMClient()
        self.runner = runner or SandboxRunner()

    async def run(self, request: str, lang: str = "en-IN") -> ExecResult:
        """Run the coding workflow: patch, test, and self-heal up to 3 attempts."""
        last_error = ""

        # Step 1: Collect available source code in workspace
        code_context = self._gather_context()

        for attempt in range(1, 4):
            logger.info("coder attempt %d/3 for request: %s", attempt, request[:80])
            prompt = CODER_PROMPT.format(
                task=request,
                context=code_context or "(New project / no existing files)",
                error=last_error or "None",
            )
            messages = [
                {"role": "system", "content": "You are a professional software engineer."},
                {"role": "user", "content": prompt},
            ]

            try:
                completion = await self.llm.complete(task_kind="code", messages=messages)
                text = completion.text.strip()
                if text.startswith("```"):
                    import re

                    text = re.sub(r"^```(?:json)?\s*", "", text)
                    text = re.sub(r"\s*```$", "", text).strip()
                patch_data = json.loads(text)
            except Exception as exc:
                last_error = f"Failed to parse LLM patch output: {exc}"
                continue

            # Apply file patches
            files_modified = []
            for f in patch_data.get("files", []):
                p = self.runner.resolve_safe_path(f["path"])
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(f["content"], encoding="utf-8")
                files_modified.append(f["path"])

            # Run tests in sandbox
            test_res = await self.runner.run_command("pytest -q", timeout_s=60)
            if test_res.get("ok"):
                return ExecResult(
                    ok=True,
                    summary=f"I patched {len(files_modified)} file(s) and verified tests pass in the sandbox.",
                    data={
                        "files": files_modified,
                        "attempts": attempt,
                        "tests_passed": True,
                        "stdout": test_res.get("stdout", "")[:300],
                    },
                )

            # Failure: capture output and retry
            last_error = test_res.get("stderr") or test_res.get("stdout") or "Test command failed"
            code_context = self._gather_context()

        return ExecResult(
            ok=False,
            summary=f"I attempted to patch the code but tests are still failing after 3 attempts: {last_error[:120]}.",
            data={"attempts": 3, "tests_passed": False, "error": last_error},
        )

    def _gather_context(self, max_chars: int = 4000) -> str:
        snippets = []
        chars = 0
        for p in self.runner.workspace.glob("**/*.py"):
            if ".pytest_cache" in p.parts:
                continue
            try:
                rel = p.relative_to(self.runner.workspace)
                content = p.read_text(encoding="utf-8", errors="replace")
                entry = f"--- File: {rel} ---\n{content}\n"
                if chars + len(entry) > max_chars:
                    snippets.append(f"--- File: {rel} (truncated) ---\n{content[:500]}\n")
                    break
                snippets.append(entry)
                chars += len(entry)
            except Exception:
                continue
        return "\n".join(snippets)
