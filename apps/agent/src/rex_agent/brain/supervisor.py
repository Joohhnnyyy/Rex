"""Supervisor: routes a request to a specialist and handles fast vs slow work.

Fast specialists run inline and their summary is returned to the LLM to speak.
Slow specialists get an instant spoken acknowledgement, run as background jobs,
and report back through ``report`` when done — the voice loop never blocks.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable, Mapping

from rex_agent.brain.acks import fast_ack
from rex_agent.brain.specialists import REGISTRY, ExecResult, Executor, NotConnected

logger = logging.getLogger("rex.supervisor")

Say = Callable[[str], Awaitable[None]]
Report = Callable[[str, ExecResult], Awaitable[None]]


class Supervisor:
    def __init__(self, say: Say, report: Report, executors: Mapping[str, Executor] | None = None) -> None:
        self._say = say
        self._report = report
        self._executors = dict(executors or {})
        self._jobs: dict[str, asyncio.Task] = {}

    def executor_for(self, name: str) -> Executor:
        return self._executors.get(name) or NotConnected(name)

    async def delegate(self, specialist: str, request: str, lang: str) -> str:
        if specialist not in REGISTRY:
            raise ValueError(f"unknown specialist {specialist!r}")
        spec = REGISTRY[specialist]
        run = self.executor_for(specialist)

        if spec.slow and specialist in self._executors:
            job_id = uuid.uuid4().hex[:8]
            await self._say(fast_ack(specialist, lang))
            self._jobs[job_id] = asyncio.create_task(self._run_job(job_id, run, request, lang))
            logger.info("job started", extra={"job_id": job_id, "specialist": specialist})
            return f"Started job {job_id} in the background; the user has been told you'll report back."

        result = await self._safe(run, request, lang)
        return result.summary

    async def _run_job(self, job_id: str, run: Executor, request: str, lang: str) -> None:
        result = await self._safe(run, request, lang)
        try:
            await self._report(job_id, result)
        finally:
            self._jobs.pop(job_id, None)

    @staticmethod
    async def _safe(run: Executor, request: str, lang: str) -> ExecResult:
        try:
            return await run(request, lang)
        except Exception as exc:  # never crash the voice loop
            logger.exception("specialist failed")
            return ExecResult(ok=False, summary=f"That didn't work: {exc}")

    async def wait_idle(self) -> None:
        if self._jobs:
            await asyncio.gather(*self._jobs.values(), return_exceptions=True)
