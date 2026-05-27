"""AC-2: Análisis Estadístico de Discursos."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analisis_discurso import AnalisisDiscurso
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

TEXTO_DISCURSO = (
    "La educacion es la herramienta mas poderosa para transformar una sociedad. En Mexico, la "
    "inversion en educacion debe ser prioritaria para garantizar el desarrollo economico y social. "
    "Los jovenes mexicanos merecen oportunidades de calidad en todos los niveles educativos. Las "
    "universidades tecnologicas y los institutos de investigacion son pilares fundamentales para "
    "la innovacion. La ciencia y la tecnologia son motores del progreso nacional. El Instituto "
    "Tecnologico de Morelia ha formado generaciones de ingenieros que contribuyen al desarrollo "
    "del pais. La inteligencia artificial y la programacion son competencias esenciales para el "
    "futuro laboral. Mexico necesita mas profesionales en ciencias computacionales y recuperacion "
    "de informacion."
)

TEXTO_CIENTIFICO = (
    "El procesamiento de lenguaje natural permite a las computadoras comprender y generar texto "
    "humano. Los modelos de aprendizaje profundo como BERT y GPT han revolucionado este campo. "
    "La representacion vectorial de documentos mediante TF-IDF sigue siendo fundamental para "
    "sistemas de recuperacion de informacion. Los algoritmos de clasificacion como Naive Bayes y "
    "SVM logran alta precision en categorizacion de texto. El analisis de sentimientos combina "
    "tecnicas lexicas con aprendizaje automatico para determinar la polaridad emocional de un texto."
)

st.set_page_config(page_title="SIMANW | AC-2: Análisis de Discursos", page_icon="📊", layout="wide")
aplicar_estilo_global()



@st.cache_resource
def get_analizador() -> AnalisisDiscurso:
    return AnalisisDiscurso()


def mostrar_analisis(analisis: dict) -> None:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Oraciones", analisis.get("oraciones", 0))
    m2.metric("Palabras", analisis.get("palabras_totales", 0))
    m3.metric("Vocabulario único", analisis.get("vocabulario_unico", 0))
    m4.metric("Riqueza léxica", f"{analisis.get('riqueza_lexica_global', 0):.3f}")
    m5.metric("Prom. palabras/oración", f"{analisis.get('promedio_palabras_oracion', 0):.1f}")

    col1, col2 = st.columns(2)
    with col1:
        bigramas = analisis.get("top_bigramas", [])
        if bigramas:
            st.subheader("Top bigramas")
            df_b = pd.DataFrame(bigramas[:8], columns=["Bigrama", "Frecuencia"])
            fig = px.bar(df_b, x="Frecuencia", y="Bigrama", orientation="h",
                         color_discrete_sequence=["#4F46E5"], template="plotly_white")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        entidades = analisis.get("posibles_entidades", [])
        if entidades:
            st.subheader("Posibles entidades nombradas")
            df_e = pd.DataFrame(entidades[:10], columns=["Entidad", "Frecuencia"])
            fig = px.bar(df_e, x="Frecuencia", y="Entidad", orientation="h",
                         color_discrete_sequence=["#7C3AED"], template="plotly_white")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    riqueza_sec = analisis.get("riqueza_por_seccion", [])
    if riqueza_sec:
        st.subheader("Riqueza léxica por sección")
        df_r = pd.DataFrame({"Sección": range(1, len(riqueza_sec) + 1), "Riqueza": riqueza_sec})
        fig = px.line(df_r, x="Sección", y="Riqueza", markers=True,
                      color_discrete_sequence=["#06B6D4"], template="plotly_white")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    encabezado(
        "AC-2 | Análisis de Discursos",
        "Análisis Estadístico de Discursos",
        "Análisis léxico completo: oraciones, bigramas, entidades y riqueza léxica por sección.",
    )

    analizador = get_analizador()
    tab1, tab2, tab3 = st.tabs(["Discurso educativo", "Texto científico", "Comparativa"])

    with tab1:
        st.subheader("Discurso educativo")
        texto1 = st.text_area("Texto a analizar", TEXTO_DISCURSO, height=160, key="ta_disc")
        if st.button("Analizar discurso", key="btn_disc"):
            with st.spinner("Analizando…"):
                resultado = analizador.analizar(texto1, "Discurso Educativo")
            st.session_state["analisis_disc"] = resultado
        if "analisis_disc" in st.session_state:
            mostrar_analisis(st.session_state["analisis_disc"])

    with tab2:
        st.subheader("Texto científico NLP")
        texto2 = st.text_area("Texto a analizar", TEXTO_CIENTIFICO, height=140, key="ta_cient")
        if st.button("Analizar texto", key="btn_cient"):
            with st.spinner("Analizando…"):
                resultado = analizador.analizar(texto2, "Texto Científico")
            st.session_state["analisis_cient"] = resultado
        if "analisis_cient" in st.session_state:
            mostrar_analisis(st.session_state["analisis_cient"])

    with tab3:
        st.subheader("Comparativa entre textos")
        if st.button("Generar comparativa", key="btn_comp"):
            with st.spinner("Comparando…"):
                a1 = analizador.analizar(TEXTO_DISCURSO, "Discurso Educativo")
                a2 = analizador.analizar(TEXTO_CIENTIFICO, "Texto Científico")
                comparativa = analizador.comparar_textos([a1, a2])
            st.session_state["comparativa"] = comparativa
        if "comparativa" in st.session_state:
            df_comp = pd.DataFrame(st.session_state["comparativa"])
            st.dataframe(df_comp, use_container_width=True, hide_index=True)
            fig = px.bar(df_comp, x="titulo", y=["palabras", "vocabulario"],
                         barmode="group", template="plotly_white",
                         color_discrete_sequence=["#4F46E5", "#7C3AED"])
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Haz clic en **Generar comparativa** para comparar ambos textos.")


if __name__ == "__main__":
    main()

