"""Instant spoken acknowledgements for slow jobs, in the user's language."""

_ACKS: dict[str, dict[str, str]] = {
    "hi-en": {
        "meeting": "Theek hai, meeting join kar raha hoon. Minutes ready hote hi bataunga.",
        "coder": "Theek hai, code dekh raha hoon. Fix ho jaane par batata hoon.",
        "_": "Theek hai, kar raha hoon. Ho jaane par batata hoon.",
    },
    "hi-IN": {
        "_": "ठीक है, कर रहा हूँ। हो जाने पर बताता हूँ।",
    },
    "en-IN": {
        "meeting": "On it, joining the meeting. I'll share the minutes when it ends.",
        "coder": "On it, looking at the code. I'll tell you when the fix is ready.",
        "_": "On it. I'll let you know when it's done.",
    },
}


def fast_ack(specialist: str, lang: str) -> str:
    table = _ACKS.get(lang, _ACKS["en-IN"])
    return table.get(specialist, table["_"])


# Spoken while a direct tool runs (JARVIS-style: one line, picked by tool, no immediate repeats).
_FILLERS: dict[str, dict[str, list[str]]] = {
    "en-IN": {
        "calendar": ["Checking your calendar.", "Let me look at your calendar."],
        "gmail": ["Checking your inbox.", "Looking through your email."],
        "browser": ["Opening that page.", "Having a look at that page."],
        "location": ["Looking that up.", "Checking the map."],
        "slack": ["Checking Slack.", "Looking at Slack."],
        "notion": ["Checking Notion.", "Looking in Notion."],
        "desktop": ["Okay, doing it now.", "On it, give me a sec.", "Sure, one moment."],
        "screen": ["Let me see.", "Hmm, let me have a look."],
        "_": ["One moment.", "Give me a second."],
    },
    "hi-en": {
        "calendar": ["Calendar dekh raha hoon.", "Ek second, calendar check karta hoon."],
        "gmail": ["Inbox dekh raha hoon.", "Mail check kar raha hoon."],
        "browser": ["Page khol raha hoon.", "Ek second, page dekhta hoon."],
        "location": ["Map pe dekh raha hoon.", "Ek second, check karta hoon."],
        "desktop": ["Haan, kar raha hoon.", "Ek second, abhi karta hoon."],
        "screen": ["Dekhta hoon.", "Ek second, dekh raha hoon."],
        "_": ["Ek second.", "Bas ek minute."],
    },
}
_last_filler: dict[str, str] = {}


def tool_filler(server: str, lang: str | None) -> str:
    table = _FILLERS.get(lang or "en-IN", _FILLERS["en-IN"])
    options = table.get(server, table["_"])
    pick = next((o for o in options if o != _last_filler.get(server)), options[0])
    _last_filler[server] = pick
    return pick
