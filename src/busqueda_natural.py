from __future__ import annotations


class BusquedaNatural:
    """Permite buscar noticias con frases naturales en espanol."""

    def __init__(self, motor_busqueda) -> None:
        self.motor = motor_busqueda

    def interpretar_consulta(self, consulta_natural: str) -> dict:
        consulta = consulta_natural.lower()
        filtros = {"sentimiento": None, "categoria": None}

        if any(palabra in consulta for palabra in ["buena", "positiva", "positivo", "optimista"]):
            filtros["sentimiento"] = "positivo"
        elif any(palabra in consulta for palabra in ["mala", "negativa", "negativo", "pesimista", "preocupante"]):
            filtros["sentimiento"] = "negativo"

        categorias_map = {
            "tecnologia": "tecnologia",
            "tecnología": "tecnologia",
            "tech": "tecnologia",
            "computacion": "tecnologia",
            "computación": "tecnologia",
            "programacion": "tecnologia",
            "programación": "tecnologia",
            "python": "tecnologia",
            "economia": "economia",
            "economía": "economia",
            "mercados": "economia",
            "finanzas": "economia",
            "ciencia": "ciencia",
            "cientifico": "ciencia",
            "científico": "ciencia",
            "investigacion": "ciencia",
            "investigación": "ciencia",
            "clima": "ciencia",
            "gobierno": "politica",
            "politica": "politica",
            "política": "politica",
            "datos abiertos": "politica",
        }

        for keyword, categoria in categorias_map.items():
            if keyword in consulta:
                filtros["categoria"] = categoria
                break

        return filtros

    def buscar_natural(self, consulta_natural: str, top_k: int = 3) -> list[dict]:
        filtros = self.interpretar_consulta(consulta_natural)
        resultados = self.motor.buscar_vectorial(consulta_natural, top_k=max(top_k * 3, self.motor.N))
        filtrados = []

        for resultado in resultados:
            if filtros["sentimiento"] and resultado["sentimiento"] != filtros["sentimiento"]:
                continue
            if filtros["categoria"] and resultado["categoria"] != filtros["categoria"]:
                continue
            filtrados.append(resultado)

        if filtrados:
            return filtrados[:top_k]

        fallback_filtrado = self._buscar_por_filtros(filtros)
        if fallback_filtrado:
            return fallback_filtrado[:top_k]

        return resultados[:top_k]

    def _buscar_por_filtros(self, filtros: dict) -> list[dict]:
        if not filtros["sentimiento"] and not filtros["categoria"]:
            return []

        resultados = []
        for doc_id, documento in self.motor.documentos.items():
            categoria = documento.get("categoria_predicha", documento.get("categoria_original", "?"))
            sentimiento = documento.get("sentimiento", {}).get("etiqueta", "?")

            if filtros["sentimiento"] and sentimiento != filtros["sentimiento"]:
                continue
            if filtros["categoria"] and categoria != filtros["categoria"]:
                continue

            resultados.append(
                {
                    "doc_id": doc_id,
                    "titulo": documento["titulo"],
                    "relevancia": 0.0,
                    "categoria": categoria,
                    "sentimiento": sentimiento,
                    "snippet": documento["cuerpo"][:80] + ("..." if len(documento["cuerpo"]) > 80 else ""),
                }
            )

        return resultados
