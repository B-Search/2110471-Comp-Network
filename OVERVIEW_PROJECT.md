# Project Overview & Single Source of Truth

> **Document Status:** Active
> **Last Synchronized:** 2026-11-03
> **Current Sprint / Phase:** Phase 1 - Protocol Contract (Part 1, Part 2 & Part 3 Bonus) Locked & Skeleton Initialized

---

## 1. Project Synopsis & Background
- **What is this project?** A multi-client networked chat application built in Python using raw TCP Socket Programming and a Tkinter GUI.
- **Origin & Context:** Term Project for Computer Networks (`Simple Chat Application`). Designed to demonstrate socket programming across at least two physical client computers communicating through a central server (hosted on LAN or a Cloud VPS).
- **Scope:** Covers **Part 1 (System Architecture Design: R1–R2)**, **Part 2 (Fundamental Implementation: R3–R11)**, and **Part 3 (Bonus / Special Features: B1–B4)**.

---

## 2. Objectives & Requirements Mapping (`R1`–`R11` & `B1`–`B4`)

### Part 1: System Architecture Design (1.5 points)
- **R1 (1.0):** Present system architecture with at least two clients on different physical computers and one server (on one of those computers, a third machine, or a Cloud VPS). Explain protocols used (TCP/IP + custom JSON application framing), why selected (reliable, ordered, connection-oriented delivery), and how used.
- **R2 (0.5):** Chat messages between server and clients must be implemented using **Socket Programming only** (`socket` module).

### Part 2: Fundamental Implementation (7.0 points)
- **R3 (0.5):** Each client must have a **unique name** (validated by server upon login/registration).
- **R4 (0.5):** Each client can see a **list of names of all clients** currently connected to the server, **including its own name**.
- **R5 (0.5):** Each chat between clients (both **Private** and **Group** message) must have **its own chat room** (implemented as dedicated `tk.Toplevel` windows per peer/group).
- **R6 (0.5):** Each chat room (both **Private** and **Group** message) must include a **chat box** for sending text messages and a **chat window** for displaying sent messages and new incoming messages.
- **R7 (1.0) [Private]:** Each client can send a direct text message to any client in the list. **Only the sender and receiver** can see the messages.
- **R8 (1.0) [Group]:** Each client can create chat group(s), which **initially includes only themselves** as a member.
- **R9 (1.0) [Group]:** Each client can see a **list of all existing chat groups (with the member list)** created by any client.
- **R10 (1.0) [Group]:** Clients can choose to **join a group chat only by themselves**; they are **not** added automatically by the group creator.
- **R11 (1.0) [Group]:** Each client can send a text message to a group they have joined. **Only the members of that chat group** can see the messages.

### Part 3: Bonus / Special Features (1.5 points)
- **B1 [AI Summary]:** Server stores per-room chat history in memory and summarizes the conversation on request (`AI_SUMMARY_REQ`) using an LLM API (`server/ai_service.py`), broadcasting the summary (`AI_SUMMARY_RES`) to all participants in that room.
- **B2 [Cloud VPS Deployment]:** Server binds to `0.0.0.0` on a Cloud VPS with an open TCP firewall port so clients on any network can connect via the VPS Public IP.
- **B3 [Typing Indicator]:** Discord-style real-time `"<user> is typing..."` status bar (`TYPING`) in both Private and Group chat rooms, with automatic debounce/timeout after 3 seconds of inactivity or upon sending a message.
- **B4 [Voice Message]:** Push-to-talk / recorded `.wav` audio clips (`client/audio.py`) encoded in Base64 (`VOICE_MSG`) and sent over the same TCP JSON connection for playback inside Private and Group chat rooms.

---

## 3. System Architecture & Tech Stack
- **Architecture Overview:** Centralized Client-Server star topology over TCP/IP (LAN or Cloud VPS Public IP).
  - **Transport Layer:** TCP (`socket.AF_INET`, `socket.SOCK_STREAM`) for reliable, ordered byte-stream delivery without packet loss.
  - **Application Protocol Layer:** Newline-delimited (`\n`) UTF-8 JSON messages using a standardized 3-key Envelope (`type`, `timestamp`, `payload`).
