# Repository Guidelines

## Project Structure & Module Organization

SIMANW is a Python project organized by pipeline phases. Source modules live in `src/`: crawling and extraction (`extractor.py`, `control_rastreo.py`), NLP (`pipeline_nlp.py`, `representacion_vectorial.py`, `similitud.py`), classification and analysis (`clasificador_noticias.py`, `sentimientos.py`, `recomendacion.py`), and search (`motor_busqueda.py`, `busqueda_natural.py`, `evaluador_irs.py`). Tests are in `test/` and follow one test file per module. Demo data exports are stored in `data/`. Scrapy production reference code is in `scrapy_spider/`. Entry points are `main.py`, `main_fase2.py`, `main_fase3.py`, and `main_fase4.py`.

## Build, Test, and Development Commands

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Prepare NLTK resources:

```powershell
python -m src.nltk_setup
```

Run the full pipeline:

```powershell
python main.py
```

Run phase-specific demos:

```powershell
python main_fase2.py
python main_fase3.py
python main_fase4.py
```

Run tests:

```powershell
python -m pytest
```

## Coding Style & Naming Conventions

Use Python 3 with 4-space indentation and type hints where practical. Keep modules focused by responsibility and use Spanish domain names consistent with the project, such as `ExtractorNoticias`, `PipelineNLP`, and `MotorBusqueda`. Prefer small classes with explicit methods over large scripts. Use ASCII in new code unless Spanish output text or existing content needs accents.

## Testing Guidelines

The project uses `pytest`; test discovery is configured in `pytest.ini` for the `test/` directory. Name test files `test_<module>.py` and test functions `test_<behavior>()`. Add focused tests for each new module, including edge cases such as empty inputs, invalid modes, and fallback behavior. Before committing, run:

```powershell
python -m pytest
```

## Commit & Pull Request Guidelines

Git history uses short imperative commit messages grouped by phase, for example `Add phase 4 intelligent search` and `Wire SIMANW phase pipeline`. Keep commits scoped: configuration, each phase, and integration changes should be separate. Pull requests should include a concise summary, affected phase/modules, test results, and any generated data changes under `data/`.

## Security & Configuration Tips

Do not commit `.venv/`, caches, `.env`, or temporary pytest folders; these are ignored in `.gitignore`. Network-dependent setup should go through `src.nltk_setup` rather than ad hoc downloads inside tests.
