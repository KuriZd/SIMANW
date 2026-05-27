# SIMANW — Sistema Inteligente de Monitoreo y Análisis de Noticias Web

Sistema Inteligente de Monitoreo y Análisis de Noticias Web. Implementa un pipeline completo de procesamiento desde extracción y NLP hasta clasificación, análisis de sentimientos, búsqueda inteligente y un dashboard visual interactivo.

## Objetivo de la Fase 1

Construir un módulo inicial capaz de:

- Analizar la estructura DOM de una página HTML.
- Extraer noticias con título, cuerpo, fecha, autor, categoría y URL.
- Controlar qué enlaces puede visitar el rastreador.
- Evitar rastreo fuera del dominio o directorio permitido.
- Generar un resumen de extracción.
- Exportar los datos a JSON y CSV.
- Dejar una base para una futura implementación con Scrapy.

## Estructura del proyecto

```txt
simanw_fase1/
├── main.py
├── requirements.txt
├── README.md
├── data/
│   ├── noticias_extraidas.json
│   └── noticias_extraidas.csv
├── src/
│   ├── __init__.py
│   ├── control_rastreo.py
│   ├── exportador.py
│   ├── extractor.py
│   ├── html_demo.py
│   └── parser_dom.py
└── scrapy_spider/
    └── simanw_spider.py
```

## Instalación

Crear un entorno virtual:

```bash
python -m venv .venv
```

Activar el entorno virtual en Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

Desde la raíz del proyecto:

```bash
python main.py
```

## Pruebas

Ejecutar la suite de tests:

```bash
python -m pytest
```

## Salida esperada

El programa ejecuta cuatro pasos:

1. Analiza el DOM del HTML de prueba.
2. Extrae las noticias disponibles.
3. Simula el control de rastreo de URLs.
4. Exporta los datos en archivos JSON y CSV.

Los archivos generados se guardan en la carpeta `data/`.

## Módulos principales

### `parser_dom.py`

Analiza la estructura básica de una página HTML y devuelve información general como título, navegación, tendencias y cantidad de artículos.

### `extractor.py`

Contiene la clase `ExtractorNoticias`, encargada de convertir artículos HTML en datos estructurados.

### `control_rastreo.py`

Contiene la clase `ControlRastreo`, encargada de validar URLs, mantener una cola de rastreo, registrar URLs visitadas y rechazar enlaces fuera del alcance definido.

### `exportador.py`

Guarda las noticias extraídas en formato JSON y CSV.

### `scrapy_spider/simanw_spider.py`

Incluye una versión base del spider usando Scrapy para una futura implementación en producción.

## Nota sobre la versión Scrapy

El archivo `scrapy_spider/simanw_spider.py` es una referencia inicial. Para ejecutarlo como proyecto Scrapy real, primero habría que crear un proyecto con:

```bash
scrapy startproject simanw_scrapy
```

Después se movería el spider a la carpeta `spiders/` del proyecto generado.

## Resultado de la fase

Al finalizar esta fase, el sistema cuenta con una base funcional para extraer noticias desde HTML, controlar el alcance de rastreo y almacenar los datos. Esta información podrá ser utilizada en las siguientes fases para procesamiento de lenguaje natural, clasificación, búsqueda inteligente, análisis semántico y generación de reportes.

---

## Interfaz visual con Streamlit

SIMANW incluye un dashboard interactivo construido con Streamlit que expone todas las capacidades del sistema en un entorno visual moderno.

### Instalación de dependencias

```bash
pip install -r requirements.txt
```

### Preparación de recursos NLTK

Al ejecutar la aplicación por primera vez se descargan automáticamente los recursos de NLTK necesarios (`punkt`, `punkt_tab`, `stopwords`, `vader_lexicon`). Si prefieres descargarlos manualmente:

```python
import nltk
nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("stopwords")
nltk.download("vader_lexicon")
```

### Generar los datos (si aún no existen)

```bash
python main.py
```

Esto produce `data/noticias_extraidas.json` con el corpus procesado completo.

