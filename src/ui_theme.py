THEME = {
    "bg_base": "#0f1117",
    "bg_surface": "#1c1e26",
    "bg_sidebar": "#151821",
    "bg_input": "#11131a",
    "accent": "#4f8ef7",
    "success": "#3ddc84",
    "warning": "#f0b429",
    "error": "#e05252",
    "text_1": "#e8eaf0",
    "text_2": "#8b8fa8",
    "border": "#2e3147",
}

FONT_H1 = ("Segoe UI", 14, "bold")
FONT_H2 = ("Segoe UI", 11, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_META = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 9)

CARD_RADIUS = 8
CARD_PADDING = 12
SIDEBAR_WIDTH = 230
STATUS_HEIGHT = 34
HEADER_HEIGHT = 82

SECTIONS = [
    ("cargar",     "Cargar noticias",    True),
    ("dashboard",  "Dashboard",          True),
    ("explorador", "Explorador",         True),
    ("resultados", "Resultados NLP",     True),
    ("busqueda",   "Búsqueda y Q&A",     False),
    ("grafo",      "Grafo RDF",          False),
    ("exportar",   "Exportar",           True),
]

# Alias para compatibilidad con código heredado
PHASES = SECTIONS
