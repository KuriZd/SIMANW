"""AC-2: Análisis Estadístico de Discursos — integrado con el corpus del sistema."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analisis_discurso import AnalisisDiscurso, generar_nube_palabras  # noqa: E402
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

TEXTO_DISCURSO = (
    "La educacion es la herramienta mas poderosa para transformar una sociedad. En Mexico, la "
    "inversion en educacion debe ser prioritaria para garantizar el desarrollo economico y social. "
    "Los jovenes mexicanos merecen oportunidades de calidad en todos los niveles educativos. Las "
    "universidades tecnologicas y los institutos de investigacion son pilares fundamentales para "
    "la innovacion. La ciencia y la tecnologia son motores del progreso nacional. El Instituto "
    "Tecnologico de Morelia ha formado generaciones de ingenieros que contribuyen al desarrollo "
    "del pais. La inteligencia artificial y la programacion son competencias esenciales para el "
    "futuro laboral. Mexico necesita mas profesionales en ciencias computacionales y recuperacion "
    "de informacion."
)

TEXTO_CIENTIFICO = (
    "El procesamiento de lenguaje natural permite a las computadoras comprender y generar texto "
    "humano. Los modelos de aprendizaje profundo como BERT y GPT han revolucionado este campo. "
    "La representacion vectorial de documentos mediante TF-IDF sigue siendo fundamental para "
    "sistemas de recuperacion de informacion. Los algoritmos de clasificacion como Naive Bayes y "
    "SVM logran alta precision en categorizacion de texto. El analisis de sentimientos combina "
    "tecnicas lexicas con aprendizaje automatico para determinar la polaridad emocional de un texto."
)

st.set_page_config(
    page_title="SIMANW | AC-2: Análisis de Discursos",
    page_icon="📊",
    layout="wide",
)
aplicar_estilo_global()


@st.cache_resource
def get_analizador() -> AnalisisDiscurso:
    return AnalisisDiscurso()


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
    """Retorna noticias desde sesión o desde archivo."""
    sesion = st.session_state.get("noticias", [])
    if sesion:
        return sesion
    return _cargar_noticias_archivo()


def _texto_noticia(n: dict) -> str:
    return (
        n.get("cuerpo") or n.get("texto_original") or
        n.get("resumen") or n.get("titulo", "")
    ).strip()


# ── Visualización de un análisis individual ───────────────────────────────────

def mostrar_analisis(analisis: dict) -> None:
    if analisis.get("estado") == "insuficiente":
        st.warning(f"Texto insuficiente: {analisis.get('motivo', 'muy corto')}")
        return

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Oraciones", analisis.get("oraciones", 0))
    m2.metric("Palabras", analisis.get("palabras_totales", 0))
    m3.metric("Vocabulario único", analisis.get("vocabulario_unico", 0))
    m4.metric("Riqueza léxica", f"{analisis.get('riqueza_lexica_global', 0):.3f}")
    m5.metric("Prom. palabras/oración", f"{analisis.get('promedio_palabras_oracion', 0):.1f}")

    col1, col2, col3 = st.columns(3)

    with col1:
        bigramas = analisis.get("top_bigramas", [])
        if bigramas:
            st.subheader("Top bigramas")
            df_b = pd.DataFrame(
                [(" ".join(b[0]) if isinstance(b[0], (list, tuple)) else str(b[0]), b[1])
                 for b in bigramas[:8]],
                columns=["Bigrama", "Frecuencia"],
            )
            fig = px.bar(df_b, x="Frecuencia", y="Bigrama", orientation="h",
                         color_discrete_sequence=["#4F46E5"], template="plotly_white")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        trigramas = analisis.get("top_trigramas", [])
        if trigramas:
            st.subheader("Top trigramas")
            df_t = pd.DataFrame(
                [(" ".join(t[0]) if isinstance(t[0], (list, tuple)) else str(t[0]), t[1])
                 for t in trigramas[:5]],
                columns=["Trigrama", "Frecuencia"],
            )
            fig = px.bar(df_t, x="Frecuencia", y="Trigrama", orientation="h",
                         color_discrete_sequence=["#06B6D4"], template="plotly_white")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col3:
        entidades = analisis.get("posibles_entidades", [])
        if entidades:
            st.subheader("Entidades detectadas")
            rows = []
            for e in entidades[:10]:
                if len(e) == 3:
                    rows.append({"Entidad": e[0], "Tipo": e[1], "Frecuencia": e[2]})
                else:
                    rows.append({"Entidad": e[0], "Tipo": "DESCONOCIDO", "Frecuencia": e[1]})
            df_e = pd.DataFrame(rows)
            fig = px.bar(
                df_e, x="Frecuencia", y="Entidad", orientation="h", color="Tipo",
                color_discrete_map={"PERSONA": "#4F46E5", "LUGAR": "#059669",
                                    "ORG": "#D97706", "DESCONOCIDO": "#94A3B8"},
                template="plotly_white",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    riqueza_sec = analisis.get("riqueza_por_seccion", [])
    if riqueza_sec:
        st.subheader("Riqueza léxica por sección")
        df_r = pd.DataFrame({"Sección": range(1, len(riqueza_sec) + 1), "Riqueza": riqueza_sec})
        fig = px.line(df_r, x="Sección", y="Riqueza", markers=True,
                      color_discrete_sequence=["#7C3AED"], template="plotly_white")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_range=[0, 1])
        st.plotly_chart(fig, use_container_width=True)


def _analizar_y_mostrar(key: str, texto_default: str, titulo: str, btn_label: str) -> dict | None:
    texto = st.text_area("Texto a analizar", texto_default, height=160, key=f"ta_{key}")
    if st.button(btn_label, key=f"btn_{key}"):
        if not texto.strip():
            st.warning("El texto está vacío.")
            return None
        with st.spinner("Analizando…"):
            resultado = get_analizador().analizar(texto, titulo)
        st.session_state[f"analisis_{key}"] = resultado
    if f"analisis_{key}" in st.session_state:
        mostrar_analisis(st.session_state[f"analisis_{key}"])
        return st.session_state[f"analisis_{key}"]
    return None


# ── Tab Corpus ────────────────────────────────────────────────────────────────

def _tab_corpus(noticias: list[dict]) -> None:
    analizador = get_analizador()

    if not noticias:
        st.info(
            "No hay corpus disponible. Ejecuta `python main.py` para generar "
            "`data/noticias_extraidas.json` o carga noticias desde el Dashboard."
        )
        return

    st.caption(f"{len(noticias)} noticias disponibles — fuente: `data/noticias_extraidas.json`")

    sub_individual, sub_corpus = st.tabs(["Noticia individual", "Análisis del corpus completo"])

    # ── Sub-tab: noticia individual ───────────────────────────────────────────
    with sub_individual:
        opciones = {
            f"{i + 1}. {n.get('titulo', 'Sin título')[:70]}": i
            for i, n in enumerate(noticias[:50])
        }
        sel_key = st.selectbox("Selecciona una noticia", list(opciones.keys()), key="sel_corpus")
        if st.button("Analizar noticia", key="btn_corpus"):
            noticia = noticias[opciones[sel_key]]
            texto = _texto_noticia(noticia)
            if not texto:
                st.warning("La noticia no tiene contenido de texto.")
            else:
                with st.spinner("Analizando…"):
                    resultado = analizador.analizar(texto, noticia.get("titulo", "Noticia"))
                st.session_state["analisis_corpus"] = resultado
                st.session_state["analisis_corpus_titulo"] = noticia.get("titulo", "Noticia")

        if "analisis_corpus" in st.session_state:
            st.markdown(f"**{st.session_state.get('analisis_corpus_titulo', '')}**")
            mostrar_analisis(st.session_state["analisis_corpus"])

            tokens = st.session_state["analisis_corpus"].get("_tokens_filtrados", [])
            if tokens:
                ruta_nube = Path("data/wordcloud_ac2.png")
                if st.button("Generar nube de palabras", key="btn_nube"):
                    ok = generar_nube_palabras(tokens, ruta_nube)
                    if ok:
                        st.image(str(ruta_nube), caption="Nube de palabras")
                    else:
                        st.warning("Instala `wordcloud`: `pip install wordcloud`")

    # ── Sub-tab: corpus completo ──────────────────────────────────────────────
    with sub_corpus:
        _max_corpus = min(50, len(noticias))
        _min_corpus = min(5, _max_corpus)
        if _min_corpus < _max_corpus:
            limite = st.slider("Noticias a analizar", min_value=_min_corpus, max_value=_max_corpus,
                               value=min(20, _max_corpus), step=1, key="slider_corpus")
        else:
            limite = _max_corpus
            st.caption(f"Analizando {limite} noticia(s) disponible(s).")

        if st.button("Analizar corpus completo", key="btn_corpus_total", type="primary"):
            resultados = []
            progreso = st.progress(0, text="Analizando noticias…")
            for i, noticia in enumerate(noticias[:limite]):
                texto = _texto_noticia(noticia)
                if texto:
                    res = analizador.analizar(texto, noticia.get("titulo", f"Noticia {i + 1}"))
                    if res.get("estado") != "insuficiente":
                        res["_titulo"] = noticia.get("titulo", f"Noticia {i + 1}")
                        res["_categoria"] = noticia.get("categoria_predicha") or noticia.get("categoria", "")
                        resultados.append(res)
                progreso.progress((i + 1) / limite, text=f"Analizando {i + 1}/{limite}…")
            progreso.empty()
            st.session_state["analisis_corpus_completo"] = resultados

        if "analisis_corpus_completo" in st.session_state:
            resultados = st.session_state["analisis_corpus_completo"]
            if not resultados:
                st.warning("No se obtuvieron resultados válidos.")
            else:
                st.success(f"{len(resultados)} noticias analizadas correctamente.")

                # Tabla resumen
                filas = [
                    {
                        "Título": r["_titulo"][:60],
                        "Categoría": r.get("_categoria", "—"),
                        "Oraciones": r.get("oraciones", 0),
                        "Palabras": r.get("palabras_totales", 0),
                        "Vocabulario único": r.get("vocabulario_unico", 0),
                        "Riqueza léxica": round(r.get("riqueza_lexica_global", 0), 3),
                    }
                    for r in resultados
                ]
                df_resumen = pd.DataFrame(filas)
                st.subheader("Resumen del corpus")
                st.dataframe(df_resumen, use_container_width=True, hide_index=True)

                # Estadísticas agregadas
                c1, c2, c3 = st.columns(3)
                riquezas = [r.get("riqueza_lexica_global", 0) for r in resultados]
                c1.metric("Riqueza léxica promedio", f"{sum(riquezas) / len(riquezas):.3f}")
                c2.metric("Promedio de palabras", f"{sum(r.get('palabras_totales', 0) for r in resultados) / len(resultados):.0f}")
                c3.metric("Promedio de oraciones", f"{sum(r.get('oraciones', 0) for r in resultados) / len(resultados):.1f}")

                # Riqueza léxica del corpus
                st.subheader("Riqueza léxica por noticia")
                df_riq = pd.DataFrame({
                    "Noticia": [r["_titulo"][:40] for r in resultados],
                    "Riqueza": riquezas,
                })
                fig = px.bar(df_riq, x="Riqueza", y="Noticia", orientation="h",
                             color_discrete_sequence=["#7C3AED"], template="plotly_white")
                fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=max(300, len(resultados) * 28))
                st.plotly_chart(fig, use_container_width=True)

                # Guardar evidencia con datos reales
                if st.button("Guardar evidencia AC-2 (corpus real)", key="btn_guardar_corpus"):
                    comparativa = analizador.comparar_textos(resultados)
                    ruta = Path("data/analisis_ac2.json")
                    AnalisisDiscurso.guardar_json(ruta, resultados, comparativa)
                    st.success(f"Evidencia guardada en `{ruta}` con {len(resultados)} noticias reales.")


# ── Tab Comparativa ───────────────────────────────────────────────────────────

def _tab_comparativa(noticias: list[dict]) -> None:
    analizador = get_analizador()

    fuentes_disponibles = ["Discurso educativo", "Texto científico"]
    if "analisis_libre" in st.session_state:
        fuentes_disponibles.append("Texto libre")
    if "analisis_corpus" in st.session_state:
        fuentes_disponibles.append("Noticia del corpus")

    # Agregar noticias del corpus como opciones individuales (hasta 5)
    noticias_comp: dict[str, dict] = {}
    for i, n in enumerate(noticias[:5]):
        label = f"Noticia {i + 1}: {n.get('titulo', '')[:40]}"
        fuentes_disponibles.append(label)
        noticias_comp[label] = n

    seleccion = st.multiselect("Textos a comparar", fuentes_disponibles,
                               default=fuentes_disponibles[:2])

    if st.button("Generar comparativa", key="btn_comp"):
        mapa_fijo = {
            "Discurso educativo": lambda: analizador.analizar(TEXTO_DISCURSO, "Discurso Educativo"),
            "Texto científico": lambda: analizador.analizar(TEXTO_CIENTIFICO, "Texto Científico"),
            "Texto libre": lambda: st.session_state.get("analisis_libre"),
            "Noticia del corpus": lambda: st.session_state.get("analisis_corpus"),
        }

        with st.spinner("Comparando…"):
            lista = []
            for s in seleccion:
                if s in mapa_fijo:
                    res = mapa_fijo[s]()
                elif s in noticias_comp:
                    texto = _texto_noticia(noticias_comp[s])
                    res = analizador.analizar(texto, noticias_comp[s].get("titulo", s)) if texto else None
                else:
                    res = None
                if res and res.get("estado") != "insuficiente":
                    lista.append(res)
            comparativa = analizador.comparar_textos(lista)
        st.session_state["comparativa"] = comparativa

    if "comparativa" in st.session_state and st.session_state["comparativa"]:
        df_comp = pd.DataFrame(st.session_state["comparativa"])
        st.dataframe(df_comp, use_container_width=True, hide_index=True)
        fig = px.bar(df_comp, x="titulo", y=["palabras", "vocabulario"],
                     barmode="group", template="plotly_white",
                     color_discrete_sequence=["#4F46E5", "#7C3AED"])
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

        if st.button("Guardar evidencia AC-2", key="btn_guardar"):
            mapa2 = {
                "Discurso educativo": analizador.analizar(TEXTO_DISCURSO, "Discurso Educativo"),
                "Texto científico": analizador.analizar(TEXTO_CIENTIFICO, "Texto Científico"),
            }
            analisis_guardados = [v for v in mapa2.values() if v.get("estado") != "insuficiente"]
            ruta = Path("data/analisis_ac2.json")
            AnalisisDiscurso.guardar_json(ruta, analisis_guardados, st.session_state["comparativa"])
            st.success(f"Evidencia guardada en `{ruta}`")
    else:
        st.info("Selecciona al menos dos textos y haz clic en **Generar comparativa**.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    encabezado(
        "AC-2 | Análisis de Discursos",
        "Análisis Estadístico de Discursos",
        "Análisis léxico completo: unigramas, bigramas, trigramas, entidades y riqueza léxica.",
    )

    analizador = get_analizador()
    noticias = _noticias_disponibles()

    corpus_label = f"Corpus ({len(noticias)} noticias)" if noticias else "Corpus (sin datos)"
    tabs = st.tabs(["Discurso educativo", "Texto científico", "Texto libre", corpus_label, "Comparativa"])

    with tabs[0]:
        _analizar_y_mostrar("disc", TEXTO_DISCURSO, "Discurso Educativo", "Analizar discurso")

    with tabs[1]:
        _analizar_y_mostrar("cient", TEXTO_CIENTIFICO, "Texto Científico NLP", "Analizar texto")

    with tabs[2]:
        texto_libre = st.text_area("Pega tu texto aquí", "", height=200, key="ta_libre",
                                   placeholder="Pega cualquier texto en español…")
        if st.button("Analizar", key="btn_libre"):
            if not texto_libre.strip():
                st.warning("El texto está vacío.")
            else:
                with st.spinner("Analizando…"):
                    resultado = analizador.analizar(texto_libre, "Texto libre")
                st.session_state["analisis_libre"] = resultado
        if "analisis_libre" in st.session_state:
            mostrar_analisis(st.session_state["analisis_libre"])

    with tabs[3]:
        _tab_corpus(noticias)

    with tabs[4]:
        _tab_comparativa(noticias)


if __name__ == "__main__":
    main()
