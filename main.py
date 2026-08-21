import sys
import serial
from serial_monitor import SerialMonitor, list_serial_ports



def build_monitor_from_prompts():
    print("Configuracao do Monitor Serial")
    list_serial_ports()

    port_input = input("Digite a porta (ex: COM3 ou apenas 3): ").strip().upper()
    if not port_input:
        raise ValueError("Porta nao informada.")

    if port_input.startswith("COM"):
        port_name = port_input
    else:
        port_name = f"COM{port_input}"

    while True:
        baud_input = input("Digite o Baud rate [padrao 115200]: ").strip()
        if not baud_input:
            baudrate = 115200
            break
        try:
            baudrate = int(baud_input)
            break
        except ValueError:
            print("Valor invalido. O baud rate deve ser um numero inteiro.")

    while True:
        bits_input = input("Digite os bits de dados (5, 6, 7, 8) [padrao 8]: ").strip()
        if not bits_input:
            bytesize = serial.EIGHTBITS
            break
        try:
            bytesize = int(bits_input)
            if bytesize in [5, 6, 7, 8]:
                break
            print("Valor invalido. Selecione 5, 6, 7 ou 8.")
        except ValueError:
            print("Valor invalido. O tamanho em bits deve ser um numero inteiro.")

    parity_input = input("Digite a paridade (par, impar, nenhum) [padrao nenhum]: ").strip().lower()
    if parity_input == 'par':
        parity = serial.PARITY_EVEN
    elif parity_input == 'impar':
        parity = serial.PARITY_ODD
    else:
        parity = serial.PARITY_NONE
    stop_input = input("Digite os bits de parada (1, 1.5, 2) [padrao 1]: ").strip()
    if stop_input == '1.5':
        stopbits = serial.STOPBITS_ONE_POINT_FIVE
    elif stop_input == '2':
        stopbits = serial.STOPBITS_TWO
    else:
        stopbits = serial.STOPBITS_ONE

    log_file = None
    log_format = "text"
    while True:
        save_file = input("Deseja gravar os dados em um arquivo? (s/n) [padrao n]: ").strip().lower()
        if save_file == 's':
            log_file = input("Digite o nome do arquivo (ex: dados.txt): ").strip()
            if log_file:
                while True:
                    fmt = input("Formato de log (text/csv/json) [padrao text]: ").strip().lower()
                    if not fmt:
                        log_format = "text"
                        break
                    if fmt in ("text", "csv", "json"):
                        log_format = fmt
                        break
                    print("Formato invalido. Escolha text, csv ou json.")
                break
            print("O nome do arquivo nao pode estar em branco.")
        else:
            break

    tx_append_newline = True
    newline_input = input("Adicionar CRLF em cada TX de texto? (s/n) [padrao s]: ").strip().lower()
    if newline_input == 'n':
        tx_append_newline = False

    return SerialMonitor(
        port=port_name,
        baudrate=baudrate,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        timeout=1,
        log_file=log_file,
        log_format=log_format,
        tx_append_newline=tx_append_newline,
        print_output=True,
    )


def interactive_console(monitor):
    print("Comandos: /exit para sair, /hex AA55FF para enviar bytes HEX.")
    print("Qualquer outra linha sera enviada como TX em texto.")

    while monitor.is_running:
        try:
            command = input("TX> ").strip()
        except EOFError:
            monitor.stop()
            break

        if not monitor.is_running:
            break
        if not command:
            continue

        if command.lower() == "/exit":
            monitor.stop()
            break

        if command.lower().startswith("/hex"):
            hex_payload = command[4:].strip()
            if not hex_payload:
                print("Uso: /hex AA55FF")
                continue
            monitor.send_hex(hex_payload)
            continue

        monitor.send_text(command)


def main():
    try:
        monitor = build_monitor_from_prompts()
        monitor.start()
    except Exception as e:
        print(f"Falha ao iniciar monitor: {e}")
        sys.exit(1)

    try:
        interactive_console(monitor)
    except KeyboardInterrupt:
        monitor.stop()
    except Exception as e:
        print(f"Erro inesperado no laco principal: {e}")
        monitor.stop()

if __name__ == "__main__":
    main()