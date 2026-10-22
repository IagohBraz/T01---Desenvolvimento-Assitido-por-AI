# Handoff para o revisor — Onda 2 (Extração, chunks, embeddings e Chroma)

Executor: Claude Code (Opus 5.5). Data: 21/10/2026, America/Sao_Paulo. Sem git (DEC-004): a revisão usa o inventário com hashes abaixo.

> **Para o revisor (OpenAI):** siga `Revisor.md` e `revisoes/MODELO_REVISAO.md`. Salve o relatório em `revisoes/onda-2/revisao-001.md`.
> **Dependência:** a revisão da onda 1 (`revisoes/onda-1/revisao-001.md`) ficou **BLOQUEADA** por ambiente, sem defeito de produto apontado. A onda 1 precisa ser revisada de novo; a onda 2 foi desenvolvida em paralelo a pedido do usuário.

## Objetivo da onda (SPEC, item 2)

Tratar os PDFs, quebrar em chunks com overlap, gerar os embeddings com `text-embedding-3-small` e salvar no Chroma. OCR só se o texto não puder ser extraído.

## Critérios de aceite

1. Originais de `docs/` preservados; extração fiel de texto, números, tabelas e cláusulas.
2. Arquivos vazios, corrompidos, protegidos por senha ou sem texto tratados com erro ou aviso explícito.
3. Chunks de até 350 caracteres com overlap de até 52 (DEC-001, DEC-009).
4. Metadados rastreáveis: documento, título, classificação, hash, página inicial e final, cláusula, posição e ID.
5. Embeddings `text-embedding-3-small` (1536 dimensões), persistência no Chroma e recuperação após reabrir.
6. Reingestão sem duplicação; documento alterado é reindexado e documento removido é apagado.
7. Envio externo conforme a decisão do usuário: todos os documentos, inclusive confidenciais, são autorizados na POC (DEC-002, DEC-007). **Não há bloqueio de confidenciais por decisão do usuário.** A classificação fica só como metadado.

## Decisões aprovadas

`DECISOES.md`, DEC-001 a DEC-010. Novas nesta onda:
- **DEC-009:** instalação de `langchain-text-splitters` e chunking em fronteira de palavra.
- **DEC-010:** OCR não foi necessário.

## Arquivos da entrega

| Arquivo | Papel | SHA-256 (prefixo) |
| --- | --- | --- |
| `src/xperiun_rag/extract.py` | Extração PyMuPDF: blocos em ordem de leitura; tabelas lidas célula a célula com `clip`; remoção do rodapé; junção de parágrafos quebrados; erros e avisos | 2970de4c26e75bca |
| `src/xperiun_rag/chunking.py` | `RecursiveCharacterTextSplitter` 350/52 em fronteira de palavra; metadados de página e cláusula | 2e2c874929ac11a9 |
| `src/xperiun_rag/vectorstore.py` | Chroma persistente (cosseno) + `OpenAIEmbeddings`; detecta coleção indexada com outro modelo | 5acdd5df926fab6a |
| `src/xperiun_rag/ingest.py` | Sincronização idempotente por documento (nome + SHA-256) | 5a0c10592a1ef692 |
| `scripts/ingest.py` | CLI: `--dry-run` (sem API), ingestão real e `--rebuild`; relatório em `data/ingest_report.json` | 9819f78768919af3 |
| `scripts/check_stack.py` | Agora inclui `langchain-text-splitters` | 09a592e1c1c3a07a |
| `tests/test_extract.py` | 11 testes: fidelidade nos PDFs reais e arquivos inválidos | 2a15c84a8f9d9f2a |
| `tests/test_chunking.py` | 6 testes: tamanho, overlap, cobertura, palavras inteiras, metadados, IDs | 6f3da8f50bcac9ad |
| `tests/test_ingest.py` | 7 testes com Chroma real temporário e embeddings falsos (sem API) | 7480bd5f88e23fa1 |
| `requirements.txt` / `requirements.lock.txt` | + `langchain-text-splitters` 1.1.3 | ebc739a7459468b8 / e7c9dc6743870fa0 |
| `DECISOES.md`, `README.md` | DEC-009, DEC-010; uso da ingestão | 25d3a44389072c29 / 4f0b35ad8b3b535b |

## Visualização no Streamlit (pedido do usuário)

