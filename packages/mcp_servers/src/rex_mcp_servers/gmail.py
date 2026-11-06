"""Gmail MCP server: search and read the inbox [R], send or reply [A].

Uses the same Google login as the calendar server (scopes gmail.readonly + gmail.send).
After adding Gmail, run `uv run python -m rex_mcp_servers.calendar login` once so the
token includes the Gmail scopes, and enable the Gmail API in the Google Cloud project.
"""

from __future__ import annotations

import base64
import json
import re
from email.message import EmailMessage
from html import unescape
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from rex_mcp_servers.calendar import LOGIN_HINT, google_creds

MAX_BODY = 3000  # chars of an email body sent to the LLM


def _real_service():
    from googleapiclient.discovery import build

    return build("gmail", "v1", credentials=google_creds("Gmail"), cache_discovery=False)


def _headers(msg: dict[str, Any]) -> dict[str, str]:
    return {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}


def _body_text(payload: dict[str, Any]) -> str:
    """Plain-text body; falls back to HTML with tags stripped."""
    parts, html = [payload], ""
    while parts:
        p = parts.pop(0)
        parts.extend(p.get("parts", []))
        data = p.get("body", {}).get("data")
        if not data:
            continue
        text = base64.urlsafe_b64decode(data + "==").decode("utf-8", "replace")
        if p.get("mimeType") == "text/plain":
            return text.strip()
        if p.get("mimeType") == "text/html" and not html:
            html = text
    text = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", text))).strip()


def _api(call):
    """Run a Gmail API request, turning auth/permission errors into a re-login hint."""
    from googleapiclient.errors import HttpError

    try:
        return call.execute()
    except HttpError as e:
        if e.resp.status in (401, 403):
            raise ToolError(
                f"Gmail refused the request ({e.resp.status}): the login may lack Gmail access or the "
                f"Gmail API is not enabled. {LOGIN_HINT}"
            ) from e
        raise ToolError(f"Gmail error {e.resp.status}: {e.reason}") from e


def build_server(service=None) -> MCPServer:
    """Build the Gmail MCPServer. `service` can be a fake for tests."""
    server = MCPServer("gmail")
    cache: dict[str, Any] = {}

    def svc():
        if service is not None:
            return service
        if "svc" not in cache:
            cache["svc"] = _real_service()
        return cache["svc"]

    @server.tool()
    async def search_emails(query: str = "in:inbox", max_results: int = 5) -> str:
        """Find emails with Gmail search syntax and list sender, subject, date and a snippet [Tier R].

        Args:
            query: Gmail search, e.g. "is:unread", "from:shanky newer_than:7d", "subject:invoice"
            max_results: how many to return (1-10)
        """
        n = max(1, min(int(max_results), 10))
        found = _api(svc().users().messages().list(userId="me", q=query, maxResults=n))
        out = []
        for m in found.get("messages", []):
            msg = _api(
                svc()
                .users()
                .messages()
                .get(userId="me", id=m["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"])
            )
            h = _headers(msg)
            out.append(
                {
                    "id": msg["id"],
                    "from": h.get("from", ""),
                    "subject": h.get("subject", ""),
                    "date": h.get("date", ""),
                    "snippet": unescape(msg.get("snippet", "")),
                    "unread": "UNREAD" in msg.get("labelIds", []),
                }
            )
        return json.dumps({"query": query, "count": len(out), "emails": out}, ensure_ascii=False)

    @server.tool()
    async def read_email(message_id: str) -> str:
        """Read one email in full: sender, recipients, subject, date and body text [Tier R].

        Args:
            message_id: the id from search_emails
        """
        msg = _api(svc().users().messages().get(userId="me", id=message_id, format="full"))
        h = _headers(msg)
        body = _body_text(msg.get("payload", {}))
        return json.dumps(
            {
                "id": msg["id"],
                "thread_id": msg.get("threadId", ""),
                "from": h.get("from", ""),
                "to": h.get("to", ""),
                "subject": h.get("subject", ""),
                "date": h.get("date", ""),
                "body": body[:MAX_BODY] + (" …(truncated)" if len(body) > MAX_BODY else ""),
            },
            ensure_ascii=False,
        )

    @server.tool()
    async def send_email(to: str, subject: str, body: str, reply_to_id: str = "") -> str:
        """Send an email, or reply in a thread [Tier A: requires the user's approval].

        Args:
            to: recipient email address(es), comma separated
            subject: subject line (ignored when replying; the thread's subject is used)
            body: plain-text message
            reply_to_id: optional message id from search_emails to reply to in its thread
        """
        mail = EmailMessage()
        mail["To"] = to
        mail.set_content(body)
        thread_id = None
        if reply_to_id:
            orig = _api(
                svc()
                .users()
                .messages()
                .get(userId="me", id=reply_to_id, format="metadata", metadataHeaders=["Subject", "Message-ID"])
            )
            h = _headers(orig)
            subj = h.get("subject", subject)
            mail["Subject"] = subj if subj.lower().startswith("re:") else f"Re: {subj}"
            if h.get("message-id"):
                mail["In-Reply-To"] = mail["References"] = h["message-id"]
            thread_id = orig.get("threadId")
        else:
            mail["Subject"] = subject
        raw = {"raw": base64.urlsafe_b64encode(mail.as_bytes()).decode()}
        if thread_id:
            raw["threadId"] = thread_id
        sent = _api(svc().users().messages().send(userId="me", body=raw))
        return json.dumps({"ok": True, "id": sent.get("id"), "to": to, "subject": mail["Subject"]}, ensure_ascii=False)

    return server


if __name__ == "__main__":
    build_server().run()
