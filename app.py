"""Dashboard principal de SIMANW."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from src.clasificador_noticias import (  # noqa: E402
    ETIQUETAS_ENTRENAMIENTO,
    TEXTOS_ENTRENAMIENTO,
    ClasificadorNoticias,
)
from src.pipeline_nlp import PipelineNLP  # noqa: E402
from src.sentimientos import AnalizadorSentimientos  # noqa: E402
from src.ui_streamlit import (  # noqa: E402
    COLORES_CATEGORIA,
    COLORES_SENTIMIENTO,
    aplicar_estilo_global,
    encabezado,
)


st.set_page_config(
    page_title="SIMANW | Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_estilo_global()


@st.cache_data(show_spinner="Cargando y preparando el corpus...")
def load_data() -> list[dict]:
    ruta = Path("data") / "noticias_extraidas.json"
    if not ruta.exists() or ruta.stat().st_size < 10:
        return []

    with ruta.open(encoding="utf-8") as archivo:
        noticias = json.load(archivo)

    if not noticias:
        return []
    if any("nlp" not in noticia for noticia in noticias):
        PipelineNLP().procesar_noticias(noticias)
    if any("categoria_predicha" not in noticia for noticia in noticias):
        clasificador = ClasificadorNoticias()
        clasificador.entrenar(TEXTOS_ENTRENAMIENTO, ETIQUETAS_ENTRENAMIENTO)
        clasificador.clasificar_noticias(noticias)
    if any("sentimiento" not in noticia for noticia in noticias):
        AnalizadorSentimientos().analizar_noticias(noticias)
    return noticias


def _sentimiento(noticia: dict) -> str:
    return (noticia.get("sentimiento") or {}).get("etiqueta", "neutral")


def _categoria(noticia: dict) -> str:
    return noticia.get("categoria_predicha") or noticia.get("categoria_original") or "general"


def _df_corpus(noticias: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Titulo": noticia.get("titulo", ""),
                "Fecha": noticia.get("fecha", ""),
                "Autor": noticia.get("autor", ""),
                "Categoria": _categoria(noticia),
                "Fuente": noticia.get("fuente", ""),
                "Sentimiento": _sentimiento(noticia),
            }
            for noticia in noticias
        ]
    )


def _grafico_categorias(noticias: list[dict]) -> None:
    df_cat = pd.Series([_categoria(n) for n in noticias]).value_counts().reset_index()
    df_cat.columns = ["Categoria", "Noticias"]
    fig = px.bar(
        df_cat,
        x="Noticias",
        y="Categoria",
        orientation="h",
        color="Categoria",
        color_discrete_map=COLORES_CATEGORIA,
        template="plotly_white",
        text="Noticias",
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        showlegend=False,
        height=330,
        margin=dict(l=8, r=28, t=8, b=8),
        xaxis_title=None,
        yaxis_title=None,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafico_sentimientos(noticias: list[dict]) -> None:
    df_sent = pd.Series([_sentimiento(n) for n in noticias]).value_counts().reset_index()
    df_sent.columns = ["Sentimiento", "Noticias"]
    fig = px.pie(
        df_sent,
        names="Sentimiento",
        values="Noticias",
        color="Sentimiento",
        color_discrete_map=COLORES_SENTIMIENTO,
        hole=0.58,
        template="plotly_white",
    )
    fig.update_traces(textinfo="label+percent", textposition="outside")
    fig.update_layout(
        height=330,
        margin=dict(l=8, r=8, t=8, b=8),
        showlegend=False,
        paper_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig, use_container_width=True)


def _tabla_actividades() -> None:
    actividades = [
        ("Fase 1", "Rastreador Web de Noticias", "DOM, alcance del rastreo y exportacion JSON/CSV."),
        ("Fase 2", "Procesamiento NLP", "Limpieza, tokenizacion y representacion textual."),
        ("Fase 3", "Clasificacion y Analisis", "Categorias, sentimiento y recomendacion."),
        ("Fase 4", "Busqueda Inteligente", "Busqueda booleana, vectorial y lenguaje natural."),
        ("Fase 5", "Chatbot", "Preguntas y respuestas con contexto conversacional."),
        ("Fase 6", "Knowledge Graph", "Grafo RDF, SPARQL, enlaces externos y JSON-LD."),
        ("Fase 7", "Reportes", "Resumen ejecutivo y artefactos reproducibles."),
        ("AC-8 a AC-13", "Actividades complementarias", "Calidad, tendencias, alertas, usabilidad y trazabilidad."),
    ]
    st.dataframe(
        pd.DataFrame(actividades, columns=["Modulo", "Seccion", "Cobertura"]),
        use_container_width=True,
        hide_index=True,
    )


def main() -> None:
    encabezado(
        "Sistema Inteligente de Monitoreo y Analisis de Noticias Web",
        "SIMANW Dashboard",
        "Panel visual para revisar el corpus, validar resultados del pipeline y navegar por las fases del proyecto.",
    )

    noticias = load_data()
    if not noticias:
        st.markdown(
            """
<div class="simanw-callout">
No hay corpus disponible. Ejecuta <strong>python main.py</strong> para generar
<strong>data/noticias_extraidas.json</strong> y vuelve a abrir el dashboard.
</div>
""",
            unsafe_allow_html=True,
        )
        return

    etiquetas = [_sentimiento(noticia) for noticia in noticias]
    categorias = [_categoria(noticia) for noticia in noticias]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Noticias", len(noticias))
    c2.metric("Categorias", len(set(categorias)))
    c3.metric("Autores", len({n.get("autor", "desconocido") for n in noticias}))
    c4.metric("Sentimiento dominante", max(set(etiquetas), key=etiquetas.count).capitalize())

    st.markdown("### Resumen del corpus")
    col1, col2 = st.columns([1.15, 0.85])
    with col1:
        st.markdown('<div class="simanw-panel">', unsafe_allow_html=True)
        st.subheader("Noticias por categoria")
        _grafico_categorias(noticias)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="simanw-panel">', unsafe_allow_html=True)
        st.subheader("Distribucion de sentimientos")
        _grafico_sentimientos(noticias)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Corpus completo")
    st.dataframe(_df_corpus(noticias), use_container_width=True, hide_index=True, height=360)

    st.markdown("### Cobertura del proyecto")
    _tabla_actividades()
    st.caption("Usa el menu lateral para abrir cada actividad complementaria o fase visualizada.")


if __name__ == "__main__":
    main()
