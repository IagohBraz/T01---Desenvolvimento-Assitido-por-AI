"""Frontend Streamlit: uma aba por onda executada, mostrando visualmente o que cada uma entregou."""

import html
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from xperiun_rag.config import load_settings  # noqa: E402
from xperiun_rag.explorer import explained_variance, load_snapshot, nearest_neighbors, pca_fit, project_2d  # noqa: E402
from xperiun_rag.generator import CONFIDENTIAL_NOTICE, SYSTEM_PROMPT, AnswerStream, GenerationError  # noqa: E402
from xperiun_rag.reference_questions import REFERENCE_QUESTIONS  # noqa: E402
from xperiun_rag.retriever import LOW_RELEVANCE_THRESHOLD, RetrievalError, retrieve  # noqa: E402
from xperiun_rag.vectorstore import get_vectorstore  # noqa: E402

# Paleta categórica (slots 1–3 validados para todos os pares, inclusive daltonismo) e realce de overlap.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
OVERLAP_PREV_BG = "rgba(235, 104, 52, 0.22)"
OVERLAP_NEXT_BG = "rgba(42, 120, 214, 0.20)"
PACKAGES = (
    "streamlit",
    "langchain",
    "langchain-openai",
    "langchain-anthropic",
    "langchain-chroma",
    "langchain-text-splitters",
    "chromadb",
    "python-dotenv",
    "pymupdf",
)

st.set_page_config(page_title="Xperiun — Busca de Informações", page_icon="🔎", layout="wide")
st.title("🔎 Xperiun — Busca de Informações")
st.caption("POC interna · cada aba mostra o que foi entregue em uma onda")

settings = load_settings()


@st.cache_data(show_spinner="Lendo o Chroma…")
def cached_snapshot(chroma_dir: str, collection: str, mtime: float):
    return load_snapshot(Path(chroma_dir), collection)


def chroma_mtime() -> float:
    db = settings.chroma_dir / "chroma.sqlite3"
    return db.stat().st_mtime if db.exists() else 0.0


def doc_colors(sources: list[str]) -> alt.Scale:
    return alt.Scale(domain=sources, range=SERIES[: len(sources)])


def short(source: str) -> str:
    return source.removesuffix(".pdf").removesuffix(" Xperiun")


# ---------------------------------------------------------------- Onda 1
def wave1() -> None:
    st.subheader("Onda 1 · Stack e ambiente")
    missing = settings.missing_keys()
    if missing:
        st.warning(
            "Configuração incompleta. Copie `.env.exemple` para `.env` e preencha: "
            + ", ".join(f"`{name}`" for name in missing)
        )
    else:
        st.success("Chaves de API configuradas.")

    left, right = st.columns(2)
    with left:
        st.markdown("**Configuração atual**")
        st.table(
            {
                "Parâmetro": ["Embeddings", "LLM", "Coleção Chroma", "Chunk / overlap", "Top-k"],
                "Valor": [
                    settings.embedding_model,
                    settings.llm_model,
                    settings.chroma_collection,
                    f"{settings.chunk_size} / {settings.chunk_overlap}",
                    str(settings.top_k),
                ],
            }
        )
    with right:
        st.markdown("**Stack instalada no `.venv`**")
        rows = []
        for package in PACKAGES:
            try:
                rows.append({"Pacote": package, "Versão": version(package)})
            except PackageNotFoundError:
                rows.append({"Pacote": package, "Versão": "não instalado"})
        st.table(pd.DataFrame(rows))
        st.caption(f"Python {sys.version.split()[0]}")


# ---------------------------------------------------------------- Onda 2
def highlighted(text: str, overlap_prev: int, overlap_next: int) -> str:
    n = len(text)
    a = min(overlap_prev, n)
    b = max(a, n - overlap_next)
    parts = []
    if a:
        parts.append(f'<span style="background:{OVERLAP_PREV_BG};border-radius:3px">{html.escape(text[:a])}</span>')
    parts.append(html.escape(text[a:b]))
    if overlap_next:
        parts.append(f'<span style="background:{OVERLAP_NEXT_BG};border-radius:3px">{html.escape(text[b:])}</span>')
    body = "".join(parts).replace("\n", "<br>")
    return f'<div style="font-size:0.95rem;line-height:1.6;padding:12px 14px;border:1px solid rgba(128,128,128,.3);border-radius:8px">{body}</div>'


def select_chunk(chunk_id: str) -> None:
    st.session_state.chunk_id = chunk_id


