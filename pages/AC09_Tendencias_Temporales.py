"""AC-9: Línea de Tiempo y Tendencias por Categoría."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tendencias_temporales import NOTICIAS_AC9_DEMO, TendenciasTemporales
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

st.set_page_config(page_title="SIMANW | AC-9: Tendencias Temporales", page_icon="📈", layout="wide")
aplicar_estilo_global()


COLORES_CAT = {"tecnologia": "#4F46E5", "economia": "#7C3AED", "ciencia": "#06B6D4", "politica": "#F59E0B"}


@st.cache_data
def analizar_tendencias(granularidad: str) -> TendenciasTemporales:
    t = TendenciasTemporales(granularidad=granularidad)
    t.cargar_noticias(NOTICIAS_AC9_DEMO)
    return t


def main() -> None:
    encabezado(
        "AC-9 | Tendencias Temporales",
        "Línea de Tiempo y Tendencias por Categoría",
        "Distribución temporal de noticias por categoría, picos notables y evolución de términos.",
    )

    granularidad = st.radio("Granularidad temporal", ["mes", "semana"], horizontal=True)
    analizador = analizar_tendencias(granularidad)

    tab1, tab2, tab3, tab4 = st.tabs(["Corpus", "Línea de tiempo", "Pico notable", "Tendencias de términos"])

    with tab1:
        st.subheader(f"Corpus de demo — {len(NOTICIAS_AC9_DEMO)} noticias")
        df_n = pd.DataFrame([{
            "Título": n.get("titulo",""), "Categoría": n.get("categoria_original","?"),
            "Fecha": n.get("fecha",""),
        } for n in NOTICIAS_AC9_DEMO]).sort_values("Fecha")
        st.dataframe(df_n, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Distribución por categoría y período")
        conteos = analizador.conteo_por_periodo()

        filas = []
        for cat, periodos in conteos.items():
            for periodo, count in periodos.items():
                filas.append({"Categoría": cat, "Período": periodo, "Noticias": count})
        if filas:
            df_t = pd.DataFrame(filas).sort_values("Período")
            fig = px.bar(
                df_t, x="Período", y="Noticias", color="Categoría",
                color_discrete_map=COLORES_CAT, barmode="group",
                template="plotly_white",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_tickangle=-20)
            st.plotly_chart(fig, use_container_width=True)

            fig_area = px.area(
                df_t, x="Período", y="Noticias", color="Categoría",
                color_discrete_map=COLORES_CAT, template="plotly_white",
            )
            fig_area.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_area, use_container_width=True)

        st.subheader("Tabla resumen exportable")
        tabla = analizador.tabla_resumen()
        if tabla:
            st.dataframe(pd.DataFrame(tabla), use_container_width=True, hide_index=True)
            csv_bytes = pd.DataFrame(tabla).to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Descargar CSV", data=csv_bytes,
                               file_name="ac9_tendencias.csv", mime="text/csv")

        with st.expander("Visualización ASCII"):
            st.code(analizador.visualizacion_texto(), language="text")

    with tab3:
        st.subheader("Pico notable — período con mayor concentración de noticias")
        pico = analizador.pico_notable()
        c1, c2, c3 = st.columns(3)
        c1.metric("Categoría", pico.get("categoria", "?"))
        c2.metric("Período", pico.get("periodo", "?"))
        c3.metric("Noticias", pico.get("count", 0))

        titulos_pico = pico.get("titulos", [])
        if titulos_pico:
            st.subheader("Noticias del pico")
            for t in titulos_pico[:5]:
                st.markdown(f"- {t}")

        st.divider()
        st.subheader("Conclusión del análisis")
        with st.expander("Ver conclusión completa"):
            st.markdown(analizador.conclusion())

    with tab4:
        st.subheader("Evolución de términos: primer período vs. último período")
        conteos = analizador.conteo_por_periodo()
        categorias_top = sorted(conteos, key=lambda c: sum(conteos[c].values()), reverse=True)[:4]

        for cat in categorias_top:
            tend = analizador.tendencia_terminos(cat)
            if tend.get("aumentan") or tend.get("disminuyen"):
                with st.expander(f"[{cat}]  {tend.get('primer_periodo','?')} → {tend.get('ultimo_periodo','?')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Términos que aumentan:**")
                        for t in tend.get("aumentan", [])[:5]:
                            st.markdown(f"- `{t}`")
                    with col2:
                        st.markdown("**Términos que disminuyen:**")
                        for t in tend.get("disminuyen", [])[:5]:
                            st.markdown(f"- `{t}`")


if __name__ == "__main__":
    main()