### Ejecutar la interfaz

```bash
streamlit run app.py
```

La aplicación abre en `http://localhost:8501` en el navegador.

### Secciones del dashboard

| Sección | Descripción |
|---------|-------------|
| **Dashboard** | Vista general con métricas del corpus (total noticias, categorías, autores, sentimiento predominante), gráfica de distribución por categoría, gráfica de sentimientos y tabla resumen. |
| **Noticias extraídas** | Catálogo filtrable por categoría, sentimiento, autor y rango de fechas. Muestra título, cuerpo, categoría original, categoría predicha, sentimiento y enlace a la fuente. |
| **Pipeline NLP** | Para cualquier noticia seleccionada: texto original, texto limpio, tokens, tokens sin stopwords y stems. Estadísticas del corpus (vocabulario, riqueza léxica) y palabras más frecuentes. Top términos TF-IDF por documento. |
| **Clasificación** | Comparación entre categoría original y categoría predicha (LinearSVC). Scores de decisión por categoría visualizados en barras horizontales. Tabla comparativa del corpus completo. |
| **Sentimientos** | Distribución de sentimientos (positivo/neutral/negativo) con gráfica de pastel y barras de compound score. Detalle por noticia con gauge de intensidad de sentimiento. |
| **Búsqueda inteligente** | Búsqueda en lenguaje natural o vectorial. Interpreta filtros semánticos (sentimiento, categoría) automáticamente. Muestra resultados con relevancia, snippet y metadatos. |
| **Recomendaciones** | Selecciona una noticia base y obtiene las más similares por contenido TF-IDF. Mapa de calor con la matriz de similitud coseno del corpus. |
| **Evaluación IRS** | Tabla de métricas (Precision, Recall, F1, Average Precision) para consultas de ejemplo por categoría. MAP global del sistema. Herramienta interactiva de Precision@K. |
| **Exportación** | Descarga el corpus en JSON (completo con NLP) o CSV (campos tabulares con métricas de sentimiento). Guardado directo en disco en `data/`. |

---

## Web Semántica — Knowledge Graph (AC-13)

SIMANW construye un Knowledge Graph en RDF a partir del corpus procesado.

### Archivos generados

| Archivo | Formato | Descripción |
|---------|---------|-------------|
| `data/ac13_simanw.ttl` | Turtle | Volcado RDF principal |
| `data/ac13_simanw.jsonld` | JSON-LD compacto | Mismos datos con `@context` legible |
| `shapes/simanw_shapes.ttl` | SHACL | Reglas de validación formal |
| `queries/*.rq` | SPARQL | Consultas sobre el grafo local |
| `docs/ontologia_simanw.md` | Markdown | Documentación completa de la ontología |

### Generar el grafo

```powershell
python main_actividades_complementarias.py
```

Esto ejecuta `ejecutar_ac13()` y regenera los archivos RDF en `data/`.

### Prefijos principales

| Prefijo | URI |
|---------|-----|
| `simanw:` | `http://simanw.org/ontology/` |
| `dc:` | `http://purl.org/dc/elements/1.1/` |
| `schema:` | `https://schema.org/` |
| `foaf:` | `http://xmlns.com/foaf/0.1/` |
| `skos:` | `http://www.w3.org/2004/02/skos/core#` |

### Consultas SPARQL

```powershell
# Ejecutar las consultas AC-13 en consola
python -c "
from main_actividades_complementarias import ejecutar_ac13
ejecutar_ac13()
"
```

### Validación SHACL

```python
from src.knowledge_graph import KnowledgeGraphSIMANW
kg = KnowledgeGraphSIMANW()
# ... construir grafo ...
resultado = kg.validar_con_shacl('shapes/simanw_shapes.ttl')
print(resultado['conforme'], resultado['texto'])
```

---

### Ejecución del pipeline por consola

El proyecto también funciona sin la interfaz visual:

```bash
# Pipeline completo
python main.py

# Por fases
python main_fase2.py
python main_fase3.py
python main_fase4.py

# Tests
python -m pytest
```
