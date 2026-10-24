#!/usr/bin/env python3
"""Seed the project knowledge graph (memory/project-graph.jsonl).

The file uses the JSONL format of the MCP memory server
(@modelcontextprotocol/server-memory): one JSON object per line, either
  {"type":"entity","name":...,"entityType":...,"observations":[...]}
  {"type":"relation","from":...,"to":...,"relationType":...}

Run once at project start:  python scripts/seed_graph.py --force
After that, update the graph through the MCP tools (or by hand) and run
scripts/progress.py to regenerate PROGRESS.md.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPH = ROOT / "memory" / "project-graph.jsonl"

PHASES = [
    ("Phase 0", "Setup + accounts", "2026-10-24..2026-10-25", "G0: both run make dev"),
    ("Phase 1", "Voice loop + supervisor", "2026-10-25..2026-10-27", "G1: Hindi answer < 2 s"),
    ("Phase 2", "Core tools + dashboard v1", "2026-10-28..2026-10-31", "G2: demo steps 1+3; scope freeze"),
    ("Phase 3", "Caller + Meeting", "2026-11-01..2026-11-04", "G3: demo steps 1-3"),
    ("Phase 4", "Coder + Screen + Browser", "2026-11-03..2026-11-06", "G4: demo step 4"),
    ("Phase 5", "Safety, polish, languages, evals", "2026-11-05..2026-11-07", "G5: demo 10/10"),
    ("Phase 6", "Demo, post, submit", "2026-11-08..2026-11-10", "Submitted by 10 Nov 23:59 IST"),
]

# (id, phase, owner, title, component, depends_on)
TASKS = [
    ("T-01", "Phase 0", "Shanky", "Monorepo scaffold, lint, CI", "Repo", []),
    (
        "T-02",
        "Phase 0",
        "Johny",
        "Accounts and API keys (Gnani, LiveKit, Twilio, Google, Slack, Notion, GitHub, Gemini, Mistral)",
        "Repo",
        [],
    ),
    ("T-03", "Phase 0", "Shanky", "docker-compose: postgres, redis, vexa, langfuse", "Infra", ["T-01"]),
    ("T-04", "Phase 0", "Johny", "Project graph + claude-mem setup", "Repo", []),
    ("T-05", "Phase 0", "Both", "Agree shared schemas", "Shared schemas", ["T-01"]),
    ("T-10", "Phase 1", "Johny", "LiveKit worker with Gnani Prisma STT", "Voice loop", ["T-02", "T-05"]),
    ("T-11", "Phase 1", "Johny", "Gnani Timbre TTS adapter with barge-in", "Voice loop", ["T-10"]),
    ("T-12", "Phase 1", "Johny", "VAD/turn tuning + latency metrics", "Voice loop", ["T-11"]),
    ("T-13", "Phase 1", "Shanky", "LLM router v1 (Gemini, Mistral, fallback)", "LLM router", ["T-01"]),
    ("T-14", "Phase 1", "Shanky", "Supervisor LangGraph v1 + fast ack", "Supervisor", ["T-13"]),
    ("T-15", "Phase 1", "Johny", "Web dashboard v0 (PTT + transcript)", "Web dashboard", ["T-10"]),
    ("T-16", "Phase 1", "Shanky", "API v0: auth, LiveKit token, sessions", "Backend API", ["T-03"]),
    ("T-20", "Phase 2", "Shanky", "MCP gateway v1 + audit events", "MCP gateway", ["T-14", "T-16"]),
    ("T-21", "Phase 2", "Shanky", "Permission tiers + approval flow", "MCP gateway", ["T-20"]),
    ("T-22", "Phase 2", "Shanky", "Google OAuth + Calendar specialist", "Specialists", ["T-20"]),
    ("T-23", "Phase 2", "Shanky", "Slack + Notion specialists", "Specialists", ["T-20"]),
    ("T-24", "Phase 2", "Shanky", "Maps tools: places, ETA, share pin", "Specialists", ["T-20"]),
    ("T-25", "Phase 2", "Johny", "Dashboard v1: timeline, approvals, connections", "Web dashboard", ["T-15", "T-21"]),
    ("T-26", "Phase 2", "Johny", "Voice approvals (haan/nahi)", "Voice loop", ["T-21"]),
    ("T-27", "Phase 2", "Both", "Eval set v1 (60 utterances)", "Evals", ["T-14"]),
    ("T-30", "Phase 3", "Johny", "Twilio SIP trunk to LiveKit", "Telephony", ["T-02"]),
    ("T-31", "Phase 3", "Johny", "Caller agent (8 kHz, disclosure, booking)", "Telephony", ["T-30", "T-11"]),
    ("T-32", "Phase 3", "Johny", "call_tool MCP server", "Telephony", ["T-31", "T-20"]),
    ("T-33", "Phase 3", "Shanky", "Vexa setup + meeting.join", "Meeting pipeline", ["T-03"]),
    ("T-34", "Phase 3", "Johny", "Gnani batch STT for recordings", "Meeting pipeline", ["T-33"]),
    ("T-35", "Phase 3", "Shanky", "Minutes generator to Notion + Slack", "Meeting pipeline", ["T-34", "T-23"]),
    ("T-40", "Phase 4", "Shanky", "Docker sandbox runner", "Coder", ["T-03"]),
    ("T-41", "Phase 4", "Shanky", "Coder specialist: patch, test, draft PR", "Coder", ["T-40", "T-20"]),
    ("T-42", "Phase 4", "Johny", "Tauri desktop companion + hotkey PTT", "Desktop companion", ["T-15"]),
    ("T-43", "Phase 4", "Johny", "Screen capture + screen_tool bridge", "Desktop companion", ["T-42", "T-20"]),
    ("T-44", "Phase 4", "Shanky", "Playwright browser MCP with Tier A", "Browser", ["T-21"]),
    ("T-50", "Phase 5", "Johny", "Fallback STT/TTS for non-Gnani languages", "Voice loop", ["T-12"]),
    ("T-51", "Phase 5", "Shanky", "Undo for Tier W actions", "MCP gateway", ["T-21"]),
    ("T-52", "Phase 5", "Shanky", "Prompt-injection guard + tests", "MCP gateway", ["T-21"]),
    ("T-53", "Phase 5", "Johny", "Dashboard polish + mobile", "Web dashboard", ["T-25"]),
    ("T-54", "Phase 5", "Both", "Eval run v2 + latency pass", "Evals", ["T-27"]),
    ("T-55", "Phase 5", "Shanky", "Stretch pick (memory / briefing / Gmail)", "Specialists", ["T-54"]),
    ("T-60", "Phase 6", "Johny", "Record 60 s demo video", "Demo", ["T-54"]),
    ("T-61", "Phase 6", "Shanky", "Written explanation + contributions", "Demo", ["T-54"]),
    ("T-62", "Phase 6", "Both", "Post on LinkedIn and X with tags", "Demo", ["T-60"]),
    ("T-63", "Phase 6", "Both", "Submit form with post links", "Demo", ["T-61", "T-62"]),
]

DECISIONS = [
    ("D-003", "LiveKit Agents over Pipecat", "Voice loop"),
    ("D-005", "Gemini + Mistral + Codestral router on free tiers", "LLM router"),
    ("D-008", "Twilio trial via LiveKit SIP", "Telephony"),
    ("D-009", "Tauri desktop companion + Playwright browser", "Desktop companion"),
    ("D-011", "Gnani + faster-whisper fallback for other languages", "Voice loop"),
    ("D-016", "Permission tiers R/W/A in gateway", "MCP gateway"),
    ("D-017", "Progress tracked in MCP memory graph + claude-mem", "Repo"),
]

RISKS = [
    ("R-01", "Scope too wide", "Scope freeze 31 Oct; cut list in roadmap"),
    ("R-02", "Twilio trial limits", "Verify team phones; trial message accepted"),
    ("R-03", "Gnani STT finals only", "Tight VAD + fast ack"),
    ("R-04", "Free-tier LLM rate limits", "Router fallback chain"),
    ("R-05", "Meeting bot admission", "Admit manually; synthetic recording fallback"),
]


def build() -> list[dict]:
    lines: list[dict] = []
    ent = lambda name, typ, obs: lines.append({"type": "entity", "name": name, "entityType": typ, "observations": obs})
    rel = lambda a, b, r: lines.append({"type": "relation", "from": a, "to": b, "relationType": r})

    ent("Rex", "Project", ["goal: multilingual voice operator on Gnani STT/TTS", "deadline: 2026-11-10 23:59 IST"])
    ent("Johny", "Person", ["role: voice, telephony, desktop, frontend"])
    ent("Shanky", "Person", ["role: orchestrator, MCP tools, backend, coder"])
    rel("Johny", "Rex", "member_of")
    rel("Shanky", "Rex", "member_of")

    for name, title, window, gate in PHASES:
        ent(name, "Phase", [f"title: {title}", f"window: {window}", f"gate: {gate}"])
        rel(name, "Rex", "part_of")

    components = sorted({t[4] for t in TASKS})
    for c in components:
        ent(c, "Component", [])
        rel(c, "Rex", "part_of")

    for tid, phase, owner, title, comp, deps in TASKS:
        ent(tid, "Task", [f"title: {title}", "status: todo"])
        rel(tid, phase, "part_of")
        rel(tid, comp, "builds")
        owners = ["Johny", "Shanky"] if owner == "Both" else [owner]
        for o in owners:
            rel(o, tid, "owns")
        for d in deps:
            rel(tid, d, "depends_on")

    for did, summary, comp in DECISIONS:
        ent(did, "Decision", [f"summary: {summary}", "date: 2026-10-24"])
        rel(did, comp, "affects")

    for rid, title, mitigation in RISKS:
        ent(rid, "Risk", [f"title: {title}", f"mitigation: {mitigation}", "status: open"])
        rel(rid, "Rex", "threatens")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite an existing graph")
    args = ap.parse_args()
    if GRAPH.exists() and not args.force:
        raise SystemExit(f"{GRAPH} exists; use --force to overwrite")
    GRAPH.parent.mkdir(parents=True, exist_ok=True)
    with GRAPH.open("w", encoding="utf-8") as f:
        for obj in build():
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print(f"wrote {GRAPH}")


if __name__ == "__main__":
    main()
