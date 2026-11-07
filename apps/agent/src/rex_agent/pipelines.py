"""Reusable pipelines: named, step-by-step routines Rex runs the same way every time.

The voice model only picks a pipeline and fills its inputs; the steps run here in code, in order, each
result checked before the next step starts. A model doing multi-step work turn by turn skipped steps,
chose the wrong chat and reported sends that never happened. Pipelines make the same task repeatable.

A pipeline (YAML):
    share_research:
      description: Research a topic and send the top results with links to someone on WhatsApp.
      inputs: {topic: what to look up, to: chat name}
      steps:
        - {id: found, do: research, query: "{{topic}}"}
        - {id: message, do: write, prompt: "Write a WhatsApp message for {{to}} ... {{found}}"}
        - {id: sent, do: send, app: WhatsApp, to: "{{to}}", text: "{{message}}"}

Step kinds: research (query or url), write (prompt -> text from the LLM), send (verified chat message),
tool (call: server.tool, args: {...}; any gateway tool, so tiers and approvals still apply).
Placeholders: inputs, earlier step ids, and today / tomorrow / now (Asia/Kolkata).

Built-in pipelines live in infra/pipelines.yaml; ones Rex saves for the user in ~/.config/rex/pipelines.yaml
(REX_PIPELINES_PATH overrides).
"""

from __future__ import annotations

import os
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from rex_mcp_gateway.gateway import Gateway, NeedsApproval

IST = ZoneInfo("Asia/Kolkata")
REPO_ROOT = Path(__file__).resolve().parents[4]
BUILTIN_PATH = REPO_ROOT / "infra" / "pipelines.yaml"
KINDS = ("research", "write", "send", "tool")
_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z_][\w]*)\s*\}\}")
MAX_OUTPUT = 4000  # chars of one step's output carried into later steps

WRITE_SYSTEM = (
    "You write text for Rex, a voice assistant, to send or read out. Use only the facts given; never invent "
    "prices, links or names. Plain text only: no markdown bold or headings; lists as lines starting with '- '. "
    "Return just the text, nothing before or after it."
)


def user_path() -> Path:
    override = os.environ.get("REX_PIPELINES_PATH")
    return Path(override).expanduser() if override else Path.home() / ".config" / "rex" / "pipelines.yaml"


@dataclass
class StepResult:
    id: str
    kind: str
    ok: bool
    output: str
    note: str = ""


@dataclass
class Run:
    name: str
    ok: bool
    steps: list[StepResult] = field(default_factory=list)
    stopped: str = ""  # why the run stopped early, if it did

    def report(self) -> str:
        lines = [f"Pipeline {self.name}: {'finished' if self.ok else 'STOPPED'}."]
        for s in self.steps:
            mark = "ok" if s.ok else "FAILED"
            lines.append(f"- {s.id} ({s.kind}): {mark}{' ' + s.note if s.note else ''}")
        if self.stopped:
            lines.append(f"Why it stopped: {self.stopped}")
        if self.steps and self.ok:
            lines.append(f"Final result:\n{self.steps[-1].output[:1500]}")
        return "\n".join(lines)


def load_pipelines() -> dict[str, dict]:
    """Built-in pipelines, then the user's saved ones (a saved one can replace a built-in of the same name)."""
    out: dict[str, dict] = {}
    for path in (BUILTIN_PATH, user_path()):
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except FileNotFoundError:
            continue
        out.update(data.get("pipelines") or {})
    return out


def catalog(pipelines: dict[str, dict] | None = None) -> str:
    """One line per pipeline for Rex's prompt: name(inputs): description."""
    pipelines = load_pipelines() if pipelines is None else pipelines
    return "\n".join(
        f"- {name}({', '.join((p.get('inputs') or {}).keys())}): {p.get('description', '').strip()}"
        for name, p in sorted(pipelines.items())
    )


def validate(name: str, spec: dict) -> str:
    """'' if the pipeline is runnable, else what's wrong (checked before saving and before running)."""
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,40}", name or ""):
        return "name must be lowercase letters, digits and underscores, e.g. share_flights"
    steps = spec.get("steps")
    if not isinstance(steps, list) or not steps:
        return "a pipeline needs at least one step"
    known = set((spec.get("inputs") or {}).keys()) | {"today", "tomorrow", "now"}
    for i, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            return f"step {i} must be a mapping"
        kind, sid = step.get("do"), step.get("id")
        if kind not in KINDS:
            return f"step {i}: 'do' must be one of {', '.join(KINDS)}"
        if not sid or not re.fullmatch(r"[a-z][a-z0-9_]*", str(sid)):
            return f"step {i}: needs an id like 'found' or 'message'"
        need = {"research": ("query", "url"), "write": ("prompt",), "send": ("to", "text"), "tool": ("call",)}[kind]
        if kind == "research" and not (step.get("query") or step.get("url")):
            return f"step {sid}: research needs query or url"
        if kind != "research" and any(not step.get(k) for k in need):
            return f"step {sid}: {kind} needs {', '.join(need)}"
        for ref in _PLACEHOLDER.findall(yaml.safe_dump(step)):
            if ref not in known:
                return f"step {sid}: '{{{{{ref}}}}}' is not an input or an earlier step"
        known.add(str(sid))
    return ""


