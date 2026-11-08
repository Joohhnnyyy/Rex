# Bloub eye tracking and animation reference

Reviewed 2026-11-08 at commit `b4bb3c1b5f93c7b87a2e8d620f667c4093d97749`.
Source: https://github.com/jeremy-prt/bloub

## What makes the eyes feel alive

The renderer uses SVG, not WebGL or an animation library. The eyes are capsule paths projected from tangent frames on a virtual sphere. Each eye receives a position, a 2×2 transform and a depth. As the head turns, the outside eye compresses and tilts naturally; eyes behind the sphere disappear. This is materially different from moving both flat eye rectangles by the same offset.

The geometry is in [face.ts](https://github.com/jeremy-prt/bloub/blob/b4bb3c1b5f93c7b87a2e8d620f667c4093d97749/src/bot/face.ts), particularly `eyePoses()`. Head yaw, pitch and roll are separate from each eye's own tilt. Mirrored eye tilts create anger/sadness; changing head roll alone tilts both eyes in the same direction.

### Pointer tracking

[BloubBot.vue](https://github.com/jeremy-prt/bloub/blob/b4bb3c1b5f93c7b87a2e8d620f667c4093d97749/src/components/BloubBot.vue) handles the DOM; [gaze.ts](https://github.com/jeremy-prt/bloub/blob/b4bb3c1b5f93c7b87a2e8d620f667c4093d97749/src/ui/gaze.ts) calculates targets.

- Window-level `pointermove` records the latest cursor, excluding touch input. Document `pointerleave` clears it.
- The avatar bounds are read each animation frame, so tracking remains correct while the layout moves.
- Cursor distance from the avatar centre is divided by half the viewport dimensions, then clamped to [-1, 1]. It does not saturate merely because the cursor leaves the avatar.
- Zero-sized avatar bounds are ignored to avoid invalid values when hidden.
- This particular UI turns toward its settings panel by -26° first. Pointer displacement adds up to ±16° yaw and ±13° pitch around an absolute pitch of 10°. The -26° bias belongs to that layout, not a general tracking requirement.
- Tracking blends with the expression's gaze rather than simply adding expression offsets. This prevents mood changes from shifting the tracking baseline.
- Pointer following only applies to `baseFace` states (`idle` and UI-only `swirl`); choreographed states retain their own gaze.
- Without a known pointer, slow gaze drift resumes. Pointer tracking suppresses that drift.
- `BotEngine.LOOK_MORPH` is 0.24 s. Retargeting starts from the currently interpolated look, avoiding a jump back toward a previous target.

### Idle motion and blinking

`liveliness(t)` combines smooth periodic noise at several periods for gaze drift, rather than choosing new random screen offsets on a timer.

The seeded blink schedule starts at 1.4 s, uses 1.9–4.6 s intervals and occasionally inserts close-spaced blinks. A blink lasts 0.18 s: 45% closing and 55% reopening. Eyelids flatten the eye in screen-vertical coordinates **after** its tilt/projection, preserving the apparent eye width. `blinkScale()` retains 6% height at full closure. Certain state transitions also trigger a 0.2 s blink.

The engine has tiny optional body drift/breathing; Rex's requested fixed capsule should omit those.

## Expressions versus showcase animations

[expressions.ts](https://github.com/jeremy-prt/bloub/blob/b4bb3c1b5f93c7b87a2e8d620f667c4093d97749/src/bot/expressions.ts) contains **16 expressions**: neutral, attentive, surprised, excited, happy, laughing, angry, sad, frightened, suspicious, confused, curious, proud, shy, bored and drowsy.

Expressions vary four things: head orientation, eye separation, each eye's width/height/opening, and independent tilt. Suspicious and confused expressions use different shapes for the two eyes. Near-circular eyes cannot visibly communicate tilt, so angled expressions need elongated shapes.

[states.ts](https://github.com/jeremy-prt/bloub/blob/b4bb3c1b5f93c7b87a2e8d620f667c4093d97749/src/bot/states.ts) contains **14 showcase states plus one UI transition**:

| State | Behaviour | Relation to Rex's eye-only brief |
|---|---|---|
| idle | Resting gaze and blinking | Directly relevant |
| thinking | Body becomes three pulsing dots | Keep Rex's body; use thinking gaze instead |
| wink | One eye becomes a wider horizontal dash | Relevant eye gesture |
| wide | Tall, widened eyes with changed gaze | Relevant for surprise |
| alert | Travelling exclamation mark | Body morph; outside current brief |
| notify | Badge pops onto body, gaze looks away | Gaze reaction useful; badge optional and not requested |
| exclaim | Upright exclamation-mark silhouette | Body morph; outside current brief |
| sleep | Body becomes a bouncing small dot | Use closed eyes instead for Rex |
| egg | Egg-shaped body and narrower eye spacing | Body morph; outside current brief |
| hexagon | Hexagonal silhouette | Body morph; outside current brief |
| play | Triangle and sweeping arcs | Body/decor animation; outside current brief |
| orbit | Rotating triangle returns to sphere with orbiting rings | Outside current brief |
| burst | Collapse, particles, reassembly | Outside current brief |
| comet | Small central dot with orbiting ribbon trails | Outside current brief |
| swirl | UI-only entry with rings and gaze handoff | Gaze handoff relevant; rings not requested |

## Timing and transitions

[engine.ts](https://github.com/jeremy-prt/bloub/blob/b4bb3c1b5f93c7b87a2e8d620f667c4093d97749/src/bot/engine.ts) separates target changes from frame sampling. `sample(t)` is deterministic for a configured transition history, enabling fixed-frame tests and export.

The implementation uses quintic ease-out (`1 - (1 - t)^5`) for the main morphs, not a global spring simulation. Morph durations in the state catalogue range from 0.3 to 0.6 s. If a state change interrupts a morph, it freezes the current composite pose as the next transition's start. Transitions therefore continue from what is actually visible.

The component owns the requestAnimationFrame clock and clamps each elapsed step to 64 ms after background-tab pauses. Gaze spin scripts use ease-in-out; a full spherical eye orbit is explicitly limited to circular bodies because non-circular profiles can introduce visible trajectory changes.

The source cuts eyes out through an SVG mask. Its non-circular bodies also use precomputed fitting offsets so the pair stays inside the silhouette without a per-frame constraint solver. Rex's fixed capsule and bounded gaze do not need the whole shape-morph system.

## Rex integration (2026-11-08)

The subsequent user request expanded scope to all animations and expressions. The framework-free
core is now vendored under `apps/web/lib/bloub/` at the reviewed revision, with the MIT licence retained.
The React renderer lives in `components/dash/Mascot.tsx`; live state mappings and viewport-normalized
pointer targets are in `lib/mascot.ts`. The default body remains the red capsule, with white eyes.

All 15 states and 16 expressions are exposed in Lab → Mascot studio, with Replay and sequence playback.
Pointer following is enabled only on base-face states so it does not override choreographed eye motion.
Reduced motion renders representative stills. Vue UI, export encoders and the timeline editor were not imported.

One upstream capsule issue was caught by a regression test: interrupting a body transition preserved the
composite body pose but not its interpolated eye-fitting correction. The local engine now freezes and
blends that correction too, preventing a positional eye jump. `lib/bloub/README.md` records the patch.

Regression tests sample every state, validate all expressions/live mappings and pointer bounds, check
interrupted-transition continuity and ensure masks/gradients remain unique across mascot instances.
