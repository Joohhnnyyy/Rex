# Rex foundation — design (Superpowers brainstorming output)

Date: 2026-10-24 · Status: approved (Johny) · Next: `.planning/phases/00-foundation/00-01-PLAN.md`

## Problem
Two people must build voice, tools and backend in parallel from day 1 without stepping on each other. They need: one install command, shared data contracts both sides trust, and a model layer that survives free-tier rate limits.

## Options considered

| Topic | Options | Chosen | Why |
|---|---|---|---|
| Repo shape | polyrepo · monorepo | Monorepo (uv workspace + pnpm later) | One PR can change a contract and both sides |
| Contracts | ad-hoc dicts · Pydantic · protobuf | Pydantic v2 | Validation + JSON + TS generation; same language as backend/agent |
| LLM access | vendor SDKs · LiteLLM · own thin client | Own thin OpenAI-compatible client | Gemini, Mistral and OpenRouter all expose OpenAI-compatible chat APIs; ~150 lines, no heavy deps, fully testable offline |
| Fallback | none · retry same · chain per task | Chain per task kind | Free tiers hit 429s; the voice loop can't stall |

## Model chains (initial — tune after evals)

| Task kind | Chain |
|---|---|
| supervise | gemini-flash → mistral-small → openrouter-free |
| summarise | mistral-small → gemini-flash |
| code | codestral → gemini-flash |
| vision | gemini-flash |

Model IDs are config (env-overridable), because free-tier model names change.

## Error policy
429 / 5xx / timeout / connection error → next model. Other 4xx → raise (our bug). Missing key → skip that provider. All failed → `AllModelsFailed` with attempts, so the voice layer can say "I'm having trouble thinking right now, let me try again."

## Testing
All provider calls go through an injectable `httpx` transport → tests use `MockTransport`; zero network in CI.
