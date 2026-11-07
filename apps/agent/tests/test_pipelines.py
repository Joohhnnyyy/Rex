"""Pipelines: reusable routines run step by step in code, each step checked before the next."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from rex_agent.main import parse_inputs
from rex_agent.pipelines import PipelineRunner, catalog, load_pipelines, save_pipeline, validate
from rex_agent.prompts import system_prompt
from rex_mcp_gateway.gateway import NeedsApproval, ToolOutcome


class FakeResearch:
    def __init__(self):
        self.calls = []

    async def run(self, query="", url=""):
        self.calls.append(query or url)
        return '<untrusted_data source="web">1. Redwolf\n   https://redwolf.in/naruto\n   Rs 599</untrusted_data>'


class FakeDesktop:
    def __init__(self, replies):
        self.replies, self.sent = list(replies), []

    async def send(self, app, to, text):
        self.sent.append((app, to, text))
        return self.replies.pop(0)


class FakeGateway:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    async def call(self, specialist, tool, args, summary=None):
        self.calls.append((specialist, tool, args))
        return self.reply


def runner(desktop=None, gw=None, written=None):
    async def write(prompt):
        written.append(prompt) if written is not None else None
        return "Hey Shanky, here you go:\n- Redwolf: Rs 599 - https://redwolf.in/naruto"

    return PipelineRunner(gw or FakeGateway(None), FakeResearch(), desktop or FakeDesktop([]), write)


def test_builtin_pipelines_are_valid_and_listed():
    pipes = load_pipelines()
    assert {"share_research", "send_whatsapp", "email_research", "daily_brief"} <= set(pipes)
    for name, spec in pipes.items():
        assert validate(name, spec) == "", name
    assert "- share_research(topic, to):" in catalog(pipes)


@pytest.mark.asyncio
async def test_share_research_fills_each_step_from_the_last():
    desktop = FakeDesktop(["SENT and verified: it's now the newest message in the chat with Shankyy."])
    written = []
    r = runner(desktop=desktop, written=written)
    run = await r.run("share_research", load_pipelines()["share_research"], {"topic": "naruto tees", "to": "Shanky"})
    assert run.ok, run.report()
    assert r.research.calls == ["naruto tees"]
    assert "https://redwolf.in/naruto" in written[0] and "<untrusted_data" not in written[0]
    assert desktop.sent == [
        ("WhatsApp", "Shanky", "Hey Shanky, here you go:\n- Redwolf: Rs 599 - https://redwolf.in/naruto")
    ]
    assert "Pipeline share_research: finished." in run.report()


@pytest.mark.asyncio
async def test_unverified_send_is_never_repeated_but_not_sent_is_retried():
    spec = load_pipelines()["share_research"]
    inputs = {"topic": "x", "to": "Shanky"}

    desktop = FakeDesktop(["UNVERIFIED: pressed Return in the chat with Shankyy, but ..."])
    run = await runner(desktop=desktop).run("share_research", spec, inputs)
    assert not run.ok and len(desktop.sent) == 1 and "step sent failed" in run.stopped

    spec = {**spec, "steps": [*spec["steps"][:-1], {**spec["steps"][-1], "retry": 1}]}
    desktop = FakeDesktop(["NOT SENT: couldn't open a chat named 'Shanky'", "SENT and verified: ok"])
    run = await runner(desktop=desktop).run("share_research", spec, inputs)
    assert run.ok and len(desktop.sent) == 2


@pytest.mark.asyncio
async def test_approval_pauses_the_run_and_missing_inputs_are_asked_for():
    gw = FakeGateway(NeedsApproval(action_id="a1", summary="email to x@y.com", tool="gmail.send_email"))
    run = await runner(gw=gw).run(
        "email_research", load_pipelines()["email_research"], {"topic": "t", "email": "x@y.com"}
    )
    assert not run.ok and "waiting for the user's approval (action a1)" in run.stopped
    assert gw.calls[0][1] == "gmail.send_email" and gw.calls[0][2]["to"] == "x@y.com"

    run = await runner().run("share_research", load_pipelines()["share_research"], {"topic": "t"})
    assert run.stopped == "missing inputs: to. Ask the user for them." and run.steps == []


@pytest.mark.asyncio
async def test_tool_steps_use_dates_and_failures_stop():
    gw = FakeGateway(ToolOutcome(ok=False, text="The tool failed: invalid_grant"))
    run = await runner(gw=gw).run("daily_brief", load_pipelines()["daily_brief"], {})
    assert not run.ok and run.steps[0].id == "events"
    assert gw.calls[0][2]["date_from"].count("-") == 2  # {{today}} became YYYY-MM-DD


def test_save_validates_and_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("REX_PIPELINES_PATH", str(tmp_path / "p.yaml"))
    bad = {
        "description": "x",
        "inputs": {"to": "who"},
        "steps": [{"id": "s", "do": "send", "to": "{{to}}", "text": "{{msg}}"}],
    }
    assert "'{{msg}}' is not an input or an earlier step" in save_pipeline("greet", bad)
    assert "lowercase" in save_pipeline("Greet Shanky!", bad)

    good = {
        "description": "Say good morning to someone.",
        "inputs": {"to": "who"},
        "steps": [
            {"id": "msg", "do": "write", "prompt": "Good morning text for {{to}}"},
            {"id": "sent", "do": "send", "to": "{{to}}", "text": "{{msg}}"},
        ],
    }
    assert save_pipeline("good_morning", good) == ""
    assert load_pipelines()["good_morning"]["description"] == "Say good morning to someone."
    assert "share_research" in load_pipelines()  # built-ins still there


def test_inputs_parse_and_prompt_lists_pipelines():
    assert parse_inputs('{"topic": "flights", "to": "Shanky"}') == {"topic": "flights", "to": "Shanky"}
    assert parse_inputs("topic=flights; to=Shanky") == {"topic": "flights", "to": "Shanky"}
    assert parse_inputs(None) == {}
    p = system_prompt("Johny", datetime(2026, 11, 7, tzinfo=UTC), pipelines=catalog())
    assert "run_pipeline" in p and "share_research(topic, to)" in p


@pytest.mark.asyncio
async def test_a_step_that_raises_is_a_failure_not_a_result():
    class Down:
        async def call(self, *a, **k):
            raise RuntimeError("server 'calendar' is not connected")

    written = []
    run = await runner(gw=Down(), written=written).run("daily_brief", load_pipelines()["daily_brief"], {})
    assert not run.ok and "not connected" in run.stopped
    assert written == []  # nothing was written from an error message
