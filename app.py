"""Dashboard principal de SIMANW."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from src.clasificador_noticias import (  # noqa: E402
    ETIQUETAS_ENTRENAMIENTO,
    TEXTOS_ENTRENAMIENTO,
    ClasificadorNoticias,
)
from src.pipeline_nlp import PipelineNLP  # noqa: E402
from src.sentimientos import AnalizadorSentimientos  # noqa: E402
from src.ui_streamlit import (  # noqa: E402
    COLORES_CATEGORIA,
    COLORES_SENTIMIENTO,
    aplicar_estilo_global,
    encabezado,
)


st.set_page_config(
    page_title="SIMANW | Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_estilo_global()


@st.cache_data(show_spinner="Cargando y preparando el corpus...")
def load_data(_mtime: float) -> list[dict]:
    ruta = Path("data") / "noticias_extraidas.json"
    if not ruta.exists() or ruta.stat().st_size < 10:
        return []

    with ruta.open(encoding="utf-8") as archivo:
        noticias = json.load(archivo)

    if not noticias:
        return []
    if any("nlp" not in noticia for noticia in noticias):
        PipelineNLP().procesar_noticias(noticias)
    if any("categoria_predicha" not in noticia for noticia in noticias):
        _clasificar_con_ac3_o_fallback(noticias)
    if any("sentimiento" not in noticia for noticia in noticias):
        AnalizadorSentimientos().analizar_noticias(noticias)
    return noticias


def _clasificar_con_ac3_o_fallback(noticias: list[dict]) -> None:
    modelo_path = Path("models/mejor_modelo_ac3.joblib")
    vec_path = Path("models/vectorizer_ac3.joblib")
    if modelo_path.exists() and vec_path.exists():
        try:
            from src.selector_modelo import SelectorModelo
            selector = SelectorModelo()
            selector.cargar_modelo(modelo_path, vec_path)
            textos = [_texto_noticia(n) for n in noticias]
            predicciones = selector.predecir(textos)
            for noticia, pred in zip(noticias, predicciones):
                noticia["categoria_predicha"] = pred
            return
        except Exception:
            pass
    clasificador = ClasificadorNoticias()
    clasificador.entrenar(TEXTOS_ENTRENAMIENTO, ETIQUETAS_ENTRENAMIENTO)
    clasificador.clasificar_noticias(noticias)


def _texto_noticia(n: dict) -> str:
    return " ".join(
        str(n.get(c, "") or "") for c in ("titulo", "cuerpo", "resumen")
    ).strip() or "sin contenido"


def _sentimiento(noticia: dict) -> str:
    return (noticia.get("sentimiento") or {}).get("etiqueta", "neutral")


def _categoria(noticia: dict) -> str:
    return noticia.get("categoria_predicha") or noticia.get("categoria_original") or "general"


def _df_corpus(noticias: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Titulo": noticia.get("titulo", ""),
                "Fecha": noticia.get("fecha", ""),
                "Autor": noticia.get("autor", ""),
                "Categoria": _categoria(noticia),
                "Fuente": noticia.get("fuente", ""),
                "Sentimiento": _sentimiento(noticia),
            }
            for noticia in noticias
        ]
    )


def _grafico_categorias(noticias: list[dict]) -> None:
    df_cat = pd.Series([_categoria(n) for n in noticias]).value_counts().reset_index()
    df_cat.columns = ["Categoria", "Noticias"]
    fig = px.bar(
        df_cat, x="Noticias", y="Categoria", orientation="h",
        color="Categoria", color_discrete_map=COLORES_CATEGORIA,
        template="plotly_white", text="Noticias",
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        showlegend=False, height=330,
        margin=dict(l=8, r=28, t=8, b=8),
        xaxis_title=None, yaxis_title=None,
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafico_sentimientos(noticias: list[dict]) -> None:
    df_sent = pd.Series([_sentimiento(n) for n in noticias]).value_counts().reset_index()
    df_sent.columns = ["Sentimiento", "Noticias"]
    fig = px.pie(
        df_sent, names="Sentimiento", values="Noticias",
        color="Sentimiento", color_discrete_map=COLORES_SENTIMIENTO,
        hole=0.58, template="plotly_white",
    )
    fig.update_traces(textinfo="label+percent", textposition="outside")
    fig.update_layout(
        height=330, margin=dict(l=8, r=8, t=8, b=8),
        showlegend=False, paper_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig, use_container_width=True)


def _tabla_actividades() -> None:
    actividades = [
        ("Fase 1", "Rastreador Web de Noticias", "DOM, alcance del rastreo y exportacion JSON/CSV."),
        ("Fase 2", "Procesamiento NLP", "Limpieza, tokenizacion y representacion textual."),
        ("Fase 3", "Clasificacion y Analisis", "Categorias, sentimiento y recomendacion."),
        ("Fase 4", "Busqueda Inteligente", "Busqueda booleana, vectorial y lenguaje natural."),
        ("Fase 5", "Chatbot", "Preguntas y respuestas con contexto conversacional."),
        ("Fase 6", "Knowledge Graph", "Grafo RDF, SPARQL, enlaces externos y JSON-LD."),
        ("Fase 7", "Reportes", "Resumen ejecutivo y artefactos reproducibles."),
        ("AC-8 a AC-13", "Actividades complementarias", "Calidad, tendencias, alertas, usabilidad y trazabilidad."),
    ]
    st.dataframe(
        pd.DataFrame(actividades, columns=["Modulo", "Seccion", "Cobertura"]),
        use_container_width=True, hide_index=True,
    )


# ── Tab: Smart Results ────────────────────────────────────────────────────────

def _tab_smart_results(noticias: list[dict]) -> None:
    ruta_ac3 = Path("data/resultados_ac3.json")
    if ruta_ac3.exists():
        datos_ac3 = json.loads(ruta_ac3.read_text(encoding="utf-8"))
        mejor = datos_ac3.get("mejor_modelo", "—")
        resultados_modelos = datos_ac3.get("resultados", {})
        acc = resultados_modelos.get(mejor, {}).get("accuracy_mean")
        std = resultados_modelos.get(mejor, {}).get("accuracy_std")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Modelo AC-3 activo", mejor)
        c2.metric("Accuracy CV", f"{acc:.3f}" if acc is not None else "—")
        c3.metric("Desv. estándar", f"{std:.3f}" if std is not None else "—")
        c4.metric("Corpus entrenamiento", datos_ac3.get("total_textos", 0))

        if resultados_modelos:
            st.subheader("Comparación de modelos")
            filas = [
                {
                    "Modelo": nombre,
                    "Accuracy (media)": round(m.get("accuracy_mean", 0), 4),
                    "Std Dev": round(m.get("accuracy_std", 0), 4),
                    "Mejor": "✅" if nombre == mejor else "",
                }
                for nombre, m in resultados_modelos.items()
                if "accuracy_mean" in m
            ]
            if filas:
                df_mod = pd.DataFrame(filas).sort_values("Accuracy (media)", ascending=False)
                col_tabla, col_grafico = st.columns([1, 1])
                with col_tabla:
                    st.dataframe(df_mod, use_container_width=True, hide_index=True)
                with col_grafico:
                    fig = px.bar(
                        df_mod, x="Accuracy (media)", y="Modelo", orientation="h",
                        error_x="Std Dev", color_discrete_sequence=["#4F46E5"],
                        template="plotly_white",
                    )
                    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin evidencia AC-3 aún. Ejecuta el análisis completo para generar `data/resultados_ac3.json`.")

    if not noticias:
        return

    st.subheader("Recomendaciones por noticia")
    st.caption("Noticias similares calculadas por similitud de contenido TF-IDF.")
    try:
        from src.recomendacion import SistemaRecomendacion
        recomendador = SistemaRecomendacion(noticias)

        opciones = {
            f"{i + 1}. {n.get('titulo', 'Sin título')[:70]}": i
            for i, n in enumerate(noticias[:30])
        }
        sel = st.selectbox("Selecciona una noticia", list(opciones.keys()), key="sel_smart")
        idx = opciones[sel]
        recomendaciones = recomendador.recomendar_detallado(idx, top_n=5)

        if recomendaciones:
            df_rec = pd.DataFrame(recomendaciones)
            df_rec["similitud"] = df_rec["similitud"].map(lambda x: f"{x:.4f}")
            st.dataframe(
                df_rec[["titulo", "categoria", "similitud"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("Sin noticias similares para esta selección.")
    except Exception as exc:
        st.warning(f"Recomendaciones no disponibles: {exc}")

    st.subheader("Distribución de categorías predichas")
    df_cat = pd.Series([_categoria(n) for n in noticias]).value_counts().reset_index()
    df_cat.columns = ["Categoria", "Noticias"]
    fig = px.pie(
        df_cat, names="Categoria", values="Noticias",
        color="Categoria", color_discrete_map=COLORES_CATEGORIA,
        hole=0.45, template="plotly_white",
    )
    fig.update_layout(height=320, margin=dict(l=8, r=8, t=8, b=8), paper_bgcolor="#FFFFFF")
    st.plotly_chart(fig, use_container_width=True)


# ── Tab: Evidencia Académica AC-3 ─────────────────────────────────────────────

def _tab_evidencia_ac3() -> None:
    ruta = Path("data/resultados_ac3.json")
    if not ruta.exists():
        st.info(
            "Sin evidencia AC-3 registrada. "
            "Ejecuta el análisis completo desde la app de escritorio o `python main_ac3.py`."
        )
        return

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    mejor = datos.get("mejor_modelo", "")
    resultados = datos.get("resultados", {})
    acc = resultados.get(mejor, {}).get("accuracy_mean")
    std = resultados.get(mejor, {}).get("accuracy_std")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Actividad", datos.get("actividad", "AC-3"))
    c2.metric("Mejor modelo", mejor or "—")
    c3.metric("Accuracy CV", f"{acc:.3f}" if acc is not None else "—")
    c4.metric("Std Dev", f"{std:.3f}" if std is not None else "—")

    st.caption(
        f"Generado: {datos.get('fecha_generacion', '—')}  |  "
        f"Corpus: {datos.get('total_textos', 0)} textos  |  "
        f"Clases: {', '.join(datos.get('clases', []))}"
    )

    if resultados:
        st.subheader("Métricas por modelo")
        filas = [
            {
                "Modelo": nombre,
                "Accuracy (media)": round(m.get("accuracy_mean", 0), 4),
                "Std Dev": round(m.get("accuracy_std", 0), 4),
                "Folds": len(m.get("scores", [])),
                "Mejor": "✅" if nombre == mejor else "",
            }
            for nombre, m in resultados.items()
            if "accuracy_mean" in m
        ]
        if filas:
            df = pd.DataFrame(filas).sort_values("Accuracy (media)", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)

    predicciones = datos.get("predicciones_prueba", [])
    if predicciones:
        st.subheader(f"Predicciones registradas ({len(predicciones)})")
        df_pred = pd.DataFrame(predicciones)
        st.dataframe(df_pred, use_container_width=True, hide_index=True, height=220)

    modelo_path = Path("models/mejor_modelo_ac3.joblib")
    st.subheader("Artefactos")
    artefactos = [
        ("data/resultados_ac3.json", ruta.exists()),
        ("models/mejor_modelo_ac3.joblib", modelo_path.exists()),
        ("models/vectorizer_ac3.joblib", Path("models/vectorizer_ac3.joblib").exists()),
    ]
    for nombre_arc, existe in artefactos:
        icono = "✅" if existe else "❌"
        st.markdown(f"{icono} `{nombre_arc}`")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    encabezado(
        "Sistema Inteligente de Monitoreo y Analisis de Noticias Web",
        "SIMANW Dashboard",
        "Panel visual para revisar el corpus, validar resultados del pipeline y navegar por las fases del proyecto.",
    )

    _ruta_corpus = Path("data") / "noticias_extraidas.json"
    _mtime = _ruta_corpus.stat().st_mtime if _ruta_corpus.exists() else 0.0
    noticias = load_data(_mtime)

    # Poner noticias en sesión para que AC-2 y otras páginas las usen
    if noticias and "noticias" not in st.session_state:
        st.session_state["noticias"] = noticias

    if not noticias:
        st.markdown(
            """
