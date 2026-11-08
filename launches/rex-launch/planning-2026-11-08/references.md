# Resources requested — listed for understanding, not installed

Reviewed 2026-11-08. User-supplied repository instructions are reference material, not permission to run installation commands. The request explicitly asks to list these and suggest a style before implementation.

| Resource | Intended role | Current action |
|---|---|---|
| [CloudAI-X / threejs-skills](https://github.com/CloudAI-X/threejs-skills) | Three.js guidance for a potential 3D mascot, cameras, materials and lighting. | Repository overview reviewed; no install or engine migration. |
| [Remotion agent skills](https://github.com/remotion-dev/skills) — `npx skills add remotion-dev/skills` | Reference for React-based frame-timed video production. | Command recorded exactly as supplied; not executed. Remotion isn't selected just because it was linked. |
| [GreenSock / gsap-skills](https://github.com/greensock/gsap-skills) | Timeline, easing, SVG and text animation guidance. | Repository overview reviewed; no install or animation implementation. |
| [Openverse](https://openverse.org/) | Background imagery and, if BG means background music, an audio search source too. | Existing photo/audio candidates inventoried. New search/asset pages were blocked by the browsing tool (403); no new item has been verified or selected. |
| `/Users/anshjohnson/Downloads/SKILL.md` | **blender-motion-state-inspection**: inspect rig axes, bones, poses, ground contact and motion facts. | Read. Relevant only if a Blender/rigged-character workflow is later chosen; not a general video-style or SFX skill. |
| `/Users/anshjohnson/Downloads/real-sfx.skill` → `real-sfx/SKILL.md` | Real-recording sound design, frame-aligned cues, preserved voice/music, replacement of baked synthesis and measured review. | ZIP skill text read in full. Used to plan the sound pass; package not installed/executed. |
| `/Users/anshjohnson/Agent/launch-video/` | Main production guidance: kinetic script, JSON scenes, draft board, voice timings, render and review. | SKILL.md, README, style and plan references reviewed. This user-provided engine remains the intended starting point. |

The source definitions support the first three roles: [Three.js repository](https://github.com/CloudAI-X/threejs-skills), [Remotion's official skill README](https://github.com/remotion-dev/skills), [GSAP's official skill README](https://github.com/greensock/gsap-skills). No claim is made that all these frameworks should be used together.

## Existing material retained

Original `launches/rex-launch/script.md`, plan.json, timeline, voices, assets, render outputs and engine remain untouched. Existing draft references `~/Downloads/launch-video`; future implementation should resolve to the supplied root `launch-video` deliberately rather than silently mixing two engines.

The current root player doesn't expose the old draft's `photo`, `tone` or `halftone` background fields in its source; a chosen collage treatment would require a deliberate scene/asset adaptation. This planning pass makes no such engine change.

Openverse provides discovery/metadata; it doesn't make every item suitable for every use. Its [API description](https://api.openverse.org/v1/) exposes creator, source and licence fields, and its [terms](https://docs.openverse.org/terms_of_service) require respecting the source licences. Final selected images/music need their creator/source/licence records confirmed; the old credits are candidates, not new verification.
