#!/usr/bin/env python3
"""Run routing evaluation set against Rex.

Usage:
    uv run --env-file .env python scripts/run_evals.py
    uv run --env-file .env python scripts/run_evals.py --limit 10
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
from pathlib import Path

import yaml
from livekit.agents import AgentSession

from rex_agent.config import AgentConfig
from rex_agent.main import Rex, load_runtime_registry
from rex_agent.models import build_llm
from rex_agent.tools_bridge import build_tools
from rex_mcp_gateway.gateway import Gateway
from rex_shared.schemas import ActionEvent

ROOT = Path(__file__).resolve().parent.parent
EVALS_FILE = ROOT / "evals" / "routing.yaml"
RESULTS_FILE = ROOT / "evals" / "RESULTS.md"


def load_cases(limit: int | None = None) -> list[dict]:
    data = yaml.safe_load(EVALS_FILE.read_text()) or []
    if limit:
        return data[:limit]
    return data


async def evaluate_case(case: dict, gw: Gateway, tools: list, llm: object, events: list[ActionEvent]) -> dict:
    utterance = case["utterance"]
    expect_tool = case.get("expect_tool", "none")
    actual_tool = "none"

    try:
        events.clear()
        async with AgentSession(llm=llm) as session:
            await session.start(Rex(AgentConfig.from_env(), gateway=gw, tools=tools))
            result = await session.run(user_input=utterance)
            # Find function call in expectations or events
            for exp in result.expect:
                ev = exp.event()
                if hasattr(ev, "item") and getattr(ev.item, "type", None) == "function_call":
                    actual_tool = getattr(ev.item, "name", "none")
                    break
            if actual_tool == "none" and events:
                actual_tool = events[0].tool.replace(".", "__")

        matched = actual_tool == expect_tool
    except Exception as exc:
        matched = False
        actual_tool = f"ERROR: {exc}"

    return {
        "utterance": utterance,
        "expect": expect_tool,
        "actual": actual_tool,
        "ok": matched,
    }


async def main_async(limit: int | None):
    cases = load_cases(limit)
    print(f"Running evaluation on {len(cases)} cases...")

    results = []
    correct = 0

    events: list[ActionEvent] = []

    async def sink(ev: ActionEvent) -> None:
        events.append(ev)

    async with Gateway(load_runtime_registry(), on_event=sink) as gw:
        tools = await build_tools(gw, "rex")
        llm = build_llm()

        for i, case in enumerate(cases, 1):
            r = await evaluate_case(case, gw, tools, llm, events)
            results.append(r)
            if r["ok"]:
                correct += 1
                print(f"[{i}/{len(cases)}] PASS: {r['utterance'][:40]} -> {r['actual']}")
            else:
                print(f"[{i}/{len(cases)}] FAIL: {r['utterance'][:40]} -> got {r['actual']}, expected {r['expect']}")

    total = len(results)
    pct = round(100 * correct / total, 1) if total else 0
    print(f"\nFinal Score: {correct}/{total} ({pct}%)")

    # Write RESULTS.md
    lines = [
        "# Evaluation Results — Routing",
        "",
        f"_Run on {dt.datetime.now(dt.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}_",
        "",
        f"**Accuracy:** {correct}/{total} ({pct}%)",
        "",
        "| # | Utterance | Expected | Actual | Result |",
        "|---|---|---|---|---|",
    ]
    for idx, r in enumerate(results, 1):
        icon = "PASS" if r["ok"] else "FAIL"
        lines.append(f"| {idx} | {r['utterance']} | `{r['expect']}` | `{r['actual']}` | {icon} |")

    RESULTS_FILE.write_text("\n".join(lines) + "\n")
    print(f"Wrote {RESULTS_FILE.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Limit number of eval cases to run")
    args = parser.parse_args()
    asyncio.run(main_async(args.limit))


if __name__ == "__main__":
    main()
