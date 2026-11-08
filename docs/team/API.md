# Rex API Reference (v1)

Base URL: `http://localhost:8000` · JSON · FastAPI

The Rex API provides session tokens, connection status verification, file library indexing, and persistent memory storage.

---

## Service Endpoints

### Health Check

| Method | Path | Description |
|---|---|---|
| `GET` | `/healthz` | Returns service health status and identity (`{"status": "ok", "service": "rex-api"}`). |

---

## Realtime & Session

### Mint LiveKit Room Token

| Method | Path | Request Body | Response |
|---|---|---|---|
| `POST` | `/v1/livekit/token` | `{"identity": "user_id", "room": "rex-room"}` | `{"token": "<jwt>", "url": "wss://...", "room": "..."}` |

Generates a cryptographically signed LiveKit access token with microphone and audio publishing permissions, binding the client session to the LiveKit agent worker room.

---

## External Connections

### List Connection Statuses

| Method | Path | Description | Response |
|---|---|---|---|
| `GET` | `/v1/connections` | Evaluates OAuth tokens and credentials for Google, Slack, and Notion. | `{"google": true, "slack": true, "notion": true}` |

### Google OAuth Verification

| Method | Path | Description | Response |
|---|---|---|---|
| `GET` | `/v1/connections/google/token` | Inspects local Google OAuth token validity in `~/.config/rex/google_token.json`. | `{"valid": true, "scopes": [...]}` |

---

## Memory & Personalization

### Read Stored Memories

| Method | Path | Description | Response |
|---|---|---|---|
| `GET` | `/v1/memory` | Retrieves persistent user preferences, facts, and routines. | `[{"id": "...", "fact": "...", "created_at": "..."}]` |

### Save Fact

| Method | Path | Request Body | Response |
|---|---|---|---|
| `POST` | `/v1/memory` | `{"fact": "Prefers morning standups before 11 AM IST"}` | `{"id": "...", "status": "saved"}` |

### Delete Fact

| Method | Path | Description | Response |
|---|---|---|---|
| `DELETE` | `/v1/memory/{fact_id}` | Removes a remembered fact. | `{"status": "deleted"}` |

---

## Proactive Discoveries

### List Discoveries

| Method | Path | Description | Response |
|---|---|---|---|
| `GET` | `/v1/discoveries` | Returns background research discoveries and personalized recommendations. | `[{"id": "...", "title": "...", "summary": "...", "url": "..."}]` |

### Trigger Discovery Run

| Method | Path | Description | Response |
|---|---|---|---|
| `POST` | `/v1/discoveries/trigger` | Manually triggers the autonomous background research loop. | `{"status": "triggered"}` |

---

## File Library (`~/Documents/Rex`)

### List Files

| Method | Path | Description | Response |
|---|---|---|---|
| `GET` | `/v1/files` | Lists categorized documents, downloads, and notes managed by Rex. | `[{"name": "...", "path": "...", "size": 1024, "modified_at": "..."}]` |

### Save Note

| Method | Path | Request Body | Response |
|---|---|---|---|
| `POST` | `/v1/files/note` | `{"filename": "project-notes.md", "content": "# Notes..."}` | `{"path": "...", "status": "saved"}` |
