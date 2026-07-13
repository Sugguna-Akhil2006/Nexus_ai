# ChatArchitectureReport

## Current Routing Before Fix

- Frontend route: `frontend/app/dashboard/chat/page.tsx`
- Previous message path: the page opened a new WebSocket per send at `/api/chat/ws`.
- Previous payload: `conversation_id`, `workspace_id`, `message`, `user_id`.
- Missing field: no `selected_agent` was sent by the UI.
- Backend behavior: `backend/api/main.py` always executed the global `chat_agent = ChatAgent()` instance.
- Result: all conversations used the default chat implementation with no user-visible or backend-enforced agent routing.

## Backend Endpoint Before Fix

- Existing conversation list: `GET /api/conversations?workspace_id=...`
- Existing message history: `GET /api/conversations/{id}/messages`
- Existing streaming endpoint: `WebSocket /api/chat/ws`
- Missing required contract:
  - `GET /api/agents`
  - `GET /api/agents/{id}`
  - `POST /api/chat/session`
  - `POST /api/chat/message`
  - `GET /api/chat/history`
  - `WebSocket /ws/chat/{session_id}`

## WebSocket Implementation Before Fix

- Endpoint: `/api/chat/ws`
- Protocol: client sent `{"action":"send_message", ...}`.
- Server created a conversation when `conversation_id` was missing.
- Server persisted user and assistant messages in SQLite.
- Server streamed token packets with `conversation_id`, `token`, and `citations`.
- Server sent final `metadata`, but `active_agent` was hardcoded to `ChatAgent`.

## Conversation Model Before Fix

- SQLite table `conversations`: `conversation_id`, `workspace_id`, `title`, `created_at`.
- SQLite table `messages`: `message_id`, `conversation_id`, `role`, `content`, `created_at`.
- Missing persistence:
  - selected agent
  - provider
  - attachments
  - workspace/project/knowledge context metadata
  - execution metadata
  - token usage/runtime metadata

## Runtime Registry Finding

- The project already had `backend.runtime.registry.AgentRegistry`.
- The chat backend initialized concrete agents but did not register chat-routable agents into the runtime registry for Chat UI consumption.
- The fix uses `AgentRegistry` as the source for `GET /api/agents`; the frontend does not hardcode agent entries.
