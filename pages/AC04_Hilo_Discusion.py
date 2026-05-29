"""AC-4: Análisis de Hilo de Discusión."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analizador_hilo import HILO_IA_DEMO, AnalizadorHiloDiscusion
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

st.set_page_config(page_title="SIMANW | AC-4: Hilo de Discusión", page_icon="💬", layout="wide")
aplicar_estilo_global()


COLORES_SENT = {"positivo": "#10B981", "neutral": "#6B7280", "negativo": "#EF4444"}


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


@st.cache_resource
def get_analizador() -> AnalizadorHiloDiscusion:
    analizador = AnalizadorHiloDiscusion()
    analizador.cargar_hilo(HILO_IA_DEMO)
    return analizador


def _etiqueta(compound: float) -> str:
    if compound >= 0.05:
        return "positivo"
    if compound <= -0.05:
        return "negativo"
    return "neutral"


def _render_mensajes(analizador: AnalizadorHiloDiscusion) -> None:
    resumen = analizador.resumen_hilo()
    st.subheader(f"Hilo de discusión — {resumen.get('total_mensajes', 0)} mensajes")
    for msg in analizador.mensajes:
        compound = msg.get("sentimiento", 0.0)
        etiqueta = _etiqueta(compound)
        color = COLORES_SENT[etiqueta]
        st.markdown(
            f"""<div style="background:#F9FAFB; border-left:3px solid {color};
            padding:0.5rem 0.8rem; border-radius:5px; margin-bottom:0.4rem;">
            <b>{msg.get('usuario','?')}</b>
            <span style="color:#6B7280; font-size:0.75rem; margin-left:0.5rem;">
            {msg.get('timestamp','')}</span><br>
            {msg.get('texto','')}
            <span style="float:right; font-size:0.72rem; color:{color};">
            compound: {compound:+.3f}</span>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_evolucion(analizador: AnalizadorHiloDiscusion) -> None:
    evolucion = analizador.evolucion_sentimiento(ventana=3)
    st.subheader("Evolución del sentimiento (ventana deslizante = 3)")
    if evolucion:
        df_ev = pd.DataFrame(evolucion)
        fig = px.line(
            df_ev, x="posicion", y=["sentimiento_puntual", "tendencia"],
            markers=True, template="plotly_white",
            color_discrete_sequence=["#4F46E5", "#10B981"],
            labels={"posicion": "Mensaje #", "value": "Score", "variable": ""},
        )
        fig.add_hline(y=0.05, line_dash="dot", line_color="#6B7280", annotation_text="umbral +")
        fig.add_hline(y=-0.05, line_dash="dot", line_color="#6B7280", annotation_text="umbral −")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)


def _render_subtemas(analizador: AnalizadorHiloDiscusion) -> None:
    st.subheader("Subtemas detectados (K-Means sobre TF-IDF)")
    n_clusters = st.slider("Número de subtemas", 2, 5, 3)
    with st.spinner("Detectando subtemas…"):
        subtemas = analizador.detectar_subtemas(n_clusters=n_clusters)
    for cluster_id, info in subtemas.items():
        with st.expander(f"Subtema {cluster_id + 1} — {info.get('n_mensajes', 0)} mensajes"):
            st.markdown(f"**Keywords:** `{'`, `'.join(info.get('keywords', []))}`")
            for msg in info.get("mensajes", []):
                st.markdown(f"- **{msg.get('usuario','?')}**: {msg.get('texto','')}")


def _render_resumen(analizador: AnalizadorHiloDiscusion) -> None:
    resumen = analizador.resumen_hilo()
    st.subheader("Resumen del hilo")
    st.json(resumen)
    hashtags = resumen.get("hashtags_top", [])
    if hashtags:
        st.subheader("Hashtags más frecuentes")
        df_ht = pd.DataFrame(hashtags, columns=["Hashtag", "Frecuencia"])
        fig = px.bar(df_ht, x="Frecuencia", y="Hashtag", orientation="h",
                     color_discrete_sequence=["#7C3AED"], template="plotly_white")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    encabezado(
        "AC-4 | Hilo de Discusión",
        "Análisis de Hilo de Discusión",
        "Sentimiento mensaje a mensaje, evolución temporal y detección de subtemas en redes sociales.",
    )

    analizador = get_analizador()
    resumen = analizador.resumen_hilo()

    # Métricas del hilo (demo)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Mensajes", resumen.get("total_mensajes", 0))
    col2.metric("Participantes", resumen.get("participantes", 0))
    col3.metric("Tono general", str(resumen.get("tono", "neutral")).capitalize())
    col4.metric("Sent. promedio", f"{resumen.get('sentimiento_promedio', 0):+.3f}")
    col5.metric("Positivos", f"{resumen.get('positivos_pct', 0):.0f}%")

    st.divider()
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Mensajes del hilo", "Evolución sentimiento", "Subtemas", "Resumen", "Corpus como hilo",
    ])

    with tab1:
        _render_mensajes(analizador)

    with tab2:
        _render_evolucion(analizador)

    with tab3:
        _render_subtemas(analizador)

    with tab4:
        _render_resumen(analizador)

    with tab5:
        st.subheader("Corpus de noticias analizado como hilo de discusión")
        noticias = _noticias_disponibles()
        if not noticias:
            st.info("Sin corpus disponible. Ejecuta la fase de extracción para generar `data/noticias_extraidas.json`.")
        else:
            st.caption(f"Corpus cargado: {len(noticias)} noticias.")
            mensajes_corpus: list[dict] = []
            for n in noticias:
                usuario = n.get("fuente_nombre") or n.get("autor") or "Redacción"
                titulo = n.get("titulo", "")
                fragmento = (n.get("resumen") or n.get("cuerpo", ""))[:200]
                texto = f"{titulo}. {fragmento}" if fragmento else titulo
                timestamp = n.get("fecha", "2026-01-01")
                mensajes_corpus.append({"usuario": usuario, "texto": texto, "timestamp": timestamp})

            analizador_corpus = AnalizadorHiloDiscusion()
            analizador_corpus.cargar_hilo(mensajes_corpus)
            resumen_corpus = analizador_corpus.resumen_hilo()
            evolucion_corpus = analizador_corpus.evolucion_sentimiento(ventana=3)

            # Métricas del corpus como hilo
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            mc1.metric("Mensajes", resumen_corpus.get("total_mensajes", 0))
            mc2.metric("Participantes", resumen_corpus.get("participantes", 0))
            mc3.metric("Tono general", str(resumen_corpus.get("tono", "neutral")).capitalize())
            mc4.metric("Sent. promedio", f"{resumen_corpus.get('sentimiento_promedio', 0):+.3f}")
            mc5.metric("Positivos", f"{resumen_corpus.get('positivos_pct', 0):.0f}%")

            st.divider()

            # Evolución del corpus
            if evolucion_corpus:
                st.subheader("Evolución del sentimiento (ventana = 3)")
                df_ev = pd.DataFrame(evolucion_corpus)
                fig = px.line(
                    df_ev, x="posicion", y=["sentimiento_puntual", "tendencia"],
                    markers=True, template="plotly_white",
                    color_discrete_sequence=["#4F46E5", "#10B981"],
                    labels={"posicion": "Mensaje #", "value": "Score", "variable": ""},
                )
                fig.add_hline(y=0.05, line_dash="dot", line_color="#6B7280", annotation_text="umbral +")
                fig.add_hline(y=-0.05, line_dash="dot", line_color="#6B7280", annotation_text="umbral −")
                fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.subheader("Resumen del corpus como hilo")
            st.json(resumen_corpus)


if __name__ == "__main__":
    main()
