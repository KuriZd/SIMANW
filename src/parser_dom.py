from bs4 import BeautifulSoup


def analizar_dom(html_content: str) -> dict:
    """Analiza una página HTML y devuelve información general del DOM."""
    soup = BeautifulSoup(html_content, "html.parser")

    return {
        "titulo_portal": soup.title.string if soup.title else "Sin título",
        "navegacion": [a.get_text(strip=True) for a in soup.select("nav a")],
        "total_articulos": len(soup.select("article")),
        "tendencias": [a.get_text(strip=True) for a in soup.select("aside li a")],
        "estructura": {
            "nav_enlaces": len(soup.select("nav a")),
            "main_articulos": len(soup.select("main article")),
            "aside_tendencias": len(soup.select("aside li")),
            "footer": soup.footer.get_text(strip=True) if soup.footer else "Sin footer",
        },
    }
