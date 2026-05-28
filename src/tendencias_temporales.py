"""AC-9: Línea de tiempo y tendencias por tema.

Granularidad elegida: mes.
Justificación: el corpus del SIMANW abarca noticias de distintos meses;
la granularidad mensual ofrece suficientes periodos para detectar tendencias
sin fragmentar en exceso un corpus de tamaño medio (docenas a centenas de
noticias). La semana sería adecuada con corpus de miles de documentos diarios.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Literal


Granularidad = Literal["mes", "semana"]

_STOPWORDS_ES = {
    "para", "como", "este", "esta", "esto", "esos", "esas", "ellos", "ellas",
    "pero", "sobre", "entre", "desde", "hasta", "cuando", "donde", "como",
    "también", "tambien", "solo", "más", "mas", "que", "con", "los", "las",
    "del", "una", "por", "sus", "sus", "nuevo", "nueva", "nuevos", "nuevas",
}


class TendenciasTemporales:
    """Agrupa noticias por periodo y analiza tendencias temáticas."""

    def __init__(self, granularidad: Granularidad = "mes") -> None:
        self.granularidad = granularidad
        self.noticias: list[dict] = []

    def cargar_noticias(self, noticias: list[dict]) -> None:
        self.noticias = [n for n in noticias if self._periodo(n.get("fecha", ""))]

    # ------------------------------------------------------------------
    # Análisis principal
    # ------------------------------------------------------------------

    def conteo_por_periodo(self) -> dict[str, dict[str, int]]:
        """Retorna {categoria: {periodo: count}}, periodos ordenados."""
        resultado: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for noticia in self.noticias:
            periodo = self._periodo(noticia.get("fecha", ""))
            categoria = self._categoria(noticia)
            if periodo:
                resultado[categoria][periodo] += 1
        return {cat: dict(sorted(ps.items())) for cat, ps in resultado.items()}

    def tendencia_terminos(self, categoria: str, n_top: int = 5) -> dict:
        """
        Compara frecuencia de términos entre el primer y el último periodo
        para una categoría dada.  Retorna los que más aumentaron y disminuyeron.
        """
        noticias_cat = [n for n in self.noticias if self._categoria(n) == categoria]
        if not noticias_cat:
            return {"aumentan": [], "disminuyen": [], "primer_periodo": None, "ultimo_periodo": None}

        periodos_ord = sorted({self._periodo(n["fecha"]) for n in noticias_cat if n.get("fecha")})
        if len(periodos_ord) < 2:
            return {
                "aumentan": [],
                "disminuyen": [],
                "primer_periodo": periodos_ord[0] if periodos_ord else None,
                "ultimo_periodo": periodos_ord[-1] if periodos_ord else None,
            }

        primer_p, ultimo_p = periodos_ord[0], periodos_ord[-1]
        freq_inicial = self._frecuencia_tokens(noticias_cat, primer_p)
        freq_final = self._frecuencia_tokens(noticias_cat, ultimo_p)

        todos = set(freq_inicial) | set(freq_final)
        deltas = {t: freq_final.get(t, 0) - freq_inicial.get(t, 0) for t in todos}

        aumentan = sorted((t for t, d in deltas.items() if d > 0), key=lambda t: -deltas[t])[:n_top]
        disminuyen = sorted((t for t, d in deltas.items() if d < 0), key=lambda t: deltas[t])[:n_top]

        return {
            "aumentan": aumentan,
            "disminuyen": disminuyen,
            "primer_periodo": primer_p,
            "ultimo_periodo": ultimo_p,
        }

    def pico_notable(self) -> dict:
        """Devuelve la (categoría, periodo) con mayor concentración de noticias."""
        conteos = self.conteo_por_periodo()
        mejor: dict = {"categoria": None, "periodo": None, "count": 0, "titulos": []}
        for categoria, periodos in conteos.items():
            for periodo, count in periodos.items():
                if count > mejor["count"]:
                    titulos = [
                        n["titulo"]
                        for n in self.noticias
                        if self._categoria(n) == categoria and self._periodo(n.get("fecha", "")) == periodo
                    ]
                    mejor = {"categoria": categoria, "periodo": periodo, "count": count, "titulos": titulos}
        return mejor

    # ------------------------------------------------------------------
    # Exportación y visualización
    # ------------------------------------------------------------------

    def tabla_resumen(self) -> list[dict]:
        """Lista plana exportable: una fila por (categoria, periodo)."""
        conteos = self.conteo_por_periodo()
        return [
            {"categoria": cat, "periodo": periodo, "noticias": count}
            for cat in sorted(conteos)
            for periodo, count in sorted(conteos[cat].items())
        ]

    def exportar_csv(self, ruta: str | Path = "data/ac9_tendencias.csv") -> Path:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["categoria", "periodo", "noticias"])
            writer.writeheader()
            writer.writerows(self.tabla_resumen())
        return ruta

    def exportar_png(self, ruta: str | Path = "outputs/tendencias.png") -> Path:
        """Genera una visualizacion PNG de noticias por categoria y periodo."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        tabla = self.tabla_resumen()
        fig, ax = plt.subplots(figsize=(10, 5))
        if not tabla:
            ax.text(0.5, 0.5, "Sin datos de tendencias", ha="center", va="center")
            ax.set_axis_off()
        else:
            periodos = sorted({fila["periodo"] for fila in tabla})
            categorias = sorted({fila["categoria"] for fila in tabla})
            ancho = 0.8 / max(len(categorias), 1)
            posiciones = list(range(len(periodos)))

            for idx, categoria in enumerate(categorias):
                valores = [
                    next(
                        (
                            fila["noticias"]
                            for fila in tabla
                            if fila["categoria"] == categoria and fila["periodo"] == periodo
                        ),
                        0,
                    )
                    for periodo in periodos
                ]
                desplazamiento = (idx - (len(categorias) - 1) / 2) * ancho
                ax.bar([p + desplazamiento for p in posiciones], valores, width=ancho, label=categoria)

            ax.set_title("Tendencias temporales por categoria")
            ax.set_xlabel("Periodo")
            ax.set_ylabel("Noticias")
            ax.set_xticks(posiciones)
            ax.set_xticklabels(periodos, rotation=30, ha="right")
            ax.legend()
            ax.grid(axis="y", alpha=0.25)

        fig.tight_layout()
        fig.savefig(ruta, dpi=140)
        plt.close(fig)
        return ruta

    def visualizacion_texto(self, ancho_max: int = 35) -> str:
        """Diagrama de barras ASCII por categoría y periodo."""
        conteos = self.conteo_por_periodo()
        if not conteos:
            return "(sin datos)"
        max_count = max(c for ps in conteos.values() for c in ps.values()) or 1
        lineas: list[str] = []
        for categoria in sorted(conteos):
            lineas.append(f"\n  [{categoria.upper()}]")
            for periodo, count in sorted(conteos[categoria].items()):
                barra = "#" * round(count / max_count * ancho_max)
                lineas.append(f"  {periodo}  {barra} {count}")
        return "\n".join(lineas)

    def conclusion(self) -> str:
        """Genera conclusión de ~una página con los hallazgos principales."""
        conteos = self.conteo_por_periodo()
        pico = self.pico_notable()
        total = len(self.noticias)
        categorias = sorted(conteos.keys())
        periodos_globales = sorted({p for ps in conteos.values() for p in ps})
        n_periodos = len(periodos_globales)
        primer_p = periodos_globales[0] if periodos_globales else "N/A"
        ultimo_p = periodos_globales[-1] if periodos_globales else "N/A"
        gran_txt = "mensual" if self.granularidad == "mes" else "semanal"

        resumen_cats = ", ".join(
            f"{cat} ({sum(conteos[cat].values())} noticias)" for cat in categorias[:3]
        )

        texto = (
            f"CONCLUSIÓN — Análisis de Tendencias Temporales del SIMANW\n"
            f"{'=' * 55}\n\n"
            f"El corpus analizado contiene {total} noticias distribuidas en {n_periodos} periodo(s) "
            f"{gran_txt}(s), desde {primer_p} hasta {ultimo_p}. "
            f"La granularidad {gran_txt} fue elegida porque permite observar ciclos editoriales "
            f"sin fragmentar en exceso un corpus de tamaño medio; la semana sería preferible "
            f"con miles de documentos diarios.\n\n"
            f"Las categorías con mayor presencia son: {resumen_cats}. "
        )

        if pico["categoria"]:
            titulos_str = "; ".join(f'"{t[:55]}"' for t in pico["titulos"][:3])
            texto += (
                f"\n\nEl pico más notable se registra en {pico['categoria'].upper()} "
                f"durante {pico['periodo']}, con {pico['count']} noticia(s). "
                f"Los títulos que explican esta concentración son: {titulos_str}. "
                f"Esta acumulación refleja mayor actividad periodística en el tema "
                f"durante ese periodo, posiblemente asociada a eventos, lanzamientos "
                f"o debates de relevancia pública.\n"
            )

        cat_con_mas_periodos = max(conteos, key=lambda c: len(conteos[c]), default=None)
        if cat_con_mas_periodos:
            tend = self.tendencia_terminos(cat_con_mas_periodos)
            if tend["aumentan"] or tend["disminuyen"]:
                texto += (
                    f"\nEn la categoría {cat_con_mas_periodos}, comparando {tend['primer_periodo']} "
                    f"con {tend['ultimo_periodo']}, los términos con mayor incremento de frecuencia "
                    f"son: {', '.join(tend['aumentan'][:3]) or 'N/A'}. "
                    f"Los que disminuyeron: {', '.join(tend['disminuyen'][:3]) or 'N/A'}. "
                    f"Este desplazamiento léxico evidencia una evolución en el enfoque editorial.\n"
                )

        texto += (
            f"\nEn síntesis, el análisis temporal confirma que el corpus del SIMANW presenta "
            f"variaciones temáticas observables a nivel {gran_txt}, validando la utilidad del "
            f"módulo para monitorear la agenda informativa y detectar tendencias emergentes."
        )
        return texto

    def guardar_reporte_json(self, ruta: str | Path = "reports/tendencias_ac9.json") -> Path:
        """Exporta conteos, pico y tabla a JSON."""
        import json
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "actividad": "AC-9",
            "granularidad": self.granularidad,
            "total_noticias": len(self.noticias),
            "conteo_por_periodo": self.conteo_por_periodo(),
            "tabla_resumen": self.tabla_resumen(),
            "pico_notable": self.pico_notable(),
        }
        with ruta.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return ruta

    def guardar_conclusion_markdown(self, ruta: str | Path = "reports/conclusion_tendencias_ac9.md") -> Path:
        """Exporta la conclusion como archivo Markdown."""
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(self.conclusion(), encoding="utf-8")
        return ruta

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _periodo(self, fecha: str) -> str:
        try:
            dt = datetime.strptime(str(fecha).strip(), "%Y-%m-%d")
            if self.granularidad == "mes":
                return dt.strftime("%Y-%m")
            iso = dt.isocalendar()
            return f"{iso[0]}-W{iso[1]:02d}"
        except ValueError:
            return ""

    @staticmethod
    def _categoria(noticia: dict) -> str:
        return noticia.get("categoria_predicha") or noticia.get("categoria_original", "desconocido")

    def _frecuencia_tokens(self, noticias_cat: list[dict], periodo: str) -> Counter:
        noticias_p = [n for n in noticias_cat if self._periodo(n.get("fecha", "")) == periodo]
        texto = " ".join(
            f"{n.get('titulo', '')} {n.get('cuerpo', '')}" for n in noticias_p
        )
        texto = unicodedata.normalize("NFKD", texto.lower())
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        tokens = re.findall(r"\b[a-z]{4,}\b", texto)
        return Counter(t for t in tokens if t not in _STOPWORDS_ES)