def on_map_select() -> None:
    points = st.session_state.get("embedding_map", {}).get("selection", {}).get("pick", [])
    if points:
        select_chunk(points[0]["id"])


def wave2() -> None:
    st.subheader("Onda 2 · Extração, chunks e embeddings")
    snap = cached_snapshot(str(settings.chroma_dir), settings.chroma_collection, chroma_mtime())
    if snap is None:
        st.info("Nenhum embedding no Chroma ainda. Rode `.venv\\Scripts\\python scripts\\ingest.py`.")
        return

    df, vectors = snap.chunks.copy(), snap.vectors
    sources = sorted(df["source"].unique())
    df["doc"] = df["source"].map(short)
    df["label"] = df["doc"] + " #" + df["chunk_index"].astype(str).str.zfill(2)
    df["snippet"] = df["text"].str.slice(0, 120) + "…"
    colors = alt.Scale(domain=[short(s) for s in sources], range=SERIES[: len(sources)])

    # KPIs
    has_overlap = df[df["overlap_prev"] > 0]
    k = st.columns(6)
    k[0].metric("Documentos", len(sources))
    k[1].metric("Chunks", len(df))
    k[2].metric("Embeddings gerados", len(vectors))
    k[3].metric("Dimensões por vetor", vectors.shape[1])
    k[4].metric("Tamanho médio", f"{df['length'].mean():.0f} car.", help=f"Máximo configurado: {settings.chunk_size}")
    k[5].metric(
        "Overlap médio",
        f"{has_overlap['overlap_prev'].mean():.0f} car." if len(has_overlap) else "—",
        help=f"Máximo configurado: {settings.chunk_overlap}",
    )
    st.caption(
        f"Modelo: `{snap.collection_metadata.get('embedding_model', '?')}` · "
        f"distância: `{snap.collection_metadata.get('hnsw:space', '?')}` · coleção: `{settings.chroma_collection}`"
    )

    # Por documento
    per_doc = (
        df.groupby("source")
        .agg(
            Classificação=("classification", "first"),
            Páginas=("page_end", "max"),
            Chunks=("id", "count"),
            Tamanho_médio=("length", "mean"),
            Overlaps=("overlap_prev", lambda s: int((s > 0).sum())),
            Overlap_médio=("overlap_prev", lambda s: s[s > 0].mean() if (s > 0).any() else 0),
        )
        .round(0)
        .reset_index()
        .rename(columns={"source": "Documento", "Tamanho_médio": "Tamanho médio", "Overlap_médio": "Overlap médio"})
    )
    st.dataframe(per_doc, hide_index=True, width="stretch")

    tab_nav, tab_map, tab_sizes, tab_all = st.tabs(
        ["🧭 Navegar pelos chunks", "🗺️ Mapa dos embeddings", "📏 Tamanho e overlap", "📋 Todos os chunks"]
    )

    ids = df["id"].tolist()
    if st.session_state.get("chunk_id") not in ids:
        st.session_state.chunk_id = ids[0]

    with tab_map:
        coords = project_2d(vectors)
        plot = df[["id", "doc", "label", "page_start", "section", "snippet"]].assign(x=coords[:, 0], y=coords[:, 1])
        plot["selecionado"] = plot["id"].eq(st.session_state.chunk_id)
        pick = alt.selection_point(name="pick", fields=["id"], on="click")
        tooltip = [
            alt.Tooltip("label:N", title="Chunk"),
            alt.Tooltip("page_start:Q", title="Página"),
            alt.Tooltip("section:N", title="Cláusula"),
            alt.Tooltip("snippet:N", title="Texto"),
        ]
        points = (
            alt.Chart(plot)
            .mark_circle(stroke="white", strokeWidth=2, opacity=0.9)
            .encode(
                x=alt.X("x:Q", title="Componente 1", axis=alt.Axis(labels=False, ticks=False, grid=False)),
                y=alt.Y("y:Q", title="Componente 2", axis=alt.Axis(labels=False, ticks=False, grid=False)),
                color=alt.Color("doc:N", scale=colors, legend=alt.Legend(title="Documento", orient="top")),
                size=alt.condition("datum.selecionado", alt.value(420), alt.value(110)),
                tooltip=tooltip,
            )
            .add_params(pick)
        )
        st.altair_chart(
            points.properties(height=460), width="stretch", on_select=on_map_select, key="embedding_map"
        )
        st.caption(
            f"Cada ponto é um embedding de {vectors.shape[1]} dimensões projetado em 2D por PCA "
            f"({explained_variance(vectors):.0%} da variância). Pontos próximos têm significado parecido. "
            "O ponto maior é o chunk selecionado; clique em outro ponto para abri-lo na aba **Navegar pelos chunks**."
        )

    with tab_nav:
        current = ids.index(st.session_state.chunk_id)
        c1, c2, c3 = st.columns([1, 6, 1])
        c1.button("◀ Anterior", on_click=select_chunk, args=(ids[current - 1],), disabled=current == 0, width="stretch")
        c2.selectbox(
            "Chunk",
            ids,
            key="chunk_id",
            format_func=lambda i: f"{df.loc[ids.index(i), 'label']} · pág. {df.loc[ids.index(i), 'page_start']} · {df.loc[ids.index(i), 'section'][:60]}",
            label_visibility="collapsed",
        )
        c3.button("Próximo ▶", on_click=select_chunk, args=(ids[min(current + 1, len(ids) - 1)],), disabled=current == len(ids) - 1, width="stretch")

        row = df.iloc[current]
        vec = vectors[current]
        m = st.columns(5)
        m[0].metric("Caracteres", int(row["length"]))
        m[1].metric("Overlaps", int(row["overlap_count"]), help="Com quantos vizinhos (anterior/próximo) este chunk compartilha texto")
        m[2].metric("Overlap c/ anterior", f"{int(row['overlap_prev'])} car.")
        m[3].metric("Overlap c/ próximo", f"{int(row['overlap_next'])} car.")
        m[4].metric("Páginas", f"{row['page_start']}" + (f"–{row['page_end']}" if row["page_end"] != row["page_start"] else ""))

        st.markdown(
            f'<span style="background:{OVERLAP_PREV_BG};padding:1px 6px;border-radius:3px">compartilhado com o anterior</span> '
            f'&nbsp;<span style="background:{OVERLAP_NEXT_BG};padding:1px 6px;border-radius:3px">compartilhado com o próximo</span>',
            unsafe_allow_html=True,
        )
        st.markdown(highlighted(row["text"], int(row["overlap_prev"]), int(row["overlap_next"])), unsafe_allow_html=True)
        st.caption(
            f"**{row['source']}** · {row['section']} · classificação: {row['classification']} · "
            f"ID `{row['id']}` · posição {row['start_index']} no documento"
        )

        left, right = st.columns([3, 2])
        with left:
            st.markdown(f"**Vetor do embedding** · {len(vec)} dimensões · norma {np.linalg.norm(vec):.3f}")
            vdf = pd.DataFrame({"dimensão": np.arange(len(vec)), "valor": vec})
            bars = (
                alt.Chart(vdf)
                .mark_line(color=SERIES[0], strokeWidth=1)  # 1 path em vez de 1536 barras: render leve
                .encode(
                    x=alt.X("dimensão:Q", title="Dimensão", scale=alt.Scale(domain=[0, len(vec)])),
                    y=alt.Y("valor:Q", title="Valor"),
                    tooltip=["dimensão:Q", alt.Tooltip("valor:Q", format=".4f")],
                )
                .properties(height=220)
            )
            st.altair_chart(bars, width="stretch")
            with st.expander("Primeiros 16 valores"):
                st.code(np.array2string(vec[:16], precision=4, separator=", "))
        with right:
            st.markdown("**Chunks mais parecidos** (cosseno, calculado localmente)")
            neighbors = nearest_neighbors(vectors, current, k=5)
            for idx, sim in neighbors:
                n = df.iloc[idx]
                st.button(
                    f"{sim:.2f} · {n['label']} · pág. {n['page_start']}",
                    key=f"nb_{n['id']}",
                    help=n["snippet"],
                    on_click=select_chunk,
                    args=(n["id"],),
                    width="stretch",
                )

    with tab_sizes:
        base = alt.Chart(df).encode(
            x=alt.X("label:N", sort=None, title=None, axis=alt.Axis(labels=False, ticks=False)),
            color=alt.Color("doc:N", scale=colors, legend=alt.Legend(title="Documento", orient="top")),
            tooltip=[
                alt.Tooltip("label:N", title="Chunk"),
                alt.Tooltip("length:Q", title="Caracteres"),
                alt.Tooltip("overlap_prev:Q", title="Overlap c/ anterior"),
                alt.Tooltip("overlap_next:Q", title="Overlap c/ próximo"),
            ],
        )
        st.markdown(f"**Tamanho de cada chunk** (limite {settings.chunk_size})")
        limit = alt.Chart(pd.DataFrame({"y": [settings.chunk_size]})).mark_rule(strokeDash=[4, 4], color="gray").encode(y="y:Q")
        st.altair_chart(
            (base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(y=alt.Y("length:Q", title="Caracteres")) + limit).properties(height=240),
            width="stretch",
        )
        st.markdown(f"**Overlap com o chunk anterior** (limite {settings.chunk_overlap})")
        limit_o = alt.Chart(pd.DataFrame({"y": [settings.chunk_overlap]})).mark_rule(strokeDash=[4, 4], color="gray").encode(y="y:Q")
        st.altair_chart(
            (base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(y=alt.Y("overlap_prev:Q", title="Caracteres")) + limit_o).properties(height=200),
            width="stretch",
        )
        st.caption("O primeiro chunk de cada documento não tem anterior, por isso tem overlap 0.")

    with tab_all:
        st.dataframe(
            df[["label", "page_start", "page_end", "section", "length", "overlap_prev", "overlap_next", "text"]].rename(
                columns={
                    "label": "Chunk",
                    "page_start": "Pág. ini",
                    "page_end": "Pág. fim",
                    "section": "Cláusula",
                    "length": "Caracteres",
                    "overlap_prev": "Overlap ant.",
                    "overlap_next": "Overlap próx.",
                    "text": "Texto",
                }
            ),
            hide_index=True,
            width="stretch",
            height=520,
        )


