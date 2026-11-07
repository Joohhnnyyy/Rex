"""Supervisor: runs a specialist's long job in the background so the voice loop never blocks.

Rex speaks an instant acknowledgement, the job runs as a task, and ``report`` is called when it ends.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable, Mapping

from rex_agent.brain.acks import fast_ack
from rex_agent.brain.specialists import ExecResult, Executor

logger = logging.getLogger("rex.supervisor")

Say = Callable[[str], Awaitable[None]]
Report = Callable[[str, ExecResult], Awaitable[None]]


class Supervisor:
    def __init__(self, say: Say, report: Report, executors: Mapping[str, Executor]) -> None:
        self._say = say
        self._report = report
        self._executors = dict(executors)
        self._jobs: dict[str, asyncio.Task] = {}

    async def delegate(self, specialist: str, request: str, lang: str) -> str:
        run = self._executors.get(specialist)
        if run is None:
            raise ValueError(f"unknown specialist {specialist!r}")
        job_id = uuid.uuid4().hex[:8]
        await self._say(fast_ack(specialist, lang))
        self._jobs[job_id] = asyncio.create_task(self._run_job(job_id, run, request, lang))
        logger.info("job started", extra={"job_id": job_id, "specialist": specialist})
        return f"Started job {job_id} in the background; the user has been told you'll report back."

    async def _run_job(self, job_id: str, run: Executor, request: str, lang: str) -> None:
        try:
            result = await run(request, lang)
        except Exception as exc:  # never crash the voice loop
            logger.exception("specialist failed")
            result = ExecResult(ok=False, summary=f"That didn't work: {exc}")
        try:
            await self._report(job_id, result)
        finally:
            self._jobs.pop(job_id, None)

    async def wait_idle(self) -> None:
        if self._jobs:
            await asyncio.gather(*self._jobs.values(), return_exceptions=True)
