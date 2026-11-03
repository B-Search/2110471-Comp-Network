"""
Module: server/state.py
Purpose: Thread-Safe In-Memory State Manager for Connected Clients, Chat Groups, & Room History
Mapped Requirements:
  - R3 (Unique Client Name): Validates and registers unique client usernames.
  - R4 (Connected Client List): Retrieves the list of all currently connected client names.
  - R7 (Private Message Routing): Looks up the target receiver's socket for 1-to-1 delivery.
  - R8 (Create Group): Creates a new group containing only the creator initially.
  - R9 (Group List with Members): Retrieves all existing groups along with their member lists.
  - R10 (Self-Join Group): Adds a requesting client to an existing group.
  - R11 (Group Message Routing): Retrieves sockets of all members belonging to a specific group.
  - B1 (AI Summary History): Stores in-memory text message history per Private pair and per Group
    so the Server can summarize any room's conversation on request.
"""

# ==============================================================================
# TODO 1: Define `ServerState` Class with Thread Synchronization
# ==============================================================================
# - Initialize `self.lock = threading.Lock()` to protect concurrent access from multiple client threads.
# - Initialize `self.clients: dict[str, socket.socket] = {}` mapping `username -> client_socket`.
# - Initialize `self.groups: dict[str, set[str]] = {}` mapping `group_name -> set of member usernames`.
# - Initialize in-memory chat history stores for AI Summary (B1):
#     * `self.private_history: dict[tuple[str, str], list[dict]] = {}`
#       (keyed by sorted tuple `tuple(sorted([user_a, user_b]))` -> list of `{"timestamp": str, "sender": str, "text": str}`)
#     * `self.group_history: dict[str, list[dict]] = {}`
#       (keyed by `group_name` -> list of `{"timestamp": str, "sender": str, "text": str}`)
#     * Optional `MAX_HISTORY_PER_ROOM = 100` to cap memory usage.

# ==============================================================================
# TODO 2: Implement Client Registration & Removal Methods (R3, R4)
# ==============================================================================
# - `register_client(username: str, sock: socket.socket) -> bool`:
#     Acquire `self.lock`. Check if `username` is non-empty and not already in `self.clients`.
#     If unique, store `self.clients[username] = sock` and return `True`; otherwise return `False` (R3).
#
# - `remove_client(username: str) -> None`:
#     Acquire `self.lock`. Remove `username` from `self.clients` and remove from `self.groups` member sets.
#
# - `get_client_list() -> list[str]`:
#     Acquire `self.lock`. Return `list(self.clients.keys())` (R4).
#
# - `get_client_socket(username: str) -> socket.socket | None`:
#     Acquire `self.lock`. Return `self.clients.get(username)` for private message routing (R7).

# ==============================================================================
# TODO 3: Implement Group Management Methods (R8, R9, R10, R11)
# ==============================================================================
# - `create_group(group_name: str, creator_username: str) -> tuple[bool, str]`:
#     Acquire `self.lock`. Verify `group_name` does not already exist.
#     Create `self.groups[group_name] = {creator_username}` so it initially includes ONLY
#     the creator as a member (R8), and initialize `self.group_history[group_name] = []`.
#     Return `(True, "Group created")` or `(False, "Group name already exists")`.
#
# - `join_group(group_name: str, username: str) -> tuple[bool, str]`:
#     Acquire `self.lock`. Verify `group_name` exists in `self.groups`.
#     Add `username` to `self.groups[group_name]` (R10). Return success/error tuple.
#
# - `get_groups_with_members() -> dict[str, list[str]]`:
#     Acquire `self.lock`. Return `{group: list(members) for group, members in self.groups.items()}`
#     so every client can see all existing groups and their member lists (R9).
#
# - `get_group_member_sockets(group_name: str, sender_username: str, exclude_sender: bool = False) -> list[socket.socket]`:
#     Acquire `self.lock`. Verify `group_name` exists AND `sender_username` is a member of that group (R11).
#     Return the active sockets for all currently connected members of `group_name`
#     (excluding `sender_username` when `exclude_sender=True`, e.g., for `MSG_TYPING`).

# ==============================================================================
# TODO 4: Implement Room History Methods for AI Summary (B1)
# ==============================================================================
# - `add_private_message(sender: str, receiver: str, text: str, timestamp: str) -> None`:
#     Acquire `self.lock`. Compute `pair_key = tuple(sorted([sender, receiver]))`.
#     Append `{"timestamp": timestamp, "sender": sender, "text": text}` to `self.private_history[pair_key]`.
#
# - `add_group_message(group_name: str, sender: str, text: str, timestamp: str) -> None`:
#     Acquire `self.lock`. Append `{"timestamp": timestamp, "sender": sender, "text": text}`
#     to `self.group_history.setdefault(group_name, [])`.
#
# - `get_room_history(room_type: str, requester: str, target: str) -> list[dict]`:
#     Acquire `self.lock`.
#     If `room_type == "PRIVATE"`: return a copy of `self.private_history.get(tuple(sorted([requester, target])), [])`.
#     If `room_type == "GROUP"`: return a copy of `self.group_history.get(target, [])`.
