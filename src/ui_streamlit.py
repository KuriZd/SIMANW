"""Utilidades visuales compartidas para el dashboard Streamlit de SIMANW."""
from __future__ import annotations

import streamlit as st


COLORES_CATEGORIA = {
    "tecnologia": "#2563EB",
    "economia": "#059669",
    "ciencia": "#7C3AED",
    "politica": "#D97706",
    "general": "#64748B",
}

COLORES_SENTIMIENTO = {
    "positivo": "#059669",
    "neutral": "#64748B",
    "negativo": "#DC2626",
}

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def inject_sidebar_styles() -> None:
    """Inyecta CSS específico para la sidebar oscura con contraste completo."""
    st.markdown(
        """
<style>
/* ── Contenedor principal ─────────────────────────────────────── */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"] {
  background-color: #0F172A !important;   /* slate-900 */
  border-right: 1px solid #1E293B !important;
}

/* Franja de acento en la parte superior */
[data-testid="stSidebar"]::before {
  content: "";
  display: block;
  height: 3px;
  background: linear-gradient(90deg, #2563EB, #7C3AED);
  position: sticky;
  top: 0;
  z-index: 10;
}

/* ── Todo el texto dentro de la sidebar ──────────────────────── */
/* El !important es necesario porque config.toml fuerza textColor oscuro
   en todo el app, y la sidebar tiene fondo oscuro — hay que revertirlo. */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] em,
[data-testid="stSidebar"] strong {
  color: #CBD5E1 !important;   /* slate-300 */
}

/* ── Logo / encabezado del app ──────────────────────────────── */
[data-testid="stSidebarHeader"] {
  background: #0F172A !important;
  border-bottom: 1px solid #1E293B !important;
  padding-bottom: 0.5rem;
}
[data-testid="stSidebarHeader"] img {
  filter: brightness(1.15);
}

/* ── Navegación: lista de páginas ───────────────────────────── */
[data-testid="stSidebarNavLink"],
[data-testid="stPageLink"],
[data-testid="stSidebar"] a {
  color: #CBD5E1 !important;
  text-decoration: none !important;
  border-radius: 7px;
  transition: background 0.15s ease, color 0.15s ease;
}

[data-testid="stSidebarNavLink"] span,
[data-testid="stPageLink"] span,
[data-testid="stSidebar"] a span {
  color: inherit !important;
}

/* Hover */
[data-testid="stSidebarNavLink"]:hover,
[data-testid="stPageLink"]:hover,
[data-testid="stSidebar"] a:hover {
  background: rgba(255, 255, 255, 0.07) !important;
  color: #F1F5F9 !important;
}

/* Página activa */
[data-testid="stSidebarNavLink"][aria-current="page"],
[data-testid="stPageLink"][aria-current="page"],
[data-testid="stSidebar"] a[aria-current="page"] {
  background: rgba(37, 99, 235, 0.18) !important;
  color: #93C5FD !important;              /* blue-300 */
  border-left: 3px solid #3B82F6 !important;
  padding-left: calc(0.6rem - 3px) !important;
  font-weight: 600;
}
[data-testid="stSidebarNavLink"][aria-current="page"] span,
[data-testid="stPageLink"][aria-current="page"] span,
[data-testid="stSidebar"] a[aria-current="page"] span {
  color: #93C5FD !important;
}

/* Iconos SVG — heredan el color del texto */
[data-testid="stSidebar"] svg {
  color: inherit !important;
  fill: currentColor !important;
}

/* ── Botón colapsar (la flecha «») ──────────────────────────── */
/* #94A3B8 sobre #0F172A = 6.8:1, pasa AA incluso como texto */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapseButton"] button svg {
  color: #94A3B8 !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
  color: #E2E8F0 !important;
  background: rgba(255, 255, 255, 0.08) !important;
  border-radius: 6px !important;
}

/* ── Botón expandir cuando sidebar está colapsada ─────────────── */
[data-testid="collapsedControl"] {
  background: #0F172A !important;
  border-right: 1px solid #1E293B !important;
}
[data-testid="collapsedControl"] button {
  color: #94A3B8 !important;   /* 6.8:1 sobre #0F172A */
  background: transparent !important;
}
[data-testid="collapsedControl"] button:hover {
  color: #93C5FD !important;
  background: rgba(255, 255, 255, 0.08) !important;
}

/* ── Inputs / selects dentro de la sidebar (futuro) ──────────── */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-testid="stTextInput"] input {
  background: #1E293B !important;
  color: #E2E8F0 !important;
  border-color: #334155 !important;
  caret-color: #3B82F6;
}
[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder {
  color: #94A3B8 !important;   /* 5.8:1 sobre #1E293B — pasa AA */
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus {
  border-color: #3B82F6 !important;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
}

/* Selectbox */
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
  background: #1E293B !important;
  color: #E2E8F0 !important;
  border-color: #334155 !important;
}

/* Radio / Checkbox */
[data-testid="stSidebar"] [data-testid="stRadio"] label,
[data-testid="stSidebar"] [data-testid="stCheckbox"] label {
  color: #CBD5E1 !important;
}

/* Botones primarios en sidebar */
[data-testid="stSidebar"] button[kind="primary"] {
  background: #2563EB !important;
  color: #FFFFFF !important;
  border: none !important;
}
[data-testid="stSidebar"] button[kind="primary"]:hover {
  background: #1D4ED8 !important;
}

/* Botones secundarios en sidebar */
[data-testid="stSidebar"] button[kind="secondary"] {
  background: #1E293B !important;
  color: #CBD5E1 !important;
  border-color: #334155 !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
  background: #263347 !important;
  color: #F1F5F9 !important;
}

/* Widget labels (st.text_input, st.selectbox, etc.) en sidebar */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  color: #94A3B8 !important;
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.01em;
}

/* Caption / texto secundario — #94A3B8 sobre #0F172A = 6.8:1, pasa AA */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
  color: #94A3B8 !important;
  font-size: 0.78rem;
}

/* Divider horizontal */
[data-testid="stSidebar"] hr {
  border-color: #1E293B !important;
}
</style>
""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Estilos principales (contenido + sidebar)
# ---------------------------------------------------------------------------

_NAV_PAGES: list[tuple[str, str, str]] = [
    ("📊", "Dashboard",                    "app.py"),
    ("F1", "Rastreo Web",                  "pages/AC01_Rastreo_Paginado.py"),
    ("F2", "Análisis de Discurso",         "pages/AC02_Analisis_Discurso.py"),
    ("F3", "Selección de Modelo",          "pages/AC03_Seleccion_Modelo.py"),
    ("F4", "Hilo de Discusión",            "pages/AC04_Hilo_Discusion.py"),
    ("F5", "Comparador de Búsqueda",       "pages/AC05_Comparador_Busqueda.py"),
    ("F6", "Chatbot Contextual",           "pages/AC06_Chatbot_Contextual.py"),
    ("F7", "Enriquecimiento KG",           "pages/AC07_Enriquecimiento_KG.py"),
    ("08", "Control de Calidad",           "pages/AC08_Control_Calidad.py"),
    ("09", "Tendencias Temporales",        "pages/AC09_Tendencias_Temporales.py"),
    ("10", "Alertas de Consulta",          "pages/AC10_Alertas_Consulta.py"),
    ("11", "Usabilidad",                   "pages/AC11_Usabilidad.py"),
    ("12", "Trazabilidad",                 "pages/AC12_Trazabilidad.py"),
    ("13", "Publicación Semántica",        "pages/AC13_Publicacion_Semantica.py"),
]


def _render_sidebar_nav() -> None:
    with st.sidebar:
        st.markdown(
            "<div style='padding:0.6rem 0 0.25rem;font-size:1.1rem;font-weight:700;"
            "color:#93C5FD;letter-spacing:0.04em'>SIMANW</div>",
            unsafe_allow_html=True,
        )
        st.divider()
        for icon, label, path in _NAV_PAGES:
            st.page_link(path, label=f"{icon} · {label}")
        st.divider()
        st.caption("Sistema Inteligente de Monitoreo\ny Análisis de Noticias Web")


def aplicar_estilo_global() -> None:
    """Aplica la capa visual al dashboard completo e inyecta los estilos de sidebar."""
    _render_sidebar_nav()
    st.markdown(
        """
<style>
/* ── Variables globales ──────────────────────────────────────── */
:root {
  --simanw-ink:    #111827;
  --simanw-muted:  #475569;   /* slate-600: ≥4.5:1 sobre #F3F6FA y #FFFFFF */
  --simanw-border: #D7DEE8;
  --simanw-panel:  #F8FAFC;
  --simanw-brand:  #2563EB;
  --simanw-accent: #059669;
}

/* ── Layout principal ────────────────────────────────────────── */
.stApp {
  background: #F3F6FA;
  color: var(--simanw-ink);
}

.block-container {
  padding-top: 2rem;
  padding-bottom: 3rem;
  max-width: 1280px;
}

/* ── Tipografía ──────────────────────────────────────────────── */
h1, h2, h3 {
  letter-spacing: 0;
  color: var(--simanw-ink);
}
h1 { font-size: 2.2rem; line-height: 1.12; }
h2 { font-size: 1.35rem; }
h3 { font-size: 1.05rem; }

/* ── Métricas ────────────────────────────────────────────────── */
div[data-testid="stMetric"] {
  background: #FFFFFF;
  border: 1px solid var(--simanw-border);
  border-top: 3px solid var(--simanw-brand);
  border-radius: 8px;
  padding: 0.85rem 1rem;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}
div[data-testid="stMetric"] label {
  color: var(--simanw-muted) !important;
}
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] > div {
  color: var(--simanw-ink) !important;
}

