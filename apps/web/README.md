# Rex dashboard (T-15 v0)

Next.js 15 + LiveKit components. Talk to Rex in the browser: live state orb, audio visualiser,
mic controls and a live transcript with language chips (EN / HINGLISH / HI / TA / KN …).

```bash
cd apps/web
npm install
cp .env.local.example .env.local      # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                           # http://localhost:3000
```

Also run, from the repo root: the API (`uv run --env-file .env uvicorn rex_api.main:app --port 8000`)
and the agent (`uv run --env-file .env python -m rex_agent dev`). "Talk to Rex" asks the API for a room
token; the token dispatches the `rex` agent into that room.

Checks: `npm run typecheck`, `npm run lint`, `npm run build`.
