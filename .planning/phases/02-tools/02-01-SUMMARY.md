# Summary 02-01 — MCP gateway, approvals, location tools, Actions timeline

Built 2026-10-24.

- `packages/mcp_gateway` (rex_mcp_gateway): YAML registry with `${ENV}` expansion; per-specialist allow-lists; R/W/A tiers (unknown → strictest); Tier A returns `NeedsApproval(action_id)` and runs only after `approve()`; deny/expiry; one retry; ActionEvents for every step; output wrapped in `<untrusted_data>`. Async context manager (MCP connections opened/closed in one task — anyio requirement).
- `packages/mcp_servers` (rex_mcp_servers.location): `find_place`, `travel_time`, `map_link` on OpenStreetMap; no API key. Verified live from Johny's Mac.
- `infra/mcp_servers.yaml`: runtime servers; `rex → [location]`.
- Agent: gateway tools exposed as LiveKit raw function tools with real schemas (`tools_bridge.py`); `approve_action` / `deny_action` tools; timeline events published on text-stream topic `rex.timeline`; RPC `rex.decide` for dashboard approvals; session lifetime holds the gateway open.
- Dashboard: Actions timeline (tool, tier, status, time) with Approve / Deny buttons.
- Tests: 83 Python (incl. real stdio subprocess integration), web typecheck/lint/build.

Next: Google Calendar (OAuth), Slack bot, Notion integration — just add servers to `infra/mcp_servers.yaml` with tiers.
