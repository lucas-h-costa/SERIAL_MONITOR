import csv
import json
import tempfile
import unittest
from pathlib import Path
import serial
from serial_monitor import SerialMonitor


class FakeSerial:
    def __init__(self):
        self.is_open = True
        self.written = []
        self._in_waiting = 0

    @property
    def in_waiting(self):
        return self._in_waiting

    def read(self, size):
        return b""

    def write(self, data):
        self.written.append(data)
        return len(data)

    def reset_input_buffer(self):
        return None

    def close(self):
        self.is_open = False


class SerialMonitorTests(unittest.TestCase):
    def _create_monitor(self, **overrides):
        base = {
            "port": "COM_TEST",
            "baudrate": 115200,
            "bytesize": serial.EIGHTBITS,
            "parity": serial.PARITY_NONE,
            "stopbits": serial.STOPBITS_ONE,
            "timeout": 1,
            "log_file": None,
            "log_format": "text",
            "tx_append_newline": True,
            "print_output": False,
        }
        base.update(overrides)
        return SerialMonitor(**base)

    def test_start_and_stop_with_fake_serial_instance(self):
        fake = FakeSerial()
        monitor = self._create_monitor(serial_instance=fake)

        monitor.start()
        self.assertTrue(monitor.is_running)
        self.assertTrue(monitor.read_thread.is_alive())

        monitor.stop()
        self.assertFalse(monitor.is_running)
        self.assertFalse(fake.is_open)

    def test_send_text_appends_crlf_and_logs_tx_event(self):
        fake = FakeSerial()
        monitor = self._create_monitor(serial_instance=fake, tx_append_newline=True)

        monitor.start()
        monitor.send_text("HELLO")
        monitor.stop()

        self.assertEqual(fake.written[-1], b"HELLO\r\n")
        events = monitor.drain_events()
        tx_events = [e for e in events if e.direction == "TX"]
        self.assertEqual(len(tx_events), 1)
        self.assertEqual(tx_events[0].payload, "HELLO")

    def test_on_data_received_buffers_partial_lines(self):
        monitor = self._create_monitor()
        monitor.start_simulation()

        monitor.on_data_received(b"abc")
        self.assertEqual(monitor.drain_events(), [])

        monitor.on_data_received(b"123\nxyz\n")
        monitor.stop()

        events = monitor.drain_events()
        rx_payloads = [e.payload for e in events if e.direction == "RX"]
        self.assertIn("abc123", rx_payloads)
        self.assertIn("xyz", rx_payloads)

    def test_non_ascii_payload_is_logged_as_hex(self):
        monitor = self._create_monitor()
        monitor.start_simulation()

        monitor.on_data_received(bytes([0xFF, 0x01, 0xAA]))
        monitor.stop()

        events = monitor.drain_events()
        rx_events = [e for e in events if e.direction == "RX"]
        self.assertEqual(len(rx_events), 1)
        self.assertEqual(rx_events[0].payload, "FF 01 AA")

    def test_json_log_format_writes_jsonl_events(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "events.jsonl"
            monitor = self._create_monitor(log_file=str(log_path), log_format="json")
            monitor.start_simulation()

            monitor.emit_simulated_rx("RX_SAMPLE")
            monitor.emit_simulated_tx("TX_SAMPLE")
            monitor.stop()

            lines = log_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            payloads = []
            for line in lines:
                entry = json.loads(line)
                self.assertIn("timestamp_iso", entry)
                self.assertIn("timestamp_ms", entry)
                self.assertIn("direction", entry)
                self.assertIn("payload", entry)
                payloads.append(entry["payload"])
            self.assertEqual(payloads, ["RX_SAMPLE", "TX_SAMPLE"])

    def test_csv_log_format_writes_header_once_and_rows(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "events.csv"
            monitor = self._create_monitor(log_file=str(log_path), log_format="csv")
            monitor.start_simulation()

            monitor.emit_simulated_rx("ROW1")
            monitor.emit_simulated_tx("ROW2")
            monitor.stop()

            with log_path.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.reader(f))

            self.assertEqual(rows[0], ["timestamp_iso", "timestamp_ms", "direction", "payload"])
            self.assertEqual(rows[1][2:], ["RX", "ROW1"])
            self.assertEqual(rows[2][2:], ["TX", "ROW2"])


if __name__ == "__main__":
    unittest.main()
