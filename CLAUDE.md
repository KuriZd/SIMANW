# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SIMANW** (Sistema Inteligente de Monitoreo y Análisis de Noticias Web) is a 4-phase intelligent news monitoring and analysis system built in Python. It crawls news sites, applies NLP, classifies articles, runs sentiment analysis, and provides an intelligent search engine.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.nltk_setup   # Download Spanish NLTK resources (run once)
```

**Python version**: Use Python 3.12. Python 3.13+ causes pandas/NumPy compilation issues on Windows.

If `Activate.ps1` is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first.

## Commands

```powershell
# Run the full 4-phase pipeline
python main.py

# Run individual phases
python main_fase2.py
python main_fase3.py
python main_fase4.py

# Run all tests
python -m pytest

# Run a single test file
python -m pytest test/test_extractor.py -v
```

## Architecture

The pipeline executes four sequential phases, each with its own `main_faseN.py` entry point and corresponding modules under `src/`:

**Phase 1 – Crawling & Extraction** (`src/extractor.py`, `parser_dom.py`, `control_rastreo.py`, `exportador.py`)
Fetches HTML, parses DOM to detect news structure, extracts title/body/date/author/category/URL, and exports to `data/noticias_extraidas.{json,csv}`. `html_demo.py` generates sample HTML for testing.

**Phase 2 – NLP Pipeline** (`src/pipeline_nlp.py`, `representacion_vectorial.py`, `similitud.py`)
Cleans and tokenizes Spanish text, removes stop words, applies stemming, builds a TF-IDF matrix, and computes cosine similarity to cluster thematically related articles.

**Phase 3 – Classification & Analysis** (`src/clasificador_noticias.py`, `sentimientos.py`, `recomendacion.py`, `detector_publicidad.py`)
Classifies articles into categories (scikit-learn), runs VADER sentiment analysis, generates content-based recommendations, and detects advertising topics.

**Phase 4 – Intelligent Search** (`src/motor_busqueda.py`, `evaluador_irs.py`, `busqueda_natural.py`)
Builds an inverted index, supports boolean and TF-IDF vector search, interprets natural-language queries, and evaluates retrieval quality (precision, recall, F1, MAP, P@K).

**`main.py`** wires all four phases end-to-end; each `main_faseN.py` is a standalone demo for that phase only.

## Coding Conventions

- Domain identifiers are in Spanish (e.g., `noticias`, `clasificador`, `sentimientos`).
- Type hints are required on all function signatures.
- 4-space indentation.
- One test file per module in `test/` (e.g., `test/test_extractor.py` ↔ `src/extractor.py`).
- Commit messages: short imperative, prefix with phase when relevant (e.g., `Add fase3 sentiment module`).
