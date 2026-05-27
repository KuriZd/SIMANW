"""AC-12: Trazabilidad y Reproducibilidad del Pipeline."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trazabilidad import TrazabilidadPipeline, trazabilidad_demo
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

st.set_page_config(page_title="SIMANW | AC-12: Trazabilidad", page_icon="📋", layout="wide")
aplicar_estilo_global()



@st.cache_resource
def get_trazabilidad() -> TrazabilidadPipeline:
    return trazabilidad_demo()


def main() -> None:
    encabezado(
        "AC-12 | Trazabilidad",
        "Trazabilidad y Reproducibilidad del Pipeline",
        "Manifiestos de ejecución, logs estructurados JSONL y procedimiento para reproducir el pipeline.",
    )

    traza = get_trazabilidad()

    tab1, tab2, tab3, tab4 = st.tabs(["Etapas del pipeline", "Manifiesto", "Log estructurado", "Reproducibilidad"])

    with tab1:
        st.subheader("Etapas registradas en el pipeline")
        if traza.eventos:
            filas = []
            for ev in traza.eventos:
                filas.append({
                    "Etapa": ev.etapa,
                    "Docs entrada": ev.documentos_entrada,
                    "Docs salida": ev.documentos_salida,
                    "Artefacto": ev.artefacto,
                    "Estado": ev.estado,
                    "Marca de tiempo": ev.marca_tiempo,
                })
            df_ev = pd.DataFrame(filas)
            st.dataframe(df_ev, use_container_width=True, hide_index=True)

            # Diagrama de flujo de documentos
            fig = px.funnel(
                df_ev, x="Docs salida", y="Etapa",
                color_discrete_sequence=["#4F46E5"],
                template="plotly_white",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Manifiesto de ejecución")
        archivos_salida = {
            "rastreo": "data/noticias_extraidas.json",
            "reporte": "data/reporte_final.md",
            "grafo": "data/simanw.ttl",
        }
        if st.button("Generar y guardar manifiesto", type="primary"):
            ruta = traza.guardar_manifiesto("data/ac12_manifiesto.json", archivos_salida)
            st.success(f"Manifiesto guardado en `{ruta}`")

        ruta_manifest = Path("data") / "ac12_manifiesto.json"
        if ruta_manifest.exists():
            manifest_data = json.loads(ruta_manifest.read_text(encoding="utf-8"))
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Versión del proyecto", manifest_data.get("version_proyecto", "?"))
                st.metric("Fuente de noticias", manifest_data.get("fuente_noticias", "?"))
            with col2:
                st.metric("Fecha/Hora", manifest_data.get("fecha_hora", "?"))
                docs_por_etapa = manifest_data.get("documentos_por_etapa", {})
                st.metric("Etapas registradas", len(docs_por_etapa))
            st.subheader("Archivos de salida declarados")
            archivos = manifest_data.get("archivos_salida", {})
            df_arch = pd.DataFrame(list(archivos.items()), columns=["Tipo", "Ruta"])
            st.dataframe(df_arch, use_container_width=True, hide_index=True)
        else:
            st.info("Haz clic en **Generar y guardar manifiesto** para crear el archivo.")

    with tab3:
        st.subheader("Log estructurado (JSONL)")
        if st.button("Generar log JSONL"):
            ruta_log = traza.guardar_log_jsonl("data/ac12_log.jsonl")
            st.success(f"Log guardado en `{ruta_log}`")

        ruta_log = Path("data") / "ac12_log.jsonl"
        if ruta_log.exists():
            lineas = ruta_log.read_text(encoding="utf-8").strip().splitlines()
            st.metric("Eventos en el log", len(lineas))
            registros = [json.loads(l) for l in lineas if l.strip()]
            if registros:
                st.dataframe(pd.DataFrame(registros), use_container_width=True, hide_index=True)
            with st.expander("Ver JSONL raw"):
                st.code(ruta_log.read_text(encoding="utf-8"), language="json")
        else:
            st.info("Haz clic en **Generar log JSONL** para crear el archivo.")

    with tab4:
        st.subheader("Procedimiento reproducible")
        st.info(traza.procedimiento_reproducible())

        st.subheader("Checklist de reproducibilidad")
        alumno = st.text_input("Nombre o código del alumno", "Alumno SIMANW")
        checklist = traza.checklist_firmado(alumno)
        st.code(checklist, language="text")

        st.subheader("Anexo de limitaciones conocidas")
        st.warning(traza.anexo_limitaciones())

        st.subheader("Versión del proyecto")
        st.code(f"Versión Git: {traza.version_proyecto}", language="text")


if __name__ == "__main__":
    main()

