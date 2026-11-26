# CLAUDE.md

## Projeto
DownGrab: gestor de downloads pessoal em Python (estilo IDM). Projeto de aprendizagem do Tomas, para portfolio no GitHub.

## Regras
- Responder sempre em portugues de Portugal, de forma direta e curta.
- Trabalhar uma fase do README de cada vez. Nao saltar fases.
- Codigo simples e legivel, com comentarios curtos. O objetivo e o Tomas perceber o que o codigo faz.
- Usar `httpx` + `asyncio` para o nucleo. Nao adicionar dependencias sem explicar porque.
- Nunca apagar nem sobrescrever ficheiros descarregados pelo utilizador.
- Antes de grandes alteracoes, explicar o plano em poucas linhas.
- Escrever testes em `tests/` com `pytest` para a logica de divisao em partes e retoma.

## Comandos
- Criar ambiente: `python -m venv .venv`
- Instalar: `pip install -r requirements.txt`
- Testes: `pytest`

## Estado atual
Fase 1 (nucleo em linha de comandos) feita. Proxima: Fase 2 (pausar e retomar).
