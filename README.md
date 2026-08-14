# SERIAL_MONITOR - Documentacao Completa do Produto

Data de referencia: 2026-08-14

## 1. Visao Geral
SERIAL_MONITOR e um monitor serial para Windows pensado para dois cenarios:
- uso direto no terminal (modo standalone), com leitura RX e envio TX
- uso como biblioteca Python, para integrar captura serial em sistemas maiores

O projeto foi evoluido para servir tanto debug rapido de bancada quanto base de desenvolvimento para automacao e analise.

## 2. Objetivos do Produto
- Facilitar captura serial com configuracao simples
- Permitir envio interativo de comandos para o dispositivo
- Registrar trafego de dados com timestamps precisos
- Suportar execucao sem hardware, por simulacao
- Garantir qualidade por testes automatizados sem dependencia de porta fisica

## 3. Estrutura Atual do Projeto
- [main.py](main.py): entrada standalone (CLI interativa)
- [serial_monitor.py](serial_monitor.py): biblioteca central do monitor
- [simulate_serial.py](simulate_serial.py): simulacao de dados sem hardware
- [tests/test_serial_monitor.py](tests/test_serial_monitor.py): testes automatizados
- [.vscode/tasks.json](.vscode/tasks.json): tarefa pronta para rodar testes no VS Code
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

### 4.2 Modo Biblioteca
[serial_monitor.py](serial_monitor.py) expoe a classe SerialMonitor para integracao em qualquer app Python.

Recursos principais da API:
- callbacks de evento em tempo real
- fila interna de eventos para polling
- suporte a context manager (with)
- metodos de envio TX texto e HEX
- modo simulacao sem porta serial real

### 4.3 Modelo de Evento
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

## 8. Qualidade e Testes
Cobertura atual da suite automatizada:
- start/stop com serial fake
- envio TX texto com CRLF
- buffering RX com fragmentacao
- conversao de payload nao ASCII para HEX
- escrita JSONL valida
- escrita CSV com cabecalho e linhas

Resultado mais recente: testes executados com sucesso (6/6 ok).

#
