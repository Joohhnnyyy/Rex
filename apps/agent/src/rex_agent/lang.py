"""Per-turn language detection from the transcript text.

Gnani STT returns text in the script of the spoken language, so Unicode script
ranges identify most Indian languages reliably. Latin-script text is either
English or romanised Hindi ("Hinglish"), told apart by common Hindi words.
"""

from __future__ import annotations

import re

# (first codepoint, last codepoint) -> BCP-47 code
_SCRIPTS: list[tuple[int, int, str]] = [
    (0x0900, 0x097F, "hi-IN"),  # Devanagari (Hindi / Marathi -> default Hindi)
    (0x0980, 0x09FF, "bn-IN"),  # Bengali
    (0x0A00, 0x0A7F, "pa-IN"),  # Gurmukhi
    (0x0A80, 0x0AFF, "gu-IN"),  # Gujarati
    (0x0B80, 0x0BFF, "ta-IN"),  # Tamil
    (0x0C00, 0x0C7F, "te-IN"),  # Telugu
    (0x0C80, 0x0CFF, "kn-IN"),  # Kannada
    (0x0D00, 0x0D7F, "ml-IN"),  # Malayalam
]

_HINGLISH_WORDS = {
    "kal",
    "aaj",
    "baje",
    "ke",
    "ki",
    "ka",
    "ko",
    "se",
    "mein",
    "main",
    "hai",
    "hain",
    "karo",
    "kar",
    "karke",
    "rakho",
    "rakh",
    "saath",
    "bhejo",
    "batao",
    "bolo",
    "kya",
    "kaise",
    "kab",
    "kahan",
    "nahi",
    "haan",
    "theek",
    "accha",
    "acha",
    "ruko",
    "chalo",
    "mujhe",
    "mera",
    "meri",
    "tum",
    "aap",
    "wala",
    "wali",
    "dena",
    "do",
    "lo",
    "hoga",
    "gaya",
    "shaam",
    "subah",
    "raat",
    "abhi",
    "phir",
    "par",
    "pe",
    "liye",
    "yeh",
    "ye",
}
_WORD = re.compile(r"[a-z]+")

TTS_SUPPORTED = {"hi-IN", "en-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN", "mr-IN", "bn-IN", "gu-IN", "pa-IN"}


def detect_language(text: str, previous: str | None = None) -> str:
    """Return a BCP-47 code for ``text``; 'hi-en' for romanised Hindi / Hinglish."""
    counts: dict[str, int] = {}
    latin = 0
    for ch in text:
        cp = ord(ch)
        if ch.isascii():
            latin += ch.isalpha()
            continue
        for lo, hi, code in _SCRIPTS:
            if lo <= cp <= hi:
                counts[code] = counts.get(code, 0) + 1
                break
    if counts:
        return max(counts, key=counts.__getitem__)
    words = _WORD.findall(text.lower())
    if not words:
        return previous or "en-IN"
    hindi = sum(w in _HINGLISH_WORDS for w in words)
    if hindi >= 2 or hindi / len(words) >= 0.25:
        return "hi-en"
    return "en-IN"


def tts_language(code: str) -> str:
    """Map a detected code to a language Timbre TTS accepts."""
    if code == "hi-en":
        return "hi-IN"
    return code if code in TTS_SUPPORTED else "en-IN"
