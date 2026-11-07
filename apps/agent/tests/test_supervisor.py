import asyncio

import pytest

from rex_agent.brain.acks import fast_ack
from rex_agent.brain.specialists import REGISTRY, ExecResult
from rex_agent.brain.supervisor import Supervisor


def test_registry_is_the_background_specialists():
    assert set(REGISTRY) == {"meeting", "coder"}


@pytest.mark.parametrize(
    "lang, needle",
    [("hi-en", "code dekh raha hoon"), ("hi-IN", "रहा"), ("en-IN", "On it"), ("ta-IN", "On it")],
)
def test_fast_ack_matches_language(lang, needle):
    assert needle in fast_ack("coder", lang)


class Recorder:
    def __init__(self):
        self.said: list[str] = []
        self.reports: list[tuple[str, ExecResult]] = []

    async def say(self, text: str) -> None:
        self.said.append(text)

    async def report(self, job_id: str, result: ExecResult) -> None:
        self.reports.append((job_id, result))


async def test_acks_first_then_reports_in_background():
    rec = Recorder()
    gate = asyncio.Event()

    async def coder_exec(request: str, lang: str) -> ExecResult:
        await gate.wait()
        return ExecResult(ok=True, summary="Fixed and PR opened")

    sup = Supervisor(say=rec.say, report=rec.report, executors={"coder": coder_exec})
    out = await sup.delegate("coder", "fix the failing test", lang="hi-en")
    assert "background" in out.lower()
    assert len(rec.said) == 1 and "dekh raha hoon" in rec.said[0]
    assert rec.reports == []
    gate.set()
    await sup.wait_idle()
    assert rec.reports[0][1].summary == "Fixed and PR opened"


async def test_executor_failure_is_reported_not_raised():
    rec = Recorder()

    async def boom(request: str, lang: str) -> ExecResult:
        raise RuntimeError("sandbox 500")

    sup = Supervisor(say=rec.say, report=rec.report, executors={"coder": boom})
    await sup.delegate("coder", "x", lang="en-IN")
    await sup.wait_idle()
    assert rec.reports[0][1].summary.lower().startswith("that didn't work")


async def test_unknown_specialist_raises_value_error():
    sup = Supervisor(say=Recorder().say, report=Recorder().report, executors={})
    with pytest.raises(ValueError):
        await sup.delegate("caller", "x", lang="en-IN")
