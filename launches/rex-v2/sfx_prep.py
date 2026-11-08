"""Cut the real Openverse/Freesound recordings in sfx-library/ into the cue files the mixer plays (sfx/<cue>.<n>.wav).

The engine's cues keep their names (swish, pop, key1..3, ding, boom, riser, click); each gets real recordings instead of
synthesis, trimmed to the attack, length-capped with a fade, and peak-matched to the synthesized sound it replaces.
Run: python3 launches/rex-launch/sfx_prep.py
"""

import glob
import os
import subprocess
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LIB, OUT, SR = os.path.join(HERE, "sfx-library"), os.path.join(HERE, "sfx"), 48000

# cue -> (library folder, max length s, peak). Peaks sit near the synth kit's so the engine's per-cue gains still fit.
CUES = {
    "swish": ("whoosh", 0.7, 0.7),
    "pop": ("pop", 0.25, 0.8),
    "click": ("click", 0.15, 0.8),
    "ding": ("ding", 1.2, 0.6),
    "boom": ("impact", 2.2, 0.9),
    "riser": ("riser", 1.0, 0.6),
}


def read(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, 2)


def write(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def shape(x, max_s, peak, from_end=False):
    """Trim to the attack (first sample above -40 dB of the peak), cap the length with a 30 ms fade, set the peak."""
    env = np.abs(x).max(1)
    if from_end:  # a riser: keep its last max_s, which is where it builds
        x = x[-int(max_s * SR):]
    else:
        start = max(0, int(np.argmax(env > env.max() * 0.01)) - int(0.003 * SR))
        x = x[start:start + int(max_s * SR)]
    f = min(len(x), int(0.03 * SR))
    x = x.copy()
    x[-f:] *= np.linspace(1, 0, f)[:, None]
    return x / (np.abs(x).max() + 1e-9) * peak


def keystrokes(n=3):
    """Single keystrokes sliced from the typing recordings (onsets at least 60 ms apart), 70 ms each."""
    hits = []
    for p in sorted(glob.glob(os.path.join(LIB, "typing", "*.mp3"))):
        x = read(p)
        env = np.convolve(np.abs(x).max(1), np.ones(96) / 96, "same")
        thr, last = env.max() * 0.35, -SR
        for i in np.flatnonzero((env[1:] > thr) & (env[:-1] <= thr)):
            if i - last > 0.06 * SR:
                hits.append(shape(x[i:i + int(0.07 * SR)], 0.07, 0.5)); last = i
    hits.sort(key=lambda h: -np.sqrt((h ** 2).mean()))  # the fullest-bodied strokes, not ticks
    return hits[:n]


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "*.wav")):
        os.remove(f)
    for cue, (folder, max_s, peak) in CUES.items():
        files = sorted(glob.glob(os.path.join(LIB, folder, "*.mp3")))
        for i, p in enumerate(files):
            write(os.path.join(OUT, f"{cue}.{i}.wav"), shape(read(p), max_s, peak, from_end=cue == "riser"))
        print(cue, len(files), "variant(s) from", folder)
    keys = keystrokes()
    assert len(keys) == 3, "need three keystrokes from sfx-library/typing"
    for i, k in enumerate(keys, 1):
        write(os.path.join(OUT, f"key{i}.wav"), k)
    print("key1..3 sliced from typing")


if __name__ == "__main__":
    main()
