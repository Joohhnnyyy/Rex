# MCP Connection Guide

How Rex connects to tools. Owner: **Shanky** (gateway); Johny owns `call_tool` and `screen_tool` servers.

## 1. Two kinds of MCP in this repo

| Kind | Used by | Config |
|---|---|---|
| **Runtime MCP** — tools Rex uses for users | `packages/mcp_gateway` | `infra/mcp_servers.yaml` |
| **Dev MCP** — tools that help *us* build (project graph, GitHub) | Claude Code / IDE agents | `.mcp.json` (see CLAUDE.md) |

Don't mix them: runtime servers get per-user OAuth tokens; dev servers use your own credentials.

## 2. Runtime server registry — `infra/mcp_servers.yaml`

```yaml
servers:
  google_workspace:
    transport: stdio
    command: ["uvx", "workspace-mcp"]          # Google Workspace MCP (verify package name at setup)
    auth: oauth:google
    tools:
      calendar.freebusy:        { tier: R }
      calendar.create_event:    { tier: W, undo: calendar.delete_event }
      calendar.update_event:    { tier: W }
      calendar.delete_event:    { tier: A }
      gmail.send:               { tier: A }
  slack:
    transport: stdio
    command: ["npx", "-y", "@zencoderai/slack-mcp-server"]
    auth: env:SLACK_BOT_TOKEN
    tools:
      slack.list_channels:      { tier: R }
      slack.get_channel_history:{ tier: R }
      slack.post_message:       { tier: A }    # posts to others
  notion:
    transport: stdio
    command: ["npx", "-y", "@notionhq/notion-mcp-server"]   # verify at setup
    auth: oauth:notion
    default_tier: W
  maps:
    transport: http
    url: ${MAPS_MCP_URL}                        # Google Maps Grounding Lite or archived ref server
    auth: env:GOOGLE_MAPS_API_KEY
    default_tier: R
  github:
    transport: http
    url: https://api.githubcopilot.com/mcp/     # GitHub's hosted MCP (verify) or local github-mcp-server
    auth: env:GITHUB_TOKEN
    tools:
      github.create_pull_request: { tier: W }
      github.merge_pull_request:  { tier: A }
    default_tier: R
  sandbox:   { transport: stdio, command: ["python", "-m", "mcp_servers.sandbox"], default_tier: W }
  call_tool: { transport: stdio, command: ["python", "-m", "mcp_servers.call_tool"], default_tier: A }
  screen_tool: { transport: ws, url: "wss://desktop-bridge/{device_id}", default_tier: R }
  playwright:
    transport: stdio
    command: ["npx", "-y", "@playwright/mcp@latest", "--isolated"]
    tools: { browser_click: { tier: A }, browser_type: { tier: A } }
    default_tier: R
  vexa:      { transport: http, url: "${VEXA_URL}/mcp", auth: env:VEXA_API_KEY, default_tier: W }
  minutes:   { transport: stdio, command: ["python", "-m", "mcp_servers.minutes"], default_tier: W }
  approval_tool: { transport: stdio, command: ["python", "-m", "mcp_servers.approval_tool"], default_tier: R }
  search:
    transport: stdio
    command: ["npx", "-y", "@brave/brave-search-mcp-server"]
    auth: env:BRAVE_API_KEY
    default_tier: R
```

Package names marked "verify" must be confirmed during T-20; record the final choice in DECISION_LOG.md.

## 3. Gateway internals

```
specialist ──call("slack.post_message", args)──► Gateway
   1. resolve server + tool, check specialist allow-list
   2. tier = override ∨ declared ∨ "A"
   3. tier A → approval_tool.request() → wait (30 s)
   4. inject auth (OAuth token from DB / env)
   5. call with timeout (default 20 s), 1 retry on transient errors
   6. redact args/result → write action_event (+ undo spec)
   7. publish timeline event → return result (wrapped as untrusted data)
```

Python sketch:

```python
class Gateway:
    async def call(self, user: User, specialist: str, tool: str, args: dict) -> ToolResult:
        spec = self.registry.resolve(tool)
        self.policy.check_allowlist(specialist, tool)
        tier = self.policy.tier_for(user, spec)
        event = await self.events.start(user, tool, tier, args)
        if tier == "A":
            await self.approvals.require(user, event, timeout=30)
        session = await self.pool.session(spec.server, auth=await self.auth.for_(user, spec))
        result = await with_retry(lambda: session.call_tool(spec.name, args), timeout=spec.timeout)
        await self.events.finish(event, result, undo=spec.undo_for(result))
        return wrap_untrusted(result)
```

Connections are pooled per (server, user) for stdio servers that need per-user tokens; shared for env-auth servers.

## 4. Writing our own MCP server

Template (`packages/mcp_servers/_template/server.py`):

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("call_tool")

@mcp.tool()
async def start_call(to: str, goal: str, constraints: dict, lang: str = "hi-IN") -> dict:
    """Place an outbound call via LiveKit SIP + Twilio and return a CallOutcome."""
    ...

if __name__ == "__main__":
    mcp.run()          # stdio
```

Checklist: docstring per tool (the LLM reads it) · Pydantic-typed args · tier declared in yaml · unit test with the MCP in-memory client · no secrets in return values.

## 5. Adding a new skill (e.g. Jira) in 5 steps

1. Find a server in the MCP Registry (`registry.modelcontextprotocol.io`).
2. Add it to `mcp_servers.yaml` with tiers (default A until reviewed).
3. Add auth (env or OAuth provider in `connections`).
4. Add it to one specialist's allow-list (or create a specialist).
5. Add 3 eval utterances; run `make eval`.

## 6. Dev MCP (`.mcp.json`, created with `cp mcp.json.example .mcp.json`)

```json
{ "mcpServers": { "project-graph": {
  "command": "sh",
  "args": ["-c", "MEMORY_FILE_PATH=\"$PWD/memory/project-graph.jsonl\" exec npx -y @modelcontextprotocol/server-memory"] } } }
```

The `sh -c` wrapper makes the path absolute: the memory server resolves a *relative* `MEMORY_FILE_PATH` against its own package folder, not the repo (verified 24 Oct 2026). Start Claude Code from the repo root.

Plus claude-mem as a Claude Code plugin (see CLAUDE.md). Optional: add GitHub's MCP server with your own PAT for PR/issue work.

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| Tool missing from `/v1/tools` | Server failed to start — check gateway logs for its stderr |
| `ApprovalTimeout` in demo | Dashboard SSE not connected; or speak "haan" within 30 s |
| 401 from Google | Token expired — refresh failed; reconnect in Connections |
| stdio server hangs | Server printing to stdout; logs must go to stderr |
