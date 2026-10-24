# Design — UI and voice

Owner: **Johny**. Two surfaces: what users *hear* and what they *see*.

## 1. Voice design

### Persona
Rex is a calm, warm, efficient helper — like a capable friend, not a call-centre bot. Short sentences. Mirrors the user's language and code-mixing level.

### Rules
| Rule | Example |
|---|---|
| Acknowledge within 800 ms for slow work | "Theek hai, dentist ko call kar raha hoon." |
| Lead with the outcome | "Ho gaya — Saturday 6 baje ka slot mila." (not "I called the clinic and…") |
| ≤ 2 sentences per reply unless asked | |
| Confirm Tier A actions by restating them | "Shanky ko #general mein 'standup 10 baje' bhejoon?" |
| Accept natural confirmations | haan, ha, theek hai, kar do, yes, ok, sari, houdu / nahi, ruko, cancel |
| Numbers and times spoken naturally | "chhe baje shaam", not "18:00" |
| On failure: say what happened + next step | "Clinic ne phone nahi uthaya. 10 minute baad phir try karoon?" |
| Disclose AI on calls/meetings | "Hello, this is Rex, Johny's AI assistant." |

### Language behaviour
- Reply in the language of the last user turn; keep English nouns (app names, "meeting") as users do.
- Voice per language from the Timbre catalogue; same persona across voices.
- If unsure of language, ask once in English + Hindi.

### Earcons
Short sounds (≤ 300 ms): listening start, thinking (soft loop for > 2 s jobs), success, needs-approval, error. Generated once, cached.

## 2. Visual design (web + desktop)

### Principles
Calm, readable, live. The dashboard is a **mirror of the conversation and its actions**, not a control panel.

### Tokens
| Token | Light | Dark |
|---|---|---|
| `--bg` | #FAFAF7 | #111214 |
| `--surface` | #FFFFFF | #1A1C1F |
| `--text` | #1B1B1F | #ECECEF |
| `--muted` | #6B6F76 | #9A9EA6 |
| `--accent` (Rex saffron) | #E8772E | #F08A45 |
| `--ok` | #1F9D55 | #3BC07A |
| `--warn` | #C98A00 | #E3A72F |
| `--danger` | #D14343 | #EF6262 |

Type: Inter for UI, Noto Sans (Devanagari, Tamil, Kannada, Bengali…) for Indian scripts — always load the Noto family for the transcript. Radius 12 px, 8-pt spacing grid.

### Screens

1. **Home / Talk** — big push-to-talk orb (states: idle, listening, thinking, speaking, needs-approval), live transcript with language chips (`HI`, `TA`, `EN`), latest action cards.
2. **Timeline** — chronological action cards: icon per tool, one-line summary in user's language, tier badge (R/W/A), status, **Undo** (W) or **Approve / Deny** (A, with 30 s countdown ring).
3. **Connections** — cards for Google, Slack, Notion, GitHub, Maps, Twilio with connect/disconnect and scopes listed.
4. **Calls** — list of calls with outcome badge, transcript drawer.
5. **Meetings** — paste link → join; minutes preview; "Open in Notion".
6. **Settings** — language, voice, push-to-talk vs wake word, screen-access mode, tool toggles (skills).

### Desktop companion
- Tray icon states mirror the orb; **red ring = screen watch mode on**.
- Global hotkey (default `Ctrl/⌘ + Shift + Space`) push-to-talk.
- Mini overlay (bottom-right) shows the last reply and pending approval.
- Region capture: drag to select; the region flashes when captured.

### Accessibility
- WCAG AA contrast; every action reachable by keyboard; transcript is a live region (`aria-live="polite"`).
- Captions always on in the demo; font size setting.

## 3. Demo video design
- 1080×1920 vertical for social + 1920×1080 for submission.
- Split view: dashboard (left), phone receiving the call (right, camera).
- Subtitles in English for every spoken line; language chip visible.
- End card: "Built on Gnani Prisma + Timbre · #GnaniAI #GreatIndianAIInternshipChallenge".
