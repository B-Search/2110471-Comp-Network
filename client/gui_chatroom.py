"""
Module: client/gui_chatroom.py
Purpose: Dedicated Tkinter Toplevel Window for a Single Private or Group Chat Room
Mapped Requirements:
  - R5 (Own Chat Room): Each chat between clients (both Private and Group message) has its
    own independent chat room window (`tk.Toplevel`).
  - R6 (Chat Box & Chat Window): Includes a scrollable chat window (`ScrolledText` or `Text` + `Scrollbar`)
    for displaying sent and incoming messages, and a chat box (`Entry` + Send `Button`) for sending text messages.
  - R7 (Private Message): Sends direct text messages to a specific peer; displays messages only in this room.
  - R11 (Group Message): Sends text messages to a joined group; displays messages from group members.
  - B1 (AI Summary): Includes an `"✨ AI Summary"` button to request an AI summary of the room's conversation
    and displays the broadcast summary inside the room.
  - B3 (Typing Indicator): Tracks keypresses with a 3-second debounce timer to send `MSG_TYPING`, and
    displays a live Discord-style `"<user> กำลังพิมพ์..."` status bar above the input box.
  - B4 (Voice Message): Includes a `"🎤 Record / Stop"` button using `client.audio.VoiceRecorder` to send
    voice clips (`MSG_VOICE_MSG`) and embeds a clickable `"▶ Play Voice (Xs)"` button inside the chat window.
"""

# ==============================================================================
# TODO 1: Define `ChatRoomWindow` Class (`tk.Toplevel`)
# ==============================================================================
# - Constructor parameters:
#     - `parent`: parent Tkinter widget (`LobbyWindow` / `root`)
#     - `room_type`: `"PRIVATE"` or `"GROUP"` (`ROOM_PRIVATE` / `ROOM_GROUP`)
#     - `target_name`: peer's username (for `"PRIVATE"`) or group name (for `"GROUP"`)
#     - `own_username`: the current client's username
#     - `network_client`: reference to `NetworkClient` (or callbacks for text, typing, AI summary, and voice)
#     - `on_close_callback`: function to notify `LobbyWindow` when this window is closed/hidden
# - Typing Indicator state attributes (B3):
#     - `self.is_currently_typing: bool = False`
#     - `self.typing_Reset_job: str | None = None`  # stores `self.after()` timer ID for 3-second idle timeout
#     - `self.typing_users: set[str] = set()`       # tracks peers currently typing in this room

# ==============================================================================
# TODO 2: Build Chat Room UI Components (R5, R6, B1, B3, B4)
# ==============================================================================
# 1. Window Title & Top Header Bar:
#      - For Private room: `"Private Chat with <target_name> — (<own_username>)"`
#      - For Group room: `"Group Chat: <target_name> — Members: [...]"`
#      - Top-right Action Button: `"✨ AI Summary"` button that calls
#        `network_client.send_ai_summary_request(self.room_type, self.target_name)` (B1).
# 2. Chat Window (Message Display Area — R6, B1, B4):
#      - Read-only `tkinter.scrolledtext.ScrolledText` (state=`"disabled"`, enabled briefly when appending).
#      - Displays echoed sent messages, incoming text messages, embedded `"▶ Play Voice"` buttons (`window_create`),
#        and highlighted AI Summary blocks.
# 3. Discord-Style Typing Indicator Label (B3):
#      - A subtle status label (`tk.Label`) directly above the input box, e.g., `"💬 Alice กำลังพิมพ์..."`
#        (or empty string `""` when nobody is typing).
# 4. Chat Box & Voice Controls (Bottom Bar — R6, B4):
#      - Text input box (`tk.Entry`) bound to `<KeyPress>` (for typing indicator, B3) and `<Return>` (to send, R6).
#      - `"Send"` button (`tk.Button`) to send text message (R6).
#      - `"🎤 Voice"` toggle button (`tk.Button`) to start/stop recording a `.wav` voice clip via `VoiceRecorder` (B4).

# ==============================================================================
# TODO 3: Implement Text Message & Typing Indicator Handlers (R6, R7, R11, B3)
# ==============================================================================
# - `on_key_press(event) -> None` (B3 — Typing Debounce Logic):
#     1. Ignore Return/modifier keys.
#     2. If `not self.is_currently_typing`:
#          Set `self.is_currently_typing = True` and call
#          `network_client.send_typing(self.room_type, self.target_name, True)`.
#     3. Cancel any existing `self.typing_reset_job` via `self.after_cancel(...)`.
#     4. Schedule a new 3000ms timer: `self.typing_reset_job = self.after(3000, self._stop_typing)`.
#
# - `_stop_typing() -> None` (B3):
#     If `self.is_currently_typing`:
#       Set `self.is_currently_typing = False`, clear `self.typing_reset_job = None`, and call
#       `network_client.send_typing(self.room_type, self.target_name, False)`.
#
# - `on_send() -> None` (R6, B3):
#     Read text from the input box, strip whitespace. If non-empty:
#     Call `self._stop_typing()` immediately so the peer's typing indicator clears right away,
#     send the message (`send_private_message` or `send_group_message`), and clear the input box.
#
# - `update_typing_status(sender: str, is_typing: bool) -> None` (B3):
#     Add or remove `sender` from `self.typing_users`.
#     Update the Typing Indicator Label text (e.g., `"Alice กำลังพิมพ์..."` or `"Alice, Bob กำลังพิมพ์..."`).

# ==============================================================================
# TODO 4: Implement Display Handlers for Text, AI Summary, & Voice Clips (R6, B1, B4)
# ==============================================================================
# - `append_message(sender: str, text: str, timestamp: str = "") -> None` (R6):
#     Also remove `sender` from `self.typing_users` (in case a message arrived before `is_typing=False`).
#     Unlock `ScrolledText`, insert `f"[{timestamp}] {'You' if sender == self.own_username else sender}: {text}\n"`,
#     scroll to bottom (`see("end")`), and re-lock.
#
# - `append_ai_summary(requested_by: str, summary: str, timestamp: str = "") -> None` (B1):
#     Unlock `ScrolledText`, insert a visually distinct AI Summary block showing `timestamp`,
#     `requested_by`, and the `summary` text, scroll to bottom, and re-lock.
#
# - `append_voice_message(sender: str, audio_b64: str, duration: float, timestamp: str = "") -> None` (B4):
#     Unlock `ScrolledText`, insert `f"[{timestamp}] {'You' if sender == self.own_username else sender} sent a voice clip: "`,
#     embed a `tk.Button(text=f"▶ Play ({duration:.1f}s)", command=lambda: play_voice_b64(audio_b64))`
#     into the `ScrolledText` via `self.chat_display.window_create("end", window=play_btn)`,
#     insert `"\n"`, scroll to bottom, and re-lock.
