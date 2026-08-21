import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import serial

from serial_monitor import SerialMonitor, get_serial_ports


class SerialMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Serial Monitor")
        self.geometry("900x620")
        self.minsize(720, 480)
        self.monitor = None
        self._build_widgets()
        self._refresh_ports()
        self.after(50, self._poll_events)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_widgets(self):
        config = ttk.LabelFrame(self, text="Configuracao")
        config.pack(fill="x", padx=10, pady=10)

        self.port_var = tk.StringVar()
        self.baud_var = tk.StringVar(value="115200")
        self.bits_var = tk.StringVar(value="8")
        self.parity_var = tk.StringVar(value="Nenhuma")
        self.stopbits_var = tk.StringVar(value="1")
        self.log_format_var = tk.StringVar(value="text")
        self.log_path_var = tk.StringVar()
        self.crlf_var = tk.BooleanVar(value=True)

        ttk.Label(config, text="Porta").grid(row=0, column=0, padx=(8, 3), pady=8)
        self.port_combo = ttk.Combobox(config, textvariable=self.port_var, state="readonly", width=12)
        self.port_combo.grid(row=0, column=1, padx=(0, 8))

        fields = [
            ("Baud", self.baud_var, 1),
            ("Bits", self.bits_var, 2),
        ]
        for label, variable, column in fields:
            ttk.Label(config, text=label).grid(row=0, column=column * 2, padx=(8, 3), pady=8)
            ttk.Entry(config, textvariable=variable, width=12).grid(row=0, column=column * 2 + 1, padx=(0, 8))

        ttk.Label(config, text="Paridade").grid(row=0, column=6, padx=(8, 3))
        ttk.Combobox(
            config, textvariable=self.parity_var, values=("Nenhuma", "Par", "Impar"),
            state="readonly", width=10
        ).grid(row=0, column=7, padx=(0, 8))
        ttk.Label(config, text="Stop").grid(row=0, column=8, padx=(8, 3))
        ttk.Combobox(
            config, textvariable=self.stopbits_var, values=("1", "1.5", "2"),
            state="readonly", width=5
        ).grid(row=0, column=9, padx=(0, 8))
        ttk.Button(config, text="Atualizar portas", command=self._refresh_ports).grid(row=0, column=10, padx=8)

        ttk.Label(config, text="Arquivo de log").grid(row=1, column=0, padx=(8, 3), pady=8)
        ttk.Entry(config, textvariable=self.log_path_var, width=32).grid(row=1, column=1, columnspan=4, sticky="ew")
        ttk.Button(config, text="Escolher", command=self._choose_log).grid(row=1, column=5, padx=5)
        ttk.Label(config, text="Formato").grid(row=1, column=6, padx=(8, 3))
        ttk.Combobox(
            config, textvariable=self.log_format_var, values=("text", "csv", "json"),
            state="readonly", width=10
        ).grid(row=1, column=7, padx=(0, 8))
        ttk.Checkbutton(config, text="CRLF no TX", variable=self.crlf_var).grid(row=1, column=8, columnspan=2)

        self.connect_button = ttk.Button(config, text="Conectar", command=self._toggle_connection)
        self.connect_button.grid(row=1, column=10, padx=8)

        for column in range(11):
            config.columnconfigure(column, weight=1 if column in (1, 3, 5) else 0)

        output_frame = ttk.LabelFrame(self, text="Recepcao / Transmissao")
        output_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.output = tk.Text(output_frame, wrap="none", state="disabled", background="#101820", foreground="#e7edf2")
        self.output.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(output_frame, command=self.output.yview)
        scrollbar.pack(side="right", fill="y")
        self.output.configure(yscrollcommand=scrollbar.set)

        tx_frame = ttk.Frame(self)
        tx_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.tx_var = tk.StringVar()
        tx_entry = ttk.Entry(tx_frame, textvariable=self.tx_var)
        tx_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tx_entry.bind("<Return>", lambda event: self._send_text())
        ttk.Button(tx_frame, text="Enviar texto", command=self._send_text).pack(side="left", padx=3)
        ttk.Button(tx_frame, text="Enviar HEX", command=self._send_hex).pack(side="left", padx=3)
        ttk.Button(tx_frame, text="Limpar", command=self._clear_output).pack(side="left", padx=3)

        self.status_var = tk.StringVar(value="Desconectado")
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w").pack(fill="x", side="bottom")

    def _refresh_ports(self):
        ports = get_serial_ports()
        if ports:
            devices = [port.device for port in ports]
            selected_port = self.port_var.get()
            self.port_combo.configure(values=devices)
            if selected_port in devices:
                self.port_var.set(selected_port)
            else:
                self.port_var.set(devices[0])
            descriptions = [f"{port.device} - {port.description or 'Sem descricao'}" for port in ports]
            self.status_var.set(f"Portas encontradas: {', '.join(descriptions)}")
        else:
            self.port_combo.configure(values=())
            self.port_var.set("")
            self.status_var.set("Nenhuma porta serial detectada")

    def _choose_log(self):
        path = filedialog.asksaveasfilename(
            title="Salvar log",
            defaultextension=".log",
            filetypes=(("Todos os arquivos", "*.*"), ("Texto", "*.log"), ("CSV", "*.csv"), ("JSONL", "*.jsonl")),
        )
        if path:
            self.log_path_var.set(path)

    def _build_monitor(self):
        parity = {"Nenhuma": serial.PARITY_NONE, "Par": serial.PARITY_EVEN, "Impar": serial.PARITY_ODD}[self.parity_var.get()]
        stopbits = {"1": serial.STOPBITS_ONE, "1.5": serial.STOPBITS_ONE_POINT_FIVE, "2": serial.STOPBITS_TWO}[self.stopbits_var.get()]
        bits = int(self.bits_var.get())
        baud = int(self.baud_var.get())
        return SerialMonitor(
            port=self.port_var.get().strip().upper(), baudrate=baud, bytesize=bits,
            parity=parity, stopbits=stopbits, timeout=1,
            log_file=self.log_path_var.get().strip() or None,
            log_format=self.log_format_var.get(), tx_append_newline=self.crlf_var.get(),
            print_output=False,
        )

    def _toggle_connection(self):
        if self.monitor and self.monitor.is_running:
            self.monitor.stop()
            self.monitor = None
            self.connect_button.configure(text="Conectar")
            self.status_var.set("Desconectado")
            return

        try:
            self.monitor = self._build_monitor()
            self.monitor.start()
            self.connect_button.configure(text="Desconectar")
            self.status_var.set(f"Conectado a {self.port_var.get()}")
        except (ValueError, KeyError, RuntimeError) as error:
            self.monitor = None
            messagebox.showerror("Falha na conexao", str(error))

    def _send_text(self):
        if self.monitor and self.monitor.is_running and self.tx_var.get():
            self.monitor.send_text(self.tx_var.get())
            self.tx_var.set("")
        else:
            self.status_var.set("Conecte uma porta antes de enviar")

    def _send_hex(self):
        if self.monitor and self.monitor.is_running and self.tx_var.get():
            self.monitor.send_hex(self.tx_var.get())
            self.tx_var.set("")
        else:
            self.status_var.set("Conecte uma porta antes de enviar")

    def _poll_events(self):
        if self.monitor:
            for event in self.monitor.drain_events():
                self.output.configure(state="normal")
                self.output.insert("end", f"[{event.timestamp_iso}] {event.direction}: {event.payload}\n")
                self.output.see("end")
                self.output.configure(state="disabled")
            if not self.monitor.is_running and self.connect_button.cget("text") == "Desconectar":
                self.connect_button.configure(text="Conectar")
                self.status_var.set("Captura encerrada ou dispositivo desconectado")
        self.after(50, self._poll_events)

    def _clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _on_close(self):
        if self.monitor:
            self.monitor.stop()
        self.destroy()


def main():
    app = SerialMonitorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
