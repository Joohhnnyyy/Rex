import pytest
from httpx import ASGITransport, AsyncClient

from rex_api.main import create_app
from rex_api.settings import Settings


@pytest.fixture
def client():
    app = create_app(Settings(session_secret="test-secret-key-1234567890-abcdefghij", dev_auth=True))
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_magic_link_flow_and_me(client: AsyncClient):
    # 1. Request magic link
    r = await client.post("/v1/auth/magic-link", json={"email": "johny@rex.internal"})
    assert r.status_code == 202
    data = r.json()
    assert "Magic link sent" in data["message"]
    token = data["debug_token"]
    assert token

    # 2. Callback to verify token
    r_cb = await client.get(f"/v1/auth/callback?token={token}")
    assert r_cb.status_code == 200
    cb_data = r_cb.json()
    session_token = cb_data["session_token"]
    assert session_token
    assert cb_data["user"]["email"] == "johny@rex.internal"

    # 3. GET /me with session token
    r_me = await client.get("/v1/me", headers={"Authorization": f"Bearer {session_token}"})
    assert r_me.status_code == 200
    user_me = r_me.json()
    assert user_me["email"] == "johny@rex.internal"

    # 4. PATCH /me to update preferences
    r_patch = await client.patch(
        "/v1/me",
        headers={"Authorization": f"Bearer {session_token}"},
        json={"display_name": "Johny Rex", "preferred_lang": "en-IN"},
    )
    assert r_patch.status_code == 200
    updated = r_patch.json()
    assert updated["display_name"] == "Johny Rex"
    assert updated["preferred_lang"] == "en-IN"


@pytest.mark.asyncio
async def test_invalid_magic_link_token(client: AsyncClient):
    r = await client.get("/v1/auth/callback?token=invalid.jwt.token")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_secure_mode_no_token_leak_and_no_anonymous_access():
    app = create_app(Settings(session_secret="s" * 40))
    c = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    r = await c.post("/v1/auth/magic-link", json={"email": "a@rex.internal"})
    assert r.status_code == 202
    assert r.json()["debug_token"] is None
    assert (await c.get("/v1/me")).status_code == 401
    assert (await c.get("/v1/sessions")).status_code == 401
