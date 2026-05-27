"""AC-3: Selección Automática de Modelo de Clasificación."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.selector_modelo import ETIQUETAS_AC3, TEXTOS_AC3, SelectorModelo
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

st.set_page_config(page_title="SIMANW | AC-3: Selección de Modelo", page_icon="🤖", layout="wide")
aplicar_estilo_global()


COLORES_CAT = {"tecnologia": "#4F46E5", "economia": "#7C3AED", "ciencia": "#06B6D4", "politica": "#F59E0B"}


@st.cache_data(show_spinner="Entrenando y evaluando modelos…")
def evaluar_modelos() -> tuple[dict, str | None]:
    selector = SelectorModelo()
    resultados = selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)
    mejor = selector.mejor_modelo[0] if selector.mejor_modelo else None
    return resultados, mejor


@st.cache_resource
def get_selector() -> SelectorModelo:
    selector = SelectorModelo()
    selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)
    return selector


def main() -> None:
    encabezado(
        "AC-3 | Selección de Modelo",
        "Selección Automática de Modelo de Clasificación",
        "Compara Naive Bayes, SVM Lineal, Regresión Logística y Random Forest mediante validación cruzada.",
    )

    tab1, tab2, tab3 = st.tabs(["Datos de entrenamiento", "Evaluación de modelos", "Predicción"])

    with tab1:
        st.subheader(f"Corpus de entrenamiento — {len(TEXTOS_AC3)} documentos")
        df_train = pd.DataFrame({
            "Texto": [t[:80] + "…" if len(t) > 80 else t for t in TEXTOS_AC3],
            "Etiqueta": ETIQUETAS_AC3,
        })
        st.dataframe(df_train, use_container_width=True, hide_index=True)

        dist = pd.Series(ETIQUETAS_AC3).value_counts().reset_index()
        dist.columns = ["Categoría", "Documentos"]
        fig = px.bar(dist, x="Documentos", y="Categoría", orientation="h",
                     color="Categoría", color_discrete_map=COLORES_CAT, template="plotly_white")
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Comparación de modelos (cross-validation 3-fold)")
        resultados, mejor = evaluar_modelos()

        filas = []
        for nombre, metricas in resultados.items():
            filas.append({
                "Modelo": nombre,
                "Accuracy CV (media)": round(metricas.get("accuracy_mean", 0), 4),
                "Accuracy CV (std)": round(metricas.get("accuracy_std", 0), 4),
                "¿Mejor?": "✅" if nombre == mejor else "",
            })
        df_res = pd.DataFrame(filas).sort_values("Accuracy CV (media)", ascending=False)
        st.dataframe(df_res, use_container_width=True, hide_index=True)

        if mejor:
            st.metric("Modelo seleccionado", mejor)

        fig = px.bar(
            df_res, x="Accuracy CV (media)", y="Modelo", orientation="h",
            error_x="Accuracy CV (std)",
            color_discrete_sequence=["#4F46E5"], template="plotly_white",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Clasificar nuevos textos")
        nuevos_default = (
            "nueva aplicacion de machine learning para detectar fraudes\n"
            "el presidente anuncio reformas al sistema de justicia\n"
            "inflacion y tasas de interes presionan al mercado de valores"
        )
        textos_input = st.text_area(
            "Un texto por línea", nuevos_default, height=120,
        )
        if st.button("Clasificar", type="primary"):
            textos = [t.strip() for t in textos_input.splitlines() if t.strip()]
            if textos:
                selector = get_selector()
                predicciones = selector.predecir(textos)
                df_pred = pd.DataFrame({
                    "Texto": [t[:70] + "…" if len(t) > 70 else t for t in textos],
                    "Categoría predicha": predicciones,
                })
                st.dataframe(df_pred, use_container_width=True, hide_index=True)
            else:
                st.warning("Escribe al menos un texto.")


if __name__ == "__main__":
    main()

