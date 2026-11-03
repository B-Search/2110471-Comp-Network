"""
Module: common/protocol.py
Purpose: Shared Application-Layer Protocol Specification & TCP Framing Helpers
Mapped Requirements:
  - R1 (System Architecture): Defines the application-layer JSON protocol running on top of TCP/IP.
  - R2 (Socket Programming Only): Defines raw TCP byte-stream framing (newline-delimited UTF-8 JSON).
  - R3–R11 (Fundamental Features): Defines the 3-key Envelope (`type`, `timestamp`, `payload`),
    message type constants, error code constants, and payload structures.
  - B1, B3, B4 (Bonus Features): Defines `TYPING`, `AI_SUMMARY_REQ`, `AI_SUMMARY_RES`, and `VOICE_MSG`.
"""

# ==============================================================================
# TODO 1: Define Network & Framing Constants
# ==============================================================================
# - DEFAULT_HOST = "0.0.0.0"   # Server bind address across all LAN / Cloud VPS interfaces
# - DEFAULT_PORT = 5000        # Default TCP listening port
# - ENCODING     = "utf-8"     # Standard wire character encoding
# - DELIMITER    = "\n"        # Newline delimiter separating JSON packets on the TCP stream
# - BUFFER_SIZE  = 16384       # Byte chunk size for `sock.recv(BUFFER_SIZE)` (sized to handle Base64 voice clips smoothly)

# ==============================================================================
# TODO 2: Define Standard JSON Envelope Keys & Room Type Constants
# ==============================================================================
# Every packet exchanged between Client and Server MUST use this 3-key top-level structure:
#   {
#       "type": "<MESSAGE_TYPE>",
#       "timestamp": "HH:MM:SS",
#       "payload": { ... }
#   }
# - KEY_TYPE      = "type"
# - KEY_TIMESTAMP = "timestamp"
# - KEY_PAYLOAD   = "payload"
#
# Room Type Constants (used in `TYPING`, `AI_SUMMARY_REQ`, `AI_SUMMARY_RES`, `VOICE_MSG`):
# - ROOM_PRIVATE  = "PRIVATE"
# - ROOM_GROUP    = "GROUP"

# ==============================================================================
# TODO 3: Define Fundamental Message Type Constants & Payloads (R3–R11)
# ==============================================================================
# 1. Registration (R3):
#    - MSG_REGISTER     = "REGISTER"
#      Client -> Server payload: `{"username": "<str>"}`
#    - MSG_REGISTER_ACK = "REGISTER_ACK"
#      Server -> Client payload: `{"success": <bool>, "message": "<str>"}`
#
# 2. Online Client Directory (R4):
#    - MSG_CLIENT_LIST  = "CLIENT_LIST"
#      Server -> All payload:    `{"clients": ["<username1>", "<username2>", ...]}`
#
# 3. Private 1-to-1 Chat (R5, R6, R7):
#    - MSG_PRIVATE      = "PRIVATE_MSG"
#      Client -> Server payload:           `{"to": "<target_user>", "text": "<str>"}`
#      Server -> Receiver & Sender (Echo): `{"from": "<sender_user>", "to": "<target_user>", "text": "<str>"}`
#
# 4. Group Management & Directory (R8, R9, R10):
#    - MSG_CREATE_GROUP = "CREATE_GROUP"
#      Client -> Server payload: `{"group": "<group_name>"}` (creator becomes sole initial member, R8)
#    - MSG_JOIN_GROUP   = "JOIN_GROUP"
#      Client -> Server payload: `{"group": "<group_name>"}` (self-join only, R10)
#    - MSG_GROUP_LIST   = "GROUP_LIST"
#      Server -> All payload:    `{"groups": {"<group_name>": ["<member1>", "<member2>", ...]}}` (R9)
#
# 5. Group Chat Messaging (R5, R6, R11):
#    - MSG_GROUP        = "GROUP_MSG"
#      Client -> Server payload:               `{"group": "<group_name>", "text": "<str>"}`
#      Server -> Group Members (incl. Sender): `{"group": "<group_name>", "from": "<sender_user>", "text": "<str>"}`
#
# 6. Error Reporting:
#    - MSG_ERROR        = "ERROR"
#      Server -> Client payload: `{"code": "<ERROR_CODE>", "message": "<human_readable_str>"}`