# ---------------------------------------------------------------- Onda 3
@st.cache_resource(show_spinner=False)
def cached_store(collection: str, mtime: float):
    return get_vectorstore(settings)


def use_example() -> None:
    choice = st.session_state.get("example_question")
    if choice:
        st.session_state.question_input = choice


def wave3() -> None:
    st.subheader("Onda 3 · Recuperação: teste de perguntas")
    st.caption(
        f"A pergunta vira um embedding com o mesmo modelo dos documentos (`{settings.embedding_model}`), "
        f"e o Chroma devolve os {settings.top_k} chunks mais parecidos. Nada é enviado ao Claude nesta etapa."
    )
    if "OPENAI_API_KEY" in settings.missing_keys():
        st.warning("Preencha `OPENAI_API_KEY` no `.env` para gerar o embedding da pergunta.")
        return

    st.selectbox(
        "Perguntas de exemplo",
        [""] + [q for q, _, _ in REFERENCE_QUESTIONS],
        key="example_question",
        on_change=use_example,
        format_func=lambda q: q or "— escolha uma pergunta de exemplo (opcional) —",
    )
    with st.form("search", border=False):
        col_q, col_b = st.columns([6, 1], vertical_alignment="bottom")
        question = col_q.text_input("Sua pergunta", key="question_input", placeholder="Ex.: Qual a comissão do Xperiun Cloud Pro?")
        submitted = col_b.form_submit_button("🔎 Buscar", type="primary", width="stretch")

    if submitted:
        try:
            store = cached_store(settings.chroma_collection, chroma_mtime())
            with st.spinner("Gerando o embedding da pergunta e buscando no Chroma…"):
                st.session_state.last_result = retrieve(question, settings, store=store)
            history = st.session_state.setdefault("search_history", [])
            r = st.session_state.last_result
            history.insert(0, {"Pergunta": r.question, "Melhor similaridade": r.best_similarity, "Chunks": " · ".join(
                f"{short(c.document.metadata['source'])} #{c.document.metadata['chunk_index']:02d}" for c in r.chunks)})
        except RetrievalError as exc:
            st.error(str(exc))
            st.session_state.pop("last_result", None)

    result = st.session_state.get("last_result")
    if not result:
        return

    m = st.columns(4)
    m[0].metric("Chunks retornados", len(result.chunks))
    m[1].metric("Melhor similaridade", f"{result.best_similarity:.3f}")
    m[2].metric("Embedding da pergunta", f"{len(result.question_vector)} dim.", help=f"{result.embed_ms:.0f} ms na OpenAI")
    m[3].metric("Busca no Chroma", f"{result.search_ms:.0f} ms")
    if result.low_relevance:
        st.warning(
            f"⚠️ Baixa relevância: nenhum chunk passou de {LOW_RELEVANCE_THRESHOLD:.2f} de similaridade. "
            "Provavelmente os documentos não respondem a esta pergunta."
        )

    sources = sorted({c.document.metadata["source"] for c in result.chunks} | {s for _, s, _ in REFERENCE_QUESTIONS})
    colors = alt.Scale(domain=[short(s) for s in sources], range=SERIES[: len(sources)])
    rows = pd.DataFrame(
        [
            {
                # A similaridade vai no rótulo do eixo, que herda a cor de texto do tema (claro/escuro).
                "chunk": f"#{c.rank} · {short(c.document.metadata['source'])} #{c.document.metadata['chunk_index']:02d} · {c.similarity:.3f}",
                "doc": short(c.document.metadata["source"]),
                "similaridade": c.similarity,
            }
            for c in result.chunks
        ]
    )
    chart = (
        alt.Chart(rows)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            y=alt.Y("chunk:N", sort=None, title=None, axis=alt.Axis(labelLimit=320)),
            x=alt.X("similaridade:Q", title="Similaridade de cosseno (0 a 1)", scale=alt.Scale(domain=[0, 1])),
            color=alt.Color("doc:N", scale=colors, legend=alt.Legend(title="Documento", orient="top")),
            tooltip=["chunk:N", alt.Tooltip("similaridade:Q", format=".4f")],
        )
        + alt.Chart(pd.DataFrame({"x": [LOW_RELEVANCE_THRESHOLD]})).mark_rule(strokeDash=[4, 4], color="gray").encode(x="x:Q")
    )
    st.altair_chart(chart.properties(height=alt.Step(44)), width="stretch")
    st.caption(f"Linha tracejada: limite de baixa relevância ({LOW_RELEVANCE_THRESHOLD:.2f}).")

    for c in result.chunks:
        meta = c.document.metadata
        with st.container(border=True):
            head, score = st.columns([5, 2])
            head.markdown(f"**#{c.rank} · {c.citation}**")
            score.progress(max(0.0, min(1.0, c.similarity)), text=f"similaridade **{c.similarity:.3f}**")
            st.markdown(highlighted(c.document.page_content, 0, 0), unsafe_allow_html=True)
            st.caption(f"ID `{c.document.id}` · chunk {meta['chunk_index']} · classificação: {meta['classification']}")

    snap = cached_snapshot(str(settings.chroma_dir), settings.chroma_collection, chroma_mtime())
    if snap is not None:
        st.markdown("**Onde a pergunta cai no mapa dos embeddings**")
        basis = pca_fit(snap.vectors)
        coords = project_2d(snap.vectors, basis)
        q = project_2d(np.asarray(result.question_vector, dtype=np.float32), basis)[0]
        top_ids = {c.document.id: c.rank for c in result.chunks}
        df = snap.chunks.assign(x=coords[:, 0], y=coords[:, 1], doc=snap.chunks["source"].map(short))
        df["label"] = df["doc"] + " #" + df["chunk_index"].astype(str).str.zfill(2)
        df["top"] = df["id"].map(top_ids)
        df["snippet"] = df["text"].str.slice(0, 120) + "…"
        base_pts = (
            alt.Chart(df)
            .mark_circle(stroke="white", strokeWidth=2)
            .encode(
                x=alt.X("x:Q", title="Componente 1", axis=alt.Axis(labels=False, ticks=False, grid=False)),
                y=alt.Y("y:Q", title="Componente 2", axis=alt.Axis(labels=False, ticks=False, grid=False)),
                color=alt.Color("doc:N", scale=colors, legend=alt.Legend(title="Documento", orient="top")),
                size=alt.condition("isValid(datum.top)", alt.value(380), alt.value(70)),
                opacity=alt.condition("isValid(datum.top)", alt.value(1.0), alt.value(0.35)),
                tooltip=[alt.Tooltip("label:N", title="Chunk"), alt.Tooltip("top:Q", title="Posição"), alt.Tooltip("snippet:N", title="Texto")],
            )
        )
        rank_labels = alt.Chart(df[df["top"].notna()]).mark_text(dy=-16, fontWeight="bold").encode(
            x="x:Q", y="y:Q", text=alt.Text("top:Q", format="#")
        )
        question_pt = alt.Chart(pd.DataFrame({"x": [q[0]], "y": [q[1]], "nome": ["Pergunta"]})).mark_point(
            shape="diamond", size=320, filled=True, color="#e34948", stroke="white", strokeWidth=2
        ).encode(x="x:Q", y="y:Q", tooltip=alt.Tooltip("nome:N", title=""))
        st.altair_chart((base_pts + rank_labels + question_pt).properties(height=420), width="stretch")
        st.caption(
            "◆ vermelho = pergunta · números = posição no top-3 · pontos apagados = demais chunks. "
            "A projeção 2D perde informação: a ordem real vem da similaridade em 1536 dimensões, não da distância no desenho."
        )

    history = st.session_state.get("search_history", [])
    if len(history) > 1:
        with st.expander(f"Histórico desta sessão ({len(history)} perguntas)"):
            st.dataframe(pd.DataFrame(history), hide_index=True, width="stretch")


