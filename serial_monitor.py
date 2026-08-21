import csv
import json
import os
import queue
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable, List, Optional

import serial
from serial.tools import list_ports


@dataclass
class SerialEvent:
    timestamp_iso: str
    timestamp_ms: int
    direction: str
    payload: str


class SerialMonitor:
    def __init__(
        self,
        port,
        baudrate,
        bytesize,
        parity,
        stopbits,
        timeout,
        log_file=None,
        log_format="text",
        tx_append_newline=True,
        print_output=True,
        event_callback: Optional[Callable[[SerialEvent], None]] = None,
        serial_factory: Optional[Callable[..., object]] = None,
        serial_instance=None,
    ):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.log_file = log_file
        self.log_format = log_format
        self.tx_append_newline = tx_append_newline
        self.print_output = print_output
        self.serial_factory = serial_factory or serial.Serial
        self.serial_instance = serial_instance

        self.serial_port = None
        self.is_running = False
        self.read_thread = None
        self.file_obj = None
        self.csv_writer = None
        self.stop_event = threading.Event()
        self.text_buffer = ""
        self.write_lock = threading.Lock()
        self.event_queue = queue.Queue()
        self.event_callbacks: List[Callable[[SerialEvent], None]] = []
        if event_callback is not None:
            self.event_callbacks.append(event_callback)

    def start(self):
        try:
            if self.serial_instance is not None:
                self.serial_port = self.serial_instance
            else:
                self.serial_port = self.serial_factory(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=self.bytesize,
                    parity=self.parity,
                    stopbits=self.stopbits,
                    timeout=self.timeout,
                )

            self.is_running = True
            self.stop_event.clear()

            if self.log_file:
                self._open_log_output()

            self.read_thread = threading.Thread(target=self._read_serial, daemon=True)
            self.read_thread.start()

            if self.print_output:
                print(
                    f"Conectado a {self.port} a {self.baudrate} baud. "
                    f"Config: {self.bytesize},{self.parity},{self.stopbits}"
                )
        except serial.SerialException as e:
            raise RuntimeError(f"Erro ao abrir a porta {self.port}: {e}") from e
        except IOError as e:
            raise RuntimeError(f"Erro ao criar o arquivo de log: {e}") from e

        return self

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop()

    def start_simulation(self):
        self.is_running = True
        self.stop_event.clear()
        if self.log_file:
            self._open_log_output()
        if self.print_output:
            print("Monitor iniciado em modo simulacao (sem porta serial real).")
        return self

    def _open_log_output(self):
        if self.log_format == "csv":
            file_exists = os.path.exists(self.log_file)
            file_is_empty = (not file_exists) or os.path.getsize(self.log_file) == 0
            self.file_obj = open(self.log_file, "a", encoding="utf-8", newline="")
            self.csv_writer = csv.writer(self.file_obj)
            if file_is_empty:
                self.csv_writer.writerow(["timestamp_iso", "timestamp_ms", "direction", "payload"])
                self.file_obj.flush()
            return

        self.file_obj = open(self.log_file, "a", encoding="utf-8")

    def _read_serial(self):
        if hasattr(self.serial_port, "reset_input_buffer"):
            try:
                self.serial_port.reset_input_buffer()
            except Exception:
                pass

        while self.is_running and not self.stop_event.is_set():
            try:
                waiting = self._bytes_waiting()
                if waiting > 0:
                    raw_data = self.serial_port.read(waiting)
                    if raw_data:
                        self.on_data_received(raw_data)
            except Exception as e:
                if self.print_output:
                    print(f"\nErro critico de leitura (hardware desconectado): {e}")
                self.is_running = False
                self.stop_event.set()
                break

            time.sleep(0.01)

    def _bytes_waiting(self):
        waiting = getattr(self.serial_port, "in_waiting", 0)
        if callable(waiting):
            waiting = waiting()
        return int(waiting)

    def on_data_received(self, data):
        try:
            decoded_data = data.decode("ascii", errors="strict").replace("\r", "")
        except UnicodeDecodeError:
            if self.text_buffer:
                self._emit_log("RX", self.text_buffer)
                self.text_buffer = ""
            self._emit_log("RX", data.hex(" ").upper())
            return

        self.text_buffer += decoded_data
        lines = self.text_buffer.split("\n")
        self.text_buffer = lines.pop()

        for line in lines:
            if line:
                self._emit_log("RX", line)

    def _current_timestamps(self):
        now = datetime.now()
        timestamp_iso = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        timestamp_ms = int(now.timestamp() * 1000)
        return timestamp_iso, timestamp_ms

    def _emit_log(self, direction, payload):
        timestamp_iso, timestamp_ms = self._current_timestamps()
        event = SerialEvent(
            timestamp_iso=timestamp_iso,
            timestamp_ms=timestamp_ms,
            direction=direction,
            payload=payload,
        )

        self.event_queue.put(event)

        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                if self.print_output:
                    print(f"Erro em callback de evento: {e}")

        if self.print_output:
            print(f"[{timestamp_iso}] {direction}: {payload}")

        if self.file_obj and not self.file_obj.closed:
            try:
                if self.log_format == "csv":
                    self.csv_writer.writerow(
                        [event.timestamp_iso, event.timestamp_ms, event.direction, event.payload]
                    )
                elif self.log_format == "json":
                    self.file_obj.write(json.dumps(asdict(event), ensure_ascii=True) + "\n")
                else:
                    self.file_obj.write(
                        f"[{event.timestamp_iso}] {event.direction}: {event.payload}\n"
                    )
                self.file_obj.flush()
            except IOError as e:
                if self.print_output:
                    print(f"Erro de gravacao de arquivo: {e}")

    def add_event_callback(self, callback: Callable[[SerialEvent], None]):
        self.event_callbacks.append(callback)

    def get_event(self, timeout=None):
        try:
            return self.event_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def drain_events(self, max_items=None):
        events = []
        while max_items is None or len(events) < max_items:
            event = self.get_event(timeout=0)
            if event is None:
                break
            events.append(event)
        return events

    def send_text(self, message):
        if not self.serial_port or not getattr(self.serial_port, "is_open", True):
            if self.print_output:
                print("Porta serial nao esta aberta para envio.")
            return

        payload = message
        encoded = message.encode("utf-8", errors="replace")
        if self.tx_append_newline:
            encoded += b"\r\n"

        try:
            with self.write_lock:
                self.serial_port.write(encoded)
            self._emit_log("TX", payload)
        except Exception as e:
            if self.print_output:
                print(f"Erro ao enviar dados: {e}")

    def send_hex(self, hex_string):
        if not self.serial_port or not getattr(self.serial_port, "is_open", True):
            if self.print_output:
                print("Porta serial nao esta aberta para envio.")
            return

        cleaned = hex_string.replace(" ", "")
        if len(cleaned) % 2 != 0:
            if self.print_output:
                print("HEX invalido: quantidade de caracteres deve ser par.")
            return

        try:
            data = bytes.fromhex(cleaned)
            with self.write_lock:
                self.serial_port.write(data)
            self._emit_log("TX", data.hex(" ").upper())
        except ValueError:
            if self.print_output:
                print("HEX invalido: use apenas caracteres 0-9 e A-F.")
        except Exception as e:
            if self.print_output:
                print(f"Erro ao enviar HEX: {e}")

    def emit_simulated_rx(self, payload):
        self._emit_log("RX", payload)

    def emit_simulated_tx(self, payload):
        self._emit_log("TX", payload)

    def stop(self):
        self.is_running = False
        self.stop_event.set()

        if self.text_buffer:
            self._emit_log("RX", self.text_buffer)
            self.text_buffer = ""

        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        if self.serial_port and getattr(self.serial_port, "is_open", False):
            self.serial_port.close()
        if self.file_obj and not self.file_obj.closed:
            self.file_obj.close()

        if self.print_output:
            print("Operacao encerrada.")


def get_serial_ports():
    return sorted(list_ports.comports(), key=lambda p: p.device)


def list_serial_ports():
    ports = get_serial_ports()
    if not ports:
        print("Nenhuma porta serial detectada automaticamente.")
        return

    print("Portas seriais detectadas:")
    for idx, port in enumerate(ports, start=1):
        desc = port.description or "Sem descricao"
        print(f"  {idx}. {port.device} - {desc}")
