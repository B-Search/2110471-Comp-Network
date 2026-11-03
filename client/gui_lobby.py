"""
Module: client/gui_lobby.py
Purpose: Main Tkinter Lobby Window (Connected Clients List, Group List, & Room Launcher)
Mapped Requirements:
  - R4 (Connected Client List): Displays a live list of all currently connected clients,
    explicitly including the client's own name (e.g., `"Alice (You)"`).
  - R5 (Separate Chat Rooms): Opens and manages dedicated `ChatRoomWindow` (`tk.Toplevel`)
    instances for each Private chat peer and each joined Group chat.
  - R8 (Create Group): Provides UI input/button to create a new chat group (creator is sole initial member).
  - R9 (Group List with Members): Displays all existing chat groups created by any client,
    along with each group's current member list.
  - R10 (Self-Join Group): Provides a "Join Group" button allowing the client to join a selected
    group by themselves (never added automatically by the creator).
  - B1, B3, B4 (Bonus Routing): Dispatches incoming `TYPING`, `AI_SUMMARY_RES`, and `VOICE_MSG`
    packets to the appropriate open `ChatRoomWindow`.
"""

# ==============================================================================
# TODO 1: Define `LobbyWindow` Layout & State
# ==============================================================================
# - State dictionaries to track open chat room windows (R5):
#     - `self.private_rooms: dict[str, ChatRoomWindow] = {}`  # maps peer_username -> ChatRoomWindow
#     - `self.group_rooms: dict[str, ChatRoomWindow] = {}`    # maps group_name -> ChatRoomWindow
#     - `self.groups_data: dict[str, list[str]] = {}`         # latest group -> member list mapping (R9)
#
# - Left Panel — Connected Clients (R4, R5, R7):
#     - Header label showing own username.
#     - `tk.Listbox` or `ttk.Treeview` listing all connected clients (including own name, R4).
#     - "Open Private Chat" button (or double-click binding) to open/focus the 1-to-1
#       `ChatRoomWindow` with the selected peer (R5, R7).
#
# - Right Panel — Chat Groups & Member Lists (R8, R9, R10, R11):
#     - `ttk.Treeview` or `tk.Listbox` showing every existing group name AND its member list (R9).
#     - Entry + "Create Group" button: sends `MSG_CREATE_GROUP` to server (R8).
#     - "Join Selected Group" button: sends `MSG_JOIN_GROUP` for the selected group so the client
#       joins by themselves (R10).
#     - "Open Group Chat" button: if the client is a member of the selected group, opens/focuses
#       the group's `ChatRoomWindow` (R5, R11).

# ==============================================================================
# TODO 2: Implement Queue Polling & Incoming Envelope Dispatcher (`poll_incoming_queue`)
# ==============================================================================
# - Schedule `self.root.after(100, self.poll_incoming_queue)` to process envelopes from `network_client.incoming_queue`:
#   Each incoming `msg` has top-level keys `msg["type"]`, `msg["timestamp"]`, and `msg["payload"]`:
#     - `MSG_CLIENT_LIST` (R4):
#         Extract `clients = msg["payload"]["clients"]`.
#         Refresh the Connected Clients list UI, ensuring own username is included.
#     - `MSG_GROUP_LIST` (R8, R9, R10):
#         Extract `self.groups_data = msg["payload"]["groups"]` (dict of `group_name -> list[str]`).
#         Refresh the Groups + Member Lists UI in the lobby.
#         Also update member list header in any open `self.group_rooms`.
#     - `MSG_PRIVATE` (R5, R6, R7):
#         Extract `sender = msg["payload"]["from"]`, `target = msg["payload"]["to"]`, `text = msg["payload"]["text"]`,
#         and `timestamp = msg["timestamp"]`.
#         Determine the conversation peer (`target` if `sender == self.own_username` via Server Echo, else `sender`).
#         If `self.private_rooms[peer]` is not open yet, automatically create/open its `ChatRoomWindow` (R5).
#         Call `room.append_message(sender, text, timestamp)` on that room's chat display window (R6).
#     - `MSG_GROUP` (R5, R6, R11):
#         Extract `group = msg["payload"]["group"]`, `sender = msg["payload"]["from"]`, `text = msg["payload"]["text"]`,
#         and `timestamp = msg["timestamp"]`.
#         If `self.group_rooms[group]` is not open yet, create/open its `ChatRoomWindow` (R5).
#         Call `room.append_message(sender, text, timestamp)` on that group room's chat display window (R6).
#     - `MSG_TYPING` (B3 — Discord-style Typing Indicator):
#         Extract `room_type = msg["payload"]["room_type"]`, `target = msg["payload"]["target"]`,
#         `sender = msg["payload"]["from"]`, and `is_typing = msg["payload"]["is_typing"]`.
#         Locate the open `ChatRoomWindow` (`self.private_rooms.get(sender)` if `"PRIVATE"`,
#         or `self.group_rooms.get(target)` if `"GROUP"`).
#         If the room window is open, call `room.update_typing_status(sender, is_typing)`.
#     - `MSG_AI_SUMMARY_RES` (B1 — Broadcast AI Summary Result):
#         Extract `room_type = msg["payload"]["room_type"]`, `target = msg["payload"]["target"]`,
#         `requested_by = msg["payload"]["requested_by"]`, `summary = msg["payload"]["summary"]`,
#         and `timestamp = msg["timestamp"]`.
#         Locate or open the corresponding `ChatRoomWindow` and call
#         `room.append_ai_summary(requested_by, summary, timestamp)`.
#     - `MSG_VOICE_MSG` (B4 — Voice Clip Message):
#         Extract `room_type = msg["payload"]["room_type"]`, `target = msg["payload"]["target"]`,
#         `sender = msg["payload"]["from"]`, `audio_b64 = msg["payload"]["audio_b64"]`,
#         `duration = msg["payload"]["duration"]`, and `timestamp = msg["timestamp"]`.
#         Determine the room (`peer = target if sender == self.own_username else sender` for `"PRIVATE"`,
#         or `target` for `"GROUP"`), ensure its `ChatRoomWindow` is open, and call
#         `room.append_voice_message(sender, audio_b64, duration, timestamp)`.
#     - `MSG_ERROR`:
#         Extract `code = msg["payload"]["code"]` and `message = msg["payload"]["message"]`.
#         Display warning/error messagebox to the user.
