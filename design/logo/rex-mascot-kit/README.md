# Rex — mascot logo kit

**Primary:** Confused. **Companion:** Excited. Based on the expressions you selected, with the same red capsule and two white eyes as the dashboard mascot.

## Use the files

- `masters/rex-confused-red.svg` — default symbol for light or dark backgrounds.
- `masters/rex-excited-red.svg` — greetings, success and discovery moments.
- `masters/*-horizontal-red.svg` — symbol with outlined lowercase Rex lettering, on light backgrounds.
- `masters/*-horizontal-white.svg` — reversed lockup on dark backgrounds.
- `masters/*-stacked-*.svg` — vertical lockups for square formats.
- `masters/*-black.svg` / `*-white.svg` — genuine single-ink artwork with transparent eye counters. The white cuts have slightly enlarged counters to reduce apparent weight.
- `masters/*-small.svg` — use at 16–32 px; the Confused short eye is enlarged for visibility.
- `exports/png/` — 1024 px transparent PNGs; SVG remains the preferred scalable master.
- `exports/web/` — SVG/ICO favicon, 16/32/48 px favicons, 180 px Apple icon, 192/512 px app icons, maskable icon, manifest and HTML installation snippet. Dark tiles preserve red-and-white identity.
- `review/identity-board.png` — colour identity overview. `review/preview.html` — mono/size/context checks.
- `presentation.html` — five-slide presentation including app, website, social, browser-tab, sticker and card studies. These are illustrative mockups, not changes to the running product.

## One-page usage guide

**Personality:** curious, capable, playful. Confused is the recognizable default face rather than an error signal. Excited is an expressive alternative, not a second brand. Keep the same body silhouette and red between both.

**Palette:** Rex red `#FF4055` (RGB 255/64/85); ink `#141418` (20/20/24); paper `#F6F3EE` (246/243/238); night tile `#090A0D` (9/10/13). Approximate unprofiled CMYK for red: 0/75/67/0. Proof print colours with your printer; no Pantone equivalence is claimed. White eyes are deliberate colour artwork, not transparent cut-outs; use separate mono masters for one-ink reproduction.

**Typography:** new, quieter rounded lowercase lettering, drawn as paths with no external font dependency. The mascot remains the identifier. UI/body typography is outside this kit.

**Clear space:** keep at least 24 units around the artwork on the 256-unit symbol canvas, approximately one tall-eye width. Horizontal lockups have a fixed 52-unit gap between body and lettering; don't rearrange or independently stretch the pieces.

**Minimum sizes:** use the small symbol at 16–32 px square and standard symbol above 32 px; horizontal lockup at least 140 px wide; stacked lockup at least 96 px wide. Confused's small eye is a simple dot-like shape at 16 px; the tall/short eye relationship remains. Use larger sizes when expression detail matters.

**Backgrounds:** use red-and-white on a quiet light or dark surface. Use black mono on light surfaces and white mono on dark. Put the red logo on the night tile if the background is red or visually busy. Don't put white mono on white.

**Avoid:** extra mouths or brows, gradients/shadows inside the logo, stretching, recolouring individual eyes, rotating the whole mark, switching expressions randomly, or converting colour masters to mono by changing every fill. The mono masters preserve the eye counters correctly.

## Construction and checks

Replaced the sampled animation outline with a precise 208 × 124 capsule. Confused's tall eye is tilted −15°, short eye +30°, with the pair optically centred. Excited uses broad ±15° eyes. Refined spacing, larger small-size eyes and enlarged reversed counters. Filled paths only; no raster image, mask, filter, live logo text or font dependency. The review board and presentation contain ordinary annotation text.

Build with `python3 design/logo/rex-mascot-kit/build.py` from the repository root. Export self-checks parse SVGs and reject nonfinite geometry, unsupported artwork and identical expressions. Skill audit warnings about white shapes in colour files are intentional: mono masters use true holes, while colour masters retain white eyes. Rendered colour board, reversed mark and app icon visually checked; favicon sizes inspected on the board and in exported files.

## Source and scope

The starting poses derive from the existing Bloub-based dashboard mascot. Its MIT notice is included in `LICENSE`; no claim is made that this derivative character is an exclusive new trademark. Trademark/reverse-image clearance remains unperformed. This kit does not change the running dashboard, favicon configuration or animated mascot defaults.
