"""AC-3: Selección Automática de Modelo de Clasificación."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.selector_modelo import ETIQUETAS_AC3, TEXTOS_AC3, SelectorModelo  # noqa: E402
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

st.set_page_config(page_title="SIMANW | AC-3: Selección de Modelo", page_icon="🤖", layout="wide")
aplicar_estilo_global()

COLORES_CAT = {"tecnologia": "#4F46E5", "economia": "#7C3AED", "ciencia": "#06B6D4", "politica": "#F59E0B"}
_MIN_TEXTOS_CONFIABLES = 20


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


def _dataset_desde_noticias(noticias: list[dict]) -> tuple[list[str], list[str]]:
    textos, etiquetas = [], []
    for n in noticias:
        texto = " ".join(
            str(n.get(c, "") or "") for c in ("titulo", "cuerpo", "texto_original", "resumen")
        ).strip()
        etiqueta = str(
            n.get("categoria_predicha") or n.get("categoria_original") or n.get("categoria") or ""
        ).strip()
        if texto and etiqueta and etiqueta != "sin_categoria":
            textos.append(texto)
            etiquetas.append(etiqueta)
    return textos, etiquetas


def _grafico_distribucion(etiquetas: list[str], titulo: str) -> None:
    dist = pd.Series(etiquetas).value_counts().reset_index()
    dist.columns = ["Categoría", "Documentos"]
    fig = px.bar(dist, x="Documentos", y="Categoría", orientation="h",
                 color="Categoría", color_discrete_map=COLORES_CAT, template="plotly_white")
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0), title_text=titulo)
    st.plotly_chart(fig, use_container_width=True)


def _mostrar_resultados_evaluacion(resultados: dict, mejor: str | None) -> None:
    filas = [
        {
            "Modelo": nombre,
            "Accuracy CV (media)": round(m.get("accuracy_mean", 0), 4),
            "Accuracy CV (std)": round(m.get("accuracy_std", 0), 4),
            "¿Mejor?": "✅" if nombre == mejor else "",
        }
        for nombre, m in resultados.items()
        if "accuracy_mean" in m
    ]
    errores = {n: m["error"] for n, m in resultados.items() if "error" in m}
    if errores:
        for nombre, err in errores.items():
            st.warning(f"{nombre}: {err}")

    if filas:
        df_res = pd.DataFrame(filas).sort_values("Accuracy CV (media)", ascending=False)
        col_t, col_g = st.columns([1, 1])
        with col_t:
            st.dataframe(df_res, use_container_width=True, hide_index=True)
        with col_g:
            fig = px.bar(df_res, x="Accuracy CV (media)", y="Modelo", orientation="h",
                         error_x="Accuracy CV (std)",
                         color_discrete_sequence=["#4F46E5"], template="plotly_white")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    if mejor:
        acc = resultados.get(mejor, {}).get("accuracy_mean")
        st.metric("Modelo seleccionado automáticamente", mejor,
                  delta=f"accuracy {acc:.3f}" if acc is not None else None)


# ── Tabs ──────────────────────────────────────────────────────────────────────

def _tab_datos(noticias: list[dict]) -> None:
    sub_demo, sub_corpus = st.tabs(["Datos de demostración (AC-3)", "Corpus real"])

    with sub_demo:
        st.caption(f"{len(TEXTOS_AC3)} documentos de referencia — balanceados, 4 categorías.")
        df_train = pd.DataFrame({
            "Texto": [t[:80] + "…" if len(t) > 80 else t for t in TEXTOS_AC3],
            "Etiqueta": ETIQUETAS_AC3,
        })
        st.dataframe(df_train, use_container_width=True, hide_index=True)
        _grafico_distribucion(ETIQUETAS_AC3, "Distribución demo")

    with sub_corpus:
        if not noticias:
            st.info(
                "No hay corpus disponible. Ejecuta `python main.py` para generar "
                "`data/noticias_extraidas.json` o carga noticias desde el Dashboard."
            )
            return

        textos, etiquetas = _dataset_desde_noticias(noticias)
        st.caption(
            f"{len(noticias)} noticias totales — "
            f"{len(textos)} con etiqueta válida para entrenamiento."
        )

        if etiquetas:
            conteo = Counter(etiquetas)
            filas = [{"Categoría": cat, "Documentos": n} for cat, n in sorted(conteo.items())]
            col_t, col_g = st.columns([1, 1])
            with col_t:
                st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
            with col_g:
                _grafico_distribucion(etiquetas, "Distribución corpus real")

            if len(textos) < _MIN_TEXTOS_CONFIABLES:
                st.warning(
                    f"Solo {len(textos)} textos etiquetados — se recomiendan al menos "
                    f"{_MIN_TEXTOS_CONFIABLES} para que las métricas sean representativas."
                )
        else:
            st.warning(
                "Las noticias no tienen categoría asignada. "
                "Ejecuta el análisis completo desde el Dashboard para que AC-3 las etiquete."
            )


def _tab_evaluacion(noticias: list[dict]) -> None:
    sub_demo, sub_corpus = st.tabs(["Evaluación con demo", "Evaluación con corpus real"])

    with sub_demo:
        st.caption("Entrena y evalúa con los 16 documentos de referencia del AC-3.")
        if st.button("Evaluar modelos (demo)", key="btn_eval_demo"):
            selector = SelectorModelo()
            with st.spinner("Entrenando y evaluando modelos…"):
                resultados = selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)
            mejor = selector.mejor_modelo[0] if selector.mejor_modelo else None
            st.session_state["eval_demo_resultados"] = resultados
            st.session_state["eval_demo_mejor"] = mejor

        if "eval_demo_resultados" in st.session_state:
            _mostrar_resultados_evaluacion(
                st.session_state["eval_demo_resultados"],
                st.session_state.get("eval_demo_mejor"),
            )

    with sub_corpus:
        if not noticias:
            st.info("Sin corpus disponible.")
            return

        textos, etiquetas = _dataset_desde_noticias(noticias)
        if not textos:
            st.warning("Sin textos etiquetados. Ejecuta el análisis desde el Dashboard primero.")
            return

        conteo = Counter(etiquetas)
        n_clases = len(conteo)
        min_clase = min(conteo.values())
        cv_max = min(5, min_clase)

        st.caption(
            f"{len(textos)} textos — {n_clases} categorías — "
            f"clase más pequeña: {min_clase} docs — máx. folds posibles: {cv_max}"
        )

        if len(textos) < _MIN_TEXTOS_CONFIABLES:
            st.warning(
                f"Corpus pequeño ({len(textos)} textos). "
                "Las métricas no son estadísticamente representativas."
            )

        if n_clases < 2:
            st.error("Se necesitan al menos 2 categorías para evaluar modelos.")
            return
        if min_clase < 2:
            st.error(f"La categoría más pequeña tiene solo {min_clase} ejemplo. Se necesitan ≥2 por clase.")
            return

        cv_folds = st.slider("Folds de validación cruzada", 2, cv_max, min(3, cv_max), key="sl_cv")

        if st.button("Evaluar modelos con corpus real", key="btn_eval_corpus", type="primary"):
            selector = SelectorModelo()
            with st.spinner(f"Entrenando con {len(textos)} textos reales…"):
                try:
                    resultados = selector.evaluar_todos(textos, etiquetas, cv_folds=cv_folds)
                    mejor = selector.mejor_modelo[0] if selector.mejor_modelo else None
                    selector.guardar_resultados(
                        "data/resultados_ac3.json",
                        textos=textos,
                        predicciones_prueba=[],
                    )
                    selector.guardar_modelo(
                        "models/mejor_modelo_ac3.joblib",
                        "models/vectorizer_ac3.joblib",
                    )
                    st.session_state["eval_corpus_resultados"] = resultados
                    st.session_state["eval_corpus_mejor"] = mejor
                    st.session_state["eval_corpus_selector"] = selector
                    st.success(
                        f"Modelo **{mejor}** seleccionado y guardado en `models/mejor_modelo_ac3.joblib`."
                    )
                except ValueError as exc:
                    st.error(str(exc))

        if "eval_corpus_resultados" in st.session_state:
            _mostrar_resultados_evaluacion(
                st.session_state["eval_corpus_resultados"],
                st.session_state.get("eval_corpus_mejor"),
            )


def _tab_prediccion(noticias: list[dict]) -> None:
    sub_libre, sub_corpus = st.tabs(["Texto libre", "Noticias del corpus"])

    # Determina qué selector usar: preferir el entrenado con corpus real
    def _get_selector() -> SelectorModelo | None:
        if "eval_corpus_selector" in st.session_state:
            return st.session_state["eval_corpus_selector"]
        modelo_path = Path("models/mejor_modelo_ac3.joblib")
        vec_path = Path("models/vectorizer_ac3.joblib")
        if modelo_path.exists() and vec_path.exists():
            try:
                sel = SelectorModelo()
                sel.cargar_modelo(modelo_path, vec_path)
                return sel
            except Exception:
                pass
        return None

    with sub_libre:
        nuevos_default = (
            "nueva aplicacion de machine learning para detectar fraudes\n"
            "el presidente anuncio reformas al sistema de justicia\n"
            "inflacion y tasas de interes presionan al mercado de valores"
        )
        textos_input = st.text_area("Un texto por línea", nuevos_default, height=120, key="ta_pred_libre")

        origen = "corpus real" if "eval_corpus_selector" in st.session_state or \
            Path("models/mejor_modelo_ac3.joblib").exists() else "demo"
        st.caption(f"Usando modelo entrenado con: **{origen}**")

        if st.button("Clasificar", type="primary", key="btn_pred_libre"):
            textos = [t.strip() for t in textos_input.splitlines() if t.strip()]
            if not textos:
                st.warning("Escribe al menos un texto.")
            else:
                selector = _get_selector()
                if selector is None:
                    # Fallback al demo
                    selector = SelectorModelo()
                    selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)
                predicciones = selector.predecir(textos)
                df_pred = pd.DataFrame({
                    "Texto": [t[:70] + "…" if len(t) > 70 else t for t in textos],
                    "Categoría predicha": predicciones,
                })
                st.dataframe(df_pred, use_container_width=True, hide_index=True)

    with sub_corpus:
        if not noticias:
            st.info("Sin corpus disponible.")
            return

        _max_pred = min(50, len(noticias))
        _min_pred = min(5, _max_pred)
        if _min_pred < _max_pred:
            limite = st.slider("Noticias a clasificar", _min_pred, _max_pred,
                               min(20, _max_pred), step=1, key="sl_pred_corpus")
        else:
            limite = _max_pred
            st.caption(f"Clasificando {limite} noticia(s) disponible(s).")

        if st.button("Clasificar noticias del corpus", key="btn_pred_corpus", type="primary"):
            selector = _get_selector()
            if selector is None:
                selector = SelectorModelo()
                selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)
                st.caption("Modelo de demo utilizado — evalúa con corpus real para mejores resultados.")

            muestra = noticias[:limite]
            textos = [
                " ".join(str(n.get(c, "") or "") for c in ("titulo", "cuerpo", "texto_original", "resumen")).strip()
                for n in muestra
            ]
            textos = [t or "sin contenido" for t in textos]

            with st.spinner(f"Clasificando {limite} noticias…"):
                predicciones = selector.predecir(textos)

            filas = [
                {
                    "Título": n.get("titulo", "")[:60],
                    "Categoría original": n.get("categoria_predicha") or n.get("categoria", "—"),
                    "Categoría predicha (AC-3)": pred,
                    "Coincide": "✅" if pred == (n.get("categoria_predicha") or n.get("categoria", "")) else "❌",
                }
                for n, pred in zip(muestra, predicciones)
            ]
            df = pd.DataFrame(filas)
            st.dataframe(df, use_container_width=True, hide_index=True)

            coincidencias = sum(1 for f in filas if f["Coincide"] == "✅")
            st.metric("Coincidencia con etiqueta original", f"{coincidencias}/{len(filas)}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    encabezado(
        "AC-3 | Selección de Modelo",
        "Selección Automática de Modelo de Clasificación",
        "Compara Naive Bayes, SVM Lineal, Regresión Logística y Random Forest con validación cruzada sobre datos reales.",
    )

    noticias = _noticias_disponibles()

    tab1, tab2, tab3 = st.tabs(["Datos de entrenamiento", "Evaluación de modelos", "Predicción"])

    with tab1:
        _tab_datos(noticias)

    with tab2:
        _tab_evaluacion(noticias)

    with tab3:
        _tab_prediccion(noticias)


if __name__ == "__main__":
    main()
