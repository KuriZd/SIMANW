"""AC-7: Enriquecimiento del Knowledge Graph con Wikidata."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enriquecedor_kg import EnriquecedorKG, enriquecer_categorias_demo
from src.knowledge_graph import KnowledgeGraphSIMANW
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

NOTICIAS_KG = [
    {"titulo": "Avances en inteligencia artificial generativa",
     "cuerpo": "La inteligencia artificial y el aprendizaje automatico impulsan nuevas aplicaciones.",
     "fecha": "2026-05-10", "autor": "Autor 1", "categoria_predicha": "tecnologia",
     "fuente": "https://demo.test", "url": "https://demo.test/noticia/1",
     "sentimiento": {"etiqueta": "positivo", "compound": 0.4}},
    {"titulo": "Mercados financieros muestran volatilidad",
     "cuerpo": "La inflacion y las tasas de interes presionan al mercado de valores.",
     "fecha": "2026-05-09", "autor": "Autor 2", "categoria_predicha": "economia",
     "fuente": "https://demo.test", "url": "https://demo.test/noticia/2",
     "sentimiento": {"etiqueta": "negativo", "compound": -0.5}},
    {"titulo": "Descubrimiento cientifico sobre cambio climatico",
     "cuerpo": "Investigadores publican datos sobre emisiones de carbono.",
     "fecha": "2026-05-08", "autor": "Autor 3", "categoria_predicha": "ciencia",
     "fuente": "https://demo.test", "url": "https://demo.test/noticia/3",
     "sentimiento": {"etiqueta": "negativo", "compound": -0.3}},
    {"titulo": "Python mejora herramientas de programacion",
     "cuerpo": "La nueva version de Python ayuda al desarrollo de software.",
     "fecha": "2026-05-07", "autor": "Autor 4", "categoria_predicha": "tecnologia",
     "fuente": "https://demo.test", "url": "https://demo.test/noticia/4",
     "sentimiento": {"etiqueta": "positivo", "compound": 0.3}},
    {"titulo": "Gobierno publica datos abiertos",
     "cuerpo": "El gobierno libera datos abiertos para fortalecer la transparencia publica.",
     "fecha": "2026-05-06", "autor": "Autor 5", "categoria_predicha": "politica",
     "fuente": "https://demo.test", "url": "https://demo.test/noticia/5",
     "sentimiento": {"etiqueta": "positivo", "compound": 0.2}},
]

st.set_page_config(page_title="SIMANW | AC-7: Enriquecimiento KG", page_icon="🔗", layout="wide")
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


def construir_kg_enriquecido(noticias: list[dict]) -> tuple[KnowledgeGraphSIMANW, EnriquecedorKG, int]:
    kg = KnowledgeGraphSIMANW()
    kg.construir_desde_noticias(noticias)
    triples_antes = kg.total_triples()
    enriquecedor = enriquecer_categorias_demo(kg)
    return kg, enriquecedor, triples_antes


def main() -> None:
    encabezado(
        "AC-7 | Enriquecimiento KG",
        "Enriquecimiento del KG con Wikidata",
        "Enlaza las categorías del knowledge graph local con entidades externas de Wikidata usando SKOS.",
    )

    noticias_raw = _noticias_disponibles()
    if noticias_raw:
        noticias = noticias_raw[:30]
        fuente_label = f"Corpus real — {len(noticias)} de {len(noticias_raw)} noticias (límite 30)"
        usando_demo = False
    else:
        noticias = NOTICIAS_KG
        fuente_label = f"Corpus demo — {len(noticias)} noticias (no se encontró data/noticias_extraidas.json)"
        usando_demo = True

    # Normalise fields that may be absent in real noticias
    noticias_norm: list[dict] = []
    for n in noticias:
        item = dict(n)
        item["titulo"] = item.get("titulo") or "Sin título"
        item["cuerpo"] = (
            item.get("cuerpo") or item.get("resumen") or item.get("texto_original") or ""
        )
        item["fecha"] = item.get("fecha") or "2000-01-01"
        item["sentimiento"] = item.get("sentimiento") or {"etiqueta": "neutral", "compound": 0.0}
        item["fuente"] = item.get("fuente") or item.get("url", "https://simanw.local")
        noticias_norm.append(item)

    st.caption(fuente_label)

    tab1, tab2, tab3, tab4 = st.tabs(["Corpus", "Enriquecimiento", "Links locales↔Wikidata", "Consultas SPARQL"])

    with tab1:
        st.subheader(f"Noticias del corpus — {len(noticias_norm)} documentos")
        if not usando_demo:
            st.caption("Mostrando noticias cargadas desde `data/noticias_extraidas.json` o `st.session_state['noticias']`.")
        df = pd.DataFrame([{
            "Título": n.get("titulo", ""),
            "Categoría": n.get("categoria_predicha") or n.get("categoria_original") or n.get("categoria", "?"),
            "Sentimiento": n["sentimiento"]["etiqueta"],
            "Autor": n.get("autor", ""),
        } for n in noticias_norm])
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Proceso de enriquecimiento")
        cache_key = f"kg_{len(noticias_norm)}"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = construir_kg_enriquecido(noticias_norm)
        kg, enriquecedor, triples_antes = st.session_state[cache_key]
        triples_despues = kg.total_triples()

        c1, c2, c3 = st.columns(3)
        c1.metric("Triples antes", triples_antes)
        c2.metric("Triples después", triples_despues)
        c3.metric("Triples añadidos", triples_despues - triples_antes)
        st.metric("Enlaces Wikidata creados", len(enriquecedor.enlaces_externos))

        with st.expander("¿Qué hace el enriquecimiento?"):
            st.markdown("""
El `EnriquecedorKG`:
1. Asigna a cada **categoría local** (`tecnologia`, `economia`, `ciencia`, `politica`) un identificador de Wikidata.
2. Crea triples RDF con predicado `skos:exactMatch` que enlazan la entidad local con la externa.
3. Agrega propiedades descriptivas (`schema:name`, `schema:description`) tomadas de Wikidata.
4. Permite generar **consultas SPARQL** sugeridas para consultar directamente Wikidata por tema.
""")

    with tab3:
        st.subheader("Tabla de enlazado local ↔ Wikidata")
        try:
            enlaces = enriquecedor.consulta_enriquecimiento()
            if enlaces:
                filas = []
                for enlace in enlaces:
                    local = str(enlace.local).split("/")[-1]
                    externo = str(enlace.externo).split("/")[-1]
                    filas.append({
                        "Entidad local": local,
                        "Entidad Wikidata": externo,
                        "Tipo de relación": str(enlace.etiqueta),
                    })
                st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
            else:
                st.info("No se encontraron enlaces en el grafo.")
        except Exception as exc:
            st.warning(f"No se pudieron recuperar los enlaces: {exc}")

    with tab4:
        st.subheader("Consultas SPARQL sugeridas por tema")
        tema = st.selectbox("Selecciona un tema", ["tecnologia", "economia", "ciencia", "politica"])
        query = enriquecedor.generar_query_wikidata(tema)
        st.code(query, language="sparql")
        st.caption("Esta consulta puede ejecutarse en https://query.wikidata.org para obtener información complementaria.")

        st.subheader("Fragmento del grafo en Turtle")
        try:
            turtle = kg.serializar("turtle")
            lineas = [l for l in turtle.split("\n") if l.strip()][:30]
            st.code("\n".join(lineas), language="turtle")
        except Exception as exc:
            st.warning(f"Serialización no disponible: {exc}")


if __name__ == "__main__":
    main()
