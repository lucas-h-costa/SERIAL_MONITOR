<<<<<<< HEAD
# SERIAL_MONITOR - Documentacao Completa do Produto

Data de referencia: 2026-08-21

## 1. Visao Geral
SERIAL_MONITOR e um monitor serial para Windows pensado para quatro cenarios:
=======
# SERIAL_MONITOR

## 1. Visao Geral
SERIAL_MONITOR  é um monitor serial para Windows pensado para dois cenários:
>>>>>>> bfb1e0e4f7681f6a62ac66a984e322706a71dc49
- uso direto no terminal (modo standalone), com leitura RX e envio TX
- uso por interface grafica simples
- uso como biblioteca Python, para integrar captura serial em sistemas maiores
- uso em simulacao e testes sem hardware

O projeto foi evoluido para servir tanto como debug rapido de bancada quanto como base de desenvolvimento para automacao e analise.

## 2. Objetivos do Produto
- Facilitar captura serial com configuracao simples
- Permitir envio interativo de comandos para o dispositivo
- Registrar trafego de dados com timestamps precisos
- Suportar execucao sem hardware, por simulacao
- Garantir qualidade por testes automatizados sem dependencia de porta fisica

## 3. Estrutura Atual do Projeto
- [main.py](main.py): entrada standalone (CLI interativa)
- [gui.py](gui.py): interface grafica Tkinter
- [serial_monitor.py](serial_monitor.py): biblioteca central do monitor
- [simulate_serial.py](simulate_serial.py): simulacao de dados sem hardware
- [tests/test_serial_monitor.py](tests/test_serial_monitor.py): testes automatizados
- [.vscode/tasks.json](.vscode/tasks.json): tarefas para rodar testes e GUI no VS Code
- [notes.md](notes.md): notas de contexto e decisoes

## 4. Arquitetura Tecnica

### 4.1 Modo Standalone (CLI)
No modo standalone, [main.py](main.py) guia o usuario por prompts:
- selecao da porta
- parametros seriais (baud, bits, paridade, stop bits)
- opcao de persistir logs
- escolha de formato de log
- opcao de CRLF automatico em TX

Depois da conexao, o console entra em modo interativo para envio de comandos.

### 4.2 Modo Grafico
[gui.py](gui.py) oferece uma interface Tkinter para uso visual do monitor. A porta serial e escolhida por uma lista suspensa preenchida com as portas detectadas no computador. O botao `Atualizar portas` refaz a busca sem reiniciar a aplicacao.

O modo grafico permite configurar a comunicacao, conectar e desconectar, acompanhar RX/TX, enviar texto ou HEX, escolher o log, controlar CRLF e limpar somente a area visual.

### 4.3 Modo Integracao por API
[serial_monitor.py](serial_monitor.py) concentra a regra de comunicacao e pode ser importado por outro programa. A aplicacao consumidora pode escolher callback ou fila de eventos, sem depender do terminal ou da GUI.

### 4.4 Modo Teste e Simulacao
[simulate_serial.py](simulate_serial.py) exercita o pipeline sem porta fisica, gerando RX/TX, callbacks, logs e resumo de eventos. A suite em [tests/test_serial_monitor.py](tests/test_serial_monitor.py) usa uma serial fake para testar o componente de forma deterministica.

### 4.5 Biblioteca e API
[serial_monitor.py](serial_monitor.py) expoe a classe SerialMonitor para integracao em qualquer app Python.

Recursos principais da API:
- callbacks de evento em tempo real
- fila interna de eventos para polling
- suporte a context manager (with)
- metodos de envio TX texto e HEX
- modo simulacao sem porta serial real

### 4.6 Modelo de Evento
Cada evento de RX ou TX e representado por SerialEvent, com campos:
- timestamp_iso
- timestamp_ms
- direction (RX ou TX)
- payload

Esse formato padronizado reduz acoplamento com parsing textual e facilita evolucao.

## 5. Funcionalidades Implementadas

### 5.1 Captura RX robusta
- buffering de linhas parciais
- merge correto de fragmentos ate encontrar \n
- flush do buffer pendente no stop
- fallback para HEX quando payload nao e ASCII valido

### 5.2 Envio TX interativo
Comandos no console:
- /exit: encerra sessao
- /hex AA55FF: envia bytes HEX
- qualquer outra linha: envia texto