Aba **② Chunks e embeddings** em `app.py`, com dados de `src/xperiun_rag/explorer.py`. Ela só lê o Chroma local, sem API externa, e mostra:
- KPIs: documentos, chunks, embeddings, dimensões, tamanho e overlap médios;
- tabela por documento;
- navegador de chunks: anterior/próximo, texto com os trechos de overlap destacados, métricas de overlap, vetor de 1536 dimensões e os 5 vizinhos mais parecidos por cosseno;
- mapa 2D (PCA) dos embeddings, clicável;
- gráficos de tamanho e overlap por chunk, com as linhas de limite 350/52;
- tabela completa.

Usa `pandas`, `numpy` e `altair`, que já vieram instalados como dependências de `streamlit` e `chromadb`; nenhuma instalação nova. Testes: `tests/test_explorer.py` (5).

## Decisões técnicas do executor (para validação)

- **`pdftotext` × PyMuPDF:** o `pdftotext` embaralhava o Aditivo; o `get_text(sort=True)` do PyMuPDF não.
- **Tabelas:** o texto devolvido por `find_tables().extract()` **corrompe números** ("12,0%" vira "120%") e junta palavras. Por isso o `find_tables` só localiza as células, e o texto de cada célula vem de `get_text(clip=célula)`. Cada linha vira uma frase "Cabeçalho: valor; …", para a relação coluna → valor sobreviver ao chunking.
- **Overlap:** com separadores de parágrafo e frase, o splitter recursivo gerava overlap de 0 na prática e chunks como "1.1.". Com separador de palavra, o overlap observado fica entre 40 e 51 caracteres, com no máximo 52.
- **Página e cláusula:** o texto das páginas é concatenado com `\n\n`; cada chunk guarda `start_index`, `page_start`, `page_end` e `section` (última "CLÁUSULA N - …" antes do início do chunk).

## Limitações da fonte (não são defeitos de extração)

- **Aditivo, pág. 1, tabela de SLA:** o PDF original mostra **só a primeira linha**, "Até 8 minutos e 38 segundos (Dentro dos 99,98%) → 0%". A tabela está cortada no rodapé, e o "99,98%" aparece como "99 98%" porque a vírgula está cortada na imagem. As demais faixas de penalidade **não existem no documento**, e o teste `test_sla_table_only_has_rows_present_in_source` garante que nada foi inventado. Conferido visualmente na renderização da página.
- **Aditivo, cabeçalho:** "Escopo de Aplicação: Fornecedores de Data" e "Center e Links" ficam em parágrafos separados por causa do layout em duas colunas. É só um rótulo de cabeçalho, sem impacto nas cláusulas.
- **Divergência cadastral:** o contrato traz CNPJ 12.345.678/0001-99 e sede na Berrini, e o contexto traz 00.000.000/0001-00 e Faria Lima. O texto é preservado como está no documento.

## Testes executados pelo executor

| Comando | Resultado |
| --- | --- |
| `.venv\Scripts\python -m unittest discover -s tests` | **37/37 OK** (8 da onda 1 + 29 da onda 2, incluindo a visualização), sem API externa |
| `.venv\Scripts\python scripts\ingest.py --dry-run` | 3 documentos, 50 chunks (16 + 18 + 16), 0 avisos, OK |
| `.venv\Scripts\python scripts\ingest.py` (real) | 3 indexados, 50 chunks no Chroma, exit 0 |
| Mesmo comando, 2ª vez | 3 inalterados, 50 chunks no total (sem duplicação), exit 0 |
| Inspeção do Chroma | vetores de 1536 dimensões; coleção com `embedding_model=text-embedding-3-small` e `hnsw:space=cosine` |
| Busca de sanidade (3 perguntas, embeddings reais) | Fornecedores → Aditivo p2 (Net-30); híbrido → Contrato p1; comissão Cloud Pro → Política p1 |
| `scripts/check_stack.py` | STACK OK |

## Observações para a onda 3

- ~~O chunk com a linha "Xperiun Cloud Pro … 12,0%" não ficou no top-3.~~ **Corrigido:** a inspeção anterior olhou só os primeiros 90 caracteres. O chunk em 1º lugar (Política #04) contém a linha completa do Cloud Pro, com 12,0% e 15,0%.
- Para verificar sem chamar a OpenAI: rode os testes e o `--dry-run`, e inspecione `data/chunks_preview.jsonl`. O banco real fica em `data/chroma/` (fora do versionamento).

## Fora de escopo

Recuperação (onda 3), geração e system prompt (onda 4), defesa contra prompt injection nos chunks (onda 4).
