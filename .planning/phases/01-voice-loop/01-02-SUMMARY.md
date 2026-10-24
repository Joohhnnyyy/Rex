# Summary 01-02 — Supervisor (T-14) + dashboard v0 (T-15)

Built 2026-10-24 (Claude, TDD for Python; type-check/lint/build + headless browser check for web).

## Supervisor (`apps/agent/src/rex_agent/brain/`)
- `specialists.py`: registry of 7 specialists (calendar, comms, location, caller, meeting, coder, screen) with routing descriptions, `slow` flag and MCP tool namespaces; `NotConnected` placeholder executor.
- `acks.py`: instant acknowledgements in Hinglish / Hindi / English.
- `supervisor.py`: fast specialists run inline; slow ones speak an ack, run as background jobs and report back; executor failures become spoken failures, never crashes.
- Wired into the `Rex` agent as the `delegate_task` function tool; prompt lists specialists. Decision D-021 (no LangGraph in v1).
- 12 new tests.

## API
- Token now dispatches the `rex` agent into the room (`roomConfig.agents`). 1 new test. Agent name configurable (`REX_AGENT_NAME`, `livekit_agent_name`).

## Dashboard (`apps/web`)
- Next.js 15 + `@livekit/components-react` 2.9: start screen, state orb, bar visualiser, mic control, End, live transcript with language chips, friendly API/LiveKit errors, Rex design tokens, dark mode, mobile.
- Verified: `tsc`, `eslint`, `next build`; headless Chromium run caught and fixed a `useEffect` return bug.

## Pending live checks (Mac)
Full voice round trip in the browser; tools return "not connected yet" until Phase 02 wires the MCP gateway.