# ==============================================================================
# TODO 4: Define Bonus Feature Message Type Constants & Payloads (B1, B3, B4)
# ==============================================================================
# 7. Typing Indicator (B3 — Discord-style typing status):
#    - MSG_TYPING         = "TYPING"
#      Client -> Server payload:
#        `{"room_type": "PRIVATE" | "GROUP", "target": "<peer_or_group>", "is_typing": <bool>}`
#      Server -> Peer or Group Members (excluding sender) payload:
#        `{"room_type": "PRIVATE" | "GROUP", "target": "<peer_or_group>", "from": "<sender_user>", "is_typing": <bool>}`
#
# 8. AI Chat Summary (B1 — Server-side history & LLM summary broadcast):
#    - MSG_AI_SUMMARY_REQ = "AI_SUMMARY_REQ"
#      Client -> Server payload:
#        `{"room_type": "PRIVATE" | "GROUP", "target": "<peer_or_group>"}`
#    - MSG_AI_SUMMARY_RES = "AI_SUMMARY_RES"
#      Server -> All Participants in that Room payload:
#        `{"room_type": "PRIVATE" | "GROUP", "target": "<peer_or_group>", "requested_by": "<username>", "summary": "<str>"}`
#
# 9. Voice Message Clips (B4 — Base64 WAV audio clip over TCP JSON):
#    - MSG_VOICE_MSG      = "VOICE_MSG"
#      Client -> Server payload:
#        `{"room_type": "PRIVATE" | "GROUP", "target": "<peer_or_group>", "audio_b64": "<base64_wav_str>", "duration": <float>}`
#      Server -> Receiver & Sender (for PRIVATE) or All Group Members (for GROUP) payload:
#        `{"room_type": "PRIVATE" | "GROUP", "target": "<peer_or_group>", "from": "<sender_user>", "audio_b64": "<base64_wav_str>", "duration": <float>}`

# ==============================================================================
# TODO 5: Define Standard Error Code Constants (`payload["code"]` in `MSG_ERROR`)
# ==============================================================================
# - ERR_USERNAME_TAKEN   = "USERNAME_TAKEN"    # R3: Username is empty or already in use
# - ERR_NOT_REGISTERED   = "NOT_REGISTERED"    # R3: Client sent action before registering
# - ERR_USER_NOT_FOUND   = "USER_NOT_FOUND"    # R7/B4: Target private chat user is offline/missing
# - ERR_GROUP_EXISTS     = "GROUP_EXISTS"      # R8: Group name already exists on CREATE_GROUP
# - ERR_GROUP_NOT_FOUND  = "GROUP_NOT_FOUND"   # R10/R11/B1/B3/B4: Target group does not exist
# - ERR_ALREADY_IN_GROUP = "ALREADY_IN_GROUP"  # R10: Client is already a member of the group
# - ERR_NOT_IN_GROUP     = "NOT_IN_GROUP"      # R11/B1/B3/B4: Client tried acting in a group they haven't joined
# - ERR_AI_UNAVAILABLE   = "AI_UNAVAILABLE"    # B1: AI API key missing, history empty, or LLM request failed
# - ERR_INVALID_PACKET   = "INVALID_PACKET"    # Malformed JSON or missing envelope/payload keys

# ==============================================================================
# TODO 6: Implement Envelope Builder & Serialization Helpers
# ==============================================================================
# - Function `build_message(msg_type: str, payload: dict) -> dict`:
#     Construct and return the standard 3-key dictionary:
#     `{"type": msg_type, "timestamp": datetime.now().strftime("%H:%M:%S"), "payload": payload}`
#
# - Function `encode_message(msg_type: str, payload: dict) -> bytes`:
#     Call `build_message(msg_type, payload)`, serialize to a compact single-line JSON string
#     via `json.dumps(..., ensure_ascii=False)`, append `DELIMITER` ("\n"), and `.encode(ENCODING)`.
#
# - Function `decode_message(raw_line: str) -> dict`:
#     Parse a single newline-stripped JSON string via `json.loads(raw_line)` and validate that
#     it is a `dict` containing `"type"`, `"timestamp"`, and `"payload"`.

# ==============================================================================
# TODO 7: Implement TCP Stream Line-Buffer Helper
# ==============================================================================
# - Because TCP (`SOCK_STREAM`) is a continuous byte stream without built-in message boundaries:
#     * Multiple JSON packets may arrive concatenated in a single `sock.recv()` call.
#     * A single JSON packet (especially a `VOICE_MSG` containing `audio_b64`) may arrive split
#       across multiple `sock.recv()` calls.
# - Implement a helper class `SocketLineBuffer`:
#     1. Maintain an internal byte or string buffer per socket connection.
#     2. Append newly received chunks from `sock.recv(BUFFER_SIZE)` into the buffer.
#     3. While `DELIMITER` ("\n") is present in the buffer:
#          - Split off the first complete line (`line, buffer = buffer.split("\n", 1)`).
#          - Ignore empty lines, parse `line` with `decode_message(line)`, and yield/return the dict.
