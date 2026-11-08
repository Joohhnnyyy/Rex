# Rex launch video

Made with the `launch-video` skill (kinetic style + mascot beats + Openverse photo collage), 16:9.

- `script.md` — the script; `plan.json` — the scenes (engine: `~/Downloads/launch-video`, with an added `photo`
  background option: `photo`, `tone` dark|duo|color, `halftone`, `photoFrom`/`photoTo`).
- `assets/` — dashboard screenshots and crops (from a demo API with seeded data, never the private one), mascot clips
  from the dashboard's Lab tab, the logo mark, and Openverse photos (`assets/photos/CREDITS.md`, all CC BY / CC0).
- `sfx-library/` — CC0 sound effects from Openverse/Freesound for the real-sfx pass (`sfx-library/CREDITS.md`).
- `capture.py` — re-shoots the screenshots and mascot clips (needs the web app on :3000 and the demo API on :8010).

Board: `node ~/Downloads/launch-video/engine/render.mjs launches/rex-launch --board`
Voice: `python3 ~/Downloads/launch-video/vo.py eleven launches/rex-launch --voice <voice_id>`
Render: `node ~/Downloads/launch-video/engine/render.mjs launches/rex-launch`
