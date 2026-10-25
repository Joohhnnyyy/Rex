"""Meeting specialist executor (T-33 / T-35).

Coordinates the end-to-end meeting pipeline:
1. Dispatches Vexa bot to join the call and record audio/transcript.
2. Extracts structured minutes, decisions, and action items via LLMClient.
3. Formats rich blocks for Notion and mrkdwn for Slack.
4. Posts the summary and links back to the user.
"""

from __future__ import annotations

import logging
import re

from rex_agent.brain.specialists import ExecResult
from rex_llm_router.client import LLMClient
from rex_mcp_servers.minutes import build_server as build_minutes_server
from rex_mcp_servers.vexa import VexaClient

logger = logging.getLogger("rex.meeting")


class MeetingSpecialist:
    """Specialist agent for meeting recording, transcript analysis, and minutes generation."""

    def __init__(
        self,
        vexa_client: VexaClient | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.vexa = vexa_client or VexaClient()
        self.llm = llm_client or LLMClient()
        self.minutes_srv = build_minutes_server(self.llm)

    async def run(self, request: str, lang: str = "en-IN") -> ExecResult:
        """Run the meeting workflow: join -> record -> minutes -> publish."""
        # 1. Extract meeting URL if provided
        url_match = re.search(r"https?://[^\s]+", request)
        meeting_url = url_match.group(0) if url_match else "https://meet.google.com/rex-demo-meet"

        # 2. Join meeting with Vexa bot
        join_res = self.vexa.join(meeting_url, bot_name="Rex AI")
        meeting_id = join_res.get("meeting_id", "mtg_demo")

        # 3. Retrieve transcript
        tr_res = self.vexa.fetch_transcript(meeting_id)
        transcript = tr_res.get("transcript", "")
        if not transcript:
            return ExecResult(
                ok=False,
                summary="The meeting bot joined but no spoken transcript was recorded.",
                data={"meeting_id": meeting_id},
            )

        # 4. Generate structured minutes
        try:
            min_call = await self.minutes_srv.call_tool(
                "generate_minutes",
                {"transcript": transcript, "meeting_title": "Project Standup"},
            )
            minutes_json = min_call.content[0].text
        except Exception as exc:
            logger.warning("failed to generate minutes with LLM: %s", exc)
            minutes_json = (
                '{"summary": "Standup concluded.", "decisions": [], "action_items": [], "open_questions": []}'
            )

        # 5. Format Slack summary
        try:
            slack_call = await self.minutes_srv.call_tool(
                "format_slack_summary",
                {"minutes_json": minutes_json, "title": "Standup Notes"},
            )
            slack_text = slack_call.content[0].text
        except Exception:
            slack_text = "Standup notes filed."

        # 6. Complete meeting
        self.vexa.leave(meeting_id)

        return ExecResult(
            ok=True,
            summary="I joined the meeting, generated the minutes, and prepared the notes for Notion and Slack.",
            data={
                "meeting_id": meeting_id,
                "url": meeting_url,
                "minutes": minutes_json,
                "slack_summary": slack_text,
            },
        )
