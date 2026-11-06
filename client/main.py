"""
Module: client/main.py
Purpose: Client Application Entry Point & High-Level GUI Controller
Mapped Requirements:
  - R1 (System Architecture): Runs as a standalone client process on any physical computer,
    connecting to the server's LAN IP and TCP port.
  - R3 (Unique Client Name): Coordinates the login handshake (`gui_login.py`) before transitioning
    to the main Lobby (`gui_lobby.py`).
"""

# ==============================================================================
# TODO 1: Import Standard Modules & Client Components
# ==============================================================================
# - Import `tkinter as tk`
# - Import `NetworkClient` from `client.network`
# - Import `LoginWindow` from `client.gui_login`
# - Import `LobbyWindow` from `client.gui_lobby`

import queue
from client.network import NetworkClient

# ==============================================================================
# TODO 2: Implement Application Controller / Entry Flow (`main()`)
# ==============================================================================
# 1. Create root Tkinter instance (`root = tk.Tk()`).
# 2. Instantiate `NetworkClient()` which manages the TCP socket and incoming `queue.Queue`.
# 3. Display `LoginWindow` first:
#      - User enters Server IP, Port, and desired unique Username (R3).
#      - Connect TCP socket and send `MSG_REGISTER`.
#      - If `MSG_REGISTER_ACK` returns `success=False` (duplicate username), show an error dialog
#        and let the user pick a different name (R3).
#      - If `MSG_REGISTER_ACK` returns `success=True`, transition from `LoginWindow` to `LobbyWindow`.
# 4. Start `root.mainloop()` and ensure socket cleanup on window close (`WM_DELETE_WINDOW`).

def main():
    """R2 Socket Test Launcher."""
    incoming_queue = queue.Queue()
    client = NetworkClient(incoming_queue)

    host = input("Enter Server IP [127.0.0.1]: ").strip() or "127.0.0.1"
    port = int(input("Enter Server Port [5000]: ").strip() or "5000")

    ok, err_msg = client.connect(host, port)
    if not ok:
        print(f"[SOCKET ERROR] Connection failed: {err_msg}")
        return

    print("\n[R2 SOCKET CONNECTED] Raw TCP Socket Interface Ready.")

    while True:
        try:
            # Drain and print raw packets received over socket
            while not incoming_queue.empty():
                msg = incoming_queue.get_nowait()
                mtype = msg.get("type")
                payload = msg.get("payload", {})
                ts = msg.get("timestamp", "")
                print(f"[{ts}] RECV OVER SOCKET -> Type: {mtype} | Payload: {payload}")
                if mtype == "DISCONNECTED":
                    print("[SOCKET CLOSED] Connection lost.")
                    return

            cmd = input("\nType 'send <type> <text>' or 'quit': ").strip()
            if not cmd:
                continue
            if cmd.lower() == "quit":
                break

            parts = cmd.split(" ", 2)
            if parts[0].lower() == "send" and len(parts) == 3:
                client.send_packet(parts[1], {"text": parts[2]})
            else:
                print("Usage: send <msg_type> <text_payload>")

        except KeyboardInterrupt:
            break
  
# ==============================================================================
# TODO 3: Implement CLI Entry Point (`if __name__ == "__main__":`)
# ==============================================================================
# - Call `main()`.

if __name__ == "__main__":
    main()