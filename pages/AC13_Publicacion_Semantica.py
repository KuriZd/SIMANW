"""AC-13: Publicación Semántica y Validación RDF."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge_graph import (
    QUERY_AC13_AUTORES_PRODUCTIVOS,
    QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS,
    QUERY_AC13_SENTIMIENTO_POR_CATEGORIA,
    KnowledgeGraphSIMANW,
)
from src.tendencias_temporales import NOTICIAS_AC9_DEMO
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

NOTICIAS_KG = []
for _i, _n in enumerate(NOTICIAS_AC9_DEMO[:6], start=1):
    NOTICIAS_KG.append({
        **_n,
        "autor": f"Autor {_i % 3}",
        "fuente": "https://demo.test",
        "url": f"https://demo.test/kg/{_i}",
        "sentimiento": {
            "etiqueta": "positivo" if _i % 2 else "negativo",
            "compound": 0.4 if _i % 2 else -0.3,
        },
    })

st.set_page_config(page_title="SIMANW | AC-13: Publicación Semántica", page_icon="🌐", layout="wide")
aplicar_estilo_global()



@st.cache_resource
def build_kg() -> KnowledgeGraphSIMANW:
    kg = KnowledgeGraphSIMANW()
    kg.construir_desde_noticias(NOTICIAS_KG)
    return kg


def main() -> None:
    encabezado(
        "AC-13 | Publicación Semántica",
        "Publicación Semántica y Validación RDF",
        "Exportación del grafo de conocimiento como Turtle y JSON-LD, validación SHACL y consultas SPARQL propias.",
    )

    kg = build_kg()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Resumen del grafo", "Consultas SPARQL", "Exportación RDF", "Validación y enlaces", "JSON-LD"
    ])

    with tab1:
        st.subheader("Corpus del knowledge graph")
        df_n = pd.DataFrame([{
            "Título": n.get("titulo",""),
            "Categoría": n.get("categoria_original", n.get("categoria_predicha","?")),
            "Fecha": n.get("fecha",""),
            "Sentimiento": n.get("sentimiento",{}).get("etiqueta","?"),
        } for n in NOTICIAS_KG])
        st.dataframe(df_n, use_container_width=True, hide_index=True)
        st.metric("Total triples RDF", kg.total_triples())

        with st.expander("Ver Turtle (fragmento)"):
            try:
                turtle = kg.serializar("turtle")
                lineas = [l for l in turtle.split("\n") if l.strip()][:35]
                st.code("\n".join(lineas), language="turtle")
            except Exception as exc:
                st.warning(f"Serialización no disponible: {exc}")

    with tab2:
        st.subheader("Consultas SPARQL personalizadas del AC-13")
        consultas = {
            "Autores productivos": QUERY_AC13_AUTORES_PRODUCTIVOS,
            "Sentimiento por categoría": QUERY_AC13_SENTIMIENTO_POR_CATEGORIA,
            "Noticias negativas recientes": QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS,
        }
        for nombre, query in consultas.items():
            with st.expander(f"🔎 {nombre}"):
                st.code(query, language="sparql")
                try:
                    filas = kg.consultar(query)
                    if filas:
                        resultados_dict = [{k: str(v) for k, v in row.asdict().items()} for row in filas]
                        st.dataframe(pd.DataFrame(resultados_dict), use_container_width=True, hide_index=True)
                    else:
                        st.info("La consulta no devolvió resultados.")
                except Exception as exc:
                    st.warning(f"Error al ejecutar la consulta: {exc}")

    with tab3:
        st.subheader("Exportar grafo a Turtle y JSON-LD")
        if st.button("▶ Exportar RDF", type="primary"):
            try:
                rutas = kg.exportar_rdf("data/ac13_simanw")
                st.success(f"Exportado: `{rutas.get('turtle')}` y `{rutas.get('json-ld')}`")
                st.session_state["rutas_export"] = {k: str(v) for k, v in rutas.items()}
            except Exception as exc:
                st.error(f"Error al exportar: {exc}")

        rutas_guardadas = st.session_state.get("rutas_export", {})
        for fmt in ["turtle", "json-ld"]:
            ruta = Path(f"data/ac13_simanw.{'ttl' if fmt == 'turtle' else 'jsonld'}")
            if ruta.exists():
                contenido = ruta.read_bytes()
                extension = "ttl" if fmt == "turtle" else "jsonld"
                mime = "text/turtle" if fmt == "turtle" else "application/ld+json"
                st.download_button(
                    f"⬇ Descargar {fmt.upper()}",
                    data=contenido,
                    file_name=f"simanw.{extension}",
                    mime=mime,
                    key=f"dl_{fmt}",
                )

    with tab4:
        st.subheader("Validación SHACL del grafo")
        try:
            validacion = kg.validar_formas()
            conforme = validacion.get("conforme", False)
            violaciones = validacion.get("violaciones", [])
            col1, col2 = st.columns(2)
            col1.metric("¿Conforme?", "✅ Sí" if conforme else "❌ No")
            col2.metric("Violaciones", len(violaciones))
            if violaciones:
                st.subheader("Detalle de violaciones")
                for v in violaciones:
                    st.warning(str(v))
        except Exception as exc:
            st.warning(f"Validación SHACL no disponible: {exc}")

        st.divider()
        st.subheader("Enlaces externos básicos")
        try:
            enlaces = kg.agregar_enlaces_externos_basicos()
            if enlaces:
                st.metric("Enlaces externos añadidos", len(enlaces))
                df_e = pd.DataFrame(enlaces)
                st.dataframe(df_e, use_container_width=True, hide_index=True)
            else:
                st.info("No se añadieron enlaces externos.")
        except Exception as exc:
            st.warning(f"Error al agregar enlaces externos: {exc}")

        st.divider()
        st.subheader("Nota de reutilización de datos")
        try:
            nota = kg.nota_reutilizacion_datos()
            st.info(nota)
        except Exception as exc:
            st.warning(f"No disponible: {exc}")

    with tab5:
        st.subheader("Fragmento JSON-LD de una noticia")
        noticia_id = st.slider("ID de noticia", 1, len(NOTICIAS_KG), 1)
        try:
            fragmento = kg.fragmento_jsonld_noticia(noticia_id)
            if isinstance(fragmento, dict):
                st.json(fragmento)
            else:
                st.code(str(fragmento), language="json")
        except Exception as exc:
            st.warning(f"Fragmento JSON-LD no disponible: {exc}")

        st.divider()
        ruta_jsonld = Path("data") / "ac13_simanw.jsonld"
        if ruta_jsonld.exists():
            st.subheader("JSON-LD completo exportado")
            try:
                data = json.loads(ruta_jsonld.read_text(encoding="utf-8"))
                st.json(data if isinstance(data, dict) else {"contenido": str(data)[:2000]})
            except Exception:
                st.code(ruta_jsonld.read_text(encoding="utf-8")[:2000], language="json")


if __name__ == "__main__":
    main()

