"""
Module: server/ai_service.py
Purpose: Server-Side AI Summarization Service for Private & Group Chat Rooms
Mapped Requirements:
  - B1 (AI Summary Bonus): Summarizes a room's stored chat history on the Server so that
    only the Server (e.g., on Cloud VPS) needs an LLM API key, then returns the summary text
    to be broadcast via `MSG_AI_SUMMARY_RES` to all room members.
"""

# ==============================================================================
# TODO 1: Define AI Configuration & Environment Variables
# ==============================================================================
# - Read `AI_API_KEY = os.environ.get("GEMINI_API_KEY", "")` (or OpenAI/Groq API key).
# - Define `AI_MODEL = "gemini-2.5-flash"` (or configurable model endpoint).
# - Define `SYSTEM_PROMPT`:
#     Instruct the AI to summarize the provided chat conversation concisely in Thai/English
#     (bullet points of key topics, decisions, and action items).

# ==============================================================================
# TODO 2: Implement Prompt Builder (`format_history_for_prompt`)
# ==============================================================================
# - Function `format_history_for_prompt(room_name: str, history: list[dict]) -> str`:
#     1. Take a list of stored message records from `ServerState`, e.g.:
#        `[{"timestamp": "20:01:10", "sender": "Alice", "text": "Hello"}, ...]`
#     2. Format each entry into a readable transcript line:
#        `"[20:01:10] Alice: Hello"`
#     3. Combine with instructions asking the LLM to summarize the conversation in `room_name`.

# ==============================================================================
# TODO 3: Implement LLM API Caller (`generate_chat_summary`)
# ==============================================================================
# - Function `generate_chat_summary(room_name: str, history: list[dict]) -> tuple[bool, str]`:
#     1. Check if `history` is empty:
#        - If empty, return `(False, "No chat messages in this room to summarize yet.")`.
#     2. Check if `AI_API_KEY` is configured:
#        - If missing, either return `(False, "Server AI API key is not configured.")` or
#          provide a fallback local heuristic summary if offline demo mode is enabled.
#     3. Send an HTTP POST request using Python's built-in `urllib.request` (zero external dependencies)
#        to the LLM REST API endpoint with a timeout (e.g., `timeout=15`).
#     4. Parse the JSON response, extract the generated summary string, and return `(True, summary_text)`.
#     5. Catch network/HTTP exceptions cleanly and return `(False, f"AI service error: {err}")`.
