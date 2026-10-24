import asyncio

import pytest

from rex_agent.brain.acks import fast_ack
from rex_agent.brain.specialists import REGISTRY, ExecResult, NotConnected, specialist_names
from rex_agent.brain.supervisor import Supervisor


def test_registry_has_the_six_specialists_plus_location():
    assert set(specialist_names()) == {"comms", "calendar", "caller", "meeting", "coder", "screen", "location"}
    assert REGISTRY["caller"].slow and REGISTRY["coder"].slow and REGISTRY["meeting"].slow
    assert not REGISTRY["calendar"].slow


@pytest.mark.parametrize(
    "lang, needle",
    [("hi-en", "kar raha hoon"), ("hi-IN", "रहा"), ("en-IN", "On it"), ("ta-IN", "On it")],
)
def test_fast_ack_matches_language(lang, needle):
    assert needle in fast_ack("caller", lang)


class Recorder:
    def __init__(self):
        self.said: list[str] = []
        self.reports: list[tuple[str, ExecResult]] = []

    async def say(self, text: str) -> None:
        self.said.append(text)

    async def report(self, job_id: str, result: ExecResult) -> None:
        self.reports.append((job_id, result))


async def test_fast_specialist_returns_result_inline_without_ack():
    rec = Recorder()

    async def calendar_exec(request: str, lang: str) -> ExecResult:
        return ExecResult(ok=True, summary="Meeting kal 4 baje set ho gayi")

    sup = Supervisor(say=rec.say, report=rec.report, executors={"calendar": calendar_exec})
    out = await sup.delegate("calendar", "meeting kal 4 baje", lang="hi-en")
    assert out == "Meeting kal 4 baje set ho gayi"
    assert rec.said == []


async def test_slow_specialist_acks_first_then_reports_in_background():
    rec = Recorder()
    gate = asyncio.Event()

    async def caller_exec(request: str, lang: str) -> ExecResult:
        await gate.wait()
        return ExecResult(ok=True, summary="Saturday 6 PM booked")

    sup = Supervisor(say=rec.say, report=rec.report, executors={"caller": caller_exec})
    out = await sup.delegate("caller", "book dentist Saturday evening", lang="hi-en")
    assert "background" in out.lower()
    assert len(rec.said) == 1 and "kar raha hoon" in rec.said[0]
    assert rec.reports == []
    gate.set()
    await sup.wait_idle()
    assert rec.reports[0][1].summary == "Saturday 6 PM booked"


async def test_unconnected_specialist_is_reported_honestly():
    rec = Recorder()
    sup = Supervisor(say=rec.say, report=rec.report, executors={})
    out = await sup.delegate("comms", "post standup notes to Slack", lang="en-IN")
    assert "not connected yet" in out.lower()


async def test_executor_failure_becomes_spoken_failure_not_crash():
    rec = Recorder()

    async def boom(request: str, lang: str) -> ExecResult:
        raise RuntimeError("slack 500")

    sup = Supervisor(say=rec.say, report=rec.report, executors={"comms": boom})
    out = await sup.delegate("comms", "post", lang="en-IN")
    assert out.lower().startswith("that didn't work")


async def test_unknown_specialist_raises_value_error():
    sup = Supervisor(say=Recorder().say, report=Recorder().report, executors={})
    with pytest.raises(ValueError):
        await sup.delegate("astrology", "x", lang="en-IN")


def test_not_connected_executor_result():
    r = asyncio.run(NotConnected("calendar")("x", "en-IN"))
    assert not r.ok and "calendar" in r.summary.lower()
