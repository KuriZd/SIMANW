"""Fase 1 / AC-1: Rastreo Web con Paginacion."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rastreador_paginado import RastreadorPaginado, crear_fetcher_simulado  # noqa: E402
from src.rastreador_rss import FEEDS_DEMO, RastreadorRSS  # noqa: E402
from src.ui_streamlit import aplicar_estilo_global, encabezado, paso  # noqa: E402


st.set_page_config(page_title="SIMANW | Fase 1", page_icon="F1", layout="wide")
aplicar_estilo_global()


def _crear_rastreador(
    url_base: str,
    noticias_por_pagina: int,
    total_paginas: int,
) -> RastreadorPaginado:
    return RastreadorPaginado(
        url_base=url_base,
        selector_articulos="article",
        selector_siguiente="a.next-page",
        delay=0,
        max_paginas=total_paginas,
        fetcher=crear_fetcher_simulado(
            noticias_por_pagina=noticias_por_pagina,
            total_paginas=total_paginas,
        ),
        respetar_robots=False,
    )


def _tabla_resultados(resultados: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(resultados)
    columnas = [col for col in ["titulo", "fecha", "autor", "categoria_original", "url"] if col in df.columns]
    return df[columnas] if columnas else df


def _guardar_corpus(noticias: list[dict]) -> None:
    """Escribe noticias en data/noticias_extraidas.json y las pone en session_state."""
    ruta = Path("data/noticias_extraidas.json")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(noticias, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    st.session_state["noticias"] = noticias
    st.success(
        f"{len(noticias)} noticias guardadas en `{ruta}`. "
        "Ya están disponibles en F2, F3 y el Dashboard."
    )


def main() -> None:
    encabezado(
        "Fase 1 | Rastreador Web de Noticias",
        "Extraccion automatica desde paginas web",
        "Configura un rastreo simulado, revisa las paginas visitadas y exporta las noticias extraidas para el resto del pipeline.",
    )

    with st.container():
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            paso(1, "Leer HTML", "El rastreador obtiene el documento y analiza etiquetas article.")
        with col_b:
            paso(2, "Seguir alcance", "Solo visita paginas permitidas por la paginacion configurada.")
        with col_c:
            paso(3, "Guardar datos", "Entrega registros estructurados para JSON, CSV y fases posteriores.")

    tab_simulado, tab_real = st.tabs(["Rastreo simulado", "Noticias reales por RSS"])

    with tab_simulado:
        _vista_rastreo_simulado()

    with tab_real:
        _vista_rss_real()


def _vista_rastreo_simulado() -> None:
    st.markdown("### Configuracion del rastreador")
    with st.form("form_rastreo"):
        col1, col2 = st.columns([1.25, 0.75])
        with col1:
            url_base = st.text_input("URL base", "https://ejemplo-noticias.com/noticias?page=1")
        with col2:
            min_noticias = st.number_input("Minimo de noticias", min_value=5, max_value=50, value=20, step=1)

        col3, col4, col5 = st.columns(3)
        with col3:
            noticias_por_pagina = st.slider("Noticias por pagina", 3, 10, 5)
        with col4:
            total_paginas = st.slider("Paginas maximas", 2, 8, 4)
        with col5:
            respetar_robots = st.toggle("Respetar robots.txt", value=False, help="Desactivado en el simulador local.")

        ejecutar = st.form_submit_button("Ejecutar rastreo simulado", type="primary", use_container_width=True)

    if not ejecutar:
        st.markdown(
            """
