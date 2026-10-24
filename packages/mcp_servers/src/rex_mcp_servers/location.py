"""Location tools for Rex over OpenStreetMap (no API key needed).

- find_place: search places (Nominatim), biased to India.
- travel_time: driving time/distance between two places (OSRM public router; no live traffic).
- map_link: shareable map links for a place.

Run as an MCP stdio server:  python -m rex_mcp_servers.location
Nominatim usage policy: max 1 request/second and a descriptive User-Agent.
"""

from __future__ import annotations

import json
import os
from urllib.parse import quote_plus

import httpx
from mcp.server.mcpserver import MCPServer

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OSRM = "https://router.project-osrm.org/route/v1/driving"
USER_AGENT = os.environ.get("REX_HTTP_USER_AGENT", "Rex-hackathon/0.1 (Gnani AI challenge demo)")


def build_server(http: httpx.AsyncClient | None = None) -> MCPServer:
    server = MCPServer("location")
    client = http or httpx.AsyncClient(timeout=10)

    async def geocode(query: str, limit: int = 3) -> list[dict]:
        r = await client.get(
            NOMINATIM,
            params={"q": query, "format": "jsonv2", "limit": limit, "countrycodes": "in", "addressdetails": 0},
            headers={"User-Agent": USER_AGENT},
        )
        r.raise_for_status()
        out = []
        for p in r.json():
            lat, lon = float(p["lat"]), float(p["lon"])
            out.append(
                {
                    "name": p.get("name") or p["display_name"].split(",")[0],
                    "address": p["display_name"],
                    "lat": lat,
                    "lon": lon,
                    "map_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=17/{lat}/{lon}",
                }
            )
        return out

    @server.tool()
    async def find_place(query: str) -> str:
        """Search for a place in India (shop, clinic, landmark, area or address). Returns up to 3 matches with
        address, coordinates and a map link. Include the area or city in the query for better results."""
        return json.dumps({"query": query, "results": await geocode(query)}, ensure_ascii=False)

    @server.tool()
    async def travel_time(origin: str, destination: str) -> str:
        """Estimate driving time (minutes) and distance (km) between two places in India.
        Estimates do not include live traffic."""
        a, b = await geocode(origin, 1), await geocode(destination, 1)
        if not a:
            raise ValueError(f"Could not find the origin: {origin}")
        if not b:
            raise ValueError(f"Could not find the destination: {destination}")
        o, d = a[0], b[0]
        r = await client.get(
            f"{OSRM}/{o['lon']},{o['lat']};{d['lon']},{d['lat']}",
            params={"overview": "false"},
            headers={"User-Agent": USER_AGENT},
        )
        r.raise_for_status()
        route = r.json()["routes"][0]
        return json.dumps(
            {
                "origin": o["address"],
                "destination": d["address"],
                "minutes": round(route["duration"] / 60),
                "km": round(route["distance"] / 1000, 1),
                "note": "Driving estimate without live traffic; allow extra time at peak hours.",
            },
            ensure_ascii=False,
        )

    @server.tool()
    async def map_link(place: str) -> str:
        """Get shareable map links (OpenStreetMap and Google Maps) for a place, to send to someone."""
        found = await geocode(place, 1)
        if not found:
            raise ValueError(f"Could not find: {place}")
        p = found[0]
        return json.dumps(
            {
                "place": p["address"],
                "openstreetmap": p["map_url"],
                "google_maps": f"https://www.google.com/maps/search/?api=1&query={p['lat']},{p['lon']}",
                "search_link": f"https://www.google.com/maps/search/?api=1&query={quote_plus(place)}",
            },
            ensure_ascii=False,
        )

    return server


if __name__ == "__main__":
    build_server().run()
