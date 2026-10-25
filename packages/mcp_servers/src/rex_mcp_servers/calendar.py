"""Google Calendar MCP server for Rex.

Provides calendar tools with Asia/Kolkata (IST) defaults:
- list_events: read events in a date range [Tier R]
- find_free_slots: find open appointment windows [Tier R]
- create_event: add an event with optional attendees [Tier W, undo: delete_event]
- update_event: adjust an existing event [Tier W]
- delete_event: cancel / delete an event [Tier A]

Run as stdio server:
    python -m rex_mcp_servers.calendar

One-time login (saves OAuth refresh token):
    python -m rex_mcp_servers.calendar login
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("rex.calendar")
IST = ZoneInfo("Asia/Kolkata")
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def default_token_path() -> Path:
    override = os.environ.get("REX_GOOGLE_TOKEN_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".config" / "rex" / "google_token.json").resolve()


def parse_datetime(dt_str: str, default_end_of_day: bool = False) -> datetime:
    """Parse ISO date or datetime string, defaulting timezone to Asia/Kolkata."""
    dt_str = dt_str.strip()
    # Check date only: YYYY-MM-DD
    if len(dt_str) == 10 and dt_str.count("-") == 2:
        d = datetime.strptime(dt_str, "%Y-%m-%d").date()
        t = time(23, 59, 59) if default_end_of_day else time(0, 0, 0)
        return datetime.combine(d, t, tzinfo=IST)

    # Replace Z with UTC offset if present
    cleaned = dt_str.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError as err:
        raise ValueError(f"Invalid date/time string: {dt_str}") from err

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=IST)
    return parsed


def _real_service():
    """Build a Google Calendar v3 service from ~/.config/rex/google_token.json."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    token_path = default_token_path()
    if not token_path.exists():
        if os.environ.get("REX_FAKE_SERVICES") == "1":
            from rex_mcp_servers.calendar_fake import FakeCalendarService

            return FakeCalendarService()
        raise RuntimeError(
            f"Google token not found at {token_path}. Run 'python -m rex_mcp_servers.calendar login' first."
        )

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
        else:
            raise RuntimeError("Google credentials expired or invalid. Please run login again.")

    return build("calendar", "v3", credentials=creds)


