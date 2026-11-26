# DownGrab

Gestor de downloads pessoal, ao estilo do IDM, feito em Python.

Descarrega ficheiros em varias partes ao mesmo tempo, permite pausar e retomar, e tem fila de downloads.

> Projeto de aprendizagem. Feito para uso pessoal.

## Funcionalidades (plano)

- [ ] Descarregar um URL com N ligacoes em paralelo (HTTP Range)
- [ ] Pausar e retomar downloads
- [ ] Fila de downloads com barra de progresso
- [ ] Interface grafica simples
- [ ] Download de videos com yt-dlp
- [ ] Extensao de browser para apanhar downloads automaticamente

## Como funciona

1. Faz um pedido `HEAD` ao URL para saber o tamanho (`Content-Length`) e se o servidor aceita `Accept-Ranges: bytes`.
2. Divide o ficheiro em N partes.
3. Cada parte e descarregada em paralelo com o cabecalho `Range: bytes=inicio-fim`.
4. No fim, as partes sao juntas num unico ficheiro.
5. Para retomar, guarda-se o progresso de cada parte num ficheiro `.json`.

## Stack

- Python 3.11+
- `httpx` ou `aiohttp` para os pedidos
- `asyncio` para as ligacoes em paralelo
- PySide6 ou Tkinter para a interface
- `yt-dlp` para videos

## Passos para construir

### Fase 1 - Nucleo (linha de comandos)
1. Criar o ambiente: `python -m venv .venv` e instalar `httpx`.
2. Escrever `downloader.py` com uma funcao que descarrega um URL numa so ligacao.
3. Adicionar o `HEAD` e a divisao em partes com `Range`.
4. Descarregar as partes em paralelo com `asyncio.gather`.
5. Juntar as partes e apagar os ficheiros temporarios.

### Fase 2 - Pausar e retomar
1. Guardar o estado de cada parte num `.json`.
2. Ao retomar, continuar cada parte a partir dos bytes ja descarregados.

### Fase 3 - Fila e interface
1. Criar uma fila com varios downloads.
2. Criar a interface com lista, progresso, velocidade e botoes pausar/retomar.

### Fase 4 - Extras
1. Integrar `yt-dlp`.
2. Extensao de browser com native messaging.

## Como usar este projeto com o Claude no VS Code

1. Instalar o VS Code e a extensao oficial **Claude Code** (ou abrir o terminal e correr `claude`).
2. Clonar o repo:
   ```
   git clone https://github.com/TMseabra/downgrab.git
   cd downgrab
   code .
   ```
3. O ficheiro `CLAUDE.md` na raiz ja explica o projeto ao Claude. Ele le-o sozinho ao abrir a pasta.
4. Pedir uma fase de cada vez, por exemplo:
   - "Le o README e o CLAUDE.md e implementa a Fase 1."
   - "Escreve testes para a divisao em partes."
5. Depois de cada fase: correr, testar, fazer commit.

## Estrutura prevista

```
downgrab/
  README.md
  CLAUDE.md
  requirements.txt
  src/
    downloader.py
    queue.py
    gui.py
  tests/
```

## Licenca

MIT
