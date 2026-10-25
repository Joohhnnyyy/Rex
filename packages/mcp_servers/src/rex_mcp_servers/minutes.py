"""MCP server for meeting minutes generation and formatting (T-35).

Tools:
- generate_minutes: extract summary, decisions, action items (with owner and due dates),
  and open questions from a meeting transcript using LLMClient (Mistral/Groq/Gemini).
- format_notion_blocks: transform Minutes JSON into structured Notion page block children.
- format_slack_summary: transform Minutes JSON into formatted Slack mrkdwn with optional Notion link.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from typing import Any

from mcp.server.mcpserver import MCPServer

from rex_llm_router.client import LLMClient
from rex_shared.schemas import Minutes

logger = logging.getLogger("rex.mcp.minutes")

MINUTES_SYSTEM_PROMPT = """You are an expert meeting secretary for Rex AI.
Analyze the provided meeting transcript and extract structured minutes in strict JSON format.

Output JSON matching this exact schema:
{
  "summary": "Concise 1-3 sentence summary of the meeting and main outcomes.",
  "decisions": [
    "Clear statement of agreed decision 1",
    "Clear statement of agreed decision 2"
  ],
  "action_items": [
    {
      "text": "Specific task to complete",
      "owner": "Name of person responsible (or null if unassigned)",
      "due": "YYYY-MM-DD (or null if not specified)"
    }
  ],
  "open_questions": [
    "Unresolved topic or follow-up question 1"
  ]
}

Rules:
- Output ONLY raw JSON, with no markdown code blocks, backticks, or conversational text.
- If no decisions or open questions were made, use empty arrays [].
- Identify owners of action items from context (e.g. Johny, Shanky).
"""


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def minutes_to_notion_blocks(minutes: Minutes, title: str = "Meeting Minutes") -> list[dict[str, Any]]:
    """Convert a Minutes object into Notion block objects."""
    blocks: list[dict[str, Any]] = [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {"rich_text": [{"type": "text", "text": {"content": title}}]},
        },
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": minutes.summary}}],
                "icon": {"emoji": "📝"},
            },
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Decisions"}}]},
        },
    ]

    if minutes.decisions:
        for dec in minutes.decisions:
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": dec}}]},
                }
            )
    else:
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "None recorded."}}]},
            }
        )

    blocks.append(
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Action Items"}}]},
        }
    )

    if minutes.action_items:
        for item in minutes.action_items:
            owner_part = f" (@{item.owner})" if item.owner else ""
            due_part = f" [Due: {item.due.isoformat()}]" if item.due else ""
            item_text = f"{item.text}{owner_part}{due_part}"
            blocks.append(
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": item_text}}],
                        "checked": False,
                    },
                }
            )
    else:
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "No pending action items."}}]},
            }
        )

    if minutes.open_questions:
        blocks.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Open Questions"}}]},
            }
        )
        for q in minutes.open_questions:
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": q}}]},
                }
            )

    return blocks


def minutes_to_slack_mrkdwn(minutes: Minutes, title: str = "Meeting Minutes", notion_url: str = "") -> str:
    """Format a Minutes object as rich Slack mrkdwn."""
    lines = [f":memo: *{title}*", "", f"*Summary:*\n{minutes.summary}", ""]

    lines.append("*Decisions:*")
    if minutes.decisions:
        for d in minutes.decisions:
            lines.append(f"• {d}")
    else:
        lines.append("• _None recorded_")
    lines.append("")

    lines.append("*Action Items:*")
    if minutes.action_items:
        for item in minutes.action_items:
            owner = f" (`@{item.owner}`)" if item.owner else ""
            due = f" *[Due {item.due}]*" if item.due else ""
            lines.append(f"• [ ] {item.text}{owner}{due}")
    else:
        lines.append("• _No action items_")
    lines.append("")

    if minutes.open_questions:
        lines.append("*Open Questions:*")
        for q in minutes.open_questions:
            lines.append(f"• {q}")
        lines.append("")

    if notion_url:
        lines.append(f"<{notion_url}|:link: View full notes in Notion>")

    return "\n".join(lines).strip()


def build_server(llm_client: LLMClient | None = None) -> MCPServer:
    client = llm_client or LLMClient()
    server = MCPServer("minutes")

    @server.tool()
    async def generate_minutes(transcript: str, meeting_title: str = "Standup") -> str:
        """Extract summary, decisions, action items, and open questions from a transcript.

        Args:
            transcript: The meeting transcript text or speaker turns.
            meeting_title: Title or context of the meeting (default: Standup).
        """
        messages = [
            {"role": "system", "content": MINUTES_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Meeting Title: {meeting_title}\n\nTranscript:\n{transcript}",
            },
        ]
        completion = await client.complete(task_kind="summarise", messages=messages)
        cleaned = _clean_json_text(completion.text)
        try:
            parsed = json.loads(cleaned)
            # Validate with shared Pydantic schema
            minutes_obj = Minutes.model_validate(parsed)
            return minutes_obj.model_dump_json(indent=2)
        except Exception as exc:
            logger.warning("failed to validate LLM minutes output: %s; raw: %s", exc, cleaned)
            # Fallback wrapper
            fallback = Minutes(
                summary=cleaned[:300] if cleaned else "Meeting summary unavailable.",
                decisions=[],
                action_items=[],
                open_questions=[],
            )
            return fallback.model_dump_json(indent=2)

    @server.tool()
    async def format_notion_blocks(minutes_json: str, title: str = "Meeting Minutes") -> str:
        """Convert a Minutes JSON string into structured Notion block children.

        Args:
            minutes_json: JSON string matching the Minutes schema.
            title: Title for the Notion page heading.
        """
        data = json.loads(minutes_json)
        minutes_obj = Minutes.model_validate(data)
        blocks = minutes_to_notion_blocks(minutes_obj, title=title)
        return json.dumps(blocks, ensure_ascii=False)

    @server.tool()
    async def format_slack_summary(minutes_json: str, title: str = "Meeting Minutes", notion_url: str = "") -> str:
        """Convert a Minutes JSON string into formatted Slack mrkdwn with optional Notion link.

        Args:
            minutes_json: JSON string matching the Minutes schema.
            title: Meeting title for the header.
            notion_url: Optional link to the published Notion page.
        """
        data = json.loads(minutes_json)
        minutes_obj = Minutes.model_validate(data)
        return minutes_to_slack_mrkdwn(minutes_obj, title=title, notion_url=notion_url)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Rex MCP Server - Meeting Minutes Generator")
    parser.parse_args()
    srv = build_server()
    srv.run(transport="stdio")


if __name__ == "__main__":
    main()
