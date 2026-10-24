import jwt
from fastapi.testclient import TestClient

from rex_api.main import create_app
from rex_api.settings import Settings

SECRET = "test-secret-at-least-32-characters-long!!"


def _client():
    s = Settings(livekit_url="wss://example.livekit.cloud", livekit_api_key="APItest", livekit_api_secret=SECRET)
    return TestClient(create_app(s))


def test_token_grants_join_to_a_rex_room():
    r = _client().post("/v1/livekit/token", json={"identity": "johny", "client": "web"})
    assert r.status_code == 200
    body = r.json()
    assert body["url"] == "wss://example.livekit.cloud"
    assert body["room"].startswith("rex-johny-")
    claims = jwt.decode(body["token"], SECRET, algorithms=["HS256"], options={"verify_aud": False})
    assert claims["iss"] == "APItest"
    assert claims["sub"] == "johny"
    assert claims["video"]["roomJoin"] is True
    assert claims["video"]["room"] == body["room"]
    assert claims["exp"] - claims["nbf"] <= 3600


def test_token_requires_livekit_config():
    s = Settings(livekit_url="", livekit_api_key="", livekit_api_secret="")
    r = TestClient(create_app(s)).post("/v1/livekit/token", json={"identity": "johny"})
    assert r.status_code == 503


def test_identity_is_validated():
    r = _client().post("/v1/livekit/token", json={"identity": "bad name!"})
    assert r.status_code == 422


def test_token_dispatches_the_rex_agent_into_the_room():
    body = _client().post("/v1/livekit/token", json={"identity": "johny"}).json()
    claims = jwt.decode(body["token"], SECRET, algorithms=["HS256"], options={"verify_aud": False})
    agents = claims["roomConfig"]["agents"]
    assert agents == [{"agentName": "rex"}]
