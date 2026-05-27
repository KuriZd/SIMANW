from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from src.fase1_service import Fase1Service
from src.fase2_service import Fase2Service


@dataclass
class ResultadoAnalisis:
    noticias: list[dict]
    corpus: list[dict]
    estadisticas: dict
    rutas: dict[str, str]
    pipeline_estado: dict[str, str]
    errores: list[str] = field(default_factory=list)


class SIMANWAppService:
    """Orquesta Fase 1 + Fase 2 como un pipeline unificado."""

    # Mensajes de progreso en orden estricto (usados por la UI para avanzar pasos)
    PASOS = [
        "Cargando noticias…",
        "Procesando texto…",
        "Extrayendo términos relevantes…",
        "Preparando dashboard…",
        "¡Listo!",
    ]

    def __init__(self) -> None:
        self._fase1 = Fase1Service()
        self._fase2 = Fase2Service()

    def analizar_noticias(
        self,
        source: str,
        url: str = "",
        on_progreso: Callable[[str], None] | None = None,
    ) -> ResultadoAnalisis:
        errores: list[str] = []
        rutas: dict[str, str] = {}
        pipeline_estado: dict[str, str] = {}

        def _notify(msg: str) -> None:
            if on_progreso:
                on_progreso(msg)

        # ── Paso 1: extracción ──────────────────────────────────────────────
        _notify(self.PASOS[0])
        resultado_f1 = self._fase1.ejecutar(source, url)
        errores.extend(resultado_f1.errores)
        pipeline_estado["extraccion"] = "warning" if resultado_f1.errores else "ok"

        if resultado_f1.noticias:
            try:
                ruta_j, ruta_c = self._fase1.exportar_todo(resultado_f1.noticias)
                rutas["noticias_json"] = str(ruta_j)
                rutas["noticias_csv"] = str(ruta_c)
                pipeline_estado["exportacion_cruda"] = "ok"
            except Exception as exc:
                errores.append(f"Exportación cruda: {exc}")
                pipeline_estado["exportacion_cruda"] = "error"

        # ── Paso 2: NLP ─────────────────────────────────────────────────────
        _notify(self.PASOS[1])
        resultado_f2 = self._fase2.procesar_corpus(resultado_f1.noticias)
        errores.extend(resultado_f2.errores)
        pipeline_estado["nlp"] = "warning" if resultado_f2.errores else "ok"

        # ── Paso 3: export corpus procesado ────────────────────────────────
        _notify(self.PASOS[2])
        if resultado_f2.corpus:
            try:
                rutas_proc = self._fase2.exportar_todo(resultado_f2.corpus)
                rutas["corpus_json"] = str(rutas_proc["json"])
                rutas["corpus_csv"] = str(rutas_proc["csv"])
                pipeline_estado["exportacion_procesada"] = "ok"
            except Exception as exc:
                errores.append(f"Exportación NLP: {exc}")
                pipeline_estado["exportacion_procesada"] = "error"

        # ── Paso 4-5: finalizar ─────────────────────────────────────────────
        _notify(self.PASOS[3])
        _notify(self.PASOS[4])

        return ResultadoAnalisis(
            noticias=resultado_f1.noticias,
            corpus=resultado_f2.corpus,
            estadisticas=resultado_f2.estadisticas,
            rutas=rutas,
            pipeline_estado=pipeline_estado,
            errores=errores,
        )
