"""In-memory fake Google Calendar v3 service for testing and development."""

from __future__ import annotations

from typing import Any


class FakeEventsResource:
    def __init__(self) -> None:
        self.events_db: dict[str, dict[str, Any]] = {}
        self.deleted_ids: list[str] = []

    def list(self, calendarId: str = "primary", **kwargs: Any) -> Any:
        class ListRequest:
            def __init__(self, db: dict[str, dict[str, Any]], req_kwargs: dict[str, Any]) -> None:
                self.db = db
                self.req_kwargs = req_kwargs

            def execute(self) -> dict[str, Any]:
                items = list(self.db.values())
                q = self.req_kwargs.get("q")
                if q:
                    items = [it for it in items if q.lower() in it.get("summary", "").lower()]
                return {"items": items}

        return ListRequest(self.events_db, kwargs)

    def insert(self, calendarId: str = "primary", body: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        class InsertRequest:
            def __init__(self, db: dict[str, dict[str, Any]], body: dict[str, Any] | None) -> None:
                self.db = db
                self.body = body or {}

            def execute(self) -> dict[str, Any]:
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

    def patch(
        self, calendarId: str = "primary", eventId: str | None = None, body: dict[str, Any] | None = None, **kwargs: Any
    ) -> Any:
        class PatchRequest:
            def __init__(self, db: dict[str, dict[str, Any]], eventId: str | None, body: dict[str, Any] | None) -> None:
                self.db = db
                self.eventId = eventId or ""
                self.body = body or {}

            def execute(self) -> dict[str, Any]:
                item = self.db.get(self.eventId, {"id": self.eventId})
                for k, v in self.body.items():
                    item[k] = v
                self.db[self.eventId] = item
                return item

        return PatchRequest(self.events_db, eventId, body)

    def delete(self, calendarId: str = "primary", eventId: str | None = None, **kwargs: Any) -> Any:
        class DeleteRequest:
            def __init__(self, resource: FakeEventsResource, eventId: str | None) -> None:
                self.resource = resource
                self.eventId = eventId or ""

            def execute(self) -> dict[str, Any]:
                self.resource.deleted_ids.append(self.eventId)
                self.resource.events_db.pop(self.eventId, None)
                return {}

        return DeleteRequest(self, eventId)


class FakeCalendarService:
    def __init__(self) -> None:
        self._events = FakeEventsResource()

    def events(self) -> FakeEventsResource:
        return self._events
