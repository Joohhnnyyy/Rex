#!/usr/bin/env python3
"""Phase 2 (Shanky) completion checker.

Checks setup, MCP configuration, tests, quality gates and tracking for Shanky's Phase 2 work
(Calendar, Slack, Notion MCPs + workflow testing), prints a scored table, writes
docs/team/PHASE2_STATUS.md and records the score on task T-29 in the project graph.

    uv run python scripts/check_phase2.py            # offline checks + offline test suite
    uv run --env-file .env python scripts/check_phase2.py --live   # + connect MCP servers + live workflow tests
    uv run python scripts/check_phase2.py --no-run   # file/config checks only (fast)
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPH = ROOT / "memory" / "project-graph.jsonl"
STATUS = ROOT / "docs" / "team" / "PHASE2_STATUS.md"
SERVERS = ("calendar", "slack", "notion")
LIVE_TESTS = {
    "calendar": "apps/agent/tests/live/test_workflow_calendar.py",
    "slack": "apps/agent/tests/live/test_workflow_slack.py",
    "notion": "apps/agent/tests/live/test_workflow_notion.py",
    "multi-step standup": "apps/agent/tests/live/test_workflow_standup.py",
}
PHASE2_TASKS = ("T-22", "T-23", "T-27", "T-28")


@dataclass
class Check:
    section: str
    name: str
    ok: bool | None  # None = skipped
    detail: str = ""


def read_env() -> dict[str, str]:
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.split(" #")[0].strip()
    return {**env, **{k: v for k, v in os.environ.items() if k not in env}}


def load_yaml() -> dict:
    import yaml

    return yaml.safe_load((ROOT / "infra" / "mcp_servers.yaml").read_text()) or {}


def run(cmd: list[str], extra_env: dict[str, str] | None = None) -> tuple[bool, str]:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env={**os.environ, **(extra_env or {})})
    tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
    return r.returncode == 0, tail[0][:120]


def graph_status() -> dict[str, str]:
    out = {}
    for line in GRAPH.read_text().splitlines():
        o = json.loads(line)
        if o.get("type") == "entity" and o["entityType"] == "Task":
            st = [x.split(":", 1)[1].strip() for x in o["observations"] if x.startswith("status:")]
            out[o["name"]] = st[-1] if st else "todo"
    return out


def checks(live: bool, run_tests: bool) -> list[Check]:
    env, res = read_env(), []
    add = lambda s, n, ok, d="": res.append(Check(s, n, ok, d))  # noqa: E731

    # A. Setup / credentials (names only — values are never printed)
    add(
        "A. Setup",
        "GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET in .env",
        bool(env.get("GOOGLE_CLIENT_ID") and env.get("GOOGLE_CLIENT_SECRET")),
    )
    add("A. Setup", "SLACK_BOT_TOKEN (xoxb-…) in .env", env.get("SLACK_BOT_TOKEN", "").startswith("xoxb-"))
    add("A. Setup", "NOTION_TOKEN in .env", bool(env.get("NOTION_TOKEN")))
    add(
        "A. Setup",
        "Google OAuth token stored outside the repo",
        Path(env.get("REX_GOOGLE_TOKEN_PATH", Path.home() / ".config/rex/google_token.json")).expanduser().exists(),
        "run the calendar server's one-time login",
    )

    # B. MCP configuration
    cfg = load_yaml()
    servers, allow = cfg.get("servers") or {}, set((cfg.get("allowlists") or {}).get("rex") or [])
    for s in SERVERS:
        spec = servers.get(s) or {}
        add(
            "B. MCP config",
            f"`{s}` server configured and enabled",
            bool(spec) and spec.get("enabled", True) is not False,
        )
        add("B. MCP config", f"`{s}` allow-listed for rex", s in allow)
    slack_tools = (servers.get("slack") or {}).get("tools") or {}
    add(
        "B. MCP config",
        "Slack posting tools declared Tier A",
        any(re.search("post|send|reply", t) and (p or {}).get("tier") == "A" for t, p in slack_tools.items()),
    )
    cal_tools = (servers.get("calendar") or {}).get("tools") or {}
    add(
        "B. MCP config",
        "Calendar create = W with undo; delete = A",
        any("create" in t and (p or {}).get("tier") == "W" and (p or {}).get("undo") for t, p in cal_tools.items())
        and any("delete" in t and (p or {}).get("tier") == "A" for t, p in cal_tools.items()),
    )
    notion = servers.get("notion") or {}
    add(
        "B. MCP config",
        "Notion default tier W (not A-by-accident), deletes/archives A",
        notion.get("default_tier") == "W"
        and any(
            re.search("delete|archive", t) and (p or {}).get("tier") == "A"
            for t, p in (notion.get("tools") or {}).items()
        ),
    )

    # C. Tests exist
    for s in SERVERS:
        found = [p for p in ROOT.glob(f"packages/*/tests/test_*{s}*.py")] + [
            p for p in ROOT.glob(f"apps/*/tests/test_*{s}*.py")
        ]
        add(
            "C. Tests",
            f"offline tests for `{s}` (test_*{s}*.py)",
            bool(found),
            ", ".join(str(p.relative_to(ROOT)) for p in found) or "none yet",
        )
    for label, path in LIVE_TESTS.items():
        add("C. Tests", f"live workflow test: {label}", (ROOT / path).exists(), path)
    ev = ROOT / "evals" / "routing.yaml"
    n_cases = len(re.findall(r"^\s*-\s*utterance:", ev.read_text(), re.M)) if ev.exists() else 0
    add("C. Tests", "eval set has ≥ 60 utterances (evals/routing.yaml)", n_cases >= 60, f"{n_cases} found")

    # D. Quality gates
    if run_tests:
        ok, tail = run([sys.executable, "-m", "pytest", "-q", "-p", "no:warnings"], {"GNANI_API_KEY": "x"})
        add("D. Quality", "offline test suite green", ok, tail)
        ok, tail = run([sys.executable, "-m", "ruff", "check", "."])
        add("D. Quality", "ruff lint clean", ok, tail)
    else:
        add("D. Quality", "offline test suite green", None, "skipped (--no-run)")
        add("D. Quality", "ruff lint clean", None, "skipped (--no-run)")
    if live:
        ok, detail = asyncio.run(live_gateway_check())
        add(
            "D. Quality",
            "gateway connects calendar/slack/notion; every tool has a declared or default tier",
            ok,
            detail,
        )
        ok, tail = run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:warnings", "apps/agent/tests/live"],
            {"REX_LIVE_TESTS": "1"},
        )
        add("D. Quality", "live workflow tests green", ok, tail)
    else:
        add("D. Quality", "gateway connects all servers (live)", None, "use --live")
        add("D. Quality", "live workflow tests green", None, "use --live")

    # E. Tracking
    st = graph_status()
    for t in PHASE2_TASKS:
        add("E. Tracking", f"{t} marked done in project graph", st.get(t) == "done", st.get(t, "missing"))
    handoff = (ROOT / "HANDOFF.md").read_text()
    add(
        "E. Tracking",
        "HANDOFF.md has a Shanky Phase 2 entry",
        bool(re.search(r"^## .* — Shanky \(Phase 2", handoff, re.M)),
        "heading: ## YYYY-MM-DD — Shanky (Phase 2)",
    )
    return res


async def live_gateway_check() -> tuple[bool, str]:
    sys.path.insert(0, str(ROOT))
    from rex_agent.main import load_runtime_registry
    from rex_mcp_gateway.gateway import Gateway

    reg = load_runtime_registry()
    async with Gateway(reg) as gw:
        missing = [s for s in SERVERS if s not in gw.connected()]
        tools = await gw.list_tools("rex")
    counts = {s: sum(t.server == s for t in tools) for s in SERVERS}
    if missing:
        return False, f"not connected: {missing}"
    return all(counts.values()), ", ".join(f"{s}:{n} tools" for s, n in counts.items())


def write_status(res: list[Check], live: bool) -> tuple[int, int]:
    scored = [c for c in res if c.ok is not None]
    passed = sum(c.ok for c in scored)
    pct = round(100 * passed / len(scored)) if scored else 0
    icon = {True: "✅", False: "❌", None: "⏭️"}
    lines = [
        "# Phase 2 (Shanky) — completion status",
        "",
        f"_Generated by `scripts/check_phase2.py{' --live' if live else ''}` on {dt.date.today()}. Do not edit by hand._",
        "",
        f"**Score: {passed}/{len(scored)} checks ({pct}%)** · skipped: {len(res) - len(scored)}",
        "",
        "| Section | Check | Result | Detail |",
        "|---|---|---|---|",
    ]
    lines += [f"| {c.section} | {c.name} | {icon[c.ok]} | {c.detail} |" for c in res]
    lines += ["", "Phase 2 is complete when every check passes with `--live`. Fix ❌ rows top to bottom."]
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text("\n".join(lines) + "\n")
    return passed, len(scored)


def record_in_graph(passed: int, total: int, live: bool) -> None:
    rows = [json.loads(line) for line in GRAPH.read_text().splitlines() if line.strip()]
    for o in rows:
        if o.get("type") == "entity" and o["name"] == "T-29":
            o["observations"] = [x for x in o["observations"] if not x.startswith("check:")]
            o["observations"].append(f"check: {passed}/{total}{' live' if live else ''} on {dt.date.today()}")
            if live and passed == total:
                o["observations"] = [x for x in o["observations"] if not x.startswith("status:")] + ["status: done"]
    GRAPH.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in rows))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="connect MCP servers and run live workflow tests")
    ap.add_argument("--no-run", action="store_true", help="skip running the test suite and linter")
    a = ap.parse_args()
    res = checks(a.live, not a.no_run)
    passed, total = write_status(res, a.live)
    record_in_graph(passed, total, a.live)
    width = max(len(c.name) for c in res)
    for c in res:
        print(f"{ {True: 'PASS', False: 'FAIL', None: 'SKIP'}[c.ok]:4}  {c.name:<{width}}  {c.detail}")
    print(f"\n{passed}/{total} checks passed — wrote {STATUS.relative_to(ROOT)}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
