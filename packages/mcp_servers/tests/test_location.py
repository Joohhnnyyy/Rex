import json

import httpx
from mcp import Client

from rex_mcp_servers.location import build_server

PLACES = {
    "koramangala": [
        {
            "display_name": "Koramangala, Bengaluru, Karnataka, India",
            "lat": "12.9352",
            "lon": "77.6245",
            "name": "Koramangala",
        }
    ],
    "indiranagar": [
        {
            "display_name": "Indiranagar, Bengaluru, Karnataka, India",
            "lat": "12.9784",
            "lon": "77.6408",
            "name": "Indiranagar",
        }
    ],
    "dental clinic koramangala": [
        {
            "display_name": "Smile Dental Clinic, 5th Block, Koramangala, Bengaluru",
            "lat": "12.934",
            "lon": "77.62",
            "name": "Smile Dental Clinic",
        }
    ],
}


def handler(req: httpx.Request) -> httpx.Response:
    assert "Rex" in req.headers["user-agent"]
    if req.url.host == "nominatim.openstreetmap.org":
        q = req.url.params["q"].lower()
        return httpx.Response(200, json=PLACES.get(q, []))
    if req.url.host == "router.project-osrm.org":
        assert "/route/v1/driving/77.6245,12.9352;77.6408,12.9784" in req.url.path
        return httpx.Response(200, json={"code": "Ok", "routes": [{"duration": 1260.0, "distance": 6800.0}]})
    return httpx.Response(404)


def server():
    return build_server(http=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


async def test_find_place_returns_top_matches():
    async with Client(server()) as c:
        r = await c.call_tool("find_place", {"query": "dental clinic koramangala"})
        data = json.loads(r.content[0].text)
        assert data["results"][0]["name"] == "Smile Dental Clinic"
        assert data["results"][0]["map_url"].startswith("https://www.openstreetmap.org/")


async def test_find_place_no_match_is_clear():
    async with Client(server()) as c:
        r = await c.call_tool("find_place", {"query": "atlantis"})
        assert json.loads(r.content[0].text)["results"] == []


async def test_travel_time_in_minutes_and_km():
    async with Client(server()) as c:
        r = await c.call_tool("travel_time", {"origin": "Koramangala", "destination": "Indiranagar"})
        data = json.loads(r.content[0].text)
        assert data["minutes"] == 21
        assert data["km"] == 6.8
        assert "traffic" in data["note"].lower()


async def test_travel_time_unknown_place_is_an_error():
    async with Client(server()) as c:
        r = await c.call_tool("travel_time", {"origin": "atlantis", "destination": "Indiranagar"})
        assert r.is_error


async def test_tools_are_listed_with_descriptions():
    async with Client(server()) as c:
        names = {t.name: t.description for t in (await c.list_tools()).tools}
        assert set(names) == {"find_place", "travel_time", "map_link"}
        assert all(names.values())
