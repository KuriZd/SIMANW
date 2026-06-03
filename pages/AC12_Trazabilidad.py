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

# Artefactos del pipeline en orden, con la ruta de donde leer el conteo de documentos
_ETAPAS_PIPELINE: list[tuple[str, Path, Path | None]] = [
    ("F1 · Rastreo",        Path("data/noticias_extraidas.json"),           None),
    ("F2 · NLP",            Path("data/processed/corpus_procesado.json"),   Path("data/noticias_extraidas.json")),
    ("F2 · Corpus depurado",Path("data/processed/corpus_depurado.json"),    Path("data/processed/corpus_procesado.json")),
    ("F3 · Clasificación",  Path("data/resultados_ac3.json"),               Path("data/processed/corpus_depurado.json")),
    ("F3 · Calidad",        Path("outputs/reporte_calidad.json"),           Path("data/noticias_extraidas.json")),
    ("F4 · Búsqueda",       Path("data/ac10_historial_alertas.json"),       Path("data/processed/corpus_procesado.json")),
]


def _contar_docs(ruta: Path) -> int:
    """Lee un JSON y retorna len si es lista, o total_documentos si tiene esa clave."""
    if not ruta.exists():
        return 0
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        if isinstance(datos, list):
            return len(datos)
        if isinstance(datos, dict):
            for clave in ("total_textos", "total_documentos", "total_extraidas"):
                if clave in datos:
                    return int(datos[clave])
        return 0
    except Exception:
        return 0


def _construir_trazabilidad_real() -> tuple[TrazabilidadPipeline, bool]:
    """
    Construye TrazabilidadPipeline leyendo los archivos reales del pipeline.
    Retorna (traza, usando_demo).
    """
    fuente = Path("data/noticias_extraidas.json")
    if not fuente.exists():
        return trazabilidad_demo(), True

    traza = TrazabilidadPipeline(str(fuente))
    alguna_etapa = False
    for etapa, artefacto, entrada_ruta in _ETAPAS_PIPELINE:
        if not artefacto.exists():
            continue
        salida = _contar_docs(artefacto)
        entrada = _contar_docs(entrada_ruta) if entrada_ruta else 0
        traza.registrar_etapa(etapa, entrada, salida, str(artefacto))
        alguna_etapa = True

    if not alguna_etapa:
        return trazabilidad_demo(), True

    return traza, False


def main() -> None:
    encabezado(
        "AC-12 | Trazabilidad",
        "Trazabilidad y Reproducibilidad del Pipeline",
        "Manifiestos de ejecución, logs estructurados JSONL y procedimiento para reproducir el pipeline.",
    )

    traza, usando_demo = _construir_trazabilidad_real()

    if usando_demo:
        st.warning(
            "Mostrando trazabilidad de demostración. Ejecuta el pipeline desde "
            "**F1 · Rastreo Web** para generar artefactos reales."
        )
    else:
        etapas_reales = len(traza.eventos)
        st.caption(f"Trazabilidad real — {etapas_reales} etapa(s) detectadas en disco.")

    archivos_salida = {
        "rastreo":          "data/noticias_extraidas.json",
        "corpus_procesado": "data/processed/corpus_procesado.json",
        "corpus_depurado":  "data/processed/corpus_depurado.json",
        "clasificacion":    "data/resultados_ac3.json",
        "reporte_calidad":  "outputs/reporte_calidad.json",
        "grafo":            "data/simanw.ttl",
    }

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

            fig = px.funnel(
                df_ev, x="Docs salida", y="Etapa",
                color_discrete_sequence=["#4F46E5"],
                template="plotly_white",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, use_container_width=True)

            # Estado de artefactos en disco
            st.subheader("Estado de artefactos en disco")
            rows_arch = []
            for etapa, artefacto, _ in _ETAPAS_PIPELINE:
                existe = artefacto.exists()
                tamano = f"{artefacto.stat().st_size / 1024:.1f} KB" if existe else "—"
                rows_arch.append({
                    "Etapa": etapa,
                    "Artefacto": str(artefacto),
                    "Existe": "✅" if existe else "❌",
                    "Tamaño": tamano,
                })
            st.dataframe(pd.DataFrame(rows_arch), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Manifiesto de ejecución")
        if st.button("Generar y guardar manifiesto", type="primary"):
            ruta = traza.guardar_manifiesto("data/ac12_manifiesto.json", archivos_salida)
            st.success(f"Manifiesto guardado en `{ruta}`")

        ruta_manifest = Path("data/ac12_manifiesto.json")
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

        ruta_log = Path("data/ac12_log.jsonl")
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
