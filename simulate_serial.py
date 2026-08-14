import random
import time

import serial

from serial_monitor import SerialMonitor


def run_simulation(duration_seconds=8):
    collected = []

    def on_event(event):
        collected.append(event)

    monitor = SerialMonitor(
        port="SIM",
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1,
        log_file="simulated_capture.jsonl",
        log_format="json",
        tx_append_newline=True,
        print_output=True,
        event_callback=on_event,
        serial_instance=None,
    )

    monitor.start_simulation()

    start = time.time()
    packet_id = 1
    while time.time() - start < duration_seconds:
        temp = 20 + random.random() * 15
        status = "OK" if temp < 33 else "WARN"
        monitor.emit_simulated_rx(f"ID={packet_id};TEMP={temp:.2f};STATUS={status}")
        if packet_id % 3 == 0:
            monitor.emit_simulated_tx("PING")
        packet_id += 1
        time.sleep(0.4)

    monitor.stop()

    rx_count = sum(1 for e in collected if e.direction == "RX")
    tx_count = sum(1 for e in collected if e.direction == "TX")
    print(f"Resumo simulacao: eventos={len(collected)} RX={rx_count} TX={tx_count}")


if __name__ == "__main__":
    run_simulation()