<div class="simanw-callout">
La demo no hace peticiones externas: genera HTML local paginado para demostrar el flujo de Fase 1.
</div>
""",
            unsafe_allow_html=True,
        )
        return

    with st.spinner("Rastreando paginas simuladas..."):
        rastreador = _crear_rastreador(url_base, noticias_por_pagina, total_paginas)
        rastreador.respetar_robots = respetar_robots
        resultados = rastreador.rastrear(minimo_noticias=int(min_noticias))

    st.success("Rastreo completado.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Paginas visitadas", len(rastreador.paginas_visitadas))
    c2.metric("Noticias extraidas", len(resultados))
    c3.metric("Objetivo minimo", int(min_noticias))
    c4.metric("Robots.txt", "Activo" if respetar_robots else "Simulado")

    tab_resultados, tab_paginas, tab_exportacion = st.tabs(
        ["Noticias extraidas", "Paginas visitadas", "Exportacion"]
    )

    with tab_resultados:
        if resultados:
            st.dataframe(_tabla_resultados(resultados), use_container_width=True, hide_index=True, height=380)
        else:
            st.info("No se extrajeron noticias con esta configuracion.")

    with tab_paginas:
        st.code("\n".join(rastreador.paginas_visitadas), language="text")

    with tab_exportacion:
        if resultados:
            json_bytes = json.dumps(resultados, ensure_ascii=False, indent=2).encode("utf-8")
            csv_bytes = pd.DataFrame(resultados).to_csv(index=False).encode("utf-8")
            col_json, col_csv = st.columns(2)
            col_json.download_button(
                "Descargar JSON",
                data=json_bytes,
                file_name="ac1_noticias_paginadas.json",
                mime="application/json",
                use_container_width=True,
            )
            col_csv.download_button(
                "Descargar CSV",
                data=csv_bytes,
                file_name="ac1_noticias_paginadas.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.divider()
            if st.button("Guardar en corpus del sistema", type="primary",
                         use_container_width=True, key="btn_guardar_sim"):
                _guardar_corpus(resultados)
        st.caption("Estos archivos alimentan el control de calidad, NLP, clasificacion y busqueda.")


def _vista_rss_real() -> None:
    st.markdown("### Obtener noticias reales")
    st.caption(
        "La forma mas practica para esta fase es usar feeds RSS/Atom: entregan titulos, fechas, enlaces y resumen sin depender del HTML cambiante de cada portal."
    )

    fuentes = list(FEEDS_DEMO)
    col1, col2 = st.columns([1.2, 0.8])
    with col1:
        seleccionadas = st.multiselect(
            "Fuentes RSS",
            fuentes,
            default=["BBC Mundo", "El Universal", "NASA"],
        )
        feed_manual = st.text_input("Feed RSS adicional", placeholder="https://sitio.example/feed.xml")
    with col2:
        max_por_fuente = st.slider("Noticias por fuente", 3, 20, 8)
        categoria_default = st.selectbox(
            "Categoria por defecto",
            ["general", "politica", "economia", "tecnologia", "ciencia"],
            index=0,
        )

    st.markdown(
        """
<div class="simanw-callout">
Recomendacion: guarda solo metadatos, resumen y URL. Para texto completo, respeta robots.txt y terminos de uso de cada medio.
</div>
""",
        unsafe_allow_html=True,
    )

    if not st.button("Descargar noticias reales", type="primary", use_container_width=True):
        st.dataframe(
            pd.DataFrame(
                [{"Fuente": nombre, "RSS": url} for nombre, url in FEEDS_DEMO.items()]
            ),
            use_container_width=True,
            hide_index=True,
        )
        return

    feeds = {nombre: FEEDS_DEMO[nombre] for nombre in seleccionadas}
    if feed_manual.strip():
        feeds["Feed manual"] = feed_manual.strip()

    noticias: list[dict] = []
    resumenes: list[dict] = []
    with st.spinner("Consultando feeds RSS..."):
        for nombre, url in feeds.items():
            rastreador = RastreadorRSS(
                url,
                categoria_default=categoria_default,
                max_noticias=max_por_fuente,
            )
            extraidas = rastreador.extraer()
            for noticia in extraidas:
                noticia["fuente_nombre"] = nombre
            noticias.extend(extraidas)
            resumen = rastreador.resumen()
            resumen["nombre"] = nombre
            resumenes.append(resumen)

    c1, c2, c3 = st.columns(3)
    c1.metric("Fuentes consultadas", len(feeds))
    c2.metric("Noticias reales", len(noticias))
    c3.metric("Fuentes con error", sum(1 for r in resumenes if r["errores"]))

    if resumenes:
        st.subheader("Resumen de fuentes")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Fuente": r["nombre"],
                        "Extraidas": r["total_extraidas"],
                        "Errores": r["errores"],
                        "Feed": r["feed"],
                    }
                    for r in resumenes
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if noticias:
        st.subheader("Noticias descargadas")
        st.dataframe(_tabla_resultados(noticias), use_container_width=True, hide_index=True, height=380)

        json_bytes = json.dumps(noticias, ensure_ascii=False, indent=2).encode("utf-8")
        csv_bytes = pd.DataFrame(noticias).to_csv(index=False).encode("utf-8")
        col_json, col_csv = st.columns(2)
        col_json.download_button(
            "Descargar JSON real",
            data=json_bytes,
            file_name="noticias_reales_rss.json",
            mime="application/json",
            use_container_width=True,
        )
        col_csv.download_button(
            "Descargar CSV real",
            data=csv_bytes,
            file_name="noticias_reales_rss.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.divider()
        if st.button("Guardar en corpus del sistema", type="primary",
                     use_container_width=True, key="btn_guardar_rss"):
            _guardar_corpus(noticias)
    else:
        st.warning("No se obtuvieron noticias. Revisa la conectividad o prueba otra fuente RSS.")


if __name__ == "__main__":
    main()

