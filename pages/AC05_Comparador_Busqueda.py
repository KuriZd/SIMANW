"""AC-5: Comparación Modelo Booleano vs. Vectorial."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.comparador_busqueda import CONSULTAS_EVAL_AC5, ComparadorModelos
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

NOTICIAS_DEMO = [
    {"titulo": "Avances en inteligencia artificial generativa",
     "cuerpo": "La inteligencia artificial y el aprendizaje automatico impulsan nuevas aplicaciones de software."},
    {"titulo": "Mercados financieros muestran volatilidad",
     "cuerpo": "La inflacion y las tasas de interes presionan al mercado de valores y a los inversionistas."},
    {"titulo": "Descubrimiento cientifico sobre cambio climatico",
     "cuerpo": "Investigadores publican datos sobre emisiones de carbono y calentamiento global."},
    {"titulo": "Python mejora herramientas de programacion",
     "cuerpo": "La nueva version de Python ayuda al desarrollo de software e inteligencia artificial."},
    {"titulo": "Gobierno publica datos abiertos",
     "cuerpo": "El gobierno libera datos abiertos para fortalecer transparencia y politicas publicas."},
]

st.set_page_config(page_title="SIMANW | AC-5: Comparador de Búsqueda", page_icon="🔍", layout="wide")
aplicar_estilo_global()



@st.cache_resource
def get_comparador() -> ComparadorModelos:
    return ComparadorModelos(NOTICIAS_DEMO)


def main() -> None:
    encabezado(
        "AC-5 | Comparador de Búsqueda",
        "Comparación Booleano vs. Vectorial",
        "Evaluación formal de dos modelos de recuperación de información usando Precision, Recall y F1.",
    )

    comparador = get_comparador()

    tab1, tab2, tab3 = st.tabs(["Corpus y consultas", "Comparativa automática", "Consulta manual"])

    with tab1:
        st.subheader("Corpus de documentos")
        df_docs = pd.DataFrame([
            {"#": i, "Título": d["titulo"], "Cuerpo": d["cuerpo"][:80] + "…"}
            for i, d in enumerate(NOTICIAS_DEMO)
        ])
        st.dataframe(df_docs, use_container_width=True, hide_index=True)

        st.subheader("Consultas de evaluación con juicios de relevancia")
        filas_q = []
        for q in CONSULTAS_EVAL_AC5:
            filas_q.append({
                "Consulta": q.get("consulta", ""),
                "Docs relevantes": str(q.get("relevantes", [])),
            })
        st.dataframe(pd.DataFrame(filas_q), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Reporte comparativo")
        if st.button("▶ Generar reporte", type="primary"):
            with st.spinner("Evaluando…"):
                evaluaciones = comparador.evaluar_consultas(CONSULTAS_EVAL_AC5)

            filas_r = []
            for consulta, metricas in evaluaciones.items():
                bool_m = metricas.get("booleano", {})
                vec_m = metricas.get("vectorial", {})
                filas_r.append({
                    "Consulta": consulta,
                    "Bool – Precision": round(bool_m.get("precision", 0), 3),
                    "Bool – Recall": round(bool_m.get("recall", 0), 3),
                    "Bool – F1": round(bool_m.get("f1", 0), 3),
                    "Vec – Precision": round(vec_m.get("precision", 0), 3),
                    "Vec – Recall": round(vec_m.get("recall", 0), 3),
                    "Vec – F1": round(vec_m.get("f1", 0), 3),
                })
            df_r = pd.DataFrame(filas_r)
            st.dataframe(df_r, use_container_width=True, hide_index=True)

            # Gráfica comparativa de F1
            df_melted = pd.DataFrame([
                {"Consulta": r["Consulta"], "Modelo": "Booleano", "F1": r["Bool – F1"]}
                for r in filas_r
            ] + [
                {"Consulta": r["Consulta"], "Modelo": "Vectorial", "F1": r["Vec – F1"]}
                for r in filas_r
            ])
            fig = px.bar(df_melted, x="Consulta", y="F1", color="Modelo", barmode="group",
                         color_discrete_sequence=["#4F46E5", "#10B981"], template="plotly_white")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_tickangle=-20)
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Reporte de texto completo"):
                st.text(comparador.reporte(CONSULTAS_EVAL_AC5))
        else:
            st.info("Haz clic en **Generar reporte** para comparar los modelos.")

    with tab3:
        st.subheader("Búsqueda manual en tiempo real")
        consulta_manual = st.text_input("Escribe una consulta", "inteligencia artificial")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Modelo Booleano (AND)**")
            ids_bool = comparador.busqueda_booleana(consulta_manual)
            if ids_bool:
                for idx in ids_bool:
                    st.markdown(f"- **#{idx}** {NOTICIAS_DEMO[idx]['titulo']}")
            else:
                st.info("Sin resultados booleanos.")
        with col2:
            st.markdown("**Modelo Vectorial (TF-IDF)**")
            ids_vec = comparador.busqueda_vectorial(consulta_manual, top_k=3)
            if ids_vec:
                for idx, score in ids_vec:
                    st.markdown(f"- **#{idx}** `{score:.3f}` — {NOTICIAS_DEMO[idx]['titulo']}")
            else:
                st.info("Sin resultados vectoriales.")


if __name__ == "__main__":
    main()

