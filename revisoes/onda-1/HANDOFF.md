# Handoff para o revisor — Onda 1 (Stack e ambiente)

Executor: Claude Code (Opus 5.5). Data: 21/10/2026, America/Sao_Paulo. Sem git (DEC-004): a revisão usa o inventário com hashes abaixo.

> **Para o revisor (OpenAI):** siga `Revisor.md` e `revisoes/MODELO_REVISAO.md`. Salve o relatório em `revisoes/onda-1/revisao-001.md`.

## Objetivo da onda (SPEC, item 1)

Subir a stack (Python 3.11+, Streamlit, LangChain e Chroma) em ambiente virtual controlado, com um resumo do projeto e todas as variáveis no `.env.exemple`.

## Critérios de aceite

1. `.venv` com Python 3.11+ e a stack instalada, só com as bibliotecas aprovadas (DEC-008).
2. Instalação reproduzível: `requirements.txt` com as dependências diretas e `requirements.lock.txt` com as versões exatas.
3. `.env.exemple` com todas as variáveis e as chaves vazias; `.env`, `.venv/` e `data/` no `.gitignore`.
4. Resumo do projeto em `README.md`.
5. Inicialização mínima testada: o Streamlit sobe, a falta de credenciais gera um aviso compreensível, e nenhum segredo aparece na UI, no `repr` ou nas mensagens de teste.

## Decisões aprovadas

Ver `DECISOES.md`: DEC-001 a DEC-008. Resumo: overlap de 52, todos os documentos e todos os usuários na POC, PyMuPDF antes de OCR, git só no final, revisão pela OpenAI, `.env.exemple`, envio externo autorizado e instalação da onda 1 aprovada.

## Arquivos da entrega

| Arquivo | Papel | SHA-256 (prefixo) |
| --- | --- | --- |
| `app.py` | Streamlit: status da configuração (o chat entra na onda 4) | a8d2390edc0b9fc6 |
| `src/xperiun_rag/__init__.py` | Pacote | b55c9c2568308f0a |
| `src/xperiun_rag/config.py` | Leitura do `.env`; `missing_keys()` só com nomes; chaves com `repr=False` | 341353de1db24b86 |
| `scripts/check_stack.py` | Versões, smoke test do Chroma persistente, status do `.env` sem valores; sem chamadas externas | d2e4938f3bd2d90e |
| `tests/test_config.py` | 5 testes de configuração e `.env.exemple` | d176b61806087402 |
| `tests/test_app.py` | 3 testes Streamlit (`AppTest`): render, aviso sem chaves, não exibe segredos | 33850753410db933 |
| `requirements.txt` | 8 dependências diretas aprovadas | 25994bee9cca1bc1 |
| `requirements.lock.txt` | `pip freeze` (130 pacotes, com as transitivas) | f516123916b5a56a |
| `.env.exemple` | Variáveis com as chaves vazias | db7f26f0b67d8fc7 |
| `.gitignore` | `.env`, `.venv/`, `data/`, caches | 2d2c41ee2b87bc9c |
| `README.md` | Resumo do projeto, arquitetura, como rodar | 9efe3c705aa5cf11 |
| `DECISOES.md` | Decisões do usuário | 9c7afbaa13146a71 |
| `SPEC.md` | Alterada **a pedido do usuário** (DEC-001): overlap 40 → 52 | b8f53ba8934a4f8f |

Não alterados: `docs/`, `contexto/`, `PRD.md`, `Agents.md`, `Revisor.md`. `.env` existe (criado pelo usuário) e não foi lido pelo executor.

## Testes executados pelo executor

| Comando | Resultado |
| --- | --- |
| `py -3.12 -m venv .venv` e `pip install -r requirements.txt` | OK (Python 3.12.5) |
| `.venv\Scripts\python scripts\check_stack.py` | `STACK OK`, exit 0: streamlit 1.66.1, langchain 1.4.7, langchain-openai 1.7.2, langchain-anthropic 1.7.6, langchain-chroma 1.1.0, chromadb 1.5.9, python-dotenv 1.2.4, pymupdf 2.0; Chroma persistente OK; `.env` completo |
| `.venv\Scripts\python -m unittest discover -s tests -v` | 8/8 OK |
| `streamlit run app.py --server.headless true --server.port 8599` + `GET /_stcore/health` | `ok`, página HTTP 200 |

## Problemas encontrados e corrigidos durante a onda

- No Windows, o Chroma mantém os arquivos do diretório temporário abertos (`WinError 32`). Correção: `ignore_cleanup_errors=True` em `check_stack.py`.
- O teste do `.env.exemple` usava `assertIn` com o conteúdo do arquivo, e a mensagem de falha imprimiria as chaves reais quando elas estavam preenchidas. Correção: asserções por linha, com mensagens que citam só o nome da variável.
- O usuário colocou as chaves temporariamente no `.env.exemple` e depois as moveu para o `.env`. Estado atual: `.env.exemple` com 0 chaves preenchidas.

## Limitações e fora de escopo

- Nenhuma chamada real às APIs da OpenAI ou da Anthropic nesta onda; a validade das chaves será verificada nas ondas 2 e 4.
- O `AppTest` emite o aviso "missing ScriptRunContext", esperado no modo bare.
- Ingestão, chunking, recuperação e geração são das ondas 2 a 4.
