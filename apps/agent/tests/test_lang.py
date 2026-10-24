import pytest

from rex_agent.lang import detect_language, tts_language


@pytest.mark.parametrize(
    "text, expected",
    [
        ("नमस्ते, कल चार बजे मीटिंग रखो", "hi-IN"),
        ("வணக்கம், நாளை சந்திப்பு", "ta-IN"),
        ("ನಾಳೆ ಹತ್ತು ಗಂಟೆಗೆ ಕರೆ ಮಾಡಿ", "kn-IN"),
        ("నమస్కారం", "te-IN"),
        ("নমস্কার", "bn-IN"),
        ("નમસ્તે", "gu-IN"),
        ("ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "pa-IN"),
        ("നമസ്കാരം", "ml-IN"),
        ("Book a meeting with Shanky tomorrow at four", "en-IN"),
        ("Kal 4 baje Shanky ke saath meeting rakho", "hi-en"),
        ("dentist ko call karke slot book karo", "hi-en"),
    ],
)
def test_detect_language(text, expected):
    assert detect_language(text) == expected


def test_empty_text_keeps_previous_language():
    assert detect_language("", previous="ta-IN") == "ta-IN"
    assert detect_language("   ", previous=None) == "en-IN"


def test_marathi_devanagari_is_reported_as_hindi_script_default():
    # Devanagari alone can't separate Hindi from Marathi; we default to hi-IN.
    assert detect_language("उद्या भेटू") == "hi-IN"


def test_tts_language_maps_hinglish_to_supported_code():
    assert tts_language("hi-en") == "hi-IN"
    assert tts_language("ta-IN") == "ta-IN"
    assert tts_language("fr-FR") == "en-IN"
