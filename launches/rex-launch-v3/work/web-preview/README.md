# Rex Control Center

Next.js 15 + LiveKit components + Tailwind 4, icons from lucide-react, charts from recharts. A charcoal framed
workspace around Rex's mascot: press the mic or type in the command bar to talk to Rex.

The dashboard and Focus mode use the Confused mascot logo from `design/logo/rex-mascot-kit`.
`public/rex-logo.svg` is the header mark; App Router icons and the public PWA icon set use its small-size cut.

```bash
cd apps/web
npm install
cp .env.local.example .env.local      # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                           # http://localhost:3000
```

Also run, from the repo root: the API (`uv run --env-file .env uvicorn rex_api.main:app --port 8000`)
and the agent (`uv run --env-file .env python -m rex_agent dev`). "Talk to Rex" asks the API for a room
token; the token dispatches the `rex` agent into that room.

## What is live and what is demo

| Panel | Source |
|---|---|
| Eye-only mascot | Rex's voice state (listening / thinking / speaking), voice level, and a reaction when an action succeeds, fails or needs approval |
| Command bar, ⌘K "Ask Rex" | sends text to Rex on the `lk.chat` topic (starts a call first if needed) |
| Recent Activity, notifications | Rex's actions on `rex.timeline`, with Approve / Deny for Tier A |
| Task Progress (This Session), Active Agents | counted from those actions during a call |
| Lab | mascot state preview, Rex's live browser, transcript |
| Memory | `GET /v1/memory` (facts + past call summaries) |
| Settings / Agents connections | `GET /v1/connections` |
| System Health, Global Activity, Projects, Resource Utilization, Task Progress (Today / Week) | **demo data** in `lib/dashboard.ts` (`DEMO`), tagged "Demo" in the UI |

To make a demo panel live, replace its `DEMO.*` value with a fetch: e.g. an API route returning
`SystemMetrics` (psutil on the host) or `Project[]` (GitHub / Notion).

Code: `components/dash/` (Dashboard, Mascot, Panels, Shell), types and demo data in `lib/dashboard.ts`.

Checks: `npm run typecheck`, `npm run lint`, `npm run build`.

The reference-inspired overview uses a slim illuminated navigation rail, stacked agent/activity cards,
and a larger assistant workspace with the existing command bar, conversation and immersive controls.
The navigation scrolls horizontally on phones and the assistant comes first. Entrances, panel feedback
and navigation glows use CSS motion; the existing reduced-motion preference applies throughout.
Navigation buttons, Rex and voice controls share the red accent. No new live data sources were added.

Rex uses Bloub's framework-free animation core, vendored with its MIT licence in `lib/bloub/`.
The default body is a red capsule with projected white eyes and window-wide pointer tracking.
Live states map to expressions (listening → attentive, speaking → excited, error → angry,
sleeping → drowsy), thinking → pulsing dots, surprise → wide eyes and success → wink.
Voice/mic levels also open the eyes slightly.

Lab → Mascot studio exposes all 15 animation states (including the UI-only swirl) and 16 expressions.
Use Replay, Play all animations, Stop sequence or Follow Rex. Expressions switch to the resting capsule
so each is visible; choreographed animations keep their original eye poses. Reduced-motion mode shows
fixed representative frames and disables replay/sequence controls. Header icons are also static.
Run `npm run test:mascot` for geometry, state mapping, tracking, transition continuity and SVG ID checks.
The port keeps original geometry and timing; body colour and eye rendering are adapted to Rex.
See [the source analysis](../../docs/research/bloub-eye-animation.md) and `lib/bloub/README.md` for attribution
and the local capsule transition fix. No Vue or animation-library dependency was added.

Immersive view renders as a body-level dialog so the dashboard's animated frame cannot constrain it.
It locks background scrolling and interaction, keeps keyboard focus inside, closes with Escape and
restores the previous focus. Cmd/Ctrl+K focuses the immersive text input. The mascot, approval cards,
captions and command bar occupy separate rows with dynamic-viewport sizing and phone safe-area padding.
The overview is more compact, shows Rex first on tablets as well as phones, and groups supporting cards
into a responsive grid. Background mascot/globe animation pauses while immersive view is open.

Focus mode adds layered red atmosphere, slow orbital light, a ground reflection, a larger stage and a
translucent input dock. Glow, particles and the activity bars react to actual microphone/voice levels;
offline bars stay flat. State-specific presence text sits separately from the conversation captions.
The avatar scales to its available grid space, and reduced motion keeps the atmosphere and parallax still.
