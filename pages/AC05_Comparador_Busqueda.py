"""AC-5: Comparación Modelo Booleano vs. Vectorial."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.comparador_busqueda import (
    CONSULTAS_EVAL_AC5,
    ComparadorModelos,
    generar_consultas_desde_corpus,
)
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


def _get_comparador_y_consultas(
    noticias: list[dict], usando_reales: bool
) -> tuple[ComparadorModelos, list[dict]]:
    corpus_key = f"comparador_{len(noticias)}"
    if corpus_key not in st.session_state:
        comparador = ComparadorModelos(noticias)
        consultas = (
            generar_consultas_desde_corpus(noticias, max_consultas=5)
            if usando_reales
            else CONSULTAS_EVAL_AC5
        )
        st.session_state[corpus_key] = (comparador, consultas)
    return st.session_state[corpus_key]


def _render_tabla_comparativa(evaluacion: dict) -> pd.DataFrame:
    filas = []
    for r in evaluacion["resultados"]:
        b = r["booleano"]
        v = r["vectorial"]
        filas.append({
            "Consulta": r["consulta"],
            "Relevantes": len(r["relevantes"]),
            "Bool – Recup.": b["recuperados"],
            "Bool – Prec.": round(b["precision"], 3),
            "Bool – Recall": round(b["recall"], 3),
            "Bool – F1": round(b["f1"], 3),
            "Bool – P@K": round(b["precision_at_k"], 3),
            "Bool – AP": round(b["average_precision"], 3),
            "Vec – Recup.": v["recuperados"],
            "Vec – Prec.": round(v["precision"], 3),
            "Vec – Recall": round(v["recall"], 3),
            "Vec – F1": round(v["f1"], 3),
            "Vec – P@K": round(v["precision_at_k"], 3),
            "Vec – AP": round(v["average_precision"], 3),
        })
    return pd.DataFrame(filas)


def main() -> None:
    encabezado(
        "AC-5 | Comparador de Búsqueda",
        "Comparación Booleano vs. Vectorial",
        "Evaluación formal de dos modelos de recuperación de información usando Precision, Recall, F1, P@K y MAP.",
    )

    noticias_reales = _noticias_disponibles()
    usando_reales = bool(noticias_reales)
    noticias = noticias_reales if usando_reales else NOTICIAS_DEMO

    if usando_reales:
        st.caption(f"Corpus real — {len(noticias)} noticias. Juicios de relevancia generados automáticamente por categoría.")
    else:
        st.warning("Sin corpus real. Mostrando demo (5 documentos con juicios fijos). Carga noticias desde **F1 · Rastreo Web**.")

    comparador, consultas_eval = _get_comparador_y_consultas(noticias, usando_reales)

    tab1, tab2, tab3 = st.tabs(["Corpus y consultas", "Comparativa formal", "Consulta manual"])

    with tab1:
        st.subheader("Corpus de documentos")
        df_docs = pd.DataFrame([
            {"#": i, "Título": d["titulo"], "Cuerpo": d["cuerpo"][:80] + "…"}
            for i, d in enumerate(noticias)
        ])
        st.dataframe(df_docs, use_container_width=True, hide_index=True)

        st.subheader("Consultas con juicios de relevancia")
        filas_q = []
        for q in consultas_eval:
            filas_q.append({
                "Consulta": q.get("consulta", ""),
                "Docs relevantes (índices)": str(q.get("relevantes", [])),
                "Criterio": q.get("criterio_relevancia", "manual"),
            })
        st.dataframe(pd.DataFrame(filas_q), use_container_width=True, hide_index=True)
        if usando_reales:
            st.caption("Los juicios de relevancia se derivan de la categoría de cada noticia: documentos de la misma categoría son considerados relevantes para los términos más frecuentes de esa categoría.")

    with tab2:
        st.subheader("Reporte comparativo formal")
        if st.button("▶ Generar reporte", type="primary", use_container_width=True):
            with st.spinner("Evaluando ambos modelos…"):
                evaluacion = comparador.evaluar_consultas(consultas_eval)
            st.session_state["ac5_evaluacion"] = evaluacion

        if "ac5_evaluacion" not in st.session_state:
            st.info("Haz clic en **Generar reporte** para comparar los modelos.")
        else:
            evaluacion = st.session_state["ac5_evaluacion"]

            # ── Métricas promedio y ganadores ─────────────────────────────────
            pb = evaluacion["promedio_booleano"]
            pv = evaluacion["promedio_vectorial"]

            st.subheader("Métricas promedio")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("MAP Booleano", f"{evaluacion['map_booleano']:.3f}")
            c2.metric("MAP Vectorial", f"{evaluacion['map_vectorial']:.3f}")
            c3.metric("Ganador Precision", evaluacion["ganador_precision"].capitalize())
            c4.metric("Ganador F1", evaluacion["ganador_f1"].capitalize())
            c5.metric("Ganador MAP", evaluacion["ganador_map"].capitalize())

            col_b, col_v = st.columns(2)
            with col_b:
                st.markdown("**Booleano — promedios**")
                st.dataframe(pd.DataFrame([{
                    "Prec.": round(pb["precision"], 3),
                    "Recall": round(pb["recall"], 3),
                    "F1": round(pb["f1"], 3),
                    "P@K": round(pb["precision_at_k"], 3),
                    "AP": round(pb["average_precision"], 3),
                }]), hide_index=True, use_container_width=True)
            with col_v:
                st.markdown("**Vectorial — promedios**")
                st.dataframe(pd.DataFrame([{
                    "Prec.": round(pv["precision"], 3),
                    "Recall": round(pv["recall"], 3),
                    "F1": round(pv["f1"], 3),
                    "P@K": round(pv["precision_at_k"], 3),
                    "AP": round(pv["average_precision"], 3),
                }]), hide_index=True, use_container_width=True)

            # ── Tabla por consulta ────────────────────────────────────────────
            st.subheader("Resultados por consulta")
            df_r = _render_tabla_comparativa(evaluacion)
            st.dataframe(df_r, use_container_width=True, hide_index=True)

            # ── Gráficas ──────────────────────────────────────────────────────
            filas_f1 = []
            for r in evaluacion["resultados"]:
                filas_f1 += [
                    {"Consulta": r["consulta"][:30], "Modelo": "Booleano", "F1": r["booleano"]["f1"]},
                    {"Consulta": r["consulta"][:30], "Modelo": "Vectorial", "F1": r["vectorial"]["f1"]},
                ]
            fig_f1 = px.bar(
                pd.DataFrame(filas_f1), x="Consulta", y="F1", color="Modelo",
                barmode="group", color_discrete_sequence=["#4F46E5", "#10B981"],
                template="plotly_white", title="F1 por consulta",
            )
            fig_f1.update_layout(margin=dict(l=0, r=0, t=30, b=0), xaxis_tickangle=-20)

            filas_map = [
                {"Modelo": "Booleano", "MAP": evaluacion["map_booleano"]},
                {"Modelo": "Vectorial", "MAP": evaluacion["map_vectorial"]},
            ]
            fig_map = px.bar(
                pd.DataFrame(filas_map), x="Modelo", y="MAP", color="Modelo",
                color_discrete_sequence=["#4F46E5", "#10B981"],
                template="plotly_white", title="MAP (Mean Average Precision)",
            )
            fig_map.update_layout(margin=dict(l=0, r=0, t=30, b=0), yaxis_range=[0, 1])

            col_g1, col_g2 = st.columns([2, 1])
            col_g1.plotly_chart(fig_f1, use_container_width=True)
            col_g2.plotly_chart(fig_map, use_container_width=True)

            # ── Conclusión ────────────────────────────────────────────────────
            st.subheader("Conclusión")
            st.success(comparador.generar_conclusion(evaluacion))

            with st.expander("Reporte de texto completo"):
                st.text(comparador.reporte(consultas_eval))

            if st.button("Exportar evaluación JSON", key="btn_export_ac5"):
                ruta = comparador.guardar_json("data/resultados_ac5.json", consultas_eval)
                st.success("Evaluación guardada en `data/resultados_ac5.json`")

    with tab3:
        st.subheader("Búsqueda manual en tiempo real")
        consulta_manual = st.text_input("Escribe una consulta", "inteligencia artificial")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Modelo Booleano (AND)**")
            ids_bool = comparador.busqueda_booleana(consulta_manual)
            if ids_bool:
                for idx in ids_bool:
                    st.markdown(f"- **#{idx}** {noticias[idx]['titulo']}")
            else:
                st.info("Sin resultados booleanos.")
        with col2:
            st.markdown("**Modelo Vectorial (TF-IDF)**")
            ids_vec = comparador.busqueda_vectorial(consulta_manual, top_k=5)
            if ids_vec:
                for idx, score in ids_vec:
                    st.markdown(f"- **#{idx}** `{score:.3f}` — {noticias[idx]['titulo']}")
            else:
                st.info("Sin resultados vectoriales.")


if __name__ == "__main__":
    main()
