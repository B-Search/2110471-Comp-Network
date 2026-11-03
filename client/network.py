"""
Module: client/network.py
Purpose: Client TCP Socket Wrapper & Background Receiver Thread
Mapped Requirements:
  - R2 (Socket Programming Only): Uses `socket.socket(socket.AF_INET, socket.SOCK_STREAM)`
    to exchange newline-delimited JSON envelopes (`type`, `timestamp`, `payload`) with the server.
  - R3–R11 (Fundamental): Sends registration, private messages, group creation/join, and group messages.
  - B1, B3, B4 (Bonus): Sends typing indicator updates (`TYPING`), AI summary requests (`AI_SUMMARY_REQ`),
    and Base64 WAV voice clips (`VOICE_MSG`), while queuing incoming server packets for the GUI.
"""

# ==============================================================================
# TODO 1: Define `NetworkClient` Class
# ==============================================================================
# - Attributes:
#     - `self.sock: socket.socket | None = None`
#     - `self.incoming_queue: queue.Queue = queue.Queue()` (thread-safe bridge to Tkinter)
#     - `self.connected: bool = False`
#     - `self.username: str | None = None`

# ==============================================================================
# TODO 2: Implement Connection & Background Listener Thread (R1, R2, B2)
# ==============================================================================
# - `connect(host: str, port: int) -> tuple[bool, str]`:
#     Create TCP socket, connect to `(host, port)` (supports LAN IP or Cloud VPS Public IP, B2),
#     set `self.connected = True`, and spawn a daemon `threading.Thread` running `self._receive_loop()`.
#
# - `_receive_loop() -> None`:
#     Continuously read newline-delimited JSON envelopes from `self.sock` using `SocketLineBuffer`
#     from `common.protocol`.
#     Each parsed dict has the shape: `{"type": "...", "timestamp": "HH:MM:SS", "payload": {...}}`.
#     Push each parsed dictionary `msg` into `self.incoming_queue.put(msg)`.
#     If the server disconnects or an exception occurs, push a disconnect event to `self.incoming_queue`.
#
# - `disconnect() -> None`:
#     Close `self.sock` cleanly and set `self.connected = False`.

# ==============================================================================
# TODO 3: Implement Fundamental Outgoing Methods (R3, R7, R8, R10, R11)
# ==============================================================================
# All outgoing methods call `encode_message(msg_type, payload)` from `common.protocol`
# which wraps `payload` inside `{"type": msg_type, "timestamp": "HH:MM:SS", "payload": payload}\n`:
#
# - `send_register(username: str) -> None`:
#     Send `MSG_REGISTER` with payload `{"username": username}` (R3).
#
# - `send_private_message(target_user: str, text: str) -> None`:
#     Send `MSG_PRIVATE` with payload `{"to": target_user, "text": text}` (R7).
#
# - `send_create_group(group_name: str) -> None`:
#     Send `MSG_CREATE_GROUP` with payload `{"group": group_name}` (R8).
#
# - `send_join_group(group_name: str) -> None`:
#     Send `MSG_JOIN_GROUP` with payload `{"group": group_name}` (R10).
#
# - `send_group_message(group_name: str, text: str) -> None`:
#     Send `MSG_GROUP` with payload `{"group": group_name, "text": text}` (R11).

# ==============================================================================
# TODO 4: Implement Bonus Feature Outgoing Methods (B1, B3, B4)
# ==============================================================================
# - `send_typing(room_type: str, target: str, is_typing: bool) -> None`:
#     Send `MSG_TYPING` with payload:
#     `{"room_type": room_type, "target": target, "is_typing": is_typing}` (B3).
#
# - `send_ai_summary_request(room_type: str, target: str) -> None`:
#     Send `MSG_AI_SUMMARY_REQ` with payload:
#     `{"room_type": room_type, "target": target}` (B1).
#
# - `send_voice_message(room_type: str, target: str, audio_b64: str, duration: float) -> None`:
#     Send `MSG_VOICE_MSG` with payload:
#     `{"room_type": room_type, "target": target, "audio_b64": audio_b64, "duration": duration}` (B4).
