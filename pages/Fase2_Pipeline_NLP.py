"""Fase 2: Pipeline NLP — tokenización, TF-IDF, similitud y corpus procesado."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fase2_service import Fase2Service  # noqa: E402
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

st.set_page_config(
    page_title="SIMANW | Fase 2: NLP",
    page_icon="🧠",
    layout="wide",
)
aplicar_estilo_global()


@st.cache_data(show_spinner=False)
def _cargar_noticias_archivo() -> list[dict]:
    ruta = Path("data/noticias_extraidas.json")
    if not ruta.exists() or ruta.stat().st_size < 10:
        return []
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return []


def _noticias_disponibles() -> list[dict]:
    sesion = st.session_state.get("noticias", [])
    return sesion if sesion else _cargar_noticias_archivo()


def _run_fase2(noticias: list[dict]) -> None:
    service = Fase2Service()
    with st.spinner(f"Procesando {len(noticias)} noticias con NLP…"):
        resultado = service.procesar_corpus(noticias)
    st.session_state["fase2_corpus"] = resultado.corpus
    st.session_state["fase2_stats"] = resultado.estadisticas
    st.session_state["fase2_errores"] = resultado.errores
    # Guardar corpus procesado para que otras páginas lo usen
    ruta = Path("data/processed/corpus_procesado.json")
    service.exportar_json(resultado.corpus)
    st.success(
        f"Corpus procesado: {len(resultado.corpus)} documentos. "
        f"Guardado en `{ruta}`."
    )
    if resultado.errores:
        for err in resultado.errores:
            st.warning(err)


def main() -> None:
    encabezado(
        "Fase 2 | Pipeline NLP",
        "Procesamiento de Lenguaje Natural",
        "Limpieza, tokenización, stemming, TF-IDF y similitud coseno sobre el corpus rastreado.",
    )

    noticias = _noticias_disponibles()

    if not noticias:
        st.markdown(
            """