Opcionalmente, cada TX texto recebe CRLF automatico.

### 5.3 Persistencia de logs
Formatos suportados:
- text
- csv
- json (jsonl: um objeto por linha)

Todos os formatos registram RX e TX com timestamp em milissegundos.

### 5.4 Simulacao sem hardware
[simulate_serial.py](simulate_serial.py) gera eventos sinteticos RX/TX para validar fluxo completo:
- callbacks
- fila de eventos
- persistencia de log
- contagem final de eventos

### 5.5 Interface Grafica
Para iniciar a interface:

```bash
c:/Users/lucas/SERIAL_MONITOR/.venv/Scripts/python.exe gui.py
```

Tambem e possivel usar a task `Run Serial Monitor GUI` no VS Code.

## 6. Como Executar

### 6.1 Requisitos
- Python 3
- pyserial instalado no ambiente


Fluxo esperado:
1. configurar porta e parametros
2. conectar
3. digitar comandos em TX>
4. encerrar com /exit

Saida esperada:
- eventos RX e TX no console
- arquivo de log simulado (jsonl)
- resumo final com contagem de eventos

<<<<<<< HEAD
### 6.4 Rodar interface grafica
```bash
c:/Users/lucas/SERIAL_MONITOR/.venv/Scripts/python.exe gui.py
```

### 6.5 Rodar testes unitarios
Comando:

```bash
c:/Users/lucas/SERIAL_MONITOR/.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Tambem disponivel no VS Code pela task:
- Run Serial Monitor Tests
=======
>>>>>>> bfb1e0e4f7681f6a62ac66a984e322706a71dc49

## 7. Integracao em Programa Maior
Exemplo de abordagem:
- importar SerialMonitor de [serial_monitor.py](serial_monitor.py)
- registrar callback para tratar eventos
- iniciar monitor com with
- consumir eventos por callback ou polling

Pontos de design importantes:
- start levanta excecoes ao inves de encerrar o processo
- stop fecha thread, porta e arquivo de log
- fila de eventos desacopla captura e processamento

## 8. Testes Unitarios
Os testes sao executados sem hardware usando `unittest` e uma classe `FakeSerial`.

### 8.1 O que e validado
- start/stop com serial fake
- envio TX texto com CRLF
- buffering RX com fragmentacao
- conversao de payload nao ASCII para HEX
- escrita JSONL valida
- escrita CSV com cabecalho e linhas

<<<<<<< HEAD
### 8.2 Como executar
```bash
c:/Users/lucas/SERIAL_MONITOR/.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Resultado mais recente: 6 testes executados com sucesso (6/6 ok).

### 8.3 Limites atuais
Os testes nao substituem uma verificacao com equipamento real. O teste fisico ainda deve confirmar porta, cabeamento, baud rate, paridade, stop bits e comportamento eletrico do dispositivo.

## 9. Decisoes de Escopo (Atuais)
Itens deliberadamente adiados:
- parser plugavel de payload
- exportador de metricas

Motivo: nao sao necessarios no escopo atual, mas estao mapeados para retomada futura.

## 10. Troubleshooting Rapido
- Nao vejo tasks.json:
  verificar se a pasta .vscode esta visivel no Explorer.
- Nao tenho hardware agora:
  usar [simulate_serial.py](simulate_serial.py) para validar pipeline completo.
- Nao chegam linhas completas:
  confirmar delimitador \n no dispositivo e revisar configuracao serial.
- Arquivo de log nao aparece:
  conferir permissao de escrita e caminho informado no prompt.

## 11. Historico Resumido de Evolucao
1. fortalecimento de leitura serial e encerramento
2. console TX com comandos de controle
3. persistencia multi-formato (text/csv/json)
4. separacao arquitetura CLI vs biblioteca
5. simulacao sem hardware para validacao
6. testes automatizados de regressao
7. documentacao consolidada para continuidade

## 12. Proximos Passos Recomendados
1. Manter rotina de testes a cada mudanca no monitor
2. Definir formato padrao de log por ambiente (dev/prod)
3. Retomar parser plugavel quando surgir necessidade de semantica de payload
4. Retomar metricas quando houver demanda de observabilidade
=======
#
>>>>>>> bfb1e0e4f7681f6a62ac66a984e322706a71dc49
