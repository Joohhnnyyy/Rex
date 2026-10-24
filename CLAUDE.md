# CLAUDE.md

Claude Code reads this file automatically. Follow [AGENTS.md](AGENTS.md) for all general rules; this file adds Claude-specific setup and the **progress protocol**.

## Project in one line

Rex: a multilingual voice operator (Gnani STT/TTS + Gemini/Mistral/Codestral + MCP tools). Team: Johny (voice, telephony, desktop, frontend) and Shanky (orchestrator, tools, backend, coder). Deadline 10 Nov 2026 23:59 IST.

## Memory setup (do once per machine)

We use **two complementary memories**:

| Memory | What it holds | Scope |
|---|---|---|
| **Project graph** — MCP `memory` server (knowledge graph, JSONL in git) | Phases, tasks, owners, status, dependencies, decisions, blockers | Shared by both teammates via git |
| **claude-mem** plugin | Automatic per-session observations: what Claude did, files touched, debugging steps | Local to each machine; searchable across sessions |

### 1. Project graph (shared, in git)

Copy the template once: `cp mcp.json.example .mcp.json` (it registers the server):

```json
{ "mcpServers": { "project-graph": {
  "command": "sh",
  "args": ["-c", "MEMORY_FILE_PATH=\"$PWD/memory/project-graph.jsonl\" exec npx -y @modelcontextprotocol/server-memory"] } } }
```

The `sh -c` wrapper makes the path absolute: the memory server resolves a *relative* `MEMORY_FILE_PATH` against its own package folder, not the repo (verified 24 Oct 2026). Start Claude Code from the repo root.

Approve the server when Claude Code asks. Tools available: `read_graph`, `search_nodes`, `open_nodes`, `create_entities`, `create_relations`, `add_observations`, `delete_observations`, …

### 2. claude-mem (personal, automatic)

```bash
# inside Claude Code
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
# restart Claude Code
```

claude-mem hooks into SessionStart / PostToolUse / Stop etc., stores compressed observations in local SQLite + Chroma, and exposes `search`, `timeline` and `get_observations` MCP tools. Its viewer URL is printed when the worker starts (`/viewer`). Requires Node ≥ 20.

## Progress protocol (every session)

**At session start**
1. `open_nodes(["Rex"])` and `search_nodes("<your T-xx>")` to load current state.
2. Read the top entry of HANDOFF.md.
3. Use claude-mem `search` for the task ID to recall earlier attempts.

**When you start a task**
- `add_observations` on the task entity: `"status: in_progress"`, `"started: 2026-10-27 (Johny)"`.

**When you finish / block**
- Replace the status: `delete_observations` old `status: …` → `add_observations` `"status: done"` (or `"status: blocked — <reason>"`).
- Add evidence: `"pr: #12"`, `"note: p50 latency 1.4 s"`.
- New dependency discovered? `create_relations` `{from: "T-31", to: "T-30", relationType: "depends_on"}`.
- New decision? `create_entities` type `Decision` + relation `decided_in` → phase, and add a line to DECISION_LOG.md.
- Run `python scripts/progress.py` and commit `memory/project-graph.jsonl` + `PROGRESS.md` together.

### Graph schema

| Entity type | Name pattern | Observations used |
|---|---|---|
| `Project` | `Rex` | deadline, goal |
| `Person` | `Johny`, `Shanky` | role, tracks |
| `Phase` | `Phase 0` … `Phase 6` | `window: 2026-10-25..2026-10-27`, `gate: …` |
| `Task` | `T-10` … | `title: …`, `status: todo|in_progress|blocked|done`, `pr: …`, notes |
| `Component` | `Voice loop`, `MCP gateway`, … | path, owner |
| `Decision` | `D-001` … | summary, date |
| `Risk` | `R-01` … | mitigation, status |

| Relation | Meaning |
|---|---|
| `Task part_of Phase` | grouping |
| `Person owns Task` / `Person owns Component` | ownership |
| `Task depends_on Task` | ordering |
| `Task builds Component` | traceability |
| `Phase part_of Project` | hierarchy |
| `Decision affects Component` | rationale |

Keep observation strings short and prefixed (`status:`, `pr:`, `note:`, `blocked:`) — `scripts/progress.py` parses them.

## Workflow plugins (install once per machine, inside Claude Code)

| Plugin | Install | How we use it |
|---|---|---|
| **Superpowers** | `/plugin install superpowers@claude-plugins-official` (or `/plugin marketplace add obra/superpowers-marketplace` then `/plugin install superpowers@superpowers-marketplace`) | brainstorming → writing-plans → test-driven-development → requesting-code-review → verification-before-completion. Design docs go in `docs/plans/`. |
| **GSD (Get Shit Done)** | `npx get-shit-done-cc@latest` | Phase loop on `.planning/`: `/gsd:discuss-phase N` → `/gsd:plan-phase N` → `/gsd:execute-phase N` → `/gsd:verify-work N`. `.planning/` is already seeded (PROJECT, REQUIREMENTS, ROADMAP, STATE, phase 00). If GSD asks for config, run its settings command; don't re-run new-project. |
| **claude-mem** | see above | automatic session memory |

Phase numbering: GSD phase `NN` = roadmap "Phase N". After each GSD execute/verify, also update the project graph and run `python scripts/progress.py`.

## Claude-specific tips

- Use subagents for broad codebase searches; keep the main context for the task.
- Before editing a file owned by the other teammate's track, add a note to HANDOFF.md.
- Prefer `make check` over running individual linters.
- Never paste API keys into chat or files; reference `settings.*`.