# ---------------------------------------------------------------- Onda 4
PRICE_IN, PRICE_OUT = 4.00, 20.00  # US$ por milhão de tokens (Claude Opus 5.5)


def render_turn_details(turn: dict) -> None:
    retrieval, result = turn["retrieval"], turn["result"]
    if result.confidential:
        st.warning(CONFIDENTIAL_NOTICE)
    if result.missing_citations:
        st.error("A resposta não cita nenhum trecho. Confira as fontes antes de usar.")
    if result.invalid_citations:
        st.error(f"Citações que não existem entre os trechos: {result.invalid_citations}")
    if result.fallback_used:
        st.info(f"O modelo principal recusou; a resposta veio do fallback ({result.model}).")

    with st.expander(f"📚 Fontes: {len(retrieval.chunks)} trechos recuperados"):
        for c in retrieval.chunks:
            used = "✅ citado" if c.rank in result.cited else "não citado"
            st.markdown(f"**[{c.rank}] {c.citation}** · similaridade **{c.similarity:.3f}** · {used}")
            st.markdown(highlighted(c.document.page_content, 0, 0), unsafe_allow_html=True)
    with st.expander("🔍 O que foi enviado ao Claude"):
        if not result.called_model:
            st.markdown(
                "**Nada.** Nenhum trecho passou do limite de relevância, então o sistema respondeu "
                "sem chamar o Claude, para não induzir uma resposta inventada."
            )
        else:
            cost = result.input_tokens / 1e6 * PRICE_IN + result.output_tokens / 1e6 * PRICE_OUT
            k = st.columns(4)
            k[0].metric("Modelo", result.model)
            k[1].metric("Tokens (entrada / saída)", f"{result.input_tokens} / {result.output_tokens}")
            k[2].metric("Tempo do Claude", f"{result.elapsed_ms / 1000:.1f} s")
            k[3].metric("Custo estimado", f"US$ {cost:.4f}")
            st.markdown("**System prompt**")
            st.code(SYSTEM_PROMPT, language=None, wrap_lines=True)
            st.markdown("**Mensagem do usuário (trechos + pergunta)**")
            st.code(result.user_message, language="xml", wrap_lines=True)


