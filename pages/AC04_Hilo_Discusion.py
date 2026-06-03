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


def _noticias_a_mensajes(noticias: list[dict]) -> list[dict]:
    mensajes = []
    for n in noticias:
        usuario = n.get("fuente_nombre") or n.get("autor") or "Redacción"
        titulo = n.get("titulo", "")
        fragmento = (n.get("resumen") or n.get("cuerpo") or n.get("texto_original") or "")[:200]
        texto = f"{titulo}. {fragmento}" if fragmento else titulo
        timestamp = n.get("fecha", "2000-01-01")
        mensajes.append({"usuario": usuario, "texto": texto, "timestamp": timestamp})
    return mensajes


def _get_analizador(noticias: list[dict]) -> tuple[AnalizadorHiloDiscusion, bool]:
    """Devuelve (analizador, usando_demo). Cachea en session_state por tamaño."""
    cache_key = f"ac4_analizador_{len(noticias)}"
    if cache_key not in st.session_state:
        analizador = AnalizadorHiloDiscusion()
        if noticias:
            analizador.cargar_hilo(_noticias_a_mensajes(noticias))
            usando_demo = False
        else:
            analizador.cargar_hilo(HILO_IA_DEMO)
            usando_demo = True
        st.session_state[cache_key] = (analizador, usando_demo)
    return st.session_state[cache_key]


def _etiqueta(compound: float) -> str:
    if compound >= 0.05:
        return "positivo"
    if compound <= -0.05:
        return "negativo"
    return "neutral"


def _render_mensajes(analizador: AnalizadorHiloDiscusion) -> None:
    resumen = analizador.resumen_hilo()
    total = resumen.get("total_mensajes", 0)
    st.subheader(f"Hilo de discusión — {total} mensajes")
    mostrar = st.slider("Mensajes a mostrar", 1, max(1, total), min(20, total), key="sl_msgs")
    for msg in analizador.mensajes[:mostrar]:
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
    total = len(analizador.mensajes)
    ventana_max = max(2, min(10, total // 2))
    if ventana_max > 2:
        ventana = st.slider("Ventana deslizante", 2, ventana_max, min(3, ventana_max), key="sl_ventana")
    else:
        ventana = 2
        st.caption(f"Ventana fija = {ventana} (corpus pequeño).")
    evolucion = analizador.evolucion_sentimiento(ventana=ventana)
    st.subheader(f"Evolución del sentimiento (ventana = {ventana})")
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
    else:
        st.info("No hay suficientes mensajes para calcular la evolución.")


def _render_subtemas(analizador: AnalizadorHiloDiscusion) -> None:
    total = len(analizador.mensajes)
    max_clusters = max(2, min(8, total // 2))
    if max_clusters > 2:
        n_clusters = st.slider("Número de subtemas", 2, max_clusters, min(3, max_clusters), key="sl_clusters")
    else:
        n_clusters = 2
        st.caption(f"Subtemas fijos = {n_clusters} (corpus pequeño).")
    with st.spinner("Detectando subtemas…"):
        subtemas = analizador.detectar_subtemas(n_clusters=n_clusters)
    for cluster_id, info in subtemas.items():
        with st.expander(f"Subtema {cluster_id + 1} — {info.get('n_mensajes', 0)} mensajes"):
            st.markdown(f"**Keywords:** `{'`, `'.join(info.get('keywords', []))}`")
            for msg in info.get("mensajes", [])[:5]:
                st.markdown(f"- **{msg.get('usuario','?')}**: {msg.get('texto','')[:120]}")


def _render_resumen(analizador: AnalizadorHiloDiscusion) -> None:
    resumen = analizador.resumen_hilo()
    st.subheader("Resumen del hilo")

    col1, col2 = st.columns(2)
    with col1:
        campos = {k: v for k, v in resumen.items() if k != "hashtags_top"}
        st.json(campos)
    with col2:
        hashtags = resumen.get("hashtags_top", [])
        if hashtags:
            st.subheader("Hashtags más frecuentes")
            df_ht = pd.DataFrame(hashtags, columns=["Hashtag", "Frecuencia"])
            fig = px.bar(df_ht, x="Frecuencia", y="Hashtag", orientation="h",
                         color_discrete_sequence=["#7C3AED"], template="plotly_white")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se detectaron hashtags en este hilo.")


def main() -> None:
    encabezado(
        "AC-4 | Hilo de Discusión",
        "Análisis de Hilo de Discusión",
        "Sentimiento mensaje a mensaje, evolución temporal y detección de subtemas.",
    )

    noticias = _noticias_disponibles()
    analizador, usando_demo = _get_analizador(noticias)
    resumen = analizador.resumen_hilo()

    if usando_demo:
        st.warning(
            "Mostrando hilo de demostración. Carga noticias desde **F1 · Rastreo Web** "
            "y guárdalas en el corpus para analizar datos reales."
        )
    else:
        st.caption(
            f"Corpus real — {len(noticias)} noticias convertidas a mensajes de hilo. "
            "Cada noticia = un mensaje; autor = fuente/autor de la noticia."
        )

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Mensajes", resumen.get("total_mensajes", 0))
    col2.metric("Participantes", resumen.get("participantes", 0))
    col3.metric("Tono general", str(resumen.get("tono", "neutral")).capitalize())
    col4.metric("Sent. promedio", f"{resumen.get('sentimiento_promedio', 0):+.3f}")
    col5.metric("Positivos", f"{resumen.get('positivos_pct', 0):.0f}%")

    st.divider()
    tab1, tab2, tab3, tab4 = st.tabs([
        "Mensajes del hilo", "Evolución sentimiento", "Subtemas", "Resumen",
    ])

    with tab1:
        _render_mensajes(analizador)

    with tab2:
        _render_evolucion(analizador)

    with tab3:
        _render_subtemas(analizador)

    with tab4:
        _render_resumen(analizador)


if __name__ == "__main__":
    main()
