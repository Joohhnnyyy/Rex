"""Instant spoken acknowledgements for slow jobs, in the user's language."""

_ACKS: dict[str, dict[str, str]] = {
    "hi-en": {
        "caller": "Theek hai, call kar raha hoon. Ho jaane par batata hoon.",
        "meeting": "Theek hai, meeting join kar raha hoon. Minutes ready hote hi bataunga.",
        "coder": "Theek hai, code dekh raha hoon. Fix ho jaane par batata hoon.",
        "_": "Theek hai, kar raha hoon. Ho jaane par batata hoon.",
    },
    "hi-IN": {
        "caller": "ठीक है, कॉल कर रहा हूँ। हो जाने पर बताता हूँ।",
        "_": "ठीक है, कर रहा हूँ। हो जाने पर बताता हूँ।",
    },
    "en-IN": {
        "caller": "On it, I'm placing the call now and I'll let you know.",
        "meeting": "On it, joining the meeting. I'll share the minutes when it ends.",
        "coder": "On it, looking at the code. I'll tell you when the fix is ready.",
        "_": "On it. I'll let you know when it's done.",
    },
}


def fast_ack(specialist: str, lang: str) -> str:
    table = _ACKS.get(lang, _ACKS["en-IN"])
    return table.get(specialist, table["_"])