def wave4() -> None:
    st.subheader("Onda 4 · Chat com o Claude")
    st.caption(
        f"Fluxo completo: pergunta → embedding (`{settings.embedding_model}`) → {settings.top_k} trechos do Chroma → "
        f"system prompt + trechos + pergunta → `{settings.llm_model}`. Cada pergunta é respondida só com os trechos "
        "recuperados para ela, e o histórico não é reenviado."
    )
    missing = settings.missing_keys()
    if missing:
        st.warning("Preencha no `.env`: " + ", ".join(f"`{m}`" for m in missing))
        return

    history = st.session_state.setdefault("chat", [])
    top = st.container()
    if history and st.button("🗑️ Limpar conversa"):
        st.session_state.chat = []
        st.rerun()

    with top:
        for turn in history:
            with st.chat_message("user"):
                st.markdown(turn["question"])
            with st.chat_message("assistant"):
                st.markdown(turn["result"].answer)
                render_turn_details(turn)

    question = st.chat_input("Pergunte sobre contratos, comissões, fornecedores…")
    if not question:
        return
    with top:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            try:
                store = cached_store(settings.chroma_collection, chroma_mtime())
                with st.spinner("Buscando os trechos mais relevantes…"):
                    retrieval = retrieve(question, settings, store=store)
                stream = AnswerStream(retrieval, settings)
                st.write_stream(stream)
            except (RetrievalError, GenerationError) as exc:
                st.error(str(exc))
                return
            turn = {"question": retrieval.question, "retrieval": retrieval, "result": stream.result}
            render_turn_details(turn)
    history.append(turn)


tab1, tab2, tab3, tab4 = st.tabs(
    ["① Stack e ambiente", "② Chunks e embeddings", "③ Recuperação (teste)", "④ Chat com o Claude"]
)
with tab1:
    wave1()
with tab2:
    wave2()
with tab3:
    wave3()
with tab4:
    wave4()
