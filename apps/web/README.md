# Rex Control Center

Next.js 15 + LiveKit components + Tailwind 4, icons from lucide-react, charts from recharts. A dark
control-center dashboard around Rex's mascot: press the mic or type in the command bar to talk to Rex.

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
| Mascot + HUD | Rex's voice state (listening / thinking / speaking), voice level, and a reaction when an action succeeds, fails or needs approval |
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
