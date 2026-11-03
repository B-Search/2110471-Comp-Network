"""
Module: server/client_handler.py
Purpose: Per-Client Worker Thread & Packet Router
Mapped Requirements:
  - R2 (Socket Programming Only): Reads/writes newline-framed JSON envelopes over the client's TCP socket.
  - R3 (Unique Name): Handles initial `REGISTER` handshake before allowing chat operations.
  - R4 (Online Client List): Broadcasts updated `CLIENT_LIST` to all connected clients on join/leave.
  - R7 (Private Message): Routes `PRIVATE_MSG` to receiver, echoes back to sender, and logs history.
  - R8 (Create Group): Handles `CREATE_GROUP` request with creator as sole initial member.
  - R9 (Group List with Members): Broadcasts updated `GROUP_LIST` (with member dict) to all clients.
  - R10 (Self-Join Group): Handles `JOIN_GROUP` request initiated by the joining client itself.
  - R11 (Group Message): Routes `GROUP_MSG` exclusively to members of that group and logs history.
  - B1 (AI Summary): Handles `AI_SUMMARY_REQ`, calls `server.ai_service`, and broadcasts `AI_SUMMARY_RES` to all room members.
  - B3 (Typing Indicator): Routes `TYPING` status to the target peer or group members (excluding sender).
  - B4 (Voice Message): Routes `VOICE_MSG` (Base64 WAV clip) to receiver & sender or all group members.
"""

# ==============================================================================
# TODO 1: Implement Packet Send & Broadcast Helpers
# ==============================================================================
# - `send_packet(sock: socket.socket, msg_type: str, payload: dict) -> None`:
#     Encode `{"type": msg_type, "timestamp": "HH:MM:SS", "payload": payload}` using
#     `common.protocol.encode_message(msg_type, payload)` and send via `sock.sendall()`.
#
# - `send_error(sock: socket.socket, code: str, message: str) -> None`:
#     Call `send_packet(sock, MSG_ERROR, {"code": code, "message": message})`.
#
# - `broadcast_client_list(state: ServerState) -> None`:
#     Build payload `{"clients": state.get_client_list()}` with `MSG_CLIENT_LIST`
#     and send to all connected sockets (R4).
#
# - `broadcast_group_list(state: ServerState) -> None`:
#     Build payload `{"groups": state.get_groups_with_members()}` with `MSG_GROUP_LIST`
#     (where `"groups"` maps `group_name -> list[member_username]`) and send to all connected sockets (R9).

