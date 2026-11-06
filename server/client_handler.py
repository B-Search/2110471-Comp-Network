"""
Module: server/client_handler.py
Purpose: Per-Client TCP Socket Connection & JSON Message Exchange (R2 Baseline)
Requirement R2:
  - The chat messages between the server and each client must be implemented using Socket Programming only.
  - Receives JSON requests over TCP socket and sends JSON responses back over TCP socket.
  - Specific action handlers (R3 REGISTER, R7 PRIVATE_MSG, R8-R11 GROUP, etc.) will be added incrementally.
"""

import json
import logging
import socket
from typing import Any, Dict, Optional, Tuple

from common.protocol import (
    KEY_PAYLOAD,
    KEY_TYPE,
    SocketLineBuffer,
    build_message,
    encode_message,
)

logger = logging.getLogger("server.client_handler")


def send_packet(sock: socket.socket, msg_type: str, payload: Optional[Dict[str, Any]] = None) -> bool:
    """
    Sends a single JSON message envelope over raw TCP socket terminated by newline.
    Uses socket.sendall() (Socket Programming only - R2).
    """
    try:
        wire_bytes = encode_message(msg_type, payload or {})
        sock.sendall(wire_bytes)
        return True
    except (OSError, ConnectionError):
        return False


def handle_client(client_sock: socket.socket, client_addr: Tuple[str, int], state: Any = None) -> None:
    """
    Handles a single client's raw TCP socket connection (R2).
    Receives incoming JSON messages, logs them, and transmits a JSON response back.
    Specific action handlers (R3-R11) will be built step-by-step.
    """
    addr_str = f"{client_addr[0]}:{client_addr[1]}"
    logger.info(f"[R2 Socket] New client connected from {addr_str}")

    line_buffer = SocketLineBuffer(client_sock)

    try:
        for msg in line_buffer:
            msg_type = msg.get(KEY_TYPE, "UNKNOWN")
            payload = msg.get(KEY_PAYLOAD, {})
            logger.info(f"[R2 Socket] Received from {addr_str} -> Type: {msg_type} | Payload: {payload}")

            # ------------------------------------------------------------------
            # Basic R2 Socket Request & Response
            # Acknowledges and echoes the received JSON message over the socket
            # ------------------------------------------------------------------
            response = build_message(
                msg_type="RESPONSE",
                payload={
                    "status": "OK",
                    "echo_type": msg_type,
                    "echo_payload": payload,
                    "message": "Message received via TCP socket",
                },
            )
            send_packet(client_sock, response[KEY_TYPE], response[KEY_PAYLOAD])

            # NOTE: Specific action handlers (REGISTER, PRIVATE_MSG, GROUP_MSG, etc.)
            # will be integrated incrementally here as we proceed through R3-R11.

    except (EOFError, ConnectionError):
        logger.info(f"[R2 Socket] Client disconnected: {addr_str}")
    except Exception as exc:
        logger.error(f"[R2 Socket] Error handling client {addr_str}: {exc}", exc_info=True)
    finally:
        try:
            client_sock.close()
        except OSError:
            pass
        logger.info(f"[R2 Socket] Socket closed for {addr_str}")