<div class="simanw-callout">
No hay corpus disponible. Ve a <strong>F1 · Rastreo Web</strong>, ejecuta un rastreo
y haz clic en <strong>Guardar en corpus del sistema</strong>.
</div>
""",
            unsafe_allow_html=True,
        )
        return

    st.caption(f"Corpus: **{len(noticias)} noticias** listas para procesar.")

    if st.button("▶ Ejecutar Fase 2 — Pipeline NLP", type="primary", use_container_width=True):
        _run_fase2(noticias)

    if "fase2_corpus" not in st.session_state:
        st.info("Haz clic en **Ejecutar Fase 2** para procesar el corpus.")
        return

    corpus: list[dict] = st.session_state["fase2_corpus"]
    stats: dict = st.session_state["fase2_stats"]

    tabs = st.tabs([
        "Estadísticas", "Corpus procesado", "Términos frecuentes",
        "Similitud", "Detalle de documento", "Exportar",
    ])

    # ── Tab 1: Estadísticas ───────────────────────────────────────────────────
    with tabs[0]:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Documentos", stats.get("total_documentos", 0))
        c2.metric("Tokens totales", stats.get("total_tokens", 0))
        c3.metric("Vocabulario único", stats.get("vocabulario_total", 0))
        c4.metric("Riqueza léxica prom.", f"{stats.get('promedio_riqueza_lexica', 0):.4f}")
        c5.metric("Tokens / doc", f"{stats.get('promedio_tokens_doc', 0):.1f}")

        st.subheader("Riqueza léxica por documento")
        df_riq = pd.DataFrame({
            "Documento": [c["titulo"][:45] for c in corpus],
            "Riqueza léxica": [c["riqueza_lexica"] for c in corpus],
            "Tokens": [c["num_tokens"] for c in corpus],
        })
        fig = px.bar(
            df_riq, x="Riqueza léxica", y="Documento", orientation="h",
            color="Riqueza léxica", color_continuous_scale="Blues",
            template="plotly_white",
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=max(300, len(corpus) * 26),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2: Corpus procesado ───────────────────────────────────────────────
    with tabs[1]:
        st.subheader(f"Corpus procesado — {len(corpus)} documentos")
        filas = [
            {
                "Título": c["titulo"][:55],
                "Categoría": c.get("categoria", "—"),
                "Tokens": c["num_tokens"],
                "Términos": c["num_terminos"],
                "Oraciones": c["num_oraciones"],
                "Vocab. único": c["vocabulario_unico"],
                "Riqueza": f"{c['riqueza_lexica']:.4f}",
                "Top TF-IDF": ", ".join(c.get("terminos_relevantes", [])[:5]),
            }
            for c in corpus
        ]
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True, height=420)

    # ── Tab 3: Términos frecuentes ────────────────────────────────────────────
    with tabs[2]:
        service = Fase2Service()
        top_n = st.slider("Número de términos", 10, 50, 20)
        frecuencias = service.obtener_frecuencias(corpus, top_n=top_n)

        if frecuencias:
            df_freq = pd.DataFrame(frecuencias, columns=["Término", "Frecuencia"])
            col1, col2 = st.columns([1, 1])
            with col1:
                st.dataframe(df_freq, use_container_width=True, hide_index=True)
            with col2:
                fig = px.bar(
                    df_freq.head(20), x="Frecuencia", y="Término", orientation="h",
                    color_discrete_sequence=["#4F46E5"], template="plotly_white",
                )
                fig.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=500, yaxis={"categoryorder": "total ascending"},
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── Tab 4: Similitud coseno ───────────────────────────────────────────────
    with tabs[3]:
        grupos = stats.get("grupos_similares", [])
        pares = stats.get("pares_similares", [])

        if grupos:
            st.subheader(f"Grupos similares detectados — {len(grupos)} grupos (umbral ≥ 0.15)")
            for i, grupo in enumerate(grupos[:10]):
                titulos = [corpus[idx]["titulo"][:50] for idx in grupo if idx < len(corpus)]
                with st.expander(f"Grupo {i + 1} — {len(grupo)} documentos"):
                    for t in titulos:
                        st.markdown(f"- {t}")
        else:
            st.info("Sin grupos similares (corpus pequeño o sin TF-IDF).")

        if pares:
            st.subheader("Documentos más similares por noticia")
            sel = st.selectbox(
                "Selecciona un documento",
                [f"{i}. {c['titulo'][:60]}" for i, c in enumerate(corpus)],
                key="sel_sim",
            )
            idx_sel = int(sel.split(".")[0])
            similares = corpus[idx_sel].get("noticias_similares", [])
            if similares:
                df_sim = pd.DataFrame(similares)
                df_sim["similitud"] = df_sim["similitud"].map(lambda x: f"{x:.4f}")
                st.dataframe(df_sim[["indice", "titulo", "similitud"]],
                             use_container_width=True, hide_index=True)
            else:
                st.info("Sin documentos similares para este documento.")

    # ── Tab 5: Detalle de documento ───────────────────────────────────────────
    with tabs[4]:
        sel_det = st.selectbox(
            "Selecciona un documento",
            [f"{i}. {c['titulo'][:60]}" for i, c in enumerate(corpus)],
            key="sel_det",
        )
        idx_det = int(sel_det.split(".")[0])
        doc = corpus[idx_det]

        st.markdown(f"### {doc['titulo']}")
        st.caption(f"Fecha: {doc.get('fecha', '—')} | Autor: {doc.get('autor', '—')} | Categoría: {doc.get('categoria', '—')}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tokens", doc["num_tokens"])
        col2.metric("Términos filtrados", doc["num_terminos"])
        col3.metric("Oraciones", doc["num_oraciones"])
        col4.metric("Riqueza léxica", f"{doc['riqueza_lexica']:.4f}")

        st.subheader("Términos TF-IDF relevantes")
        st.markdown(" · ".join(f"`{t}`" for t in doc.get("terminos_relevantes", [])) or "—")

        col_orig, col_limpio = st.columns(2)
        with col_orig:
            st.subheader("Texto original")
            st.text_area("", doc.get("texto_original", ""), height=180, disabled=True, key="ta_orig")
        with col_limpio:
            st.subheader("Texto limpio (normalizado)")
            st.text_area("", doc.get("texto_limpio", ""), height=180, disabled=True, key="ta_limpio")

        st.subheader("Tokens (primeros 60)")
        st.markdown(" ".join(f"`{t}`" for t in doc.get("tokens", [])[:60]))

        st.subheader("Stems (primeros 30)")
        st.markdown(" ".join(f"`{s}`" for s in doc.get("stems", [])[:30]))

    # ── Tab 6: Exportar ───────────────────────────────────────────────────────
    with tabs[5]:
        service = Fase2Service()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Exportar corpus JSON", use_container_width=True):
                ruta = service.exportar_json(corpus)
                st.success(f"Exportado: `{ruta}`")
        with col2:
            if st.button("Exportar corpus CSV", use_container_width=True):
                ruta = service.exportar_csv(corpus)
                st.success(f"Exportado: `{ruta}`")

        # Descarga directa
        json_bytes = json.dumps(corpus, ensure_ascii=False, indent=2, default=str).encode("utf-8")
        df_exp = pd.DataFrame([{k: v for k, v in c.items()
                                 if not isinstance(v, (list, dict))} for c in corpus])
        csv_bytes = df_exp.to_csv(index=False).encode("utf-8")

        st.divider()
        col3, col4 = st.columns(2)
        col3.download_button(
            "⬇ Descargar JSON",
            data=json_bytes,
            file_name="corpus_procesado_fase2.json",
            mime="application/json",
            use_container_width=True,
        )
        col4.download_button(
            "⬇ Descargar CSV",
            data=csv_bytes,
            file_name="corpus_procesado_fase2.csv",
            mime="text/csv",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
