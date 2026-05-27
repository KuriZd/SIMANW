"""AC-12: Trazabilidad y reproducibilidad del pipeline."""
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class EventoPipeline:
    etapa: str
    documentos_entrada: int
    documentos_salida: int
    artefacto: str
    marca_tiempo: str
    estado: str = "ok"


@dataclass
class ManifiestoEjecucion:
    fecha_hora: str
    version_proyecto: str
    fuente_noticias: str
    documentos_por_etapa: dict[str, int]
    archivos_salida: dict[str, str]
    eventos: list[EventoPipeline] = field(default_factory=list)


class TrazabilidadPipeline:
    """Construye manifiestos, logs y anexos reproducibles."""

    def __init__(self, fuente_noticias: str, version_proyecto: str | None = None) -> None:
        self.fuente_noticias = fuente_noticias
        self.version_proyecto = version_proyecto or _version_git()
        self.eventos: list[EventoPipeline] = []

    def registrar_etapa(
        self,
        etapa: str,
        documentos_entrada: int,
        documentos_salida: int,
        artefacto: str,
        estado: str = "ok",
    ) -> None:
        self.eventos.append(
            EventoPipeline(
                etapa=etapa,
                documentos_entrada=documentos_entrada,
                documentos_salida=documentos_salida,
                artefacto=artefacto,
                marca_tiempo=_ahora_iso(),
                estado=estado,
            )
        )

    def manifiesto(self, archivos_salida: dict[str, str]) -> ManifiestoEjecucion:
        documentos_por_etapa = {evento.etapa: evento.documentos_salida for evento in self.eventos}
        return ManifiestoEjecucion(
            fecha_hora=_ahora_iso(),
            version_proyecto=self.version_proyecto,
            fuente_noticias=self.fuente_noticias,
            documentos_por_etapa=documentos_por_etapa,
            archivos_salida=archivos_salida,
            eventos=self.eventos,
        )

    def guardar_manifiesto(self, ruta: str | Path, archivos_salida: dict[str, str]) -> Path:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        manifiesto = self.manifiesto(archivos_salida)
        ruta.write_text(json.dumps(_to_dict(manifiesto), ensure_ascii=False, indent=2), encoding="utf-8")
        return ruta

    def guardar_log_jsonl(self, ruta: str | Path) -> Path:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        lineas = [json.dumps(asdict(evento), ensure_ascii=False) for evento in self.eventos]
        ruta.write_text("\n".join(lineas) + ("\n" if lineas else ""), encoding="utf-8")
        return ruta

    def procedimiento_reproducible(self) -> str:
        return (
            "Procedimiento reproducible: 1) crear y activar .venv; 2) instalar requirements.txt; "
            "3) ejecutar python -m src.nltk_setup; 4) usar como entrada versionada el JSON de "
            "rastreo real declarado en el manifiesto; 5) ejecutar python main.py o el script de "
            "fase correspondiente; 6) verificar que los artefactos de rastreo, reporte, grafo y "
            "log coincidan con las rutas del manifiesto. No se requiere HTML de demostracion."
        )

    def checklist_firmado(self, alumno: str) -> str:
        pasos = [
            "[x] Entorno virtual creado y dependencias instaladas",
            "[x] Datos de entrada versionados identificados",
            "[x] Rastreo ejecutado",
            "[x] Procesamiento NLP ejecutado",
            "[x] Analisis, busqueda, grafo y reporte generados",
            "[x] Manifiesto y log estructurado guardados",
        ]
        return "\n".join([*pasos, f"Firma del alumno: {alumno}"])

    def anexo_limitaciones(self) -> str:
        return (
            "Limitaciones conocidas: los sitios rastreados pueden cambiar su estructura HTML, "
            "bloquear solicitudes o modificar reglas de robots.txt. La conectividad afecta el "
            "rastreo y la descarga de recursos linguisticos. Las dependencias externas pueden "
            "variar resultados entre versiones, por lo que se fija requirements.txt y se registra "
            "la version del proyecto. Las fechas, categorias y sentimientos dependen de la calidad "
            "del corpus y de los modelos locales disponibles."
        )


def trazabilidad_demo() -> TrazabilidadPipeline:
    traza = TrazabilidadPipeline("data/noticias_extraidas.json", version_proyecto="demo-ac12")
    etapas = [
        ("rastreo", 0, 20, "data/ac1_noticias_paginadas.json"),
        ("procesamiento", 20, 2, "data/ac8_informe_calidad.json"),
        ("analisis", 17, 17, "data/ac9_tendencias.csv"),
        ("busqueda", 5, 5, "data/ac10_historial_alertas.json"),
        ("grafo", 23, 23, "data/ac10_consultas_guardadas.json"),
        ("reporte", 3, 3, "data/ac11_resultados_usabilidad.csv"),
    ]
    for etapa, entrada, salida, artefacto in etapas:
        traza.registrar_etapa(etapa, entrada, salida, artefacto)
    return traza


def _to_dict(manifiesto: ManifiestoEjecucion) -> dict[str, Any]:
    data = asdict(manifiesto)
    data["eventos"] = [asdict(evento) for evento in manifiesto.eventos]
    return data


def _version_git() -> str:
    try:
        resultado = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return resultado.stdout.strip()
    except Exception:
        return "version-no-disponible"


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
