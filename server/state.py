"""
Module: server/state.py
Purpose: Thread-Safe In-Memory State Manager for Connected Clients & Chat Groups
Mapped Requirements:
  - R3 (Unique Client Name): Validates and registers unique client usernames.
  - R4 (Connected Client List): Retrieves the list of all currently connected client names.
  - R7 (Private Message Routing): Looks up the target receiver's socket for 1-to-1 delivery.
  - R8 (Create Group): Creates a new group containing only the creator initially.
  - R9 (Group List with Members): Retrieves all existing groups along with their member lists.
  - R10 (Self-Join Group): Adds a requesting client to an existing group.
  - R11 (Group Message Routing): Retrieves sockets of all members belonging to a specific group.
"""

import socket
import threading
from typing import Dict, List, Optional, Set, Tuple


class ServerState:
    """
    Central thread-safe registry managing:
      - Active client sockets mapped to unique usernames (R3, R4, R7)
      - Chat groups and member sets (R8, R9, R10, R11)
      - Thread synchronization using threading.Lock()
    """

    def __init__(self):
        self.lock = threading.Lock()
        # username -> client socket mapping
        self.clients: Dict[str, socket.socket] = {}
        # group_name -> set of member usernames
        self.groups: Dict[str, Set[str]] = {}

    # ==========================================================================
    # 1. Client Registration & Directory (R3, R4, R7)
    # ==========================================================================
    def register_client(self, username: str, sock: socket.socket) -> bool:
        """Attempts to register a client socket under a unique username (R3)."""
        username = username.strip()
        if not username:
            return False

        with self.lock:
            if username in self.clients:
                return False
            self.clients[username] = sock
            return True

    def remove_client(self, username: str) -> None:
        """Removes a client from active directory and group memberships upon disconnect."""
        with self.lock:
            self.clients.pop(username, None)
            for member_set in self.groups.values():
                member_set.discard(username)

    def get_client_list(self) -> List[str]:
        """Returns a sorted list of all currently connected usernames (R4)."""
        with self.lock:
            return sorted(list(self.clients.keys()))

    def get_client_socket(self, username: str) -> Optional[socket.socket]:
        """Returns the socket for a given username, or None if offline (R7)."""
        with self.lock:
            return self.clients.get(username)

    def get_all_client_sockets(self) -> List[socket.socket]:
        """Returns a list of all active client sockets for broadcasting (R4)."""
        with self.lock:
            return list(self.clients.values())

    # ==========================================================================
    # 2. Group Management (R8, R9, R10, R11)
    # ==========================================================================
    def create_group(self, group_name: str, creator_username: str) \
        -> Tuple[bool, str]:
        """
        Creates a new group with the creator as its sole initial member (R8).
        """
        group_name = group_name.strip()
        if not group_name:
            return False, "Group name cannot be empty"

        with self.lock:
            if group_name in self.groups:
                return False, f"Group '{group_name}' already exists"
            self.groups[group_name] = {creator_username}
            return True, "Group created successfully"

    def join_group(self, group_name: str, username: str) -> Tuple[bool, str]:
        """
        Adds a user to an existing group upon their explicit request (R10).
        """
        group_name = group_name.strip()
        with self.lock:
            if group_name not in self.groups:
                return False, f"Group '{group_name}' not found"
            if username in self.groups[group_name]:
                return False, f"You are already in group '{group_name}'"
            self.groups[group_name].add(username)
            return True, "Joined group successfully"

    def get_groups_with_members(self) -> Dict[str, List[str]]:
        """
        Returns all existing groups and their member lists (R9).
        e.g. {"StudyRoom": ["Alice", "Bob"]}
        """
        with self.lock:
            return {g: sorted(list(members)) for g, members in self.groups.items()}

    def get_group_member_sockets(
        self, group_name: str, sender_username: str, exclude_sender: bool = False
    ) -> List[socket.socket]:
        """
        Returns active sockets of members in group_name (R11).
        Verifies sender is in group before returning members.
        """
        with self.lock:
            if group_name not in self.groups:
                return []
            members = self.groups[group_name]
            if sender_username not in members:
                return []

            sockets = []
            for member in members:
                if exclude_sender and member == sender_username:
                    continue
                sock = self.clients.get(member)
                if sock:
                    sockets.append(sock)
            return sockets
