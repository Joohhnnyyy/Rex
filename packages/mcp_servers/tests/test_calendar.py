import json

import pytest
from mcp import Client

from rex_mcp_servers.calendar import build_server, parse_datetime


class FakeEventsResource:
    def __init__(self):
        self.events_db = {}
        self.deleted_ids = []

    def list(self, calendarId="primary", **kwargs):
        class ListRequest:
            def __init__(self, db, kwargs):
                self.db = db
                self.kwargs = kwargs

            def execute(self):
                items = list(self.db.values())
                q = self.kwargs.get("q")
                if q:
                    items = [it for it in items if q.lower() in it.get("summary", "").lower()]
                return {"items": items}

        return ListRequest(self.events_db, kwargs)

    def insert(self, calendarId="primary", body=None, **kwargs):
        class InsertRequest:
            def __init__(self, db, body):
                self.db = db
                self.body = body or {}

            def execute(self):
                ev_id = f"evt_{len(self.db) + 1}"
                res = {
                    "id": ev_id,
                    "summary": self.body.get("summary", ""),
                    "description": self.body.get("description", ""),
                    "start": self.body.get("start"),
                    "end": self.body.get("end"),
                    "attendees": self.body.get("attendees", []),
                    "htmlLink": f"https://calendar.google.com/event?eid={ev_id}",
                }
                self.db[ev_id] = res
                return res

        return InsertRequest(self.events_db, body)

    def patch(self, calendarId="primary", eventId=None, body=None, **kwargs):
        class PatchRequest:
            def __init__(self, db, eventId, body):
                self.db = db
                self.eventId = eventId
                self.body = body or {}

            def execute(self):
                item = self.db.get(self.eventId, {"id": self.eventId})
                for k, v in self.body.items():
                    item[k] = v
                self.db[self.eventId] = item
                return item

        return PatchRequest(self.events_db, eventId, body)

    def delete(self, calendarId="primary", eventId=None, **kwargs):
        class DeleteRequest:
            def __init__(self, resource, eventId):
                self.resource = resource
                self.eventId = eventId

            def execute(self):
                self.resource.deleted_ids.append(self.eventId)
                self.resource.events_db.pop(self.eventId, None)
                return {}

        return DeleteRequest(self, eventId)


class FakeCalendarService:
    def __init__(self):
        self._events = FakeEventsResource()

    def events(self):
        return self._events


def test_parse_datetime_ist_default():
    dt = parse_datetime("2026-10-26")
    assert dt.strftime("%Y-%m-%d") == "2026-10-26"
    assert str(dt.tzinfo) == "Asia/Kolkata"

    dt_time = parse_datetime("2026-10-26T16:00:00")
    assert dt_time.hour == 16
    assert str(dt_time.tzinfo) == "Asia/Kolkata"


def test_parse_datetime_invalid():
    with pytest.raises(ValueError):
        parse_datetime("not-a-valid-date")


async def test_create_event_and_list():
    fake_svc = FakeCalendarService()
    server = build_server(service=fake_svc)

    async with Client(server) as client:
        # Create event
        r = await client.call_tool(
            "create_event",
            {
                "title": "Demo Standup",
                "start": "2026-10-26T10:00:00",
                "duration_minutes": 30,
                "attendees": ["johny@example.com"],
            },
        )
        data = json.loads(r.content[0].text)
        assert data["id"] == "evt_1"
        assert data["title"] == "Demo Standup"
        assert "+05:30" in data["start"]
        assert "+05:30" in data["end"]
        assert "calendar.google.com" in data["html_link"]

        # List events
        r_list = await client.call_tool(
            "list_events",
            {"date_from": "2026-10-26", "date_to": "2026-10-26"},
        )
        list_data = json.loads(r_list.content[0].text)
        assert list_data["count"] == 1
        assert list_data["events"][0]["title"] == "Demo Standup"


async def test_find_free_slots_with_existing_event():
    fake_svc = FakeCalendarService()
    # Prepopulate an event at 10:00-11:00
    fake_svc.events().events_db["evt_busy"] = {
        "id": "evt_busy",
        "summary": "Busy Meeting",
        "start": {"dateTime": "2026-10-26T10:00:00+05:30"},
        "end": {"dateTime": "2026-10-26T11:00:00+05:30"},
    }

    server = build_server(service=fake_svc)
    async with Client(server) as client:
        r = await client.call_tool(
            "find_free_slots",
            {"date": "2026-10-26", "duration_minutes": 60, "between": "09:00-12:00"},
        )
        data = json.loads(r.content[0].text)
        slots = data["slots"]
        # In 09:00-12:00 with busy 10:00-11:00, slots should be 09:00-10:00 and 11:00-12:00
        assert len(slots) == 2
        assert "09:00:00" in slots[0]["start"]
        assert "10:00:00" in slots[0]["end"]
        assert "11:00:00" in slots[1]["start"]
        assert "12:00:00" in slots[1]["end"]


async def test_update_and_delete_event():
    fake_svc = FakeCalendarService()
    fake_svc.events().events_db["evt_1"] = {
        "id": "evt_1",
        "summary": "Old Title",
        "start": {"dateTime": "2026-10-26T10:00:00+05:30"},
        "end": {"dateTime": "2026-10-26T10:30:00+05:30"},
    }

    server = build_server(service=fake_svc)
    async with Client(server) as client:
        # Update
        r_up = await client.call_tool(
            "update_event",
            {"event_id": "evt_1", "title": "New Title"},
        )
        up_data = json.loads(r_up.content[0].text)
        assert up_data["title"] == "New Title"

        # Delete
        r_del = await client.call_tool("delete_event", {"event_id": "evt_1"})
        del_data = json.loads(r_del.content[0].text)
        assert del_data["ok"] is True
        assert del_data["deleted_id"] == "evt_1"
        assert "evt_1" in fake_svc.events().deleted_ids
