"""Voice casting samples (ElevenLabs): one file per role, the candidate voices in order with 0.8 s gaps.
Run with ELEVENLABS_API_KEY in the environment: python3 launches/rex-launch/voice_samples.py"""

import os
import subprocess
import sys

import requests

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice-samples")
VOICES = {"Liam": "TX3LPaxmHKxFdv7VOQHJ", "Jessica": "cgSgspJ2msm6clMCkdW9", "Chris": "iP95p4xoKVk53GoZ742B",
          "Eric": "cjVigY5qzO86Huf0OWal", "Sarah": "EXAVITQu4vr4xnSDxMaL", "Will": "bIHbv24MWmeRgasZH58o",
          "Callum": "N2lVS1w4EtoT3dr4eOWO", "Laura": "FGY2WhTYpPnrIDTdsKH5", "Charlie": "IKne3meq5aSn9XLyUdCD",
          "Harry": "SOYHLrjzK2X1ezoPC6cr", "River": "SAz9YHcvj6GT2YYXdXww"}
ROLES = {
    "narrator": ("Your day moves fast. Hand some of it to Rex.", ["Liam", "Jessica", "Chris", "Eric", "Sarah"]),
    "you": ("Find Delhi to Bhopal flights for Friday, and WhatsApp Shanky.", ["Chris", "Will", "Callum", "Laura"]),
    "rex": ("On it.", ["Charlie", "Will", "Harry", "River"]),
}

os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.expanduser("~/Downloads/launch-video"))
from vo import env_key  # same lookup as the render: environment, then .env in the project / skill / cwd

key = env_key("ELEVENLABS_API_KEY", None)
for role, (text, names) in ROLES.items():
    parts = []
    for n in names:
        p = os.path.join(OUT, f"{role}-{n}.mp3")
        if not os.path.exists(p):
            r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICES[n]}", timeout=120,
                              headers={"xi-api-key": key}, params={"output_format": "mp3_44100_128"},
                              json={"text": text, "model_id": "eleven_multilingual_v2",
                                    "voice_settings": {"stability": 0.35, "similarity_boost": 0.75, "style": 0.2,
                                                       "use_speaker_boost": True}})
            r.raise_for_status()
            open(p, "wb").write(r.content)
        parts.append(p)
    # one file per role: each voice, then 0.8 s of silence
    args, chain = [], ""
    for i, p in enumerate(parts):
        args += ["-i", p]
        chain += f"[{i}:a]aresample=44100,apad=pad_dur=0.8[a{i}];"
    chain += "".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", chain, "-map", "[o]", "-b:a", "160k",
                    os.path.join(OUT, f"{role}-samples.mp3")], check=True)
    print(role, " -> ".join(names))
