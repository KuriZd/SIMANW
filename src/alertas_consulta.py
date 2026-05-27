"""AC-10: Sistema de alertas por consulta guardada."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ConsultaGuardada:
    nombre: str
    expresion: str
    fecha_creacion: str


class SistemaAlertasConsulta:
    """Mantiene consultas permanentes y alertas para noticias nuevas."""

    def __init__(self, consultas: list[ConsultaGuardada] | None = None) -> None:
        self.consultas: list[ConsultaGuardada] = consultas or []
        self.historial_alertas: list[dict[str, Any]] = []
        self._pares_emitidos: set[tuple[str, str]] = set()

    def agregar_consulta(
        self,
        nombre: str,
        expresion: str,
        fecha_creacion: str | None = None,
    ) -> ConsultaGuardada:
        consulta = ConsultaGuardada(
            nombre=nombre,
            expresion=expresion,
            fecha_creacion=fecha_creacion or _ahora_iso(),
        )
        self.consultas.append(consulta)
        return consulta

    def procesar_noticias_nuevas(
        self,
        noticias: list[dict],
        marca_tiempo: str | None = None,
    ) -> list[dict[str, Any]]:
        """Registra alertas nuevas sin duplicar la misma consulta/noticia."""
        marca = marca_tiempo or _ahora_iso()
        alertas: list[dict[str, Any]] = []

        for noticia in noticias:
            noticia_id = self._id_noticia(noticia)
            texto = self._texto_busqueda(noticia)
            for consulta in self.consultas:
                if not self._coincide(consulta.expresion, texto):
                    continue
                llave = (consulta.nombre, noticia_id)
                if llave in self._pares_emitidos:
                    continue
                alerta = {
                    "consulta": consulta.nombre,
                    "expresion": consulta.expresion,
                    "noticia_id": noticia_id,
                    "titulo": noticia.get("titulo", ""),
                    "url": noticia.get("url", ""),
                    "marca_tiempo": marca,
                }
                self.historial_alertas.append(alerta)
                self._pares_emitidos.add(llave)
                alertas.append(alerta)
        return alertas

    def guardar_consultas(self, ruta: str | Path) -> Path:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            json.dumps([asdict(c) for c in self.consultas], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return ruta

    def guardar_historial(self, ruta: str | Path) -> Path:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(self.historial_alertas, ensure_ascii=False, indent=2), encoding="utf-8")
        return ruta

    def cargar_consultas(self, ruta: str | Path) -> None:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        self.consultas = [ConsultaGuardada(**item) for item in datos]

    def documentar_deduplicacion(self) -> str:
        return (
            "El sistema evita alertas duplicadas usando una llave compuesta por el nombre de la "
            "consulta guardada y el identificador estable de la noticia. El identificador se toma "
            "de la URL cuando existe; si no hay URL, se usa el campo id y finalmente el titulo "
            "normalizado como respaldo. Antes de registrar una alerta nueva se revisa si esa llave "
            "ya fue emitida en el historial. Asi, una misma noticia puede activar consultas "
            "distintas, pero la misma consulta no vuelve a alertar sobre la misma noticia aunque "
            "el indice sea reprocesado o la noticia reaparezca en otra ejecucion."
        )

    @staticmethod
    def _texto_busqueda(noticia: dict) -> str:
        return f"{noticia.get('titulo', '')} {noticia.get('cuerpo', '')}".lower()

    @staticmethod
    def _id_noticia(noticia: dict) -> str:
        return str(noticia.get("url") or noticia.get("id") or noticia.get("titulo", "")).strip().lower()

    @staticmethod
    def _coincide(expresion: str, texto: str) -> bool:
        terminos = re.findall(r'"([^"]+)"|(\S+)', expresion.lower())
        piezas = [frase or palabra for frase, palabra in terminos]
        return all(pieza in texto for pieza in piezas)


def consultas_demo() -> list[ConsultaGuardada]:
    fecha = "2026-05-25T09:00:00Z"
    return [
        ConsultaGuardada("IA generativa", '"inteligencia artificial" generativa', fecha),
        ConsultaGuardada("Economia inflacion", "inflacion tasas", fecha),
        ConsultaGuardada("Cambio climatico", '"cambio climatico"', fecha),
        ConsultaGuardada("Datos abiertos", '"datos abiertos"', fecha),
        ConsultaGuardada("Ciberseguridad", "ciberseguridad infraestructura", fecha),
    ]


def noticias_nuevas_demo() -> list[dict]:
    return [
        {
            "titulo": "La inteligencia artificial generativa llega a nuevas empresas",
            "cuerpo": "El sector de software adopta inteligencia artificial generativa para automatizar procesos.",
            "url": "https://demo.test/nueva/ia-generativa",
        },
        {
            "titulo": "Inflacion y tasas presionan a consumidores",
            "cuerpo": "Analistas anticipan ajustes por inflacion y tasas de interes elevadas.",
            "url": "https://demo.test/nueva/inflacion",
        },
        {
            "titulo": "Reporte alerta sobre cambio climatico",
            "cuerpo": "El cambio climatico eleva riesgos en zonas costeras.",
            "url": "https://demo.test/nueva/clima",
        },
        {
            "titulo": "Gobierno publica portal de datos abiertos",
            "cuerpo": "Los datos abiertos buscan mejorar la transparencia publica.",
            "url": "https://demo.test/nueva/datos",
        },
        {
            "titulo": "Plan nacional de ciberseguridad protege infraestructura critica",
            "cuerpo": "La ciberseguridad sera prioritaria para energia, salud e infraestructura.",
            "url": "https://demo.test/nueva/ciber",
        },
    ]


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
