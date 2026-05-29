"""AC-10: Sistema de Alertas por Consulta Guardada."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.alertas_consulta import (
    ConsultaGuardada,
    SistemaAlertasConsulta,
    consultas_demo,
    noticias_nuevas_demo,
)
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

st.set_page_config(page_title="SIMANW | AC-10: Alertas por Consulta", page_icon="🔔", layout="wide")
aplicar_estilo_global()


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


def main() -> None:
    encabezado(
        "AC-10 | Alertas por Consulta",
        "Sistema de Alertas por Consulta Guardada",
        "Monitorea noticias nuevas contra consultas persistentes y evita alertas duplicadas.",
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Consultas guardadas", "Noticias nuevas", "Simulación de alertas", "Historial"])

    with tab1:
        consultas = consultas_demo()
        st.subheader(f"Consultas guardadas — {len(consultas)}")
        df_c = pd.DataFrame([{
            "Nombre": c.nombre,
            "Expresión de búsqueda": c.expresion,
            "Creada": c.fecha_creacion,
        } for c in consultas])
        st.dataframe(df_c, use_container_width=True, hide_index=True)

        st.subheader("Agregar consulta personalizada")
        col1, col2 = st.columns(2)
        with col1:
            nombre_nueva = st.text_input("Nombre", "Mi alerta")
        with col2:
            expresion_nueva = st.text_input("Expresión (términos separados por espacio, frases entre comillas)", "inteligencia artificial")
        if st.button("Agregar consulta"):
            nueva = ConsultaGuardada(nombre=nombre_nueva, expresion=expresion_nueva,
                                      fecha_creacion="2026-05-25T09:00:00Z")
            consultas.append(nueva)
            st.success(f"Consulta **{nombre_nueva}** agregada.")
            st.rerun()

    with tab2:
        fuente_radio = st.radio(
            "Fuente de noticias nuevas",
            ["Demo", "Corpus real"],
            horizontal=True,
        )

        if fuente_radio == "Corpus real":
            corpus = _noticias_disponibles()
            if corpus:
                noticias_nuevas = corpus[:20]
                st.caption(f"Corpus real cargado: mostrando {len(noticias_nuevas)} de {len(corpus)} noticias.")
            else:
                st.info("No hay corpus real disponible. Usando datos de demo.")
                noticias_nuevas = noticias_nuevas_demo()
        else:
            noticias_nuevas = noticias_nuevas_demo()

        st.session_state["ac10_noticias_fuente"] = noticias_nuevas

        st.subheader(f"Noticias nuevas para procesar — {len(noticias_nuevas)}")
        df_n = pd.DataFrame([{
            "Título": n.get("titulo", ""),
            "Cuerpo (resumen)": n.get("cuerpo", "")[:80] + "…",
            "URL": n.get("url", ""),
        } for n in noticias_nuevas])
        st.dataframe(df_n, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Simulación de procesamiento de alertas")

        noticias_para_procesar = st.session_state.get("ac10_noticias_fuente") or noticias_nuevas_demo()

        if st.button("▶ Procesar noticias nuevas (primera vez)", type="primary"):
            sistema = SistemaAlertasConsulta(consultas_demo())
            alertas = sistema.procesar_noticias_nuevas(noticias_para_procesar, "2026-05-25T12:00:00Z")
            sistema.guardar_consultas("data/ac10_consultas_guardadas.json")
            sistema.guardar_historial("data/ac10_historial_alertas.json")
            st.session_state["alertas_resultado"] = alertas
            st.session_state["doc_dedup"] = sistema.documentar_deduplicacion()

        if st.button("🔁 Reprocesar las mismas noticias (deduplicación)"):
            sistema = SistemaAlertasConsulta(consultas_demo())
            sistema.procesar_noticias_nuevas(noticias_para_procesar, "2026-05-25T12:00:00Z")
            repetidas = sistema.procesar_noticias_nuevas(noticias_para_procesar, "2026-05-25T12:05:00Z")
            st.session_state["alertas_repetidas"] = repetidas

        if "alertas_resultado" in st.session_state:
            alertas = st.session_state["alertas_resultado"]
            st.metric("Alertas generadas (1ª ejecución)", len(alertas))

            repetidas = st.session_state.get("alertas_repetidas")
            if repetidas is not None:
                st.metric("Alertas duplicadas bloqueadas (2ª ejecución)", len(repetidas))

            if alertas:
                df_a = pd.DataFrame([{
                    "Consulta": a.get("consulta", ""),
                    "Expresión": a.get("expresion", ""),
                    "Título noticia": a.get("titulo", ""),
                    "URL": a.get("url", ""),
                    "Marca de tiempo": a.get("marca_tiempo", ""),
                } for a in alertas])
                st.dataframe(df_a, use_container_width=True, hide_index=True)

            with st.expander("Mecanismo de deduplicación"):
                st.info(st.session_state.get("doc_dedup", ""))
        else:
            st.info("Haz clic en **Procesar noticias nuevas** para ver las alertas.")

    with tab4:
        ruta_hist = Path("data") / "ac10_historial_alertas.json"
        ruta_cons = Path("data") / "ac10_consultas_guardadas.json"
        if ruta_hist.exists():
            st.subheader("Historial de alertas (`data/ac10_historial_alertas.json`)")
            historial = json.loads(ruta_hist.read_text(encoding="utf-8"))
            st.metric("Total alertas en historial", len(historial))
            if historial:
                st.dataframe(pd.DataFrame(historial), use_container_width=True, hide_index=True)
        if ruta_cons.exists():
            st.subheader("Consultas persistidas (`data/ac10_consultas_guardadas.json`)")
            cons = json.loads(ruta_cons.read_text(encoding="utf-8"))
            st.dataframe(pd.DataFrame(cons), use_container_width=True, hide_index=True)
        if not ruta_hist.exists() and not ruta_cons.exists():
            st.info("No hay historial guardado. Ejecuta la simulación primero.")


if __name__ == "__main__":
    main()
