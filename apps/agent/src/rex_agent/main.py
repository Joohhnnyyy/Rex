"""Rex voice agent: Gnani Prisma STT -> LLM (Gemini > Groq > Mistral) -> Gnani Timbre TTS,
with tools from MCP servers through the Rex gateway (tiers, approvals, audit events).

Run on your laptop:
    uv run --env-file .env python -m livekit.agents download-files     # once: VAD + turn-detector models
    uv run --env-file .env python -m rex_agent console                  # talk in the terminal
    uv run --env-file .env python -m rex_agent dev                      # join LiveKit rooms (dashboard)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ChatContext,
    ChatMessage,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RunContext,
    function_tool,
    metrics,
)
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from rex_agent.brain.specialists import REGISTRY, ExecResult
from rex_agent.brain.supervisor import Supervisor
from rex_agent.config import AgentConfig
from rex_agent.lang import detect_language, tts_language
from rex_agent.models import build_llm, build_stt, build_tts
from rex_agent.prompts import greeting, system_prompt
from rex_agent.tools_bridge import build_tools
from rex_mcp_gateway.gateway import Gateway
from rex_mcp_gateway.registry import Registry, load_registry
from rex_shared.schemas import ActionEvent

logger = logging.getLogger("rex.agent")
IST = ZoneInfo("Asia/Kolkata")
REPO_ROOT = Path(__file__).resolve().parents[4]
TIMELINE_TOPIC = "rex.timeline"


class Rex(Agent):
    def __init__(self, cfg: AgentConfig, gateway: Gateway | None = None, tools: list | None = None) -> None:
        super().__init__(
            instructions=system_prompt(cfg.user_name, datetime.now(IST), cfg.english_only), tools=tools or []
        )
        self._cfg = cfg
        self.gateway = gateway
        self._lang: str | None = "en-IN" if cfg.english_only else None
        self.supervisor = Supervisor(say=self._say_now, report=self._report_back, executors={})

    async def _say_now(self, text: str) -> None:
        self.session.say(text)  # don't wait for playback; the tool call returns immediately

    async def _report_back(self, job_id: str, result: ExecResult) -> None:
        verdict = "finished" if result.ok else "failed"
        self.session.generate_reply(
            instructions=f"A background job {verdict}. Tell the user in one short sentence: {result.summary}"
        )

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        """Multilingual mode: lock the reply language to what the user just spoke."""
        if self._cfg.english_only:
            return
        text = new_message.text_content or ""
        self._lang = detect_language(text, previous=self._lang)
        if self.session.tts is not None and hasattr(self.session.tts, "update_options"):
            self.session.tts.update_options(language=tts_language(self._lang))

    @function_tool()
    async def delegate_task(self, context: RunContext, specialist: str, request: str) -> str:
        """Hand a long-running task to a specialist (phone calls, meetings, coding) that runs in the background.

        Args:
            specialist: one of calendar, comms, location, caller, meeting, coder, screen
            request: the user's request restated clearly with every detail (who, what, when, where)
        """
        if specialist not in REGISTRY:
            return f"Unknown specialist {specialist!r}. Choose one of: {', '.join(REGISTRY)}."
        return await self.supervisor.delegate(specialist, request, lang=self._lang or "en-IN")

    @function_tool()
    async def approve_action(self, context: RunContext, action_id: str) -> str:
        """Run an action the user has just approved (they said yes to your confirmation question).

        Args:
            action_id: the action_id from the approval request
        """
        if self.gateway is None:
            return "No tools are connected."
        try:
            out = await self.gateway.approve(action_id)
        except KeyError:
            return "That approval has expired or was already handled. Ask the user if they want to try again."
        return out.text

    @function_tool()
    async def deny_action(self, context: RunContext, action_id: str) -> str:
        """Cancel an action the user did not approve.

        Args:
            action_id: the action_id from the approval request
        """
        if self.gateway is None:
            return "No tools are connected."
        try:
            await self.gateway.deny(action_id)
        except KeyError:
            pass
        return "Cancelled. Nothing was done."


def load_runtime_registry() -> Registry:
    os.environ.setdefault("PYTHON", sys.executable)  # MCP servers run with the agent's interpreter
    path = Path(os.environ.get("REX_MCP_CONFIG", REPO_ROOT / "infra" / "mcp_servers.yaml"))
    return load_registry(path)


def event_to_json(ev: ActionEvent) -> str:
    return json.dumps({"type": "action_event", **json.loads(ev.model_dump_json())}, ensure_ascii=False)


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server = AgentServer(setup_fnc=prewarm)


def _turn_detection():
    """Multilingual end-of-turn model if its files are downloaded, else plain VAD-based turns."""
    if os.environ.get("REX_TURN_DETECTION", "multilingual") == "vad":
        return "vad"
    try:
        return MultilingualModel()
    except Exception:  # model files missing -> run `python -m livekit.agents download-files`
        logger.warning("turn-detector model unavailable, falling back to VAD turn detection")
        return "vad"


@server.rtc_session(agent_name=os.environ.get("REX_AGENT_NAME", "rex"))
async def entrypoint(ctx: JobContext) -> None:
    cfg = AgentConfig.from_env()
    room = ctx.room

    async def publish(ev: ActionEvent) -> None:
        try:
            await room.local_participant.send_text(event_to_json(ev), topic=TIMELINE_TOPIC)
        except Exception:
            logger.exception("could not publish timeline event")

    # The gateway's MCP connections live in this task for the whole session (anyio requirement).
    async with Gateway(load_runtime_registry(), on_event=publish) as gw:
        tools = await build_tools(gw, "rex")
        logger.info("tools ready: %s", [t.info.name for t in tools])
        agent = Rex(cfg, gateway=gw, tools=tools)

        session = AgentSession(
            stt=build_stt(cfg),
            llm=build_llm(),
            tts=build_tts(cfg),
            vad=ctx.proc.userdata["vad"],
            turn_detection=_turn_detection(),
            preemptive_generation=True,
        )

        usage = metrics.UsageCollector()

        @session.on("metrics_collected")
        def _on_metrics(ev: MetricsCollectedEvent) -> None:
            metrics.log_metrics(ev.metrics)
            usage.collect(ev.metrics)

        closed = asyncio.Event()
        session.on("close", lambda _ev: closed.set())

        async def decide(data: rtc.RpcInvocationData) -> str:
            """Dashboard Approve / Deny buttons."""
            req = json.loads(data.payload)
            action_id, decision = req["action_id"], req["decision"]
            try:
                if decision == "approve":
                    out = await gw.approve(action_id)
                    session.generate_reply(
                        instructions="The user approved the pending action on the dashboard. Tell them the result "
                        f"in one short sentence: {out.text}"
                    )
                else:
                    await gw.deny(action_id)
                    session.generate_reply(instructions="The user denied the pending action. Confirm it was cancelled.")
            except KeyError:
                return json.dumps({"ok": False, "error": "expired or already handled"})
            return json.dumps({"ok": True})

        room.local_participant.register_rpc_method("rex.decide", decide)

        await session.start(room=room, agent=agent)
        session.say(greeting(cfg.user_name))
        await closed.wait()
        logger.info("session closed; usage: %s", usage.get_summary())
