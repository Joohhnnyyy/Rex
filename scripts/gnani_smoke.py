#!/usr/bin/env python3
"""Round-trip smoke test for the Gnani key: Timbre TTS -> WAV -> Prisma STT.

uv run --env-file .env python scripts/gnani_smoke.py [--lang hi-IN] [--text "..."] [--out /tmp/rex_tts.wav]
"""

import argparse
import os
import sys
import time

import httpx

BASE = "https://api.vachana.ai"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="hi-IN")
    ap.add_argument("--text", default="नमस्ते, मैं रेक्स हूँ। कल चार बजे मीटिंग रख दूँ?")
    ap.add_argument("--voice", default="Nalini")
    ap.add_argument("--model", default="timbre-v2.5")
    ap.add_argument("--out", default=os.path.join(os.path.expanduser("~"), "rex_tts.wav"))
    args = ap.parse_args()

    key = os.environ.get("GNANI_API_KEY")
    if not key:
        sys.exit("GNANI_API_KEY not set (run with: uv run --env-file .env ...)")
    headers = {"X-API-Key-ID": key}

    with httpx.Client(timeout=60) as http:
        t0 = time.perf_counter()
        r = http.post(
            f"{BASE}/api/v1/tts/inference",
            headers=headers,
            json={
                "text": args.text,
                "voice": args.voice,
                "model": args.model,
                "language": args.lang,
                "audio_config": {
                    "sample_rate": 16000,
                    "num_channels": 1,
                    "sample_width": 2,
                    "encoding": "linear_pcm",
                    "container": "wav",
                },
            },
        )
        tts_ms = int((time.perf_counter() - t0) * 1000)
        if r.status_code != 200:
            sys.exit(f"TTS failed {r.status_code}: {r.text[:300]}")
        with open(args.out, "wb") as f:
            f.write(r.content)
        print(f"TTS ok: {len(r.content)} bytes in {tts_ms} ms -> {args.out}")

        t0 = time.perf_counter()
        with open(args.out, "rb") as f:
            s = http.post(
                f"{BASE}/stt/v3",
                headers=headers,
                files={"audio_file": ("rex.wav", f, "audio/wav")},
                data={"language_code": args.lang, "format": "transcribe"},
            )
        stt_ms = int((time.perf_counter() - t0) * 1000)
        if s.status_code != 200:
            sys.exit(f"STT failed {s.status_code}: {s.text[:300]}")
        print(f"STT ok in {stt_ms} ms: {s.json().get('transcript')!r}")


if __name__ == "__main__":
    main()