def _login():
    """One-time OAuth interactive browser flow."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env", file=sys.stderr)
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    token_path = default_token_path()
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    print(f"Logged in successfully. Token saved to {token_path}")


def _format_event(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "title": item.get("summary", ""),
        "start": (item.get("start") or {}).get("dateTime") or (item.get("start") or {}).get("date"),
        "end": (item.get("end") or {}).get("dateTime") or (item.get("end") or {}).get("date"),
        "attendees": [a.get("email") for a in item.get("attendees", []) if a.get("email")],
        "description": item.get("description", ""),
        "html_link": item.get("htmlLink", ""),
    }


def build_server(service=None) -> MCPServer:
    """Build the calendar MCPServer. `service` can be a fake for tests."""
    server = MCPServer("calendar")

    def get_svc():
        return service if service is not None else _real_service()

    @server.tool()
    async def list_events(date_from: str, date_to: str, query: str | None = None) -> str:
        """List calendar events in a date range (Asia/Kolkata by default).

        Args:
            date_from: Start date/time (ISO or YYYY-MM-DD).
            date_to: End date/time (ISO or YYYY-MM-DD).
            query: Optional search keyword in title/description.
        """
        svc = get_svc()
        t_min = parse_datetime(date_from, default_end_of_day=False).isoformat()
        t_max = parse_datetime(date_to, default_end_of_day=True).isoformat()

        req_kwargs: dict[str, Any] = {
            "calendarId": "primary",
            "timeMin": t_min,
            "timeMax": t_max,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if query:
            req_kwargs["q"] = query

        resp = svc.events().list(**req_kwargs).execute()
        items = resp.get("items", [])
        events = [_format_event(item) for item in items]
        return json.dumps({"events": events, "count": len(events)}, ensure_ascii=False)

    @server.tool()
    async def find_free_slots(date: str, duration_minutes: int = 30, between: str = "09:00-19:00") -> str:
        """Find free time slots for a meeting on a given date (Asia/Kolkata by default).

        Args:
            date: The target date (YYYY-MM-DD or ISO).
            duration_minutes: Duration required in minutes (default 30).
            between: Daily search window e.g. "09:00-19:00" (default 9 am to 7 pm).
        """
        svc = get_svc()
        day_start = parse_datetime(date, default_end_of_day=False)
        day_date = day_start.date()

        # Parse daily window e.g. "09:00-19:00"
        parts = between.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid between format: {between}. Expected 'HH:MM-HH:MM'")
        sh, sm = (int(x) for x in parts[0].split(":"))
        eh, em = (int(x) for x in parts[1].split(":"))

        win_start = datetime.combine(day_date, time(sh, sm), tzinfo=IST)
        win_end = datetime.combine(day_date, time(eh, em), tzinfo=IST)

        # Query existing events for the whole day
        t_min = win_start.isoformat()
        t_max = win_end.isoformat()
        resp = (
            svc.events()
            .list(calendarId="primary", timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy="startTime")
            .execute()
        )

        busy_spans: list[tuple[datetime, datetime]] = []
        for item in resp.get("items", []):
            st_raw = (item.get("start") or {}).get("dateTime") or (item.get("start") or {}).get("date")
            en_raw = (item.get("end") or {}).get("dateTime") or (item.get("end") or {}).get("date")
            if st_raw and en_raw:
                st = parse_datetime(st_raw)
                en = parse_datetime(en_raw)
                busy_spans.append((st, en))

        # Sort busy intervals
        busy_spans.sort(key=lambda s: s[0])

        # Step through window looking for free slots
        slot_dur = timedelta(minutes=duration_minutes)
        free_slots: list[dict[str, str]] = []
        cur = win_start

        while cur + slot_dur <= win_end and len(free_slots) < 5:
            slot_end = cur + slot_dur
            # Check overlap with any busy span
            conflict = False
            for b_start, b_end in busy_spans:
                if max(cur, b_start) < min(slot_end, b_end):
                    conflict = True
                    cur = max(cur + timedelta(minutes=15), b_end)
                    break
            if not conflict:
                free_slots.append({"start": cur.isoformat(), "end": slot_end.isoformat()})
                cur += slot_dur

        return json.dumps({"date": day_date.isoformat(), "slots": free_slots}, ensure_ascii=False)

    @server.tool()
    async def create_event(
        title: str,
        start: str,
        end: str | None = None,
        duration_minutes: int = 30,
        attendees: list[str] | None = None,
        description: str = "",
    ) -> str:
        """Create a calendar event for the user (Asia/Kolkata by default). Reversible: delete_event undoes it.

        Args:
            title: Title or summary of the meeting/event.
            start: Start date/time (ISO format or YYYY-MM-DDTHH:MM:SS).
            end: End date/time (ISO format). If omitted, start + duration_minutes is used.
            duration_minutes: Duration in minutes if end is omitted (default 30).
            attendees: Optional list of attendee email addresses.
            description: Optional event description or notes.
        """
        svc = get_svc()
        st_dt = parse_datetime(start, default_end_of_day=False)
        if end:
            en_dt = parse_datetime(end, default_end_of_day=False)
        else:
            en_dt = st_dt + timedelta(minutes=duration_minutes)

        body: dict[str, Any] = {
            "summary": title,
            "description": description,
            "start": {"dateTime": st_dt.isoformat()},
            "end": {"dateTime": en_dt.isoformat()},
        }
        if attendees:
            body["attendees"] = [{"email": a} for a in attendees]

        created = svc.events().insert(calendarId="primary", body=body, sendUpdates="none").execute()
        return json.dumps(
            {
                "id": created.get("id"),
                "title": created.get("summary", title),
                "start": st_dt.isoformat(),
                "end": en_dt.isoformat(),
                "html_link": created.get("htmlLink", ""),
            },
            ensure_ascii=False,
        )

    @server.tool()
    async def update_event(
        event_id: str,
        title: str | None = None,
        start: str | None = None,
        end: str | None = None,
        attendees: list[str] | None = None,
        description: str | None = None,
    ) -> str:
        """Update an existing calendar event.

        Args:
            event_id: ID of the event to update.
            title: New title if changing.
            start: New start time if moving.
            end: New end time if changing.
            attendees: New attendee list if replacing.
            description: New description if changing.
        """
        svc = get_svc()
        body: dict[str, Any] = {}
        if title is not None:
            body["summary"] = title
        if description is not None:
            body["description"] = description
        if start is not None:
            body["start"] = {"dateTime": parse_datetime(start).isoformat()}
        if end is not None:
            body["end"] = {"dateTime": parse_datetime(end).isoformat()}
        if attendees is not None:
            body["attendees"] = [{"email": a} for a in attendees]

        updated = svc.events().patch(calendarId="primary", eventId=event_id, body=body, sendUpdates="none").execute()
        return json.dumps(_format_event(updated), ensure_ascii=False)

    @server.tool()
    async def delete_event(event_id: str) -> str:
        """Delete / cancel a calendar event [Tier A - requires user approval].

        Args:
            event_id: The ID of the event to delete.
        """
        svc = get_svc()
        svc.events().delete(calendarId="primary", eventId=event_id).execute()
        return json.dumps({"ok": True, "deleted_id": event_id})

    return server


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        _login()
    else:
        build_server().run()