# ==============================================================================
# TODO 2: Implement Per-Client Connection Lifecycle (`handle_client`)
# ==============================================================================
# - Function `handle_client(client_sock: socket.socket, client_addr: tuple, state: ServerState) -> None`:
#     1. Track `registered_username = None` and instantiate a `SocketLineBuffer` for `client_sock`.
#     2. Read newline-delimited JSON envelopes `msg` (`{"type": ..., "timestamp": ..., "payload": {...}}`) in a loop:
#        a. Extract `msg_type = msg["type"]`, `timestamp = msg["timestamp"]`, and `payload = msg["payload"]`.
#        b. If `registered_username is None`, only accept `MSG_REGISTER` (R3):
#           - Extract `username = payload.get("username", "").strip()`.
#           - Call `state.register_client(username, client_sock)`.
#           - If accepted:
#               * Set `registered_username = username`.
#               * Send `MSG_REGISTER_ACK` with payload `{"success": True, "message": "OK"}`.
#               * Call `broadcast_client_list(state)` (R4) and send current `MSG_GROUP_LIST` (R9).
#           - If rejected (empty or duplicate name):
#               * Send `MSG_REGISTER_ACK` with payload `{"success": False, "message": "Username already taken"}`.
#        c. Once registered, dispatch Fundamental Actions by `msg_type`:
#           - `MSG_PRIVATE` (R6, R7, B1):
#               Extract `target = payload["to"]` and `text = payload["text"]`.
#               Look up receiver socket in `state.get_client_socket(target)`.
#               If target exists:
#                 Record in `state.add_private_message(registered_username, target, text, server_timestamp)`.
#                 Build outbound payload `{"from": registered_username, "to": target, "text": text}`.
#                 Send `MSG_PRIVATE` to receiver socket AND echo to `client_sock`.
#               Else:
#                 Call `send_error(client_sock, ERR_USER_NOT_FOUND, "Target user is not online")`.
#           - `MSG_CREATE_GROUP` (R8, R9):
#               Extract `group_name = payload["group"].strip()`.
#               Call `state.create_group(group_name, registered_username)`.
#               If created: call `broadcast_group_list(state)`.
#               Else: call `send_error(client_sock, ERR_GROUP_EXISTS, reason)`.
#           - `MSG_JOIN_GROUP` (R9, R10):
#               Extract `group_name = payload["group"].strip()`.
#               Call `state.join_group(group_name, registered_username)`.
#               If joined: call `broadcast_group_list(state)`.
#               Else: call `send_error(client_sock, ERR_GROUP_NOT_FOUND / ERR_ALREADY_IN_GROUP, reason)`.
#           - `MSG_GROUP` (R6, R11, B1):
#               Extract `group_name = payload["group"]` and `text = payload["text"]`.
#               Verify `registered_username` is a member of `group_name`.
#               If valid:
#                 Record in `state.add_group_message(group_name, registered_username, text, server_timestamp)`.
#                 Build outbound payload `{"group": group_name, "from": registered_username, "text": text}`.
#                 Send `MSG_GROUP` to sockets of ALL members in `group_name` (including `registered_username`).
#               Else:
#                 Call `send_error(client_sock, ERR_NOT_IN_GROUP, "You must join the group before sending messages")`.
#        d. Dispatch Bonus Feature Actions (`B1`, `B3`, `B4`):
#           - `MSG_TYPING` (B3 — Discord-style Typing State):
#               Extract `room_type = payload["room_type"]`, `target = payload["target"]`, `is_typing = payload["is_typing"]`.
#               Build outbound payload `{"room_type": room_type, "target": target, "from": registered_username, "is_typing": is_typing}`.
#               If `room_type == "PRIVATE"`: forward to `state.get_client_socket(target)` only.
#               If `room_type == "GROUP"`: forward to `state.get_group_member_sockets(target, registered_username, exclude_sender=True)`.
#           - `MSG_AI_SUMMARY_REQ` (B1 — AI Summary Request & Room Broadcast):
#               Extract `room_type = payload["room_type"]` and `target = payload["target"]`.
#               Spawn a short helper thread so the LLM HTTP request does not block the client's socket reader:
#                 1. Retrieve `history = state.get_room_history(room_type, registered_username, target)`.
#                 2. Call `ok, summary = generate_chat_summary(target, history)` from `server.ai_service`.
#                 3. If `ok`:
#                      Build outbound payload `{"room_type": room_type, "target": target, "requested_by": registered_username, "summary": summary}`.
#                      Broadcast `MSG_AI_SUMMARY_RES` to both peers (if `"PRIVATE"`) or all members of `target` (if `"GROUP"`).
#                 4. If not `ok`:
#                      Call `send_error(client_sock, ERR_AI_UNAVAILABLE, summary)`.
#           - `MSG_VOICE_MSG` (B4 — Base64 WAV Voice Clip):
#               Extract `room_type = payload["room_type"]`, `target = payload["target"]`,
#               `audio_b64 = payload["audio_b64"]`, and `duration = payload["duration"]`.
#               Build outbound payload `{"room_type": room_type, "target": target, "from": registered_username, "audio_b64": audio_b64, "duration": duration}`.
#               If `room_type == "PRIVATE"`: send `MSG_VOICE_MSG` to receiver socket AND echo to `client_sock`.
#               If `room_type == "GROUP"`: send `MSG_VOICE_MSG` to all member sockets in `target` (including `registered_username`).
#     3. In `finally:` block (on client disconnect or socket error):
#        - If `registered_username` was set, remove from `state`, close `client_sock`,
#          and broadcast updated `CLIENT_LIST` (R4) and `GROUP_LIST` (R9).
