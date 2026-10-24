"""Mint short-lived LiveKit room tokens for the dashboard / desktop companion.

NOTE: until auth (T-16 magic link) lands, the caller supplies its identity in the body.
Do not expose this endpoint publicly before auth is wired in.
"""

import secrets
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from livekit import api
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/livekit", tags=["livekit"])


class TokenRequest(BaseModel):
    identity: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    client: Literal["web", "desktop"] = "web"


class TokenResponse(BaseModel):
    url: str
    token: str
    room: str


@router.post("/token", response_model=TokenResponse)
async def create_token(body: TokenRequest, request: Request) -> TokenResponse:
    s = request.app.state.settings
    if not (s.livekit_url and s.livekit_api_key and s.livekit_api_secret):
        raise HTTPException(status_code=503, detail="LiveKit is not configured")
    room = f"rex-{body.identity.lower()}-{secrets.token_hex(3)}"
    token = (
        api.AccessToken(s.livekit_api_key, s.livekit_api_secret)
        .with_identity(body.identity)
        .with_name(body.identity)
        .with_ttl(timedelta(seconds=s.livekit_token_ttl_s))
        .with_metadata(f'{{"client":"{body.client}"}}')
        .with_grants(api.VideoGrants(room_join=True, room=room, can_publish=True, can_subscribe=True))
        .with_room_config(api.RoomConfiguration(agents=[api.RoomAgentDispatch(agent_name=s.livekit_agent_name)]))
        .to_jwt()
    )
    return TokenResponse(url=s.livekit_url, token=token, room=room)
