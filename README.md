# Plataforma de busca de informações da Xperiun (POC)

Chatbot interno com arquitetura RAG. Antes de enviar uma pergunta ao Claude, o sistema busca nos documentos oficiais da Xperiun (`docs/`) os 3 trechos mais parecidos com a pergunta. Só esses trechos vão junto com a pergunta, e a resposta sempre cita a fonte.

- **Público:** diretores e gerentes gerais, analistas Comercial, de Marketing e de RH.
- **Temas:** contratos comerciais, comissões, fornecedores e tudo o que estiver em `docs/`.
- **Regras:** não inventar (toda resposta cita documento e trecho) e não vazar segredos. Nesta POC, todos os usuários acessam todos os documentos (ver `DECISOES.md`).

## Arquitetura

```
PDFs (docs/) ─► extração (PyMuPDF) ─► chunks 350 / overlap 52 ─► embeddings OpenAI ─► Chroma
                                                                  (text-embedding-3-small)
Pergunta ─► embedding da pergunta ─► top-3 chunks no Chroma ─► system prompt + chunks + pergunta
          ─► Claude Opus 5.5 ─► resposta com citação das fontes ─► Streamlit
```

| Camada | Tecnologia |
| --- | --- |
| Linguagem | Python 3.12 (venv em `.venv/`) |
| Frontend | Streamlit |
| Orquestração RAG | LangChain |
| Banco vetorial | Chroma (persistido em `data/chroma/`) |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | Anthropic Claude Opus 5.5 (`claude-opus-5-5`) |

## Ondas de entrega

| Onda | Escopo | Status |
| --- | --- | --- |
| 1 | Stack, ambiente virtual, `.env.exemple`, resumo do projeto | desenvolvida e testada; revisão bloqueada (ambiente do revisor) |
| 2 | Extração, chunks, embeddings e persistência no Chroma | desenvolvida e testada; aguardando revisão |
| 3 | Recuperação dos 3 chunks mais similares | desenvolvida e testada; aguardando revisão |
| 4 | Geração com Claude e chat completo | desenvolvida e testada; aguardando revisão |

Cada onda é desenvolvida e testada pelo executor (Claude Code) e revisada pelo revisor (`Revisor.md`, executado na OpenAI). O pacote para o revisor fica em `revisoes/onda-<N>/HANDOFF.md`.

## Como rodar (Windows)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.exemple .env     # depois preencha as chaves
.venv\Scripts\python scripts\check_stack.py
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python scripts\ingest.py --dry-run   # extrai e quebra, sem API
.venv\Scripts\python scripts\ingest.py             # indexa no Chroma (usa a OpenAI)
.venv\Scripts\python scripts\eval_retrieval.py     # acerto@3 nas perguntas de referência (usa a OpenAI)
.venv\Scripts\python scripts\eval_generation.py    # fluxo completo + guardrails (usa OpenAI e Anthropic, ~US$ 0,30)
.venv\Scripts\streamlit run app.py
```

A ingestão é idempotente: um PDF sem mudança é pulado, um PDF alterado é reindexado e um PDF removido de `docs/` tem seus chunks apagados. `--rebuild` recria a coleção do zero.

## Estrutura

```
app.py                  Frontend Streamlit
src/xperiun_rag/        Código do RAG: config, extract (PDF), chunking, vectorstore (Chroma), ingest, retriever, generator (Claude), explorer (UI)
scripts/check_stack.py  Verificação da stack (sem chamadas externas)
scripts/ingest.py       Ingestão dos PDFs no Chroma
tests/                  Testes (unittest, da biblioteca padrão)
docs/                   Documentos oficiais (somente leitura)
contexto/               Contexto institucional
DECISOES.md             Decisões aprovadas pelo usuário
revisoes/               Relatórios do revisor e handoffs
```
