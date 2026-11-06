"""Gmail MCP server against a fake Gmail API: search, read (HTML fallback), reply in thread, tiers."""

from __future__ import annotations

import base64
import email
import json
from pathlib import Path

import pytest
import yaml

from rex_mcp_servers.gmail import build_server

REPO_ROOT = Path(__file__).resolve().parents[3]


def _b64(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


MSG = {
    "id": "m1",
    "threadId": "t1",
    "snippet": "Your slot is confirmed &amp; paid",
    "labelIds": ["INBOX", "UNREAD"],
    "payload": {
        "headers": [
            {"name": "From", "value": "Clinic <clinic@example.com>"},
            {"name": "To", "value": "johny@example.com"},
            {"name": "Subject", "value": "Booking"},
            {"name": "Date", "value": "Fri, 6 Nov 2026 10:00:00 +0530"},
            {"name": "Message-ID", "value": "<abc@example.com>"},
        ],
        "mimeType": "multipart/alternative",
        "parts": [{"mimeType": "text/html", "body": {"data": _b64("<p>See you at <b>4 pm</b></p><style>x{}</style>")}}],
    },
}


class _Req:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeGmail:
    def __init__(self):
        self.sent = []
        self.list_q = None

    def users(self):
        return self

    def messages(self):
        return self

    def list(self, userId, q, maxResults):  # noqa: N803
        self.list_q = q
        return _Req({"messages": [{"id": "m1"}]})

    def get(self, userId, id, format, metadataHeaders=None):  # noqa: A002, N803
        return _Req(MSG)

    def send(self, userId, body):  # noqa: N803
        self.sent.append(body)
        return _Req({"id": "s1"})


def _text(res) -> dict:
    return json.loads(res.content[0].text)


@pytest.mark.asyncio
async def test_search_read_and_reply():
    fake = FakeGmail()
    server = build_server(fake)

    found = _text(await server.call_tool("search_emails", {"query": "is:unread", "max_results": 50}))
    assert fake.list_q == "is:unread"
    assert found["emails"][0] == {
        "id": "m1",
        "from": "Clinic <clinic@example.com>",
        "subject": "Booking",
        "date": "Fri, 6 Nov 2026 10:00:00 +0530",
        "snippet": "Your slot is confirmed & paid",
        "unread": True,
    }

    mail = _text(await server.call_tool("read_email", {"message_id": "m1"}))
    assert mail["body"] == "See you at 4 pm"  # HTML stripped, <style> dropped

    sent = _text(
        await server.call_tool(
            "send_email", {"to": "clinic@example.com", "subject": "x", "body": "Thanks!", "reply_to_id": "m1"}
        )
    )
    assert sent["subject"] == "Re: Booking"
    body = fake.sent[0]
    assert body["threadId"] == "t1"
    out = email.message_from_bytes(base64.urlsafe_b64decode(body["raw"]))
    assert out["In-Reply-To"] == "<abc@example.com>"
    assert out.get_payload().strip() == "Thanks!"


def test_yaml_tiers():
    cfg = yaml.safe_load((REPO_ROOT / "infra" / "mcp_servers.yaml").read_text())
    tools = cfg["servers"]["gmail"]["tools"]
    assert tools["search_emails"]["tier"] == "R"
    assert tools["read_email"]["tier"] == "R"
    assert tools["send_email"]["tier"] == "A"
    assert "gmail" in cfg["allowlists"]["rex"]