- **Frontend (Client GUI):** Python `tkinter` & `tkinter.ttk`
  - **Login Window (`client/gui_login.py`):** Server IP (LAN or Cloud VPS Public IP), Port, and unique Username input.
  - **Main Lobby (`client/gui_lobby.py`):** Displays online clients (`R4`) and all groups with member lists (`R9`), plus controls to open Private Chats (`R5`), Create Group (`R8`), and Join Group (`R10`).
  - **Chat Room Window (`client/gui_chatroom.py`):** Separate `tk.Toplevel` window per Private peer or joined Group (`R5`), with message history display, input box (`R6`), Typing Indicator status bar (`B3`), AI Summary trigger (`B1`), and Voice Message recorder/player (`B4`).
  - **Audio Helper (`client/audio.py`):** Records/plays short `.wav` voice clips and converts between raw audio bytes and Base64 strings (`B4`).
- **Backend (Server):** Python `socket` + `threading`
  - One main listening thread accepting connections (`server/server.py`).
  - Thread-safe state store protected by `threading.Lock` (`server/state.py`), maintaining active clients, groups, and per-room message history for AI summarization.
  - Dedicated worker thread per connected client (`server/client_handler.py`).
  - Server-side AI Summarizer (`server/ai_service.py`) calling an LLM HTTP API via `urllib.request` so clients do not need local API keys (`B1`).
- **Directory Structure:**
  ```text
  CompNetwork/
  ├── GEMINI.md                  # Workspace rules & directives
  ├── OVERVIEW_PROJECT.md        # Single Source of Truth architecture & specs
  ├── SESSION_STATE.md           # Session progress & handoff state
  ├── common/
  │   ├── __init__.py
  │   └── protocol.py            # Shared JSON message types, schemas & TCP framing specs (R1, R2, B1, B3, B4)
  ├── server/
  │   ├── __init__.py
  │   ├── server.py              # TCP listener entry point & thread spawner (R1, R2, B2)
  │   ├── state.py               # Thread-safe registry of clients, groups & room chat history (R3, R4, R8–R10, B1)
  │   ├── client_handler.py      # Per-client packet router & broadcast logic (R2–R11, B1, B3, B4)
  │   └── ai_service.py          # LLM API integration for summarizing room chat history (B1)
  └── client/
      ├── __init__.py
      ├── main.py                # Client application entry point & UI controller
      ├── network.py             # Client TCP socket thread & thread-safe UI queue (R2, B1, B3, B4)
      ├── audio.py               # WAV voice clip recording, playback & Base64 encoding/decoding (B4)
      ├── gui_login.py           # Login dialog for Server IP (LAN/VPS), port & unique username (R1, R3, B2)
      ├── gui_lobby.py           # Main lobby showing client list & group list (R4, R8, R9, R10)
      └── gui_chatroom.py        # Separate Toplevel window per Private/Group room (R5–R7, R11, B1, B3, B4)
  ```

---

## 4. Application Protocol & Message Specifications (`common/protocol.py`)

### 4.1 Framing & Top-Level Envelope
- **TCP Stream Framing:** Every packet is serialized as a single-line UTF-8 JSON string terminated by a newline character (`\n`). Any newline inside chat text is automatically escaped as `\\n` by `json.dumps()`.
- **Standard Envelope Structure (3 Mandatory Top-Level Keys):**
  ```json
  {
    "type": "<MESSAGE_TYPE>",
    "timestamp": "HH:MM:SS",
    "payload": { ... }
  }
  ```
