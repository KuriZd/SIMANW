# Reproducibilidad SIMANW

## Procedimiento

1. Crear entorno virtual: `python -m venv .venv`.
2. Activarlo en PowerShell: `.\.venv\Scripts\Activate.ps1`.
3. Instalar dependencias: `pip install -r requirements.txt`.
4. Preparar NLTK: `python -m src.nltk_setup`.
5. Ejecutar el pipeline:
   - Demo: `python main.py --source demo`.
   - RSS: `python main.py --source rss --url <url>`.
   - Archivo: `python main.py --source archivo --input data/raw/noticias.json`.

## Fuente usada en esta ejecucion

- Source: `demo`
- URL: `N/A`
- Input: `N/A`

## Artefactos generados

- corpus_depurado: `data\processed\corpus_depurado.json`
- corpus_procesado: `data\processed\corpus_procesado.json`
- grafo_jsonld: `outputs\grafo\simanw_graph.jsonld`
- grafo_shacl_report: `outputs\grafo\shacl_report.txt`
- grafo_ttl: `outputs\grafo\simanw_graph.ttl`
- raw_csv: `data\raw\noticias.csv`
- raw_json: `data\raw\noticias.json`
- reporte_calidad: `outputs\reporte_calidad.json`
- reporte_final: `outputs\reportes\reporte_final.md`
- tendencias_csv: `outputs\tendencias.csv`
- tendencias_png: `outputs\tendencias.png`

## Limitaciones

El rastreo real depende de conectividad, disponibilidad del sitio, cambios de estructura, RSS incompletos y reglas de robots.txt. Los modelos locales de clasificacion y sentimiento son ligeros y deben recalibrarse con corpus amplio para uso productivo.

## Checklist

- [x] Dependencias declaradas.
- [x] Recursos NLTK documentados.
- [x] Datos crudos guardados.
- [x] Corpus depurado y procesado guardado.
- [x] Reporte, tendencias, grafo, manifiesto y log generados.