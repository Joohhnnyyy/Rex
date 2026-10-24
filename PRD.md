# Product Requirements Document — Rex

| Field | Value |
|---|---|
| Owner | Johny (product + voice), Shanky (platform) |
| Status | Approved for build — 24 Oct 2026 |
| Target | Hackathon submission 10 Nov 2026 |

## 1. Problem

People in India manage work across many apps and many languages. Existing assistants answer questions but rarely *act*, struggle with code-mixed speech, and cannot make phone calls on the user's behalf in Indian languages.

## 2. Goals and non-goals

**Goals**

- G1. One voice interface that understands code-mixed and Indian-language speech and replies in the same language.
- G2. Completes real multi-step tasks across ≥ 6 tools in one conversation.
- G3. Makes an outbound phone call, holds a short conversation and reports the outcome.
- G4. Turns a meeting into minutes + action items filed to Notion and Slack.
- G5. Never performs an external or irreversible action without explicit confirmation.

**Non-goals (for the hackathon)**

- Mobile app; multi-tenant billing; inbound call centre at scale; payments; fine-tuning models.

## 3. Success metrics

| Metric | Target |
|---|---|
| Voice turn latency (end of speech → first audio) | p50 ≤ 1.3 s, p90 ≤ 2.0 s |
| Intent → correct specialist routing (eval set of 60 Hinglish/regional commands) | ≥ 90 % |
| Tool-call success on the demo script | 10/10 runs |
| Languages demonstrated live | ≥ 3 (Hinglish, one South Indian, one other) |
| Unconfirmed Act-tier actions | 0 |

## 4. Users and jobs-to-be-done

| Persona | Job | Example utterance |
|---|---|---|
| Riya (student) | "Don't let me lose what was decided in meetings" | "Is meeting ke minutes Notion mein daalo aur team ko bhejo" |
| Arjun (freelancer) | "Fix small bugs and keep clients updated without context-switching" | "Login wala bug fix karke PR banao, phir client ko Slack karo" |
| Meena (salon owner) | "Call people for me in Kannada" | "Supplier-ge call maadi, naale 10 gantege delivery confirm maadi" |

## 5. Functional requirements

| ID | Requirement | Priority | Owner |
|---|---|---|---|
| F1 | Streaming voice loop with barge-in, VAD and turn detection | MVP | Johny |
| F2 | Language detection per turn; reply in detected language; fallback STT/TTS for languages Gnani lacks | MVP | Johny |
| F3 | Supervisor routes to specialists; fast acknowledgement for long tasks | MVP | Shanky |
| F4 | Calendar: free/busy, create, move, cancel, invite | MVP | Shanky |
| F5 | Slack: read channel, summarise, post, DM | MVP | Shanky |
| F6 | Notion: create page, append blocks, search | MVP | Shanky |
| F7 | Maps: place search, directions + ETA, share pin | MVP | Shanky |
| F8 | Caller: outbound Twilio call with goal, script and outcome report | MVP | Johny |
| F9 | Meeting: bot joins, records; batch STT; minutes + action items | MVP | Shanky (pipeline), Johny (STT) |
| F10 | Coder: clone repo into sandbox, edit, run tests, open PR | MVP | Shanky |
| F11 | Screen: capture + explain on request (desktop companion) | MVP | Johny |
| F12 | Browser control via Playwright with approval | MVP | Shanky |
| F13 | Approval gate (voice "haan" / dashboard button) for Tier A | MVP | Shanky (logic), Johny (UI) |
| F14 | Dashboard: live transcript, timeline, approvals, settings | MVP | Johny |
| F15 | Long-term memory of people, preferences, decisions | Stretch | Shanky |
| F16 | Morning briefing | Stretch | Shanky |
| F17 | Gmail read/draft/send | Stretch | Shanky |
| F18 | Inbound receptionist on the Twilio number | Stretch | Johny |
| F19 | Skill store (enable MCP servers from config/registry) | Stretch | Shanky |
| F20 | WhatsApp, voice cloning, proactive nudges, full computer use | Later | — |

## 6. Non-functional requirements

- **Latency**: see metrics; long tasks must speak an ack within 800 ms.
- **Reliability**: every tool call has a timeout (default 20 s) and one retry; failures are spoken plainly.
- **Privacy**: screen capture opt-in per session; screenshots never leave the machine except the cropped region sent to the LLM; tokens encrypted at rest.
- **Honesty**: Rex always identifies itself as an AI on calls and in meetings.
- **Cost**: stay inside free tiers; cache fixed TTS phrases.

## 7. The demo story (acceptance test)

1. "Rex, aaj ki standup ke minutes Notion mein daalo aur team ko Slack karo." → Notion page + Slack post.
2. "Dentist ko call karke Saturday shaam ka slot book karo." → live Twilio call (teammate plays the clinic).
3. Slot lands on Google Calendar; clinic location + ETA shared on Slack.
4. User points at an error: "Ye kya hai? Fix karo." → screen explained; Coder opens a PR; approval asked before merge.
5. "Aaj ka summary batao" → spoken recap; timeline shows all actions.

The build is "done" when this runs 10/10 times end to end.

## 8. Open questions

- Fallback TTS for non-Gnani languages: Piper vs. an API? (decide by 1 Nov — see DECISIONS.md D-012)
- Self-host Vexa or use the hosted token? (decide by 30 Oct)
