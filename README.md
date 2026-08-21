# SERIAL_SPY

## Versao atual: 0.3.1 Beta

Monitor serial para Windows com quatro formas de uso: terminal, interface grafica, integracao por API e testes/simulacao sem hardware.

## Visao geral

O projeto permite:

- configurar comunicacao serial com porta, baud rate, bits, paridade e stop bits;
- visualizar dados recebidos (RX) em tempo real;
- enviar texto ou bytes em hexadecimal (TX);
- salvar eventos em texto, CSV ou JSONL;
- usar uma interface grafica simples baseada em Tkinter;
- integrar a captura em outros programas Python;
- testar o fluxo sem equipamento fisico.

## Estrutura do projeto

- `main.py`: aplicacao standalone em terminal.
- `gui.py`: interface grafica.
- `serial_monitor.py`: biblioteca reutilizavel e API principal.
- `simulate_serial.py`: gerador de eventos para simulacao.
- `tests/test_serial_monitor.py`: testes unitarios sem hardware.
- `.vscode/tasks.json`: tarefas para executar testes e a GUI no VS Code.
- `notes.md`: notas de contexto do projeto.

## Requisitos

- Python 3.10 ou superior recomendado.
- `pyserial` instalado no ambiente Python.
- Tkinter, normalmente incluido na instalacao do Python para Windows.

Instale a dependencia, se necessario:

```powershell
python -m pip install pyserial
```

## Modo 1: terminal standalone

Execute:

```powershell
python main.py
```

O programa lista as portas seriais detectadas e solicita:

1. porta, aceitando `COM3` ou apenas `3`;
2. baud rate, com padrao `115200`;
3. bits de dados, de 5 a 8;
4. paridade: nenhuma, par ou impar;
5. bits de parada: 1, 1.5 ou 2;
6. opcao e formato do arquivo de log;
7. uso de CRLF automatico em mensagens TX de texto.

Durante a captura, qualquer linha digitada no prompt `TX>` e enviada como texto. Comandos especiais:

- `/hex AA55FF`: envia bytes em hexadecimal;
- `/exit`: encerra a captura;
- `Ctrl+C`: encerra de forma alternativa.

## Modo 2: interface grafica

Execute:

```powershell
python gui.py
```

A GUI possui:

- lista suspensa com as portas detectadas no computador;
- botao `Atualizar portas` para refazer a busca;
- configuracao de baud, bits, paridade e stop bits;
- botoes para conectar e desconectar;
- area de exibicao de RX e TX;
- envio de texto e bytes HEX;
- selecao de arquivo e formato de log;
- controle de CRLF no envio de texto;
- botao para limpar a area visual sem apagar o arquivo de log.

A lista de portas e preenchida por `get_serial_ports()` e preserva a selecao atual quando a porta continua disponivel. A thread de leitura nao altera diretamente os widgets: a GUI consulta a fila de eventos periodicamente com `after()`.

## Modo 3: integracao por API

Importe `SerialMonitor` de `serial_monitor.py` em outro programa Python. A API disponibiliza:

- `start()` e `stop()` para controlar o ciclo de vida;
- `send_text()` para transmissao de texto;
- `send_hex()` para transmissao binaria;
- `add_event_callback()` para processamento em tempo real;
- `get_event()` para consumo individual pela fila;
- `drain_events()` para consumir varios eventos;
- `SerialEvent` com timestamp, direcao e payload;
- `with SerialMonitor(...)` para fechamento automatico.

Exemplo:

```python
import serial

from serial_monitor import SerialMonitor


def analisar(evento):
    if evento.direction == "RX":
        print("Dado recebido:", evento.payload)


monitor = SerialMonitor(
    port="COM3",
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1,
    print_output=False,
    event_callback=analisar,
)

with monitor:
    monitor.send_text("STATUS")
```

O componente gera eventos com:

- `timestamp_iso`: data e hora com milissegundos;
- `timestamp_ms`: timestamp Unix em milissegundos;
- `direction`: `RX` ou `TX`;
- `payload`: texto recebido/enviado ou representacao HEX.

## Modo 4: simulacao sem hardware

Execute:

```powershell
python simulate_serial.py
```

A simulacao gera eventos RX e TX, chama callbacks, salva `simulated_capture.jsonl` e apresenta um resumo final. Ela e apropriada para validar a arquitetura quando nao ha dispositivo conectado.

## Logs

Os formatos disponiveis sao:

- `text`: uma linha legivel por evento;
- `csv`: colunas `timestamp_iso`, `timestamp_ms`, `direction` e `payload`;
- `json`: JSONL, com um objeto JSON por linha.

Eventos RX e TX usam o mesmo formato logico. Dados nao ASCII recebidos sao exibidos e registrados em hexadecimal.

## Testes unitarios

Os testes ficam em `tests/test_serial_monitor.py` e usam `unittest` com uma classe `FakeSerial`. Assim, nao dependem de hardware, portas COM ou cabos.

Execute todos os testes:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Os testes validam separadamente:

- abertura e encerramento com serial fake;
- criacao da thread de leitura;
- fechamento correto da porta;
- envio TX com CRLF;
- registro de eventos TX;
- montagem de linhas RX fragmentadas;
- conversao de payload nao ASCII para HEX;
- criacao de log JSONL;
- campos obrigatorios do JSON;
- cabecalho e linhas do log CSV.

O resultado mais recente foi de 6 testes aprovados. Os testes unitarios protegem o comportamento do software, mas nao substituem um teste fisico do equipamento.

## Tarefas do VS Code

Em `.vscode/tasks.json` existem tarefas para:

- `Run Serial Monitor Tests`: executa a suite unitaria;
- `Run Serial Monitor GUI`: inicia a interface grafica.

## Limites atuais e evolucao futura

Parser plugavel de payload e exportador de metricas foram deliberadamente adiados porque nao sao necessarios no escopo atual. A arquitetura de eventos, callbacks e fila permite adicionar esses recursos futuramente sem acoplar a logica de analise ao terminal ou a GUI.

## Documentacao adicional

- `CHANGELOG_SERIAL_MONITOR.md`: historico detalhado local, mantido fora do repositorio por enquanto;
- `DOCUMENTACAO_SERIAL_MONITOR.txt`: versao em texto puro;
- `notes.md`: notas resumidas para continuidade do projeto.
