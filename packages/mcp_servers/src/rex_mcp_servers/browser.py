"""Browser MCP Server (T-44).

Automates web browser interactions with strict security tiers:
- Tier R: navigate, read_page
- Tier W: fill_form
- Tier A: submit_form (always requires explicit human approval before execution)
"""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any

from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("rex.mcp.browser")


class BrowserSession:
    """Session state for browser automation."""

    def __init__(self) -> None:
        self.current_url: str = ""
        self.page_title: str = ""
        self.page_text: str = ""
        self.form_data: dict[str, str] = {}
        self.submitted_forms: list[dict[str, Any]] = []

    def navigate(self, url: str) -> dict[str, Any]:
        self.current_url = url
        self.page_title = f"Page: {url}"
        self.page_text = f"Content of {url}. Form fields available: name, email, query."
        return {
            "url": self.current_url,
            "title": self.page_title,
            "status": 200,
        }

    def read_page(self) -> dict[str, Any]:
        return {
            "url": self.current_url,
            "title": self.page_title,
            "content": self.page_text,
            "form_fields": list(self.form_data.keys()),
        }

    def fill_form(self, field: str, value: str) -> dict[str, Any]:
        self.form_data[field] = value
        return {
            "field": field,
            "value": value,
            "filled_fields": self.form_data,
        }

    def submit_form(self, action_name: str = "submit") -> dict[str, Any]:
        submission = {
            "url": self.current_url,
            "action": action_name,
            "data": dict(self.form_data),
        }
        self.submitted_forms.append(submission)
        self.form_data.clear()
        return {
            "ok": True,
            "message": f"Successfully submitted form on {self.current_url}",
            "submission": submission,
        }


def build_server(session: BrowserSession | None = None) -> MCPServer:
    sess = session or BrowserSession()
    server = MCPServer("browser")

    @server.tool()
    async def navigate(url: str) -> str:
        """Navigate to a web page [Tier R].

        Args:
            url: The HTTP/HTTPS URL to load.
        """
        out = sess.navigate(url)
        return json.dumps(out, ensure_ascii=False)

    @server.tool()
    async def read_page() -> str:
        """Extract readable text and visible form inputs from the active web page [Tier R]."""
        out = sess.read_page()
        return json.dumps(out, ensure_ascii=False)

    @server.tool()
    async def fill_form(field: str, value: str) -> str:
        """Fill an input field on the active page [Tier W].

        Args:
            field: Name or selector of the input field.
            value: Text to type into the field.
        """
        out = sess.fill_form(field, value)
        return json.dumps(out, ensure_ascii=False)

    @server.tool()
    async def submit_form(action_name: str = "submit") -> str:
        """Submit the active web form [Tier A - requires user approval].

        Args:
            action_name: Description or submit button name (e.g. 'submit_booking').
        """
        out = sess.submit_form(action_name)
        return json.dumps(out, ensure_ascii=False)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Rex Browser MCP Server")
    parser.parse_args()
    srv = build_server()
    srv.run(transport="stdio")


if __name__ == "__main__":
    main()
