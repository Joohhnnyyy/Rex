"""Sandbox MCP Server (T-40).

Runs commands, file edits, git operations, and test suites in an isolated sandbox.
Uses Docker container execution if docker is available and configured,
or a strictly bounded local temporary sandbox workspace with resource timeouts.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import shlex
import shutil
import tempfile
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("rex.mcp.sandbox")


_GIT_URL = re.compile(r"https://[A-Za-z0-9._~\-]+(:\d+)?(/[A-Za-z0-9._~\-]+)+(\.git)?/?")
_BRANCH = re.compile(r"[A-Za-z0-9._/\-]{1,100}")


class SandboxSecurityError(Exception):
    """Raised when an operation attempts to escape the sandbox boundary."""


class SandboxRunner:
    """Manages the isolated sandbox workspace and process execution."""

    def __init__(
        self,
        workspace_path: Path | None = None,
        use_docker: bool = True,
        docker_image: str = "rex-sandbox:latest",
        allow_host: bool | None = None,
    ):
        # Host execution is not isolated: only with explicit opt-in (REX_SANDBOX_ALLOW_HOST=1 or allow_host=True).
        if allow_host is None:
            allow_host = os.environ.get("REX_SANDBOX_ALLOW_HOST") == "1"
        self.allow_host = allow_host
        self.use_docker = use_docker and shutil.which("docker") is not None
        self.docker_image = docker_image
        if workspace_path is not None:
            self.workspace = workspace_path
            self._cleanup = False
        else:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="rex_sbx_")
            self.workspace = Path(self._temp_dir.name)
            self._cleanup = True

    def resolve_safe_path(self, relative_path: str) -> Path:
        """Resolve a path safely inside the sandbox workspace, blocking directory traversal."""
        # Normalize and resolve
        target = (self.workspace / relative_path).resolve()
        try:
            target.relative_to(self.workspace.resolve())
        except ValueError:
            msg = f"Access denied: path {relative_path!r} escapes the sandbox workspace."
            raise SandboxSecurityError(msg) from None
        return target

    async def run_command(self, command: str, timeout_s: int = 60, workdir: str = ".") -> dict[str, Any]:
        """Execute a shell command in the sandbox with timeout and resource isolation."""
        safe_workdir = self.resolve_safe_path(workdir)
        safe_workdir.mkdir(parents=True, exist_ok=True)

        if not self.use_docker and not self.allow_host:
            return {
                "exit_code": -1,
                "ok": False,
                "stdout": "",
                "stderr": "Docker unavailable and host execution disabled (set REX_SANDBOX_ALLOW_HOST=1).",
                "timed_out": False,
            }

        if self.use_docker:
            rel_workdir = safe_workdir.relative_to(self.workspace.resolve()).as_posix()
            # Run inside disposable docker container with security flags
            container_cmd = [
                "docker",
                "run",
                "--rm",
                "--network",
                "bridge",
                "--memory",
                "1g",
                "--cpus",
                "1.5",
                "-v",
                f"{self.workspace}:/workspace",
                "-w",
                f"/workspace/{rel_workdir}",
                "--user",
                "1000:1000",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--pids-limit",
                "256",
                self.docker_image,
                "bash",
                "-c",
                command,
            ]
            cmd = container_cmd
            cwd = None
        else:
            cmd = ["/bin/bash", "-c", command]
            cwd = safe_workdir

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # Minimal env: never forward API keys / tokens from the parent process.
                env={
                    "HOME": str(self.workspace),
                    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                    "LANG": "C.UTF-8",
                },
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")
            return {
                "exit_code": proc.returncode,
                "ok": proc.returncode == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "timed_out": False,
            }
        except TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {
                "exit_code": -1,
                "ok": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout_s} seconds.",
                "timed_out": True,
            }
        except Exception as exc:
            return {
                "exit_code": -1,
                "ok": False,
                "stdout": "",
                "stderr": str(exc),
                "timed_out": False,
            }

    def close(self) -> None:
        if self._cleanup and hasattr(self, "_temp_dir"):
            self._temp_dir.cleanup()


def build_server(runner: SandboxRunner | None = None) -> MCPServer:
    sbx = runner or SandboxRunner()
    server = MCPServer("sandbox")

    @server.tool()
    async def execute(command: str, timeout_s: int = 60, workdir: str = ".") -> str:
        """Run a shell command inside the isolated sandbox workspace.

        Args:
            command: The command line string to run.
            timeout_s: Maximum execution duration in seconds (default 60).
            workdir: Working directory relative to sandbox workspace root.
        """
        res = await sbx.run_command(command, timeout_s=timeout_s, workdir=workdir)
        return json.dumps(res, ensure_ascii=False)

    @server.tool()
    async def read_file(path: str) -> str:
        """Read text from a file inside the sandbox workspace.

        Args:
            path: Relative path to the file inside the workspace.
        """
        try:
            safe_p = sbx.resolve_safe_path(path)
            if not safe_p.is_file():
                return json.dumps({"ok": False, "error": f"File not found: {path}"})
            content = safe_p.read_text(encoding="utf-8", errors="replace")
            return json.dumps({"ok": True, "path": path, "content": content})
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)})

    @server.tool()
    async def write_file(path: str, content: str) -> str:
        """Write text to a file inside the sandbox workspace.

        Args:
            path: Relative path to the file to create or overwrite.
            content: Text content to write into the file.
        """
        try:
            safe_p = sbx.resolve_safe_path(path)
            safe_p.parent.mkdir(parents=True, exist_ok=True)
            safe_p.write_text(content, encoding="utf-8")
            return json.dumps({"ok": True, "path": path, "bytes_written": len(content)})
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)})

    @server.tool()
    async def git_clone(repo_url: str, branch: str = "main", target_dir: str = "repo") -> str:
        """Clone a git repository into the sandbox workspace.

        Args:
            repo_url: Git clone URL.
            branch: Git branch to clone (default 'main').
            target_dir: Target directory relative to sandbox workspace.
        """
        if not _GIT_URL.fullmatch(repo_url) or not _BRANCH.fullmatch(branch):
            return json.dumps({"ok": False, "error": "Invalid repo_url (https only) or branch name."})
        try:
            sbx.resolve_safe_path(target_dir)
        except SandboxSecurityError as exc:
            return json.dumps({"ok": False, "error": str(exc)})
        cmd = " ".join(
            ["git clone --depth 1 -b", shlex.quote(branch), "--", shlex.quote(repo_url), shlex.quote(target_dir)]
        )
        res = await sbx.run_command(cmd, timeout_s=120)
        return json.dumps(res, ensure_ascii=False)

    @server.tool()
    async def run_tests(command: str = "pytest -q", workdir: str = "repo") -> str:
        """Run a test runner command inside a repository in the sandbox.

        Args:
            command: Test command line (e.g. 'pytest -q' or 'npm test').
            workdir: Directory containing tests, relative to sandbox workspace.
        """
        res = await sbx.run_command(command, timeout_s=180, workdir=workdir)
        return json.dumps(res, ensure_ascii=False)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Rex Sandbox MCP Server")
    parser.parse_args()
    srv = build_server()
    srv.run(transport="stdio")


if __name__ == "__main__":
    main()
