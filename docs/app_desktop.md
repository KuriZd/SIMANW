# SIMANW Desktop App

Interfaz de escritorio unificada para SIMANW. La app presenta secciones orientadas al usuario final y ejecuta internamente las fases academicas del proyecto.

## Ejecutar

```powershell
pip install -r requirements.txt
python -m src.nltk_setup
python app_desktop.py
```

## Flujo basico

1. Abrir `Load / Analyze News`.
2. Seleccionar `Demo local` para una ejecucion reproducible sin red.
3. Presionar `Analyze News`.
4. Revisar `Dashboard`, `Smart Results`, `News Explorer`, `Search & Q&A`, `Knowledge Graph`, `Reports & Exports` y `Academic Evidence`.

## Fuentes

| Modo | Descripcion |
|---|---|
| Demo local | Usa datos locales de demostracion. Es el modo recomendado para pruebas, clases y presentaciones sin internet. |
| Predefined source | Usa el catalogo de `config/fuentes_noticias.py`: La Jornada, Aristegui Noticias, Proceso, El Heraldo de Mexico e INEGI Sala de Prensa. |
| Custom RSS/URL | Permite ingresar una URL RSS o una URL inicial para rastreo paginado. |
| File | Soportado en el servicio unificado mediante `source="archivo"` si se invoca programaticamente. |

Las fuentes externas pueden fallar por cambios de URL, feeds retirados, cambios del DOM, bloqueos de red o reglas del proveedor. La app conserva el modo demo como respaldo reproducible.

## Secciones de producto

| Seccion | Uso |
|---|---|
| Dashboard | Metricas generales del corpus, documentos procesados, categorias, sentimiento y grafo. |
| Load / Analyze News | Seleccion de fuente y ejecucion del pipeline completo en segundo plano. |
| Smart Results | Evidencia NLP, terminos frecuentes, distribuciones y resultados analiticos. |
| News Explorer | Tabla y detalle de noticias analizadas. |
| Search & Q&A | Busqueda inteligente y preguntas respondidas con el corpus cargado. |
| Knowledge Graph | Resumen RDF, exportacion TTL/JSON-LD y consultas SPARQL de ejemplo. |
| Reports & Exports | Artefactos generados y re-exportacion de datos. |
| Academic Evidence | Estado interno por fase, advertencias, errores y lista de archivos. |

## Fases internas ejecutadas

1. Extraccion/rastreo con `Fase1Service`.
2. Procesamiento NLP con `Fase2Service`.
3. Analisis de sentimiento, clasificacion, terminos y tendencias con `Fase3Service`.
4. Busqueda TF-IDF y lenguaje natural con `Fase4Service`.
5. Q&A/chatbot con `Fase5Service`.
6. Knowledge Graph RDF/SPARQL con `Fase6Service`.
7. Reportes, manifiesto y log con `Fase7Service`.

La orquestacion vive en `src/simanw_app_service.py`; `app_desktop.py` solo administra la ventana, navegacion y estado compartido de UI.

## Archivos generados

La ejecucion completa puede generar:

- `data/raw/noticias.json`
- `data/raw/noticias.csv`
- `data/processed/corpus_procesado.json`
- `data/processed/corpus_procesado.csv`
- `outputs/analisis/reporte_analisis.json`
- `outputs/tendencias.csv`
- `outputs/tendencias.png`
- `outputs/grafo/simanw_graph.ttl`
- `outputs/grafo/simanw_graph.jsonld`
- `outputs/reportes/reporte_final.md`
- `outputs/runs/<run_id>/manifest.json`
- `outputs/runs/<run_id>/pipeline_log.jsonl`

## Limitaciones conocidas

- Los resultados con RSS/HTML reales dependen de conectividad y disponibilidad de los sitios.
- La clasificacion usa un conjunto de entrenamiento local y debe ampliarse para produccion.
- El sentimiento VADER es util como evidencia academica, pero no sustituye una validacion humana.
- SPARQL local funciona con el grafo generado; endpoints externos requieren internet y politicas de acceso estables.
