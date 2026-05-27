"""AC-11: Estudio de Usabilidad del Sistema."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.usabilidad import (
    CUESTIONARIO_USABILIDAD,
    TAREAS_USABILIDAD,
    EstudioUsabilidad,
    estudio_demo,
)
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

st.set_page_config(page_title="SIMANW | AC-11: Usabilidad", page_icon="🧪", layout="wide")
aplicar_estilo_global()



@st.cache_resource
def get_estudio() -> EstudioUsabilidad:
    return estudio_demo()


def main() -> None:
    encabezado(
        "AC-11 | Estudio de Usabilidad",
        "Estudio de Usabilidad del Sistema",
        "Evaluación de la interfaz SIMANW mediante guión de tareas y cuestionario de satisfacción.",
    )

    estudio = get_estudio()

    tab1, tab2, tab3, tab4 = st.tabs(["Guión de tareas", "Resultados por participante", "Promedios y análisis", "Mejoras y ética"])

    with tab1:
        st.subheader("Tareas del guión de usabilidad")
        for i, tarea in enumerate(estudio.tareas, 1):
            st.markdown(
                f"""<div style="background:#F9FAFB; border-left:3px solid #4F46E5;
                padding:0.5rem 0.8rem; border-radius:5px; margin-bottom:0.4rem;">
                <b>Tarea {i}</b> — {tarea}</div>""",
                unsafe_allow_html=True,
            )

        st.subheader("Ítems del cuestionario (escala 1–5)")
        for i, item in enumerate(estudio.items, 1):
            st.markdown(f"**{i}.** {item}")

    with tab2:
        st.subheader("Resultados por participante (anonimizados)")
        tabla = estudio.tabla_anonimizada()
        if tabla:
            df_p = pd.DataFrame(tabla)
            st.dataframe(df_p, use_container_width=True, hide_index=True)

            fig = px.imshow(
                df_p.set_index("participante"),
                color_continuous_scale="Blues",
                zmin=1, zmax=5,
                template="plotly_white",
                title="Heatmap de respuestas por participante",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

            csv_bytes = df_p.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Descargar CSV", data=csv_bytes,
                               file_name="ac11_resultados_usabilidad.csv", mime="text/csv")

    with tab3:
        st.subheader("Puntuaciones promedio por ítem")
        promedios = estudio.promedios()
        df_prom = pd.DataFrame(list(promedios.items()), columns=["Ítem", "Promedio"]).sort_values(
            "Promedio", ascending=True
        )
        fig = px.bar(
            df_prom, x="Promedio", y="Ítem", orientation="h",
            color="Promedio", color_continuous_scale="Blues",
            range_color=[1, 5], template="plotly_white",
        )
        fig.add_vline(x=3.0, line_dash="dot", line_color="#EF4444",
                      annotation_text="umbral mínimo")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

        puntuacion_global = sum(promedios.values()) / len(promedios) if promedios else 0
        st.metric("Puntuación global promedio", f"{puntuacion_global:.2f} / 5.0")

    with tab4:
        st.subheader("Problemas detectados y mejoras propuestas")
        mejoras = estudio.problemas_y_mejoras()
        df_m = pd.DataFrame(mejoras)
        st.dataframe(df_m, use_container_width=True, hide_index=True)

        st.subheader("Reflexión sobre consentimiento informado")
        st.info(estudio.reflexion_consentimiento())

        with st.expander("Formato de registro de participante"):
            st.markdown("""
**Código del participante:** `P___ ` (no se registran nombres reales)

**Instrucción:** Lee cada ítem y asigna un valor del 1 al 5.
- 1 = Muy en desacuerdo
- 3 = Neutral
- 5 = Muy de acuerdo

Los datos se reportan de forma **agregada** y no permiten identificar a ningún participante.
""")


if __name__ == "__main__":
    main()