# ---------------------------------------------------------------------------
# Datos demo — 16 noticias distribuidas en 3 meses y 4 categorías
# ---------------------------------------------------------------------------
NOTICIAS_AC9_DEMO: list[dict] = [
    # ── 2026-01: tecnologia×2, economia×1, ciencia×1
    {
        "titulo": "Python se consolida como lenguaje más popular del año",
        "cuerpo": "La comunidad de desarrolladores confirma que Python lidera los rankings de uso en inteligencia artificial y ciencia de datos. La programación con Python crece en universidades.",
        "fecha": "2026-01-05", "categoria_predicha": "tecnologia",
    },
    {
        "titulo": "Nuevas herramientas de IA aceleran el desarrollo de software",
        "cuerpo": "Los modelos de inteligencia artificial generativa reducen el tiempo de codificación. Las empresas de software adoptan asistentes de programación basados en transformers.",
        "fecha": "2026-01-18", "categoria_predicha": "tecnologia",
    },
    {
        "titulo": "Mercados globales cierran enero con pérdidas moderadas",
        "cuerpo": "La inflación y las tasas de interés presionan al mercado de valores. Los inversores muestran cautela ante las políticas del banco central. La economía global siente el impacto.",
        "fecha": "2026-01-22", "categoria_predicha": "economia",
    },
    {
        "titulo": "Investigadores descubren nueva especie marina en el Pacífico",
        "cuerpo": "Un equipo de biólogos marinos publica hallazgos sobre biodiversidad oceánica. La ciencia marina avanza con nuevas técnicas de exploración submarina y secuenciación genómica.",
        "fecha": "2026-01-29", "categoria_predicha": "ciencia",
    },
    # ── 2026-02: tecnologia×3, economia×2, ciencia×1, politica×1
    {
        "titulo": "OpenAI lanza nuevo modelo con capacidades multimodales avanzadas",
        "cuerpo": "El nuevo modelo de inteligencia artificial procesa texto, imágenes y audio simultáneamente. Las empresas tecnológicas compiten por liderar el mercado de IA generativa y transformers.",
        "fecha": "2026-02-03", "categoria_predicha": "tecnologia",
    },
    {
        "titulo": "Google integra IA en su motor de búsqueda con resultados inmediatos",
        "cuerpo": "La inteligencia artificial redefine la búsqueda web. Los modelos de lenguaje natural mejoran la relevancia de los resultados. La competencia entre buscadores se intensifica.",
        "fecha": "2026-02-11", "categoria_predicha": "tecnologia",
    },
    {
        "titulo": "Startups de inteligencia artificial reciben inversión récord en febrero",
        "cuerpo": "El ecosistema de startups tecnológicas atrae millones en rondas de financiamiento. Los inversores apuestan por modelos de lenguaje, visión computacional y automatización robótica.",
        "fecha": "2026-02-20", "categoria_predicha": "tecnologia",
    },
    {
        "titulo": "Banco central sube tasas de interés por tercera vez consecutiva",
        "cuerpo": "La política monetaria busca controlar la inflación. Los mercados reaccionan con volatilidad ante la decisión. El peso y otras monedas emergentes sienten presión cambiaria.",
        "fecha": "2026-02-07", "categoria_predicha": "economia",
    },
    {
        "titulo": "Exportaciones manufactureras crecen pese a incertidumbre global",
        "cuerpo": "El sector manufacturero reporta cifras positivas en comercio exterior. La demanda internacional de productos industriales impulsa la economía. Las cadenas de suministro se estabilizan.",
        "fecha": "2026-02-25", "categoria_predicha": "economia",
    },
    {
        "titulo": "Estudio vincula emisiones de carbono con aceleración del deshielo polar",
        "cuerpo": "Científicos publican evidencia sobre el cambio climático y la reducción de glaciares. Los datos satelitales confirman el calentamiento global en zonas árticas y antárticas.",
        "fecha": "2026-02-14", "categoria_predicha": "ciencia",
    },
    {
        "titulo": "Congreso aprueba reforma educativa enfocada en habilidades digitales",
        "cuerpo": "La nueva legislación incorpora programación e inteligencia artificial en el currículo escolar. El gobierno invierte en infraestructura tecnológica para escuelas públicas rurales y urbanas.",
        "fecha": "2026-02-28", "categoria_predicha": "politica",
    },
    # ── 2026-03: tecnologia×1, economia×1, ciencia×3, politica×1
    {
        "titulo": "México lanza programa nacional de ciberseguridad para infraestructura crítica",
        "cuerpo": "El gobierno refuerza la protección digital de sistemas de energía, agua y finanzas. Las empresas tecnológicas participan en el diseño de protocolos de seguridad informática.",
        "fecha": "2026-03-06", "categoria_predicha": "tecnologia",
    },
    {
        "titulo": "Inflación cede por primera vez en seis meses según datos oficiales",
        "cuerpo": "Los precios al consumidor muestran señales de desaceleración. El banco central evalúa pausar el ciclo de alzas de tasas. Los mercados responden con optimismo y recuperación bursátil.",
        "fecha": "2026-03-12", "categoria_predicha": "economia",
    },
    {
        "titulo": "Vacuna experimental contra dengue muestra eficacia del 90% en ensayo clínico",
        "cuerpo": "Investigadores médicos publican resultados prometedores en la lucha contra enfermedades tropicales. La ciencia biomédica avanza con nuevas plataformas de ARN mensajero y estudios multicéntricos.",
        "fecha": "2026-03-04", "categoria_predicha": "ciencia",
    },
    {
        "titulo": "Científicos mapean el genoma completo de especie en peligro de extinción",
        "cuerpo": "El proyecto de secuenciación genómica abre nuevas posibilidades para la conservación biológica. Los datos genéticos permiten diseñar programas de reproducción asistida y preservación de biodiversidad.",
        "fecha": "2026-03-18", "categoria_predicha": "ciencia",
    },
    {
        "titulo": "Misión espacial detecta moléculas orgánicas en asteroide cercano a la Tierra",
        "cuerpo": "El descubrimiento científico reaviva el debate sobre el origen de la vida. Los instrumentos de espectrometría identifican compuestos de carbono y agua en la superficie del asteroide.",
        "fecha": "2026-03-25", "categoria_predicha": "ciencia",
    },
    {
        "titulo": "Elecciones municipales definen nueva composición de gobiernos locales",
        "cuerpo": "Los resultados electorales muestran cambios en el mapa político regional. La participación ciudadana alcanza niveles históricos. Los partidos analizan los resultados y planean estrategias futuras.",
        "fecha": "2026-03-30", "categoria_predicha": "politica",
    },
]
