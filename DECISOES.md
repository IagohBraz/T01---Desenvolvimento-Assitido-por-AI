# Decisões do usuário — POC Xperiun

Registro das decisões aprovadas pelo usuário. Fonte: conversa com o agente executor em 21/10/2026.

| ID | Tema | Decisão | Origem da pendência |
| --- | --- | --- | --- |
| DEC-001 | Overlap dos chunks | **52 caracteres** (15% de 350 = 52,5, arredondado para baixo). A SPEC foi atualizada pelo executor a pedido do usuário. | INI-001 |
| DEC-002 | Acesso aos documentos | Nesta POC, **todos os documentos de `docs/` entram no pipeline**, inclusive os classificados como confidenciais. **Sem gestão de usuários**: todos os usuários acessam todos os documentos. | INI-002 |
| DEC-003 | Extração de PDF | Testar primeiro o **PyMuPDF**. Se a extração não ficar fiel, testar OCR (com aprovação prévia da biblioteca/instalação). | INI-003 |
| DEC-004 | Git | `git init` **somente ao final**, com o projeto 100% entregue e aprovado pelo usuário. | — |
| DEC-005 | Revisão das ondas | O revisor (`Revisor.md`) é **sempre executado pelo usuário na OpenAI**. O executor (Claude) não roda a revisão; entrega o pacote de handoff de cada onda em `revisoes/onda-<N>/HANDOFF.md`. | Agents.md |
| DEC-006 | Nome do arquivo de variáveis | `.env.exemple`, com a grafia exigida pela SPEC. | SPEC, onda 1 |

| DEC-007 | Envio externo | **Autorizado** na POC: o conteúdo de todos os documentos, inclusive a Política de Vendas ("Interno / Confidencial"), pode ser enviado à **OpenAI** (embeddings) e à **Anthropic** (geração). Confirmação explícita do usuário em 21/10/2026. | INI-002 |
| DEC-008 | Instalação da onda 1 | **Aprovadas:** criação do `.venv` (Python 3.12) e instalação via pip de `streamlit`, `langchain`, `langchain-openai`, `langchain-anthropic`, `langchain-chroma`, `chromadb`, `python-dotenv` e `pymupdf`, mais as dependências transitivas. Testes com `unittest` (biblioteca padrão). Aprovação explícita do usuário em 21/10/2026. | SPEC, guardrails |
| DEC-009 | Chunking (onda 2) | **Aprovada** a instalação de `langchain-text-splitters` (pacote oficial do LangChain), em vez de um splitter próprio. Chunks de até 350 caracteres, quebrados em fronteira de palavra; o overlap fica entre ~40 e 52 caracteres, sem cortar palavras ou números. Aprovação explícita do usuário em 21/10/2026. | DEC-001 |
| DEC-011 | Git e GitHub | **Antecipa a DEC-004:** a pedido do usuário, `git init` e push **antes** das revisões para `https://github.com/IagohBraz/T01---Desenvolvimento-Assitido-por-AI` (repositório **público**). O usuário escolheu subir **tudo, inclusive os PDFs de `docs/`** (com a Política de Vendas "Interno / Confidencial"), ciente de que o repositório é público. Ficam fora: `.env`, `.venv/` e `data/`. Decisão explícita do usuário em 21/10/2026. | DEC-004 |
| DEC-010 | Extração (onda 2) | O PyMuPDF extraiu os 3 PDFs com fidelidade, inclusive o Aditivo (que o `pdftotext` embaralhava). **OCR não foi necessário** (DEC-003). | INI-003 |
