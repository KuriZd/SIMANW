"""AC-8: Control de Calidad del Corpus."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.control_calidad import ControlCalidadCorpus
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

BASE_NOTICIA = {
    "titulo": "Avances en inteligencia artificial generativa",
    "cuerpo": "La inteligencia artificial generativa transforma procesos de software, educacion y analisis de datos.",
    "fecha": "2026-05-10",
    "autor": "Maria Garcia",
    "categoria_original": "tecnologia",
    "url": "https://demo.test/noticias/ia",
    "fuente": "https://demo.test",
}
CORPUS_DEMO = [
    BASE_NOTICIA,
    {**BASE_NOTICIA, "titulo": "Mercados reaccionan a nuevas tasas",
     "url": "https://demo.test/noticias/economia"},
    {**BASE_NOTICIA, "titulo": "", "url": "https://demo.test/noticias/sin-titulo"},
    {**BASE_NOTICIA, "titulo": "Cuerpo corto", "cuerpo": "corto",
     "url": "https://demo.test/noticias/corto"},
    {**BASE_NOTICIA, "titulo": "Fecha invalida", "fecha": "25/05/2026",
     "url": "https://demo.test/noticias/fecha"},
    {**BASE_NOTICIA, "titulo": "Duplicado URL", "url": "https://demo.test/noticias/ia"},
    {**BASE_NOTICIA, "url": "https://demo.test/noticias/ia-copia"},
]

st.set_page_config(page_title="SIMANW | AC-8: Control de Calidad", page_icon="✅", layout="wide")
aplicar_estilo_global()


COLORES_ESTADO = {"Válido": "#10B981", "Rechazado": "#EF4444"}


def main() -> None:
    encabezado(
        "AC-8 | Control de Calidad",
        "Control de Calidad del Corpus",
        "Validación de campos obligatorios, formatos, longitudes mínimas y detección de duplicados exactos y similares.",
    )

    tab1, tab2, tab3 = st.tabs(["Corpus de prueba", "Resultados de validación", "Informe guardado"])

    with tab1:
        st.subheader(f"Corpus demo — {len(CORPUS_DEMO)} registros con errores intencionales")
        st.caption("Contiene: título vacío, cuerpo demasiado corto, fecha en formato incorrecto, URL duplicada y título casi idéntico.")
        filas = []
        for i, n in enumerate(CORPUS_DEMO):
            filas.append({
                "#": i,
                "Título": n.get("titulo", "") or "⚠️ vacío",
                "Cuerpo (chars)": len(n.get("cuerpo", "")),
                "Fecha": n.get("fecha", ""),
                "URL": n.get("url", ""),
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

        with st.expander("Reglas de validación aplicadas"):
            st.markdown("""
| Campo | Regla |
|-------|-------|
| `titulo` | Obligatorio, mínimo 5 caracteres |
| `cuerpo` | Obligatorio, mínimo 50 caracteres |
| `fecha` | Formato `YYYY-MM-DD` |
| `url`, `fuente` | Deben comenzar con `http://` o `https://` |
| `autor`, `categoria_original` | Obligatorios y no vacíos |
| **Duplicados** | URL idéntica = duplicado exacto; título casi idéntico = duplicado similar |
""")

    with tab2:
        if st.button("▶ Ejecutar validación", type="primary"):
            ctrl = ControlCalidadCorpus()
            corpus_depurado = ctrl.validar(CORPUS_DEMO)
            informe = ctrl.generar_informe()
            st.session_state["informe_qc"] = informe
            st.session_state["corpus_depurado"] = corpus_depurado
            st.session_state["parrafo_qc"] = ctrl.parrafo_resumen()
            ctrl.guardar_informe("data/ac8_informe_calidad.json")

        if "informe_qc" in st.session_state:
            informe = st.session_state["informe_qc"]
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total registros", informe.get("total_registros", 0))
            c2.metric("Válidos", informe.get("registros_validos", 0))
            c3.metric("Rechazados", informe.get("registros_rechazados", 0))
            c4.metric("Dup. URL", informe.get("duplicados_exactos_url", 0))
            c5.metric("Dup. título", informe.get("duplicados_casi_identicos_titulo", 0))

            # Gráfica
            df_pie = pd.DataFrame({
                "Estado": ["Válido", "Rechazado"],
                "Cantidad": [informe.get("registros_validos", 0), informe.get("registros_rechazados", 0)],
            })
            fig = px.pie(df_pie, names="Estado", values="Cantidad", color="Estado",
                         color_discrete_map=COLORES_ESTADO, hole=0.4, template="plotly_white")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            col1, col2 = st.columns([1, 2])
            with col1:
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("Registros rechazados")
                detalle = informe.get("detalle_rechazados", [])
                if detalle:
                    df_rech = pd.DataFrame([{
                        "Título": d.get("titulo", "") or "⚠️ vacío",
                        "URL": d.get("url", ""),
                        "Motivos": "; ".join(d.get("motivos", [])),
                    } for d in detalle])
                    st.dataframe(df_rech, use_container_width=True, hide_index=True)

            st.subheader("Corpus depurado")
            corpus_dep = st.session_state.get("corpus_depurado", [])
            st.metric("Registros en corpus depurado", len(corpus_dep))
            if corpus_dep:
                st.dataframe(pd.DataFrame([{
                    "Título": n.get("titulo",""), "Fecha": n.get("fecha",""), "URL": n.get("url",""),
                } for n in corpus_dep]), use_container_width=True, hide_index=True)
            parrafo = st.session_state.get("parrafo_qc")
            if parrafo:
                st.subheader("Párrafo de resumen (máx. 200 palabras)")
                st.info(parrafo)
        else:
            st.info("Haz clic en **Ejecutar validación** para ver los resultados.")

    with tab3:
        ruta = Path("data") / "ac8_informe_calidad.json"
        if ruta.exists():
            informe_guardado = json.loads(ruta.read_text(encoding="utf-8"))
            st.subheader("Informe guardado en `data/ac8_informe_calidad.json`")
            st.json(informe_guardado)
        else:
            st.info("No hay informe guardado aún. Ejecuta la validación primero.")


if __name__ == "__main__":
    main()

