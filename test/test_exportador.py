import json

from src.exportador import ExportadorNoticias


def test_guardar_json_crea_archivo(tmp_path):
    noticias = [
        {
            "titulo": "Noticia de prueba",
            "cuerpo": "Contenido de prueba",
            "fecha": "2026-05-10",
            "autor": "Autor Prueba",
            "categoria_original": "tecnologia",
            "url": "https://portal.com/noticia",
            "fuente": "https://portal.com",
        }
    ]

    exportador = ExportadorNoticias(carpeta_salida=str(tmp_path))
    ruta = exportador.guardar_json(noticias, "noticias.json")

    assert ruta.exists()

    contenido = json.loads(ruta.read_text(encoding="utf-8"))

    assert len(contenido) == 1
    assert contenido[0]["titulo"] == "Noticia de prueba"


def test_guardar_csv_crea_archivo(tmp_path):
    noticias = [
        {
            "titulo": "Noticia de prueba",
            "cuerpo": "Contenido de prueba",
            "fecha": "2026-05-10",
            "autor": "Autor Prueba",
            "categoria_original": "tecnologia",
            "url": "https://portal.com/noticia",
            "fuente": "https://portal.com",
        }
    ]

    exportador = ExportadorNoticias(carpeta_salida=str(tmp_path))
    ruta = exportador.guardar_csv(noticias, "noticias.csv")

    assert ruta.exists()
    assert ruta.read_text(encoding="utf-8")