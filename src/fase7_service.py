from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.exportador import guardar_markdown
from src.reportes import GeneradorReportes

try:
    from src.trazabilidad import TrazabilidadPipeline
except ImportError:  # pragma: no cover
    TrazabilidadPipeline = None  # type: ignore[assignment]


class Fase7Service:
    """Reportes, manifiesto y log de ejecucion."""

    def __init__(self) -> None:
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_dir = Path("outputs/runs") / self.run_id

    def generar_reporte_final(self, resultado) -> Path:
        kg = getattr(getattr(resultado, "_grafo_obj", None), "kg", None)
        if kg is not None:
            generador = GeneradorReportes(resultado.corpus_procesado, kg)
            consulta_reporte = resultado.analisis.get("consulta_busqueda_reporte") or "sin consulta registrada"
            return generador.guardar_reporte_markdown(
                "outputs/reportes/reporte_final.md",
                tendencias=resultado.analisis.get("tendencias", {}),
                consultas_busqueda=[{"consulta": consulta_reporte, "resultados": resultado.resultados_busqueda}],
                respuestas_chatbot=[{"pregunta": "Resumen", "respuesta": resultado.respuesta_qa or ""}],
                analisis=resultado.analisis,
                grafo_info=resultado.grafo_info,
                evidencias_ac=resultado.evidencias_ac,
                estado_pipeline=resultado.pipeline_estado,
                archivos_generados=resultado.archivos_generados,
            )

        contenido = self._reporte_fallback(resultado)
        return guardar_markdown(contenido, "outputs/reportes/reporte_final.md")

    def generar_reporte_json(self, resultado) -> Path:
        kg = getattr(getattr(resultado, "_grafo_obj", None), "kg", None)
        generador = GeneradorReportes(resultado.corpus_procesado, kg)
        return generador.guardar_reporte_json(
            "outputs/reportes/reporte_final.json",
            analisis=resultado.analisis,
            grafo_info=resultado.grafo_info,
            evidencias_ac=resultado.evidencias_ac,
            estado_pipeline=resultado.pipeline_estado,
            archivos_generados=resultado.archivos_generados,
        )

    def generar_manifiesto(self, resultado) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        archivos = {Path(ruta).name: ruta for ruta in resultado.archivos_generados if ruta}
        rutas = getattr(resultado, "reporte_info", {}).get("rutas", {})
        fuente_noticias = (
            rutas.get("noticias_json")
            or rutas.get("ac8_corpus_depurado")
            or rutas.get("corpus_json")
            or "fuente-no-registrada"
        )
        if TrazabilidadPipeline is not None:
            traza = TrazabilidadPipeline(fuente_noticias)
            traza.registrar_etapa("extraccion", 0, len(resultado.noticias), rutas.get("noticias_json", "data/noticias_extraidas.json"))
            traza.registrar_etapa("procesamiento", len(resultado.noticias), len(resultado.corpus_procesado), rutas.get("corpus_json", "data/processed/corpus_procesado.json"))
            traza.registrar_etapa("analisis", len(resultado.corpus_procesado), len(resultado.corpus_procesado), rutas.get("analisis_json", "data/resultados_fase3.json"))
            traza.registrar_etapa("busqueda", len(resultado.corpus_procesado), len(resultado.resultados_busqueda), rutas.get("resultados_ac5_json", "indice_busqueda_en_memoria"))
            traza.registrar_etapa("grafo", len(resultado.corpus_procesado), resultado.grafo_info.get("total_triples", 0), rutas.get("grafo_ttl", "outputs/grafo/simanw_graph.ttl"))
            traza.registrar_etapa("reporte", len(resultado.corpus_procesado), 1, rutas.get("reporte_final", "outputs/reportes/reporte_final.md"))
            return traza.guardar_manifiesto(self.run_dir / "manifest.json", archivos)

        data = {
            "run_id": self.run_id,
            "fecha_hora": datetime.now(timezone.utc).isoformat(),
            "archivos_salida": archivos,
            "estado_pipeline": _serializable(resultado.estado_pipeline),
        }
        ruta = self.run_dir / "manifest.json"
        ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return ruta

    def generar_log_pipeline(self, eventos: list[dict]) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        ruta = self.run_dir / "pipeline_log.jsonl"
        lineas = [json.dumps(evento, ensure_ascii=False, default=str) for evento in eventos]
        ruta.write_text("\n".join(lineas) + ("\n" if lineas else ""), encoding="utf-8")
        return ruta

    def _reporte_fallback(self, resultado) -> str:
        lineas = [
            "# Reporte final SIMANW",
            "",
            f"Noticias procesadas: {len(resultado.noticias)}",
            f"Documentos NLP: {len(resultado.corpus_procesado)}",
            f"Triples RDF: {resultado.grafo_info.get('total_triples', 0)}",
            "",
            "## Categorias",
            "",
        ]
        for categoria, total in resultado.analisis.get("categorias", {}).items():
            lineas.append(f"- {categoria}: {total}")
        lineas.extend(["", "## Sentimientos", ""])
        for sentimiento, total in resultado.analisis.get("sentimientos", {}).items():
            lineas.append(f"- {sentimiento}: {total}")
        lineas.extend(["", "## Archivos generados", ""])
        for ruta in resultado.archivos_generados:
            lineas.append(f"- `{ruta}`")
        lineas.extend(
            [
                "",
                "## Limitaciones",
                "",
                "Las fuentes externas pueden cambiar URL, RSS, DOM o reglas de acceso. Los modelos locales son demostrativos.",
                "",
                "## Conclusiones",
                "",
                "La aplicacion integra extraccion, NLP, analisis, busqueda, Q&A, grafo y reportes en un flujo unico.",
            ]
        )
        return "\n".join(lineas)


def _serializable(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    return obj
