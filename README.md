# SIMANW - Fase 1: Rastreador Web de Noticias

Sistema Inteligente de Monitoreo y Análisis de Noticias Web. Esta primera fase implementa la base del rastreador encargado de leer HTML, extraer noticias, controlar el alcance del rastreo y exportar los datos obtenidos.

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

> Se recomienda usar **Python 3.12** para evitar problemas de compatibilidad con algunas dependencias.

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

## Solución de problemas

### Error al activar el entorno virtual en PowerShell

Si al intentar activar el entorno virtual aparece un error similar a este:

```txt
No se puede cargar el archivo .venv\Scripts\Activate.ps1 porque la ejecución de scripts está deshabilitada en este sistema.
```

El problema ocurre porque PowerShell tiene deshabilitada la ejecución de scripts por seguridad.

Para solucionarlo, ejecutar el siguiente comando en PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Cuando PowerShell pregunte si se desea cambiar la directiva de ejecución, escribir:

```powershell
S
```

Después, volver a activar el entorno virtual:

```powershell
.venv\Scripts\Activate.ps1
```

Si la activación fue correcta, la terminal debería mostrar algo similar a:

```powershell
(.venv) PS C:\Users\zamud\OneDrive\Documentos\SIMANW>
```

También se puede usar una solución temporal solo para la terminal actual:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.venv\Scripts\Activate.ps1
```

### Error al instalar `pandas` con `pip install -r requirements.txt`

Si al instalar las dependencias aparece un error similar a este:

```txt
Preparing metadata (pyproject.toml) ... error
ERROR: Could not find C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe
metadata-generation-failed
Encountered error while generating package metadata.
pandas
```

El problema puede ocurrir porque se está usando una versión de Python demasiado reciente, por ejemplo **Python 3.13**, mientras que algunas dependencias del proyecto, como `pandas==2.2.2`, pueden no tener una versión precompilada compatible para esa versión de Python.

Cuando esto sucede, `pip` intenta compilar `pandas` manualmente desde el código fuente, pero en Windows requiere herramientas adicionales de compilación como Visual Studio Build Tools. Para evitar este problema, se recomienda usar **Python 3.12**.

Primero, verificar la versión actual de Python:

```powershell
python --version
```

Si aparece una versión como `Python 3.13.x`, salir del entorno virtual:

```powershell
deactivate
```

Instalar Python 3.12 desde PowerShell:

```powershell
winget install --id Python.Python.3.12 -e
```

Cerrar y volver a abrir PowerShell. Después, entrar nuevamente a la carpeta del proyecto:

```powershell
cd "C:\Users\zamud\OneDrive\Documentos\SIMANW"
```

Eliminar el entorno virtual anterior:

```powershell
Remove-Item -Recurse -Force .venv
```

Crear un nuevo entorno virtual usando Python 3.12:

```powershell
py -3.12 -m venv .venv
```

Activar el entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Actualizar las herramientas de instalación:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

Instalar nuevamente las dependencias:

```powershell
pip install -r requirements.txt
```

Verificar que el entorno virtual esté usando Python 3.12:

```powershell
python --version
```

La salida esperada debe ser similar a:

```txt
Python 3.12.x
```

