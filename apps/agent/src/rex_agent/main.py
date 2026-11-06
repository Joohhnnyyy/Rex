"""Rex voice agent: Gnani Prisma STT -> LLM (Gemini > Groq > Mistral) -> Gnani Timbre TTS,
with tools from MCP servers through the Rex gateway (tiers, approvals, audit events).

Run on your laptop:
    uv run --env-file .env python -m livekit.agents download-files     # once: VAD + turn-detector models
    uv run --env-file .env python -m rex_agent console                  # talk in the terminal
    uv run --env-file .env python -m rex_agent dev                      # join LiveKit rooms (dashboard)
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import sys
import time
import uuid
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
from livekit.agents.voice import room_io
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from rex_agent.brain.coder import CoderSpecialist
from rex_agent.brain.meeting import MeetingSpecialist
from rex_agent.brain.specialists import REGISTRY, ExecResult
from rex_agent.brain.supervisor import Supervisor
from rex_agent.config import AgentConfig
from rex_agent.lang import detect_language, tts_language
from rex_agent.models import build_llm, build_stt, build_tts
from rex_agent.prompts import greeting, system_prompt
from rex_agent.screen import NOT_SHARING, ScreenWatcher, control_screen, describe_screen
from rex_agent.tools_bridge import build_tools
from rex_mcp_gateway.gateway import Gateway
from rex_mcp_gateway.registry import Registry, load_registry
from rex_mcp_servers.browser import read_live_frame
from rex_shared.schemas import ActionEvent

logger = logging.getLogger("rex.agent")
# Chat items kept per turn (messages + tool calls/results); older ones are dropped to keep the prompt small.
MAX_HISTORY_ITEMS = 30
IST = ZoneInfo("Asia/Kolkata")
REPO_ROOT = Path(__file__).resolve().parents[4]
TIMELINE_TOPIC = "rex.timeline"
BROWSER_TOPIC = "rex.browser"  # live screenshots of Rex's browser for the dashboard


class Rex(Agent):
    def __init__(self, cfg: AgentConfig, gateway: Gateway | None = None, tools: list | None = None) -> None:
        super().__init__(
            instructions=system_prompt(cfg.user_name, datetime.now(IST), cfg.english_only), tools=tools or []
        )
        self._cfg = cfg
        self.gateway = gateway
        self._lang: str | None = "en-IN" if cfg.english_only else None
        self.screen = ScreenWatcher()  # attached to the room in entrypoint
        self.publish_event = None  # set in entrypoint: sends ActionEvents to the dashboard timeline
        self.supervisor = Supervisor(
            say=self._say_now,
            report=self._report_back,
            executors={
                "coder": CoderSpecialist().run,
                "meeting": MeetingSpecialist().run,
            },
        )

    async def _say_now(self, text: str) -> None:
        self.session.say(text)  # don't wait for playback; the tool call returns immediately

    async def _report_back(self, job_id: str, result: ExecResult) -> None:
        verdict = "finished" if result.ok else "failed"
        self.session.generate_reply(
            instructions=f"A background job {verdict}. Tell the user in one short sentence: {result.summary}"
        )

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        """Trim old history (fewer prompt tokens = faster replies); multilingual: lock the reply language."""
        if len(self.chat_ctx.items) > MAX_HISTORY_ITEMS + 10:
            await self.update_chat_ctx(self.chat_ctx.copy().truncate(max_items=MAX_HISTORY_ITEMS))
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
    async def look_at_screen(self, context: RunContext, question: str) -> str:
        """Look at the user's shared screen and answer a question about it (read an error, summarise a page,
        say where to click). Use whenever the user refers to what is on their screen.

        Args:
            question: what to find out, e.g. "What does the error say?" or "Summarise this page"
        """
        jpeg = self.screen.jpeg()
        if jpeg is None:
            return NOT_SHARING
        async with context.with_filler("Let me look at your screen.", delay=0.7):
            try:
                return await describe_screen(jpeg, question)
            except Exception as e:
                logger.exception("vision call failed")
                return f"Couldn't analyse the screen right now ({type(e).__name__}). Tell the user to try again."

    @function_tool()
    async def control_screen(
        self,
        context: RunContext,
        action: str,
        target: str | None = None,
        to_target: str | None = None,
        direction: str | None = None,
        amount: int | str | None = None,
        text: str | None = None,
        submit: bool | str | None = None,
        keys: str | None = None,
    ) -> str:
        """Act on the user's shared screen with mouse and keyboard. When the user asked for it, just do it:
        don't ask "shall I?" first. Chain calls to finish the task (open the chat, then type with submit=true).

        Args:
            action: click, double_click, right_click, scroll, drag, type (types text, clicking target first if
                given) or press (a key or combo)
            target: the element to act on, described as it looks ("the green Continue button", "Asmi's chat",
                "the message box"); optional for scroll and type
            to_target: for drag, where to drop it
            direction: for scroll: up, down, left or right
            amount: for scroll: how far, 1 (a little) to 20 (a lot)
            text: for type: the text to enter
            submit: for type: press Enter afterwards (sends a chat message or a search)
            keys: for press: e.g. "enter", "esc", "tab", "cmd+a"
        """
        async with context.with_filler("On it.", delay=0.7):
            a = _clean_screen_args(target, to_target, direction, amount, text, submit, keys)
            ok, msg = await control_screen(self.screen, action, **a)
        if self.publish_event:
            what = f"{action} {a['target'] or a['keys'] or a['direction']}"
            what += f" «{a['text'][:40]}»" if a["text"] else ""
            what += f" → {a['to_target']}" if action == "drag" else ""
            await self.publish_event(
                ActionEvent(
                    id=uuid.uuid4(),
                    ts=datetime.now(IST),
                    tool=f"screen.{action}",
                    tier="W",
                    status="succeeded" if ok else "failed",
                    summary=f"screen · {what}",
                    result_redacted={"text": msg} if ok else {"error": msg},
                )
            )
        return msg

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

    @function_tool()
    async def undo_action(self, context: RunContext, action_id: str = "") -> str:
        """Undo the last reversible action (e.g. undo creating a calendar event, undo adding a note).
        Call this when the user says 'undo', 'cancel that', 'revert that', 'undo karo'.

        Args:
            action_id: Optional specific action_id to undo. If empty, undos the last reversible action.
        """
        if self.gateway is None:
            return "No tools are connected."
        try:
            out = await self.gateway.undo(action_id or None)
            return out.text
        except Exception as exc:
            return f"Nothing could be undone: {exc}."


def load_runtime_registry() -> Registry:
    os.environ.setdefault("PYTHON", sys.executable)  # MCP servers run with the agent's interpreter
    path = Path(os.environ.get("REX_MCP_CONFIG", REPO_ROOT / "infra" / "mcp_servers.yaml"))
    return load_registry(path)


def event_to_json(ev: ActionEvent) -> str:
    return json.dumps({"type": "action_event", **json.loads(ev.model_dump_json())}, ensure_ascii=False)


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()
    if sys.platform == "darwin":
        import pyautogui  # noqa: F401  # loads CoreFoundation/Quartz (~350 ms) before the first click


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
        agent.screen.attach(room)
        agent.publish_event = publish

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

        # Auto-gain control (on by default in livekit-agents 1.8) runs a native AudioProcessingModule per mic
        # stream; on this macOS build it segfaults on creation or silences the input, so Rex never hears you.
        no_agc = room_io.RoomOptions(audio_input=room_io.AudioInputOptions(auto_gain_control=False))
        await session.start(room=room, agent=agent, room_options=no_agc)  # connects the room
        room.local_participant.register_rpc_method("rex.decide", decide)  # needs a connected room
        session.say(greeting(cfg.user_name))
        live = asyncio.create_task(stream_browser_view(room))
        await closed.wait()
        live.cancel()
        logger.info("session closed; usage: %s", usage.get_summary())


_EMPTY = {"", "none", "null", "nil", "n/a"}


def _clean_screen_args(target, to_target, direction, amount, text, submit, keys) -> dict:
    """LLMs fill unused tool fields with null, "none" or copies of other fields; normalise them."""

    def s(v, default=""):
        return default if v is None or str(v).strip().lower() in _EMPTY else str(v).strip()

    try:
        n = int(float(s(amount, "5")))
    except ValueError:
        n = 5
    return {
        "target": s(target),
        "to_target": s(to_target),
        "direction": s(direction, "down").lower(),
        "amount": n if n > 0 else 5,
        "text": s(text) if text is not None else "",
        "submit": s(submit, "false").lower() in {"true", "1", "yes"},
        "keys": s(keys),
    }


async def stream_browser_view(room: rtc.Room, poll_s: float = 0.5) -> None:
    """Send each new frame of Rex's browser (written by the browser MCP server) to the dashboard."""
    started = time.time()  # frames from an earlier session are stale
    last_ts = 0.0
    while True:
        await asyncio.sleep(poll_s)
        frame = read_live_frame()
        if frame is None or frame[0].get("ts", 0) <= max(last_ts, started):
            continue
        state, jpeg = frame
        last_ts = state["ts"]
        msg = {**state, "img": "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()}
        try:
            await room.local_participant.send_text(json.dumps(msg), topic=BROWSER_TOPIC)
        except Exception:
            logger.debug("could not send browser frame", exc_info=True)