- **Room Type Values (`room_type` field in Bonus Payloads):**
  - `"PRIVATE"` — 1-to-1 private chat room (`target` is the peer's username)
  - `"GROUP"` — Group chat room (`target` is the group's name)

### 4.2 Fundamental Message Types (`R3`–`R11`)

| Direction | `type` | Purpose & Mapped Requirement | Complete Wire Format Example |
| :--- | :--- | :--- | :--- |
| Client -> Server | `REGISTER` | Request unique username (`R3`) | `{"type": "REGISTER", "timestamp": "20:00:01", "payload": {"username": "Alice"}}` |
| Server -> Client | `REGISTER_ACK` | Confirm or reject username (`R3`) | `{"type": "REGISTER_ACK", "timestamp": "20:00:01", "payload": {"success": true, "message": "OK"}}` |
| Server -> All | `CLIENT_LIST` | Broadcast all connected clients including self (`R4`) | `{"type": "CLIENT_LIST", "timestamp": "20:00:02", "payload": {"clients": ["Alice", "Bob"]}}` |
| Client -> Server | `PRIVATE_MSG` | Send 1-on-1 message (`R7`) | `{"type": "PRIVATE_MSG", "timestamp": "20:01:10", "payload": {"to": "Bob", "text": "Hi"}}` |
| Server -> Peer & Sender | `PRIVATE_MSG` | Deliver 1-on-1 message to receiver & echo to sender (`R6`, `R7`) | `{"type": "PRIVATE_MSG", "timestamp": "20:01:10", "payload": {"from": "Alice", "to": "Bob", "text": "Hi"}}` |
| Client -> Server | `CREATE_GROUP` | Create group with self as sole initial member (`R8`) | `{"type": "CREATE_GROUP", "timestamp": "20:02:00", "payload": {"group": "StudyRoom"}}` |
| Client -> Server | `JOIN_GROUP` | Self-join an existing group (`R10`) | `{"type": "JOIN_GROUP", "timestamp": "20:02:30", "payload": {"group": "StudyRoom"}}` |
| Server -> All | `GROUP_LIST` | Broadcast all groups + member lists (`R8`, `R9`, `R10`) | `{"type": "GROUP_LIST", "timestamp": "20:02:30", "payload": {"groups": {"StudyRoom": ["Alice", "Bob"]}}}` |
| Client -> Server | `GROUP_MSG` | Send message to a joined group (`R11`) | `{"type": "GROUP_MSG", "timestamp": "20:03:00", "payload": {"group": "StudyRoom", "text": "Hello group"}}` |
| Server -> Group Members | `GROUP_MSG` | Deliver group message to all group members including sender (`R6`, `R11`) | `{"type": "GROUP_MSG", "timestamp": "20:03:00", "payload": {"group": "StudyRoom", "from": "Alice", "text": "Hello group"}}` |
| Server -> Client | `ERROR` | Report invalid operation with code and message | `{"type": "ERROR", "timestamp": "20:03:05", "payload": {"code": "GROUP_EXISTS", "message": "Group name already exists"}}` |

### 4.3 Bonus / Special Feature Message Types (`B1`, `B3`, `B4`)

| Direction | `type` | Purpose & Mapped Feature | Complete Wire Format Example |
| :--- | :--- | :--- | :--- |
| Client -> Server | `TYPING` | Notify typing start/stop in Private or Group room (`B3`) | `{"type": "TYPING", "timestamp": "20:04:00", "payload": {"room_type": "GROUP", "target": "StudyRoom", "is_typing": true}}` |
| Server -> Peer / Group (excl. sender) | `TYPING` | Broadcast typing state to room participants (`B3`) | `{"type": "TYPING", "timestamp": "20:04:00", "payload": {"room_type": "GROUP", "target": "StudyRoom", "from": "Alice", "is_typing": true}}` |
| Client -> Server | `AI_SUMMARY_REQ` | Request Server to summarize stored room history (`B1`) | `{"type": "AI_SUMMARY_REQ", "timestamp": "20:05:00", "payload": {"room_type": "GROUP", "target": "StudyRoom"}}` |
| Server -> All Room Members | `AI_SUMMARY_RES` | Broadcast AI summary to everyone in that room (`B1`) | `{"type": "AI_SUMMARY_RES", "timestamp": "20:05:03", "payload": {"room_type": "GROUP", "target": "StudyRoom", "requested_by": "Alice", "summary": "Key points discussed..."}}` |
| Client -> Server | `VOICE_MSG` | Send Base64 WAV voice clip to Private or Group room (`B4`) | `{"type": "VOICE_MSG", "timestamp": "20:06:10", "payload": {"room_type": "PRIVATE", "target": "Bob", "audio_b64": "UklGRiQ...", "duration": 3.2}}` |
| Server -> Room Members (incl. sender) | `VOICE_MSG` | Deliver voice clip to receiver & sender or all group members (`B4`) | `{"type": "VOICE_MSG", "timestamp": "20:06:10", "payload": {"room_type": "PRIVATE", "target": "Bob", "from": "Alice", "audio_b64": "UklGRiQ...", "duration": 3.2}}` |

### 4.4 Standard Error Codes (`ERROR` Payload `code`)
| Error Code Constant | Value | When Triggered |
| :--- | :--- | :--- |
| `ERR_USERNAME_TAKEN` | `"USERNAME_TAKEN"` | Username is empty or already used by an active client (`R3`) |
| `ERR_NOT_REGISTERED` | `"NOT_REGISTERED"` | Client sends chat/group commands before completing `REGISTER` (`R3`) |
| `ERR_USER_NOT_FOUND` | `"USER_NOT_FOUND"` | Target recipient of `PRIVATE_MSG` / `VOICE_MSG` is offline (`R7`, `B4`) |
| `ERR_GROUP_EXISTS` | `"GROUP_EXISTS"` | Group name in `CREATE_GROUP` already exists (`R8`) |
| `ERR_GROUP_NOT_FOUND` | `"GROUP_NOT_FOUND"` | Target group does not exist (`R10`, `R11`, `B1`, `B3`, `B4`) |
| `ERR_ALREADY_IN_GROUP`| `"ALREADY_IN_GROUP"`| Client attempts `JOIN_GROUP` for a group they already joined (`R10`) |
| `ERR_NOT_IN_GROUP` | `"NOT_IN_GROUP"` | Client attempts action in a group they have not joined (`R11`, `B1`, `B3`, `B4`) |
| `ERR_AI_UNAVAILABLE` | `"AI_UNAVAILABLE"` | AI API key missing, room history empty, or LLM request failed (`B1`) |
| `ERR_INVALID_PACKET` | `"INVALID_PACKET"` | Malformed JSON, missing envelope keys (`type`, `payload`), or unknown `type` |

---

## 5. Current Status & Health
- **Overall Health:** Green (Protocol Locked & Skeleton Initialized)
- **What is Working:**
  - Complete modular file structure (`common/`, `server/`, `client/`) initialized with detailed `# TODO` blueprints and docstrings covering Part 1, Part 2, and Part 3 (Bonus).
- **Pending Implementation:**
  - Writing the executable Python code inside each initialized skeleton file.

---

## 6. Work Priority Matrix
| Priority | Task / Module | Description | Status |
| :--- | :--- | :--- | :--- |
| **P0 (Completed)** | Project Skeleton & Protocol Spec | Initialize `.py` skeleton files (`# TODO`s only) and lock JSON Envelope contract | Completed |
| **P1 (Next)** | `common/protocol.py` | Implement JSON envelope builders and TCP newline buffer framing | Pending |
| **P1 (Next)** | `server/` Core Modules | Implement `state.py`, `client_handler.py`, and `server.py` (`R1`–`R11`) | Pending |
| **P2 (Follow-up)** | `client/` Core Modules | Implement `network.py`, `gui_login.py`, `gui_lobby.py`, `gui_chatroom.py`, `main.py` | Pending |
| **P3 (Bonus)** | `server/ai_service.py` & `client/audio.py` | Implement Typing Indicator (`B3`), AI Summary (`B1`), Voice Message (`B4`), and Cloud VPS (`B2`) | Pending |

---

## 7. Tooling & Key Commands
- **Run Server (Local LAN or Cloud VPS):**
  ```powershell
  python -m server.server
  ```
- **Run Client (from workspace root):**
  ```powershell
  python -m client.main
  ```
- **Cloud VPS Note (`B2`):** Open TCP port `5000` (or custom port) in the VPS firewall/security group (`ufw allow 5000/tcp`) and set `GEMINI_API_KEY` (or LLM API key) in the server environment for `server/ai_service.py`.

---

## 8. Information Discovery Guide
- **Protocol Definitions:** Check `common/protocol.py` for all JSON action constants, `room_type` constants, and framing rules.
- **Server Concurrency, State & History:** Check `server/state.py` for how connected sockets, group memberships, and room message histories are locked and queried.
- **AI Summary Service:** Check `server/ai_service.py` for how stored room messages are formatted and sent to the LLM API.
- **Voice Clip Helper:** Check `client/audio.py` for WAV recording/playback and Base64 serialization.
- **GUI & Threading Bridge:** Check `client/network.py` and `client/gui_lobby.py` for how background socket threads safely pass events to `tkinter` via `queue.Queue`.