/* ── Tabs ────────────────────────────────────────────────────── */
button[data-baseweb="tab"] {
  color: var(--simanw-ink) !important;
}

/* ── Expander ────────────────────────────────────────────────── */
details summary,
[data-testid="stExpander"] summary {
  color: var(--simanw-ink) !important;
}

/* ── Texto en markdown y widgets ─────────────────────────────── */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {
  color: var(--simanw-ink);
}
[data-testid="stWidgetLabel"] p {
  color: var(--simanw-ink) !important;
}
[data-testid="stCaptionContainer"] p {
  color: var(--simanw-muted) !important;
}

/* ── Componentes custom ──────────────────────────────────────── */
.simanw-hero {
  background: #FFFFFF;
  border: 1px solid var(--simanw-border);
  border-radius: 8px;
  padding: 1.25rem 1.35rem;
  margin-bottom: 1rem;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}
.simanw-eyebrow {
  color: var(--simanw-brand);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 0.35rem;
}
.simanw-hero h1 { margin: 0; }
.simanw-hero p {
  margin: 0.55rem 0 0;
  max-width: 760px;
  color: var(--simanw-muted);
  font-size: 1rem;
}

.simanw-panel {
  background: #FFFFFF;
  border: 1px solid var(--simanw-border);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.simanw-step {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  background: #FFFFFF;
  border: 1px solid var(--simanw-border);
  border-radius: 8px;
  padding: 0.85rem;
  min-height: 72px;
}
.simanw-step strong {
  display: block;
  color: var(--simanw-ink);
  font-size: 0.95rem;
}
.simanw-step span {
  color: var(--simanw-muted);
  font-size: 0.9rem;
}

.simanw-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  border-radius: 999px;
  background: #EAF1FF;
  color: var(--simanw-brand);
  font-weight: 700;
}

.simanw-callout {
  border-left: 4px solid var(--simanw-brand);
  background: #EFF6FF;
  border-radius: 8px;
  padding: 0.85rem 1rem;
  color: #1E3A8A;
}
</style>
""",
        unsafe_allow_html=True,
    )
    inject_sidebar_styles()


# ---------------------------------------------------------------------------
# Componentes reutilizables
# ---------------------------------------------------------------------------

def encabezado(seccion: str, titulo: str, descripcion: str) -> None:
    st.markdown(
        f"""
<section class="simanw-hero">
  <div class="simanw-eyebrow">{seccion}</div>
  <h1>{titulo}</h1>
  <p>{descripcion}</p>
</section>
""",
        unsafe_allow_html=True,
    )


def paso(numero: int, titulo: str, descripcion: str) -> None:
    st.markdown(
        f"""
<div class="simanw-step">
  <div class="simanw-badge">{numero}</div>
  <div><strong>{titulo}</strong><span>{descripcion}</span></div>
</div>
""",
        unsafe_allow_html=True,
    )
