#!/usr/bin/env python3
"""Live smoke test for the LLM router (uses real API keys from the environment / .env).

uv run --env-file .env python scripts/llm_smoke.py supervise "Kal ka weather kaisa rahega?"
"""

import asyncio
import sys

from rex_llm_router import AllModelsFailed, LLMClient


async def main(task: str, prompt: str) -> None:
    try:
        res = await LLMClient().complete(task, [{"role": "user", "content": prompt}])
    except AllModelsFailed as exc:
        print("FAILED:", exc)
        raise SystemExit(1) from exc
    for a in res.attempts:
        print(f"  {a.model.alias:16} {a.outcome:13} {a.ms} ms {a.detail}")
    print(f"\n[{res.model.alias} / {res.model.name}]\n{res.text}")


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "supervise"
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Namaste! Reply in one short Hinglish sentence."
    asyncio.run(main(task, prompt))
