"""
Module: tests/test_client_network.py
Purpose: Unit Tests for Client Network Layer (Strict R2 Socket Operations Only)
Run with: python -m unittest tests/test_client_network.py
"""

import queue
import socket
import json
import time
import threading
import unittest
from unittest.mock import patch, MagicMock

from client.network import NetworkClient
from common.protocol import DELIMITER, ENCODING


class TestClientNetwork(unittest.TestCase):

    def setUp(self):
        """Set up test queue and client instance before each test."""
        self.incoming_queue = queue.Queue()
        self.client = NetworkClient(self.incoming_queue)

    def tearDown(self):
        """Clean up open sockets after each test."""
        if self.client.sock:
            self.client.disconnect()

    # =========================================================================
    # 1. Connection & Disconnection Tests (R2)
    # =========================================================================

    @patch("socket.socket")
    def test_connect_success(self, mock_socket_cls):
        """Test successful TCP socket connection setup."""
        mock_sock_inst = MagicMock()
        mock_socket_cls.return_value = mock_sock_inst

        # Use an event to make mock recv block so _receive_loop stays connected during assertion
        stop_event = threading.Event()

        def mock_recv(size):
            stop_event.wait(timeout=1.0)
            return b""

        mock_sock_inst.recv.side_effect = mock_recv

        success, msg = self.client.connect("127.0.0.1", 5000)

        self.assertTrue(success)
        self.assertEqual(msg, "Connected successfully")
        self.assertTrue(self.client.connected)
        mock_sock_inst.connect.assert_called_once_with(("127.0.0.1", 5000))

        # Release background mock thread
        stop_event.set()

    @patch("socket.socket")
    def test_connect_failure(self, mock_socket_cls):
        """Test handling when TCP socket connection fails."""
        mock_sock_inst = MagicMock()
        mock_sock_inst.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_cls.return_value = mock_sock_inst

        success, msg = self.client.connect("127.0.0.1", 5000)

        self.assertFalse(success)
        self.assertIn("Connection failed", msg)
        self.assertFalse(self.client.connected)

    def test_disconnect(self):
        """Test clean socket disconnection and status flag update."""
        client_side, server_side = socket.socketpair()
        self.client.sock = client_side
        self.client.connected = True

        self.client.disconnect()

        self.assertFalse(self.client.connected)
        self.assertIsNone(self.client.sock)
        server_side.close()

    # =========================================================================
    # 2. Transmission & Framing Tests (send_packet)
    # =========================================================================

    def test_send_packet_structure(self):
        """Test that send_packet writes newline-delimited JSON bytes over socket using encode_message."""
        client_sock, server_sock = socket.socketpair()
        self.client.sock = client_sock
        self.client.connected = True

        test_payload = {"key": "value"}
        self.client.send_packet("TEST_TYPE", test_payload)

        received_bytes = server_sock.recv(4096)
        raw_text = received_bytes.decode(ENCODING)

        self.assertTrue(raw_text.endswith(DELIMITER))

        data = json.loads(raw_text.strip())
        self.assertEqual(data["type"], "TEST_TYPE")
        self.assertEqual(data["payload"], test_payload)
        self.assertIn("timestamp", data)

        client_sock.close()
        server_sock.close()

    # =========================================================================
    # 3. Stream Reception & Line Buffer Tests (_receive_loop)
    # =========================================================================

    def test_receive_loop_populates_queue(self):
        """Test that background thread reads stream bytes and puts parsed JSON into incoming_queue."""
        client_sock, server_sock = socket.socketpair()
        self.client.sock = client_sock
        self.client.connected = True

        rx_thread = threading.Thread(target=self.client._receive_loop, daemon=True)
        rx_thread.start()

        pkt1 = json.dumps({"type": "MSG_1", "timestamp": "12:00:00", "payload": {"data": 1}}) + DELIMITER
        pkt2 = json.dumps({"type": "MSG_2", "timestamp": "12:00:01", "payload": {"data": 2}}) + DELIMITER
        server_sock.sendall((pkt1 + pkt2).encode(ENCODING))

        received_msg1 = self.incoming_queue.get(timeout=2.0)
        received_msg2 = self.incoming_queue.get(timeout=2.0)

        self.assertEqual(received_msg1["type"], "MSG_1")
        self.assertEqual(received_msg1["payload"]["data"], 1)

        self.assertEqual(received_msg2["type"], "MSG_2")
        self.assertEqual(received_msg2["payload"]["data"], 2)

        server_sock.close()

        disconn_msg = self.incoming_queue.get(timeout=2.0)
        self.assertEqual(disconn_msg["type"], "DISCONNECTED")

        rx_thread.join(timeout=1.0)

    def test_receive_loop_handles_fragmented_stream(self):
        """Test that line buffer reassembles chunks split across multiple socket recv calls."""
        client_sock, server_sock = socket.socketpair()
        self.client.sock = client_sock
        self.client.connected = True

        rx_thread = threading.Thread(target=self.client._receive_loop, daemon=True)
        rx_thread.start()

        full_packet = json.dumps({"type": "SPLIT_MSG", "timestamp": "12:05:00", "payload": {"status": "ok"}}) + DELIMITER
        chunk_a = full_packet[:15]
        chunk_b = full_packet[15:]

        server_sock.sendall(chunk_a.encode(ENCODING))
        time.sleep(0.05)
        server_sock.sendall(chunk_b.encode(ENCODING))

        received_msg = self.incoming_queue.get(timeout=2.0)
        self.assertEqual(received_msg["type"], "SPLIT_MSG")
        self.assertEqual(received_msg["payload"]["status"], "ok")

        server_sock.close()
        rx_thread.join(timeout=1.0)


if __name__ == "__main__":
    unittest.main()