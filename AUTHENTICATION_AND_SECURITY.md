# Authentication and Security

Owner: **Shanky** (backend, gateway) · **Johny** (desktop, client storage). An agent that can call people, post messages and see your screen must be safe by construction.

## 1. Identity

| Who | How |
|---|---|
| Web user | Magic-link email → short-lived session JWT (15 min) + httpOnly refresh cookie (7 days) |
| Desktop companion | Device-code pairing from the logged-in dashboard → device token (hashed in DB, revocable) stored in OS keychain |
| Agent worker / job worker | Service credentials from `.env`; act on behalf of a user only with that user's `user_id` from the LiveKit room metadata (signed by our API) |
| LiveKit | Room tokens minted by `/v1/livekit/token`, 1-hour TTL, room scoped to the user |
| Webhooks | Twilio `X-Twilio-Signature` validation; Vexa shared-secret HMAC |

## 2. Third-party tokens

- OAuth (Google, Slack, Notion, GitHub) with **minimum scopes**:
  - Google: `calendar.events`, `calendar.freebusy` (+ `gmail.compose` only if F17 ships)
  - Slack bot: `chat:write`, `channels:history`, `channels:read`, `users:read`
  - Notion: integration limited to shared pages
  - GitHub: fine-grained PAT / app on the demo repo only (`contents:write`, `pull_requests:write`)
- Stored encrypted (AES-256-GCM, key `TOKEN_ENC_KEY` from env; rotate by re-encrypt script).
- Tokens are injected by the **gateway** at call time; they never enter an LLM prompt or a log.

## 3. Permission tiers (enforced in the gateway)

| Tier | Meaning | Examples | Behaviour |
|---|---|---|---|
| **R** Read | No side effects | calendar.freebusy, slack.read, screen.describe, github.search | Runs; logged |
| **W** Write, reversible | Side effect with an undo | calendar.create_event, notion.create_page, github.open_draft_pr, slack.post to *self* | Runs; announced; undo offered for 10 min |
| **A** Act, external/irreversible | Affects other people or can't be undone | call_tool.start_call, slack.post to channel/others, gmail.send, github.merge, playwright.submit, desktop click | **Requires explicit approval** each time (voice "haan" or dashboard), 30 s expiry |

- Every MCP tool must declare a tier in `mcp_servers.yaml`; unknown tools default to **A**.
- Users can make a tier stricter, never looser.
- Approval prompts restate the exact action in the user's language: *"Shanky ko #general mein ye message bhejoon: '…'?"*

## 4. Prompt-injection defence

- Content from tools (emails, Slack, web pages, screen OCR, meeting transcripts) is wrapped as `<untrusted_data source="…">…</untrusted_data>` and the system prompt says it is data, never instructions.
- Specialists cannot call tools outside their allow-list.
- Tier A cannot be triggered by tool output alone: the approval UI shows the originating user utterance; if none exists (e.g. an instruction found inside an email) the request is auto-denied and flagged.
- Test suite `evals/injection/` covers: "ignore previous instructions" in Slack, malicious web page in browser, fake instruction in meeting transcript.

## 5. Screen and audio privacy

- Screen capture only on explicit request or visible "watch mode" (tray icon turns red + on-screen badge).
- Capture the active window or a selected region, not all monitors. Prefer accessibility text over pixels.
- Screenshots kept in memory, discarded after the turn; never written to DB.
- Mic is push-to-talk by default; wake word optional and local.

## 6. Calls and meetings — honesty rules

- Every outbound call starts with: *"Hello, this is Rex, {user}'s AI assistant, calling on their behalf."* (English by default; switches to the callee's language if they reply in it). Never claim to be human.
- Call recording **off** by default; transcripts kept for outcome only.
- Meeting bot joins only meetings the user owns or is invited to, and announces recording in chat.
- Trial-phase constraint: only verified test numbers (team phones). **No real third-party numbers** (contest rule: synthetic data only).

## 7. Sandbox (Coder)

- Ephemeral Docker container per job; non-root; read-only base image; CPU 2 / RAM 2 GB / 10 min.
- No host mounts, no Docker socket; egress allow-list: github.com, pypi.org, registry.npmjs.org.
- Secrets: only a repo-scoped GitHub token, injected as env for the push step only.

## 8. Application security checklist

- [ ] HTTPS everywhere (Caddy), HSTS, secure cookies, CSRF protection on cookie routes
- [ ] CORS limited to dashboard origin
- [ ] Rate limiting (per user + per IP) on auth and REST
- [ ] Input validation via Pydantic on every route
- [ ] Logs redact tokens, emails, phone numbers
- [ ] `pip-audit` + `pnpm audit` in CI
- [ ] Secrets only in `.env` (git-ignored) / VM env; `gitleaks` pre-commit hook
- [ ] Delete-my-data endpoint works

## 9. Threat model (short)

| Threat | Mitigation |
|---|---|
| Stolen session | Short JWT, refresh rotation, device revoke |
| Agent spams contacts | Tier A approvals, per-tool rate limits (e.g. 5 calls/hour) |
| Prompt injection via content | Section 4 |
| Malicious code in repo run by Coder | Sandbox isolation, Section 7 |
| Token leakage via logs/LLM | Gateway-only injection + redaction |
| Voice spoofing to approve | Approvals bound to the authenticated session's room; dashboard approval for high-risk tools (merge, payments — not in scope) |