<div class="simanw-callout">
No hay corpus disponible. Ejecuta <strong>python main.py</strong> para generar
<strong>data/noticias_extraidas.json</strong> y vuelve a abrir el dashboard.
</div>
""",
            unsafe_allow_html=True,
        )
        return

    etiquetas = [_sentimiento(noticia) for noticia in noticias]
    categorias = [_categoria(noticia) for noticia in noticias]

    tab_dashboard, tab_smart, tab_evidencia = st.tabs(
        ["Dashboard", "Smart Results", "Evidencia AC-3"]
    )

    with tab_dashboard:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Noticias", len(noticias))
        c2.metric("Categorias", len(set(categorias)))
        c3.metric("Autores", len({n.get("autor", "desconocido") for n in noticias}))
        c4.metric("Sentimiento dominante", max(set(etiquetas), key=etiquetas.count).capitalize())

        st.markdown("### Resumen del corpus")
        col1, col2 = st.columns([1.15, 0.85])
        with col1:
            st.markdown('<div class="simanw-panel">', unsafe_allow_html=True)
            st.subheader("Noticias por categoria")
            _grafico_categorias(noticias)
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="simanw-panel">', unsafe_allow_html=True)
            st.subheader("Distribucion de sentimientos")
            _grafico_sentimientos(noticias)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Corpus completo")
        st.dataframe(_df_corpus(noticias), use_container_width=True, hide_index=True, height=360)

        st.markdown("### Cobertura del proyecto")
        _tabla_actividades()
        st.caption("Las actividades academicas se reportan como evidencia; el flujo principal se organiza por modulos del sistema.")

    with tab_smart:
        _tab_smart_results(noticias)

    with tab_evidencia:
        _tab_evidencia_ac3()


if __name__ == "__main__":
    main()
