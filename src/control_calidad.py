"""AC-8: Control de calidad del corpus rastreado.

Reglas de validez mínimas documentadas
--------------------------------------
Campo           Regla
-----------     ------------------------------------------------
titulo          Obligatorio; longitud mínima 5 caracteres.
cuerpo          Obligatorio; longitud mínima 50 caracteres.
fecha           Obligatorio; formato ISO YYYY-MM-DD.
url             Obligatorio; debe comenzar con http:// o https://.
autor           Obligatorio; no puede estar vacío.
categoria_original  Obligatorio; no puede estar vacío.
fuente          Obligatorio; debe comenzar con http:// o https://.

Duplicados
----------
- Exactos: misma URL, comparada tras normalizar mayúsculas y espacios.
- Casi idénticos: mismo título normalizado, colapsando espacios y
  comparando en minúsculas.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


LONGITUD_MINIMA_CUERPO: int = 50
LONGITUD_MINIMA_TITULO: int = 5
PATRON_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PATRON_URL = re.compile(r"^https?://", re.IGNORECASE)

CAMPOS_OBLIGATORIOS: tuple[str, ...] = (
    "titulo",
    "cuerpo",
    "fecha",
    "url",
    "autor",
    "categoria_original",
    "fuente",
)


class ControlCalidadCorpus:
    """Valida y depura un corpus de noticias antes del pipeline NLP."""

    def __init__(
        self,
        longitud_minima_cuerpo: int = LONGITUD_MINIMA_CUERPO,
        longitud_minima_titulo: int = LONGITUD_MINIMA_TITULO,
    ) -> None:
        self.longitud_minima_cuerpo = longitud_minima_cuerpo
        self.longitud_minima_titulo = longitud_minima_titulo

        self.corpus_depurado: list[dict] = []
        self.registros_rechazados: list[dict[str, Any]] = []

        self._urls_vistas: set[str] = set()
        self._titulos_vistos: set[str] = set()

    def validar(self, corpus: list[dict]) -> list[dict]:
        """Valida el corpus y devuelve solo los registros válidos."""
        self.corpus_depurado = []
        self.registros_rechazados = []
        self._urls_vistas = set()
        self._titulos_vistos = set()

        for registro in corpus:
            motivos = self._evaluar(registro)
            if motivos:
                self.registros_rechazados.append({"registro": registro, "motivos": motivos})
            else:
                self.corpus_depurado.append(registro)

        return self.corpus_depurado

    def generar_informe(self) -> dict:
        """Devuelve el informe de calidad como diccionario JSON-serializable."""
        total = len(self.corpus_depurado) + len(self.registros_rechazados)
        invalidos_incompletos = sum(
            1
            for registro in self.registros_rechazados
            if any(
                motivo.startswith("Campo")
                or motivo.startswith("Longitud")
                or motivo.startswith("Formato")
                for motivo in registro["motivos"]
            )
        )
        duplicados_exactos = sum(
            1
            for registro in self.registros_rechazados
            if any("duplicado exacto" in motivo for motivo in registro["motivos"])
        )
        duplicados_similares = sum(
            1
            for registro in self.registros_rechazados
            if any("duplicado por título" in motivo for motivo in registro["motivos"])
        )

        return {
            "total_registros": total,
            "registros_validos": len(self.corpus_depurado),
            "registros_rechazados": len(self.registros_rechazados),
            "invalidos_o_incompletos": invalidos_incompletos,
            "duplicados_exactos_url": duplicados_exactos,
            "duplicados_casi_identicos_titulo": duplicados_similares,
            "detalle_rechazados": [
                {
                    "titulo": item["registro"].get("titulo", "(sin título)"),
                    "url": item["registro"].get("url", "(sin url)"),
                    "motivos": item["motivos"],
                }
                for item in self.registros_rechazados
            ],
        }

    def guardar_informe(self, ruta: str | Path = "data/informe_calidad.json") -> Path:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(self.generar_informe(), archivo, ensure_ascii=False, indent=2)
        return ruta

    def parrafo_resumen(self) -> str:
        """Genera un párrafo explicativo de máximo 200 palabras."""
        informe = self.generar_informe()
        total = informe["total_registros"]
        validos = informe["registros_validos"]
        rechazados = informe["registros_rechazados"]
        invalidos = informe["invalidos_o_incompletos"]
        duplicados_url = informe["duplicados_exactos_url"]
        duplicados_titulo = informe["duplicados_casi_identicos_titulo"]

        if rechazados == 0:
            return (
                f"El corpus procesado contiene {total} registro(s). "
                "Todos los registros superaron las reglas de validez mínima: "
                "campos obligatorios presentes, longitud de cuerpo suficiente, "
                "formato de fecha ISO correcto y URLs coherentes. "
                "No se detectaron duplicados exactos ni casi idénticos. "
                f"El corpus depurado queda compuesto por {validos} noticia(s), "
                "listo para ingresar al pipeline de lenguaje natural."
            )

        partes = []
        if invalidos:
            partes.append(
                f"{invalidos} registro(s) por campos obligatorios ausentes, "
                "cuerpo demasiado corto, fecha con formato incorrecto o URL inválida"
            )
        if duplicados_url:
            partes.append(f"{duplicados_url} registro(s) por URL duplicada (duplicado exacto)")
        if duplicados_titulo:
            partes.append(
                f"{duplicados_titulo} registro(s) por título normalizado idéntico "
                "(duplicado casi idéntico)"
            )

        motivos_texto = "; ".join(partes)
        return (
            f"Del corpus inicial de {total} registro(s), se descartaron {rechazados} "
            f"por los siguientes motivos: {motivos_texto}. "
            "Las reglas de validez aplicadas exigen que cada noticia cuente con "
            f"título (mín. {self.longitud_minima_titulo} caracteres), "
            f"cuerpo (mín. {self.longitud_minima_cuerpo} caracteres), "
            "fecha en formato YYYY-MM-DD, URL que comience con http(s):// "
            "y los campos autor, categoría y fuente no vacíos. "
            "Adicionalmente se eliminaron duplicados exactos (misma URL) y "
            "casi idénticos (mismo título normalizado). "
            f"El corpus depurado final contiene {validos} noticia(s) "
            "utilizables en las fases siguientes del pipeline."
        )

    def guardar_corpus_depurado(self, ruta: str | Path = "data/corpus_depurado_ac8.json") -> Path:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(self.corpus_depurado, archivo, ensure_ascii=False, indent=2)
        return ruta

    def guardar_rechazados(self, ruta: str | Path = "data/registros_rechazados_ac8.json") -> Path:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "titulo": item["registro"].get("titulo", ""),
                "url": item["registro"].get("url", ""),
                "motivos": item["motivos"],
            }
            for item in self.registros_rechazados
        ]
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(payload, archivo, ensure_ascii=False, indent=2)
        return ruta

    def guardar_resumen_markdown(self, ruta: str | Path = "reports/resumen_calidad_ac8.md") -> Path:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        informe = self.generar_informe()
        lineas = [
            "# AC-8: Resumen de Control de Calidad del Corpus",
            "",
            f"**Total registros:** {informe['total_registros']}  ",
            f"**Válidos:** {informe['registros_validos']}  ",
            f"**Rechazados:** {informe['registros_rechazados']}  ",
            f"**Inválidos/incompletos:** {informe['invalidos_o_incompletos']}  ",
            f"**Duplicados exactos (URL):** {informe['duplicados_exactos_url']}  ",
            f"**Duplicados casi idénticos (título):** {informe['duplicados_casi_identicos_titulo']}",
            "",
            "## Resumen",
            "",
            self.parrafo_resumen(),
        ]
        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return ruta

    def _evaluar(self, registro: dict) -> list[str]:
        motivos: list[str] = []

        for campo in CAMPOS_OBLIGATORIOS:
            valor = registro.get(campo, None)
            if valor is None or str(valor).strip() == "":
                motivos.append(f"Campo obligatorio ausente o vacío: '{campo}'")

        titulo = str(registro.get("titulo", "")).strip()
        if titulo and len(titulo) < self.longitud_minima_titulo:
            motivos.append(
                f"Longitud del título insuficiente: {len(titulo)} < {self.longitud_minima_titulo}"
            )

        cuerpo = str(registro.get("cuerpo", "")).strip()
        if cuerpo and len(cuerpo) < self.longitud_minima_cuerpo:
            motivos.append(
                f"Longitud del cuerpo insuficiente: {len(cuerpo)} < {self.longitud_minima_cuerpo}"
            )

        fecha = str(registro.get("fecha", "")).strip()
        if fecha and not PATRON_FECHA.match(fecha):
            motivos.append(f"Formato de fecha inválido: '{fecha}' (se esperaba YYYY-MM-DD)")

        for campo_url in ("url", "fuente"):
            valor_url = str(registro.get(campo_url, "")).strip()
            if valor_url and not PATRON_URL.match(valor_url):
                motivos.append(f"URL inválida en campo '{campo_url}': '{valor_url}'")

        if motivos:
            return motivos

        url_norm = str(registro.get("url", "")).strip().lower()
        if url_norm in self._urls_vistas:
            motivos.append(f"Registro duplicado exacto (URL repetida): '{url_norm}'")
            return motivos
        self._urls_vistas.add(url_norm)

        titulo_norm = re.sub(r"\s+", " ", titulo.lower()).strip()
        if titulo_norm in self._titulos_vistos:
            motivos.append(f"Registro duplicado por título normalizado: '{titulo_norm}'")
            return motivos
        self._titulos_vistos.add(titulo_norm)

        return motivos
