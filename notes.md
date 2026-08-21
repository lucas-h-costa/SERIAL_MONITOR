# Notes - SERIAL_MONITOR

- main.py agora lista portas com serial.tools.list_ports.
- Console interativo de TX: texto direto, /hex para bytes, /exit para encerrar.
- Leitura serial agora bufferiza linhas ASCII parciais e faz flush no stop().
- Payload nao-ASCII e registrado em HEX com espacos para leitura melhor.
- Logs agora suportam text, csv e jsonl com timestamp_iso e timestamp_ms.
- Arquitetura agora serve CLI e biblioteca: SerialEvent, callbacks, fila de eventos e context manager (with).
- Codigo separado em serial_monitor.py (biblioteca) e main.py (CLI standalone).
- Interface grafica simples em gui.py usando Tkinter e a mesma API da biblioteca.
- GUI lista portas detectadas em combobox e permite atualizar a lista.
- Modos atuais: terminal, interface grafica, integracao por API e testes/simulacao.
- Decisao atual: adiar parser plugavel e exportador de metricas; retomar apenas quando houver necessidade futura.
- Testes automatizados sem hardware em tests/test_serial_monitor.py cobrindo start/stop, TX CRLF, buffering RX, payload HEX, logs JSONL e CSV.
- Preferencia do usuario: manter historico consolidado e pronto para exportar em markdown/text a qualquer momento.
- Documentacao detalhada em markdown: CHANGELOG_SERIAL_MONITOR.md
- Documentacao detalhada em texto puro: DOCUMENTACAO_SERIAL_MONITOR.txt
