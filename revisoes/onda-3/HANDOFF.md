# Handoff para o revisor — Onda 3 (Augmented: recuperação dos 3 chunks)

Executor: Claude Code (Opus 5.5). Data: 21/10/2026, America/Sao_Paulo. Sem git (DEC-004): a revisão usa o inventário com hashes abaixo.

> **Para o revisor (OpenAI):** siga `Revisor.md` e `revisoes/MODELO_REVISAO.md`. Salve o relatório em `revisoes/onda-3/revisao-001.md`.
> **Dependências:** a onda 1 está BLOQUEADA por ambiente (`revisoes/onda-1/revisao-001.md`) e a onda 2 aguarda revisão (`revisoes/onda-2/HANDOFF.md`). A onda 3 foi desenvolvida a pedido do usuário.

## Objetivo da onda (SPEC, item 3)

Gerar o embedding da pergunta do usuário com o mesmo modelo e a mesma infraestrutura dos documentos (OpenAI `text-embedding-3-small`) e trazer os 3 chunks mais parecidos. Pedido do usuário: uma aba no Streamlit para fazer a pergunta e ver os 3 chunks com o grau de similaridade.

## Critérios de aceite

1. A pergunta passa pela **mesma função de embedding** da coleção, uma única vez, e o modelo é validado contra o metadado da coleção (`EmbeddingModelMismatch`, onda 2).
2. Retorna até `TOP_K=3` chunks **distintos**, ordenados por similaridade de cosseno (1 − distância), sem completar com chunks repetidos ou inventados.
3. Metadados de fonte (documento, páginas, cláusula, classificação, ID) preservados até a saída, prontos para a citação da onda 4.
4. Tratados: pergunta vazia, pergunta longa (> 2000 caracteres), base vazia, falta de `OPENAI_API_KEY`, falha do provedor (mensagem sem detalhes internos nem segredos) e menos de 3 chunks disponíveis.
5. Sinalização de **baixa relevância** quando nenhum chunk passa de 0,35, para a onda 4 poder responder "não encontrei nos documentos".
6. Confidencialidade: todos os documentos são permitidos na POC (DEC-002, DEC-007), então não há filtro por classificação. A pergunta **não é registrada** em log nem em disco; fica só na sessão do Streamlit (histórico da sessão).

## Arquivos da entrega

| Arquivo | Papel | SHA-256 (prefixo) |
| --- | --- | --- |
| `src/xperiun_rag/retriever.py` | `retrieve()`: normaliza a pergunta, gera o embedding (`store.embeddings.embed_query`), busca com `similarity_search_by_vector_with_relevance_scores`, deduplica e calcula a similaridade; erros como `RetrievalError` | 7606f62af3369537 |
| `src/xperiun_rag/reference_questions.py` | 13 perguntas de referência com o gabarito (documento + trecho literal dos PDFs) | 2b5dd1b12f5e88b7 |
| `scripts/eval_retrieval.py` | Avaliação acerto@3 com embeddings reais | b2e07115a71eeb3a |
| `src/xperiun_rag/explorer.py` | + `pca_fit`, para projetar a pergunta no mesmo mapa dos chunks | 84646c5ac6df9f0b |
| `app.py` | + aba **③ Recuperação (teste)** | d4f67072ace75735 |
| `tests/test_retriever.py` | 10 testes com Chroma real temporário e embeddings falsos | 6c0e0984afdcd354 |
| `tests/test_app.py` | + 3 testes da aba: pergunta vazia sem chamar a API, falta de chave, pergunta de exemplo | b107f4381fc80255 |
| `tests/test_explorer.py` | Sem mudança de conteúdo nesta onda | 29d9f7f7851ea32b |

## Aba ③ Recuperação (teste)

- Campo de pergunta (Enter ou botão "Buscar") e seletor com as 13 perguntas de referência.
- KPIs: quantidade de chunks, melhor similaridade, dimensões e tempo do embedding, tempo da busca no Chroma.
- Gráfico de barras com os 3 chunks e o grau de similaridade (0 a 1), cores por documento e linha tracejada no limite de baixa relevância.
- Um cartão por chunk: posição, citação (documento · página · cláusula), barra de similaridade, texto completo, ID e classificação.
- Mapa 2D (PCA) com a pergunta (◆) projetada entre os 50 chunks e o top-3 numerado.
- Aviso de baixa relevância e histórico da sessão.

## Decisões técnicas do executor (para validação)

- **Uma chamada de embedding por pergunta:** o vetor é gerado uma vez e reutilizado na busca e no mapa.
- **Limite de baixa relevância = 0,35** (`LOW_RELEVANCE_THRESHOLD`). Calibrado nos documentos atuais: perguntas dentro do tema ficaram entre ~0,52 e 0,77 no 1º lugar; "receita de bolo de cenoura" ficou em 0,22. O limite **não filtra** chunks; a SPEC pede os 3, e ele só sinaliza. A decisão de recusar fica para a onda 4.
- **Similaridade = 1 − distância de cosseno** (a coleção usa `hnsw:space=cosine`).

## Testes executados pelo executor

| Comando | Resultado |
| --- | --- |
| `.venv\Scripts\python -m unittest discover -s tests` | **50/50 OK**, sem API externa |
| `.venv\Scripts\python scripts\eval_retrieval.py` (embeddings reais) | **12/13 acertos no top-3 (92%)**, exit 1 porque há 1 falha; detalhe abaixo |
| AppTest da aba ③ com a API real | "comissão Cloud Pro" → 3 chunks da Política, melhor 0,649; "bolo de cenoura" → aviso de baixa relevância; pergunta vazia → "Digite uma pergunta." |
| Navegador (Chrome) | Aba renderizada; gráfico de barras corrigido (as 3 barras colapsavam numa linha com altura fixa; agora usa `alt.Step`) |

## Limitação conhecida (para decisão do usuário)

- **"Quando a comissão é paga ao vendedor?"**: o chunk com "15º (décimo quinto) dia útil" (Política #03) **não entra no top-3**. Os 3 primeiros (0,58, 0,55, 0,54) falam de clawback e disputas. É uma limitação da busca puramente vetorial com chunks de 350 caracteres. Opções em aberto, sem implementação até decisão do usuário: (A) manter a SPEC pura (top-3 vetorial) e aceitar o caso; (B) aumentar `TOP_K` ou adicionar reordenação ou busca híbrida, o que muda a SPEC.

## Fora de escopo

Geração com Claude, system prompt, citação na resposta e defesa contra prompt injection (onda 4).
