# SIMANW — Aplicación de escritorio

Interfaz gráfica modular para el Sistema Inteligente de Monitoreo y Análisis de Noticias Web.

## Instalación y ejecución

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app_desktop.py
```

---

## Modos de carga de noticias

La sección **Cargar noticias** ofrece tres modos de entrada:

| Modo | Uso previsto | Notas |
|------|--------------|-------|
| Demo local | Presentaciones, pruebas offline y validación rápida | No requiere red. Siempre disponible. |
| Fuente predefinida | Selección desde el catálogo configurado en `config/fuentes_noticias.py` | Requiere conexión. Conserva metadatos de fuente en cada noticia. |
| URL personalizada | RSS/Atom o paginación real con URL ingresada por el usuario | Requiere conexión. Selector secundario elige RSS o Paginado. |

### Demo local

Genera noticias a partir de un fragmento HTML local incluido en el código (`src/html_demo.py`). Útil para pruebas reproducibles sin dependencias externas. **No eliminarlo** — es el mecanismo de respaldo para validar el pipeline sin red.

### Fuente predefinida

Usa el catálogo `config/fuentes_noticias.py`. Las fuentes activas iniciales son:

| ID | Nombre | Tipo |
|----|--------|------|
| `la_jornada` | La Jornada | RSS |
| `aristegui_noticias` | Aristegui Noticias | RSS |
| `proceso` | Proceso | RSS |
| `heraldo_mexico` | El Heraldo de México | RSS |
| `inegi_sala_prensa` | INEGI Sala de Prensa | HTML |

Aristegui Noticias usa los feeds de `editorial.aristeguinoticias.com`. INEGI Sala de Prensa se configura como `tipo: "html"` porque su sala de prensa requiere parser específico de DOM.

Cuando se selecciona una fuente predefinida, cada noticia normalizada incluye tres campos adicionales:
- `fuente_nombre` — nombre legible de la fuente
- `fuente_id` — identificador de catálogo
- `fuente_tipo` — `"rss"` o `"html"`

Estos campos se muestran en el **Explorador de noticias** y en el **Dashboard**.

### URL personalizada

Permite introducir cualquier URL RSS/Atom o la página inicial de un sitio paginado. El selector secundario define el tipo de rastreador:
- **RSS** → `RastreadorRSS` con hasta 25 noticias.
- **Paginado** → `RastreadorPaginado` con hasta 5 páginas.

### Fiabilidad de fuentes externas

Las fuentes externas pueden fallar si el proveedor:
- cambia la URL del feed RSS,
- modifica la estructura del DOM,
- bloquea solicitudes automáticas,
- aplica restricciones de acceso o geobloqueo.

En esos casos, la app registra el error en la barra de estado y **no se cierra**. El modo Demo local sigue siendo el mecanismo de respaldo para pruebas reproducibles.

---

## Arquitectura de la UI

```
app_desktop.py                    ← ventana raíz (SIMANWDesktopApp)
  src/ui/sidebar.py               ← barra lateral con set_active()
  src/ui/content_header.py        ← cabecera con título y barra de progreso
  src/ui/status_bar.py            ← barra de estado global
  src/ui/seccion_cargar.py        ← Cargar noticias (pipeline completo)
  src/ui/seccion_dashboard.py     ← Dashboard de estadísticas
  src/ui/seccion_explorador.py    ← Explorador de noticias crudas
  src/ui/seccion_resultados.py    ← Resultados NLP (corpus procesado)
  src/ui/seccion_exportar.py      ← Exportar archivos generados
  src/ui_theme.py                 ← tokens de color, tipografías, SECTIONS

src/simanw_app_service.py         ← orquestación Fase 1 + Fase 2
src/fase1_service.py              ← lógica de extracción y fuentes
src/fase2_service.py              ← lógica NLP y TF-IDF
src/fuentes_service.py            ← catálogo de fuentes predefinidas
config/fuentes_noticias.py        ← datos del catálogo
```

El estado compartido entre secciones vive en `SIMANWDesktopApp`:

| Atributo              | Tipo          | Descripción |
|-----------------------|---------------|-------------|
| `noticias`            | `list[dict]`  | Corpus crudo de Fase 1 |
| `corpus_procesado`    | `list[dict]`  | Corpus NLP de Fase 2 |
| `estadisticas_fase2`  | `dict`        | Métricas del corpus NLP |
| `rutas_exportacion`   | `dict`        | Rutas de archivos generados |
| `pipeline_estado`     | `dict`        | Estado de cada paso del pipeline |

---

## Pipeline de análisis

Cuando el usuario hace clic en **Analizar noticias**, `SIMANWAppService.analizar_noticias()` ejecuta automáticamente:

1. **Cargando noticias…** — `Fase1Service.ejecutar(source, url)` extrae y normaliza.
2. **Procesando texto…** — `Fase2Service.procesar_corpus(noticias)` aplica el pipeline NLP.
3. **Extrayendo términos relevantes…** — exportación del corpus procesado a `data/processed/`.
4. **Preparando dashboard…** — consolida el resultado en `SIMANWDesktopApp`.
5. **¡Listo!** — navega automáticamente al Dashboard.

**Archivos generados:**

| Archivo | Contenido |
|---------|-----------|
| `data/raw/noticias.json` | Corpus crudo (Fase 1) |
| `data/raw/noticias.csv` | Corpus crudo en CSV |
| `data/processed/corpus_procesado.json` | Corpus NLP (Fase 2) |
| `data/processed/corpus_procesado.csv` | Corpus NLP en CSV (listas serializadas como texto) |

---

## Pipeline NLP (Fase 2)

Aplicado automáticamente a cada noticia tras la extracción:

1. **Limpieza:** normaliza a minúsculas, elimina puntuación y dígitos.
2. **Tokenización:** `word_tokenize` NLTK (español).
3. **Eliminación de stopwords:** lista española NLTK + tokens de longitud ≤ 2.
4. **Stemming:** `SnowballStemmer("spanish")`.
5. **TF-IDF:** `RepresentacionVectorial` para los términos más relevantes por documento.

El corpus procesado queda disponible en **Resultados NLP** y en el **Dashboard** sin necesidad de re-ejecutar.

---

## Navegación

| Sección | Función |
|---------|---------|
| Cargar noticias | Selector de fuente + pipeline animado |
| Dashboard | Estadísticas, términos frecuentes, pipeline status |
| Explorador | Tabla y detalle de noticias crudas + exportación |
| Resultados NLP | Corpus procesado con detalle NLP + exportación |
| Búsqueda y Q&A | Reservada (Fase futura) |
| Grafo RDF | Reservada (Fase futura) |
| Exportar | Resumen de archivos generados y re-exportación |

Para añadir una sección futura: crear `src/ui/seccion_X.py` e incorporar el caso en `SIMANWDesktopApp.show_section()`.

---

## FuentesService

`src/fuentes_service.py` expone:

| Método | Descripción |
|--------|-------------|
| `listar_fuentes(activas=True)` | Lista fuentes del catálogo |
| `obtener_fuente(id)` | Devuelve fuente por ID (KeyError si no existe) |
| `obtener_urls(id)` | Lista de URLs de una fuente |
| `validar_fuente(dict)` | Valida campos y tipos; devuelve `(bool, errores)` |
| `listar_nombres_fuentes()` | Lista de nombres de fuentes activas |
| `obtener_por_nombre(nombre)` | Búsqueda por nombre (insensible a mayúsculas) |

Para añadir una fuente nueva, agregar una entrada a `FUENTES_NOTICIAS` en `config/fuentes_noticias.py` con todos los campos requeridos y `"activo": True`.