def fill(value: Any, ctx: dict[str, str]) -> Any:
    if isinstance(value, str):
        return _PLACEHOLDER.sub(lambda m: ctx.get(m.group(1), m.group(0)), value)
    if isinstance(value, dict):
        return {k: fill(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [fill(v, ctx) for v in value]
    return value


def _unwrap(text: str) -> str:
    """Tool outputs come wrapped in <untrusted_data> tags for the voice model; steps pass on the content."""
    return re.sub(r"</?untrusted_data[^>]*>", "", text).strip()


def _failed(kind: str, output: str, expect: str) -> str:
    """'' if the step's output looks like success, else a short reason."""
    if expect:
        return "" if expect.lower() in output.lower() else f"expected {expect!r} in the result"
    low = output.lower()
    if kind == "send":
        return "" if output.startswith("SENT and verified") else output[:200]
    if kind == "tool" and (low.startswith("the tool failed") or low.startswith("error")):
        return output[:200]
    if kind == "research" and ("isn't available" in low or "isn't set up" in low or "lookup failed" in low):
        return output[:200]
    if not output.strip():
        return "empty result"
    return ""


Writer = Callable[[str], Awaitable[str]]


class PipelineRunner:
    def __init__(self, gw: Gateway, research: Any, desktop: Any, write: Writer, specialist: str = "rex") -> None:
        self.gw, self.research, self.desktop, self.write = gw, research, desktop, write
        self.specialist = specialist

    async def _step(self, step: dict, ctx: dict[str, str]) -> tuple[str, str]:
        """Run one step; returns (output, approval_id or '')."""
        kind = step["do"]
        s = fill({k: v for k, v in step.items() if k not in ("id", "do", "expect", "retry")}, ctx)
        if kind == "research":
            return _unwrap(await self.research.run(query=s.get("query", ""), url=s.get("url", ""))), ""
        if kind == "write":
            return (await self.write(s["prompt"])).strip(), ""
        if kind == "send":
            return await self.desktop.send(s.get("app", "WhatsApp"), s["to"], s["text"]), ""
        out = await self.gw.call(self.specialist, s["call"], s.get("args") or {}, summary=f"pipeline · {s['call']}")
        if isinstance(out, NeedsApproval):
            return f"Waiting for the user's approval: {out.summary}", out.action_id
        return _unwrap(out.text), ""

    async def run(self, name: str, spec: dict, inputs: dict[str, str]) -> Run:
        run = Run(name=name, ok=False)
        problem = validate(name, spec)
        if problem:
            run.stopped = f"the pipeline is invalid: {problem}"
            return run
        missing = [k for k in (spec.get("inputs") or {}) if not str(inputs.get(k, "")).strip()]
        if missing:
            run.stopped = f"missing inputs: {', '.join(missing)}. Ask the user for them."
            return run
        now = datetime.now(IST)
        ctx = {
            "today": now.strftime("%Y-%m-%d"),
            "tomorrow": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "now": now.strftime("%Y-%m-%d %H:%M"),
            **{k: str(v) for k, v in inputs.items()},
        }
        for step in spec["steps"]:
            kind, sid = step["do"], str(step["id"])
            # Retry once by default, but never a step that may already have acted (an unverified send or a
            # tool that changes things could run twice).
            tries = 1 + int(step.get("retry", 1 if kind in ("research", "write") else 0))
            output, why, approval = "", "", ""
            for _ in range(tries):
                try:
                    output, approval = await self._step(step, ctx)
                    why = "" if approval else _failed(kind, output, str(step.get("expect", "")))
                except Exception as e:  # a step must never crash the voice loop, and never count as done
                    output, why = f"{type(e).__name__}: {e}", f"{type(e).__name__}: {str(e)[:160]}"
                if approval:
                    break
                if not why:
                    break
                if kind == "send" and not output.startswith("NOT SENT"):
                    break  # UNVERIFIED: it may have gone out; don't send it again
            if approval:
                run.steps.append(StepResult(sid, kind, False, output, f"needs approval ({approval})"))
                run.stopped = f"step {sid} is waiting for the user's approval (action {approval}); the rest is on hold"
                return run
            run.steps.append(StepResult(sid, kind, not why, output, why))
            if why:
                run.stopped = f"step {sid} failed: {why}"
                return run
            ctx[sid] = output[:MAX_OUTPUT]
        run.ok = True
        return run


def save_pipeline(name: str, spec: dict, path: Path | None = None) -> str:
    """Validate and store a user pipeline; returns '' or what's wrong."""
    problem = validate(name, spec)
    if problem:
        return problem
    path = path or user_path()
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except FileNotFoundError:
        data = {}
    data.setdefault("pipelines", {})[name] = spec
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    os.replace(tmp, path)
    return ""
