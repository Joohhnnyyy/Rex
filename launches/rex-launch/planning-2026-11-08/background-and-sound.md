# Rex — background placement and real-SFX plan

This is an editorial sound/background map, not a rendered or auditioned mix. BG is covered in both senses: background imagery and background music. Openverse supplies source candidates; the real-SFX skill handles audio selection and synchronization, not visual layout.

## Visual background placement

| Time | Background | Placement / purpose |
|---|---|---|
| 0–6s | Openverse city-at-dusk candidate | Photo fills the frame; keep the detailed/lit subject right, with negative space under text on the left. Darken a separate overlay enough for caption readability. A subtle push-in is sufficient. |
| 6–11s | Charcoal reveal → paper product stage | Give the Confused logo clean separation. Actual UI comes forward; the background does not compete. |
| 11–45s | Actual UI with quiet solid surround | Readable product proof: transcript, source links, saved note and approval controls. Do not put a busy photo behind small text. Keep camera/cursor focus on what the voice describes. |
| 45–48s | One Openverse India image crop | Short place/context beat behind a large Hinglish transcript card; photos are context, not proof of language support. |
| 48–56s | Charcoal closing field | Gnani credit, Confused identity, brief Excited reaction and a clear CTA hold. No photo motion behind the final URL. |

Starting candidates already present in the project's Openverse photo inventory:

- `../assets/photos/hook-marine-drive.jpg`: “Marine drive sweep”, Swaminathan; existing record says CC BY 2.0; [source](https://commons.wikimedia.org/w/index.php?curid=5873232). Opening candidate.
- `../assets/photos/india-delhi-metro.jpg`: “HUDA City Center (Delhi Metro)”, varunshiv; existing record says CC BY 2.0; [source](https://commons.wikimedia.org/w/index.php?curid=22076886). Language/context candidate.
- `../assets/photos/india-jodhpur-market.jpg`: Vyacheslav Argenberg; existing record says CC BY 4.0; [source](https://commons.wikimedia.org/w/index.php?curid=105466051). Collage-style alternative.

Full old metadata is in `../assets/photos/CREDITS.md`. Re-check source licences before final use. Search intent for alternatives: Openverse images “Indian city dusk negative space”, “India workspace desk”, “Delhi metro architecture”. No new photos downloaded or selected during this planning pass.

## Music bed

Search Openverse audio for understated instrumental electronic/ambient tracks with no vocals and a clean ending. Target feel: warm, focused, optimistic, roughly 100–115 BPM; exact edit follows the chosen track, not an assumed beat grid. Prefer CC0 or attribution-compatible CC BY sources after source verification. Keep title, creator, source, licence/version/link and edit notes in final credits. No specific track is chosen yet.

Music starts under the opening voice, establishes momentum at 6–8s, ducks under the two user requests and Rex response, thins at 33–39s for the approval, and resolves through 50–56s. Do not run street ambience under the Hinglish demonstration. The supplied engine's default synthetic bed is not the proposed final music source.

## Recorded SFX treatment

Use the user's real-sfx workflow with `--ui library`: recorded UI/keyboard sounds, not synthesized cues. Start from the existing `../sfx-library/` candidates and verify their files/source records; no paid pack or new download is needed merely to write the plan.

| Anchor | Candidate role | Placement |
|---|---|---|
| 0–1s | Soft click / tab | At the first visible tab event; the voice itself also provides the hook. |
| ~6–8s | Short air riser + soft impact | Riser peak resolves into the actual logo arrival; at most two layers here. |
| 11–18s | Voice only / optional light UI confirmation | Keep user speech and Rex's acknowledgement clear. No exaggerated blinking sounds. |
| 18–24s | Short real keyboard run, light card settle | Match genuine typing or result appearance; never type over a static screenshot. |
| ~24–27s | Save confirmation | Arrival aligned to the visible saved-note event, not just a cut. |
| 27–33s | User voice, subtle action-card reveal | No message-delivered sound while the message is merely proposed. |
| 33–39s | Pause, optional approval click | Sound the press only if it actually happens in captured footage. Success sound requires a genuine result. |
| 39–45s | Quiet card/page moves | One consistent family; avoid a separate loud hit for every integration. |
| 45–50s | Music only | Breathing room for the language demonstration and Gnani credit. |
| ~50–56s | Soft logo settle, music resolution | Excited reaction may share the logo-settle cue; finish without a new notification. |

All times are provisional editorial anchors. Final timing must be read from the actual rendered event list and frames after voice timings are locked. Align a whoosh to visible motion, a click to the press, a hit to arrival and a riser peak to reveal. Do not put an SFX on every word or every cut.

## Integration and review after style selection

1. Leave `launch-video/` and the supplied SFX skill untouched. Work in a separate versioned output/work directory.
2. The root engine writes automatic cues (`out/cues.json`) and synthesizes effects in audio.py. Render clean picture + retained narration/music stems, or use the real-sfx baked-synthesis replacement flow. **Never stack recorded effects on top of the original synthetic effects.** Keep native sounds from any real clip.
3. At production time, check the sound-library/index setup, derive cues from the project's event list, choose all conversion flags before hand edits, inspect candidate waveforms/spectrograms and freeze picks after the first round.
4. Put effects roughly 6–10 dB below voice as a starting relationship; use the actual voice stem for ducking. Measure intelligibility/masking, phone-speaker/mono compatibility and encoded peaks. Do not claim the mix was heard based on metrics.
5. Run the real-sfx verify/review/critique loop for at least three rounds. Correct the three worst issues each round; report n/a honestly instead of adding filler sounds to chase a score. Prepare up to five short listening checks for the user.
6. Later video deliverables: 50–60s master MP4, review MP4, separate SFX WAV, retained voice/music stems, cue/source report and asset credits. None of these has been rendered in this planning-only step.
