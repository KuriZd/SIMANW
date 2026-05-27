from __future__ import annotations

from pathlib import Path

from src.analisis_discurso import AnalisisDiscurso
from src.analizador_hilo import HILO_IA_DEMO, AnalizadorHiloDiscusion
from src.alertas_consulta import SistemaAlertasConsulta, consultas_demo, noticias_nuevas_demo
from src.chatbot_contextual import CONVERSACION_AC6, ChatbotContextual
from src.comparador_busqueda import CONSULTAS_EVAL_AC5, ComparadorModelos
from src.control_calidad import ControlCalidadCorpus
from src.enriquecedor_kg import enriquecer_categorias_demo
from src.knowledge_graph import (
    QUERY_AC13_AUTORES_PRODUCTIVOS,
    QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS,
    QUERY_AC13_SENTIMIENTO_POR_CATEGORIA,
    KnowledgeGraphSIMANW,
)
from src.motor_busqueda import MotorBusqueda
from src.rastreador_paginado import RastreadorPaginado, crear_fetcher_simulado
from src.selector_modelo import ETIQUETAS_AC3, TEXTOS_AC3, SelectorModelo
from src.tendencias_temporales import NOTICIAS_AC9_DEMO, TendenciasTemporales
from src.trazabilidad import trazabilidad_demo
from src.usabilidad import estudio_demo


TEXTO_DISCURSO = """La educacion es la herramienta mas poderosa para transformar
una sociedad. En Mexico, la inversion en educacion debe ser prioritaria para
garantizar el desarrollo economico y social. Los jovenes mexicanos merecen
oportunidades de calidad en todos los niveles educativos. Las universidades
tecnologicas y los institutos de investigacion son pilares fundamentales para
la innovacion. La ciencia y la tecnologia son motores del progreso nacional.
El Instituto Tecnologico de Morelia ha formado generaciones de ingenieros que
contribuyen al desarrollo del pais. La inteligencia artificial y la programacion
son competencias esenciales para el futuro laboral. Mexico necesita mas
profesionales en ciencias computacionales y recuperacion de informacion."""


TEXTO_CIENTIFICO = """El procesamiento de lenguaje natural permite a las computadoras
comprender y generar texto humano. Los modelos de aprendizaje profundo como BERT
y GPT han revolucionado este campo. La representacion vectorial de documentos
mediante TF-IDF sigue siendo fundamental para sistemas de recuperacion de informacion.
Los algoritmos de clasificacion como Naive Bayes y SVM logran alta precision en
categorizacion de texto. El analisis de sentimientos combina tecnicas lexicas con
aprendizaje automatico para determinar la polaridad emocional de un texto."""


NOTICIAS_COMPLEMENTARIAS = [
    {
        "titulo": "Avances en inteligencia artificial generativa",
        "cuerpo": "La inteligencia artificial y el aprendizaje automatico impulsan nuevas aplicaciones de software.",
        "categoria_predicha": "tecnologia",
        "sentimiento": {"etiqueta": "positivo"},
    },
    {
        "titulo": "Mercados financieros muestran volatilidad",
        "cuerpo": "La inflacion y las tasas de interes presionan al mercado de valores y a los inversionistas.",
        "categoria_predicha": "economia",
        "sentimiento": {"etiqueta": "negativo"},
    },
    {
        "titulo": "Descubrimiento cientifico sobre cambio climatico",
        "cuerpo": "Investigadores publican datos sobre emisiones de carbono y calentamiento global.",
        "categoria_predicha": "ciencia",
        "sentimiento": {"etiqueta": "negativo"},
    },
    {
        "titulo": "Python mejora herramientas de programacion",
        "cuerpo": "La nueva version de Python ayuda al desarrollo de software e inteligencia artificial.",
        "categoria_predicha": "tecnologia",
        "sentimiento": {"etiqueta": "positivo"},
    },
    {
        "titulo": "Gobierno publica datos abiertos",
        "cuerpo": "El gobierno libera datos abiertos para fortalecer transparencia y politicas publicas.",
        "categoria_predicha": "politica",
        "sentimiento": {"etiqueta": "positivo"},
    },
]


def ejecutar_ac1() -> None:
    print("=== AC-1: Rastreo con Paginacion ===\n")

    rastreador = RastreadorPaginado(
        url_base="https://ejemplo-noticias.com/noticias?page=1",
        selector_articulos="article",
        selector_siguiente="a.next-page",
        delay=3,
        max_paginas=4,
        fetcher=crear_fetcher_simulado(noticias_por_pagina=5, total_paginas=4),
        respetar_robots=False,
    )

    resultados = rastreador.rastrear(minimo_noticias=20)
    ruta_salida = Path("data") / "ac1_noticias_paginadas.json"
    total_guardadas = rastreador.guardar_json(ruta_salida)

    print(f"Paginas visitadas: {len(rastreador.paginas_visitadas)}")
    print(f"Total noticias extraidas: {len(resultados)}")
    print(f"Archivo JSON generado: {ruta_salida} ({total_guardadas} registros)")
    print("Primeras 5:")
    for noticia in resultados[:5]:
        print(f"  - {noticia['titulo']}")
    print()


def ejecutar_ac2() -> None:
    print("=== AC-2: Analisis Estadistico de Discursos ===\n")

    analizador = AnalisisDiscurso()
    analisis_disc = analizador.analizar(TEXTO_DISCURSO, "Discurso Educativo")
    analisis_cient = analizador.analizar(TEXTO_CIENTIFICO, "Texto Cientifico")

    for analisis in [analisis_disc, analisis_cient]:
        print(f"--- {analisis['titulo']} ---")
        print(f"  Oraciones: {analisis['oraciones']}")
        print(f"  Palabras: {analisis['palabras_totales']}")
        print(f"  Vocabulario: {analisis['vocabulario_unico']}")
        print(f"  Riqueza lexica: {analisis['riqueza_lexica_global']:.3f}")
        print(f"  Prom. palabras/oracion: {analisis['promedio_palabras_oracion']:.1f}")
        print(f"  Riqueza por seccion: {[f'{valor:.3f}' for valor in analisis['riqueza_por_seccion']]}")
        print(f"  Top bigramas: {analisis['top_bigramas'][:4]}")
        print(f"  Posibles entidades: {[entidad[0] for entidad in analisis['posibles_entidades'][:5]]}")
        print()

    print("--- Comparativa ---")
    comparativa = analizador.comparar_textos([analisis_disc, analisis_cient])
    print(f"{'Texto':<20} {'Palabras':>9} {'Vocab':>7} {'Riqueza':>8} {'P/Oracion':>10}")
    for fila in comparativa:
        print(
            f"{fila['titulo']:<20} {fila['palabras']:>9} {fila['vocabulario']:>7} "
            f"{fila['riqueza']:>8.3f} {fila['promedio_oracion']:>10.1f}"
        )
    print()


def ejecutar_ac3() -> None:
    print("=== AC-3: Seleccion Automatica de Modelo ===\n")

    selector = SelectorModelo()
    selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)

    print(selector.reporte())
    print(f"\nModelo seleccionado: {selector.mejor_modelo[0] if selector.mejor_modelo else 'N/A'}")

    nuevos = [
        "nueva aplicacion de machine learning para detectar fraudes",
        "el presidente anuncio reformas al sistema de justicia",
        "inflacion y tasas de interes presionan al mercado de valores",
    ]
    predicciones = selector.predecir(nuevos)

    print("\nPredicciones con el mejor modelo:")
    for texto, prediccion in zip(nuevos, predicciones):
        print(f"  [{prediccion}] {texto[:50]}...")
    print()


def ejecutar_ac4() -> None:
    print("=== AC-4: Analisis de Hilo de Discusion ===\n")

    analizador = AnalizadorHiloDiscusion()
    analizador.cargar_hilo(HILO_IA_DEMO)

    resumen = analizador.resumen_hilo()
    print("--- Resumen del Hilo ---")
    print(f"  Mensajes: {resumen['total_mensajes']}")
    print(f"  Participantes: {resumen['participantes']}")
    print(f"  Tono general: {resumen['tono']} ({resumen['sentimiento_promedio']:+.3f})")
    print(f"  Positivos: {resumen['positivos_pct']:.0f}% | Negativos: {resumen['negativos_pct']:.0f}%")
    print(f"  Hashtags: {resumen['hashtags_top']}")
    print(f"  Mas activos: {resumen['usuarios_activos']}")

    print("\n--- Evolucion del Sentimiento ---")
    for item in analizador.evolucion_sentimiento(ventana=3):
        barra = "+" * int(max(0, item["tendencia"] * 10))
        barra += "-" * int(max(0, -item["tendencia"] * 10))
        print(
            f"  Msg {item['posicion']:>2}: [{item['sentimiento_puntual']:+.2f}] "
            f"tendencia: {item['tendencia']:+.3f} |{barra}"
        )

    print("\n--- Subtemas Detectados ---")
    subtemas = analizador.detectar_subtemas(n_clusters=3)
    for cluster_id, info in subtemas.items():
        print(f"  Subtema {cluster_id + 1} ({info['n_mensajes']} msgs): {info['keywords']}")
    print()


def ejecutar_ac5() -> None:
    print("=== AC-5: Comparacion Booleano vs. Vectorial ===\n")

    comparador = ComparadorModelos(NOTICIAS_COMPLEMENTARIAS)
    print(comparador.reporte(CONSULTAS_EVAL_AC5))
    print()


def ejecutar_ac6() -> None:
    print("=== AC-6: Chatbot con Memoria de Contexto ===\n")

    motor = MotorBusqueda()
    motor.indexar(NOTICIAS_COMPLEMENTARIAS)
    chatbot = ChatbotContextual(NOTICIAS_COMPLEMENTARIAS, motor)

    for pregunta in CONVERSACION_AC6:
        respuesta, tipo, confianza = chatbot.responder(pregunta)
        print(f"  Usuario: {pregunta}")
        print(f"  Bot [{tipo}][{confianza:.2f}]: {respuesta[:80]}...")
        print()

    stats = chatbot.estadisticas_sesion()
    print("Estadisticas de sesion:")
    print(f"  Interacciones: {stats['interacciones']}")
    print(f"  Temas de interes: {stats['temas_interes']}")
    print(f"  Tipos de respuesta: {dict(stats['tipos_respuesta'])}")
    print()


def ejecutar_ac7() -> None:
    print("=== AC-7: Enriquecimiento con Wikidata ===\n")

    kg = KnowledgeGraphSIMANW()
    noticias_kg = []
    for indice, noticia in enumerate(NOTICIAS_COMPLEMENTARIAS, start=1):
        sentimiento = noticia.get("sentimiento", {}).copy()
        sentimiento.setdefault("compound", 0.0)
        noticia_kg = {
            **noticia,
            "fecha": f"2026-05-{10 - indice:02d}",
            "autor": f"Autor {indice}",
            "fuente": "Demo complementaria",
            "url": f"https://ejemplo.test/noticia/{indice}",
            "sentimiento": sentimiento,
        }
        noticias_kg.append(noticia_kg)
    kg.construir_desde_noticias(noticias_kg)

    triples_antes = kg.total_triples()
    enriquecedor = enriquecer_categorias_demo(kg)

    print(f"Triples antes del enriquecimiento: {triples_antes}")
    print(f"Triples totales tras enriquecimiento: {kg.total_triples()}")
    print(f"Enlaces externos creados: {len(enriquecedor.enlaces_externos)}")

    print("\nEnlaces locales - Wikidata:")
    for enlace in enriquecedor.consulta_enriquecimiento():
        local_short = str(enlace.local).split("/")[-1]
        externo_short = str(enlace.externo).split("/")[-1]
        print(f"  {local_short} - {externo_short} ({enlace.etiqueta})")

    print("\nQuery sugerida para Wikidata (tecnologia):")
    print(enriquecedor.generar_query_wikidata("tecnologia"))
    print()


def _noticias_ac8_demo() -> list[dict]:
    base = {
        "titulo": "Avances en inteligencia artificial generativa",
        "cuerpo": "La inteligencia artificial generativa transforma procesos de software, educacion y analisis de datos.",
        "fecha": "2026-05-10",
        "autor": "Maria Garcia",
        "categoria_original": "tecnologia",
        "url": "https://demo.test/noticias/ia",
        "fuente": "https://demo.test",
    }
    return [
        base,
        {**base, "titulo": "Mercados reaccionan a nuevas tasas", "url": "https://demo.test/noticias/economia"},
        {**base, "titulo": "", "url": "https://demo.test/noticias/sin-titulo"},
        {**base, "titulo": "Cuerpo corto", "cuerpo": "corto", "url": "https://demo.test/noticias/corto"},
        {**base, "titulo": "Fecha invalida", "fecha": "25/05/2026", "url": "https://demo.test/noticias/fecha"},
        {**base, "titulo": "Duplicado URL", "url": "https://demo.test/noticias/ia"},
        {**base, "url": "https://demo.test/noticias/ia-copia"},
    ]


def ejecutar_ac8() -> None:
    print("=== AC-8: Control de Calidad del Corpus ===\n")
    control = ControlCalidadCorpus()
    depurado = control.validar(_noticias_ac8_demo())
    ruta = control.guardar_informe("data/ac8_informe_calidad.json")

    informe = control.generar_informe()
    print(f"Total registros: {informe['total_registros']}")
    print(f"Validos: {informe['registros_validos']} | Rechazados: {informe['registros_rechazados']}")
    print(f"Duplicados URL: {informe['duplicados_exactos_url']}")
    print(f"Duplicados por titulo: {informe['duplicados_casi_identicos_titulo']}")
    print(f"Corpus depurado disponible en memoria: {len(depurado)} noticias")
    print(f"Informe generado: {ruta}")
    print(control.parrafo_resumen())
    print()


def ejecutar_ac9() -> None:
    print("=== AC-9: Linea de Tiempo y Tendencias por Tema ===\n")
    print("Granularidad: mensual")
    print("Justificacion: el corpus abarca varios meses; el mes ofrece periodos")
    print("suficientes sin fragmentar un corpus de tamano medio.\n")

    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(NOTICIAS_AC9_DEMO)

    print("--- Visualizacion ASCII (noticias por categoria y mes) ---")
    print(analizador.visualizacion_texto())
    print()

    print("--- Tabla Resumen ---")
    print(f"{'Categoria':<15} {'Periodo':<12} {'Noticias':>8}")
    print("-" * 38)
    for fila in analizador.tabla_resumen():
        print(f"  {fila['categoria']:<13} {fila['periodo']:<12} {fila['noticias']:>8}")

    ruta = analizador.exportar_csv("data/ac9_tendencias.csv")
    print(f"\n  Tabla exportada: {ruta}")

    pico = analizador.pico_notable()
    print(f"\n--- Pico Notable ---")
    print(f"  Categoria: {pico['categoria']} | Periodo: {pico['periodo']} | Noticias: {pico['count']}")
    for titulo in pico["titulos"][:3]:
        print(f"  - {titulo[:65]}")

    conteos = analizador.conteo_por_periodo()
    categorias_top = sorted(conteos, key=lambda c: sum(conteos[c].values()), reverse=True)[:3]
    print("\n--- Tendencias de Terminos (primer vs. ultimo periodo) ---")
    for cat in categorias_top:
        tend = analizador.tendencia_terminos(cat)
        if tend["aumentan"] or tend["disminuyen"]:
            print(f"\n  [{cat}]  {tend['primer_periodo']} -> {tend['ultimo_periodo']}")
            print(f"  Aumentan  : {tend['aumentan'][:4]}")
            print(f"  Disminuyen: {tend['disminuyen'][:4]}")

    print()
    print(analizador.conclusion())
    print()


def ejecutar_ac10() -> None:
    print("=== AC-10: Alertas por Consulta Guardada ===\n")
    sistema = SistemaAlertasConsulta(consultas_demo())
    sistema.guardar_consultas("data/ac10_consultas_guardadas.json")

    sin_nuevas = sistema.procesar_noticias_nuevas([])
    con_nuevas = sistema.procesar_noticias_nuevas(noticias_nuevas_demo(), "2026-05-25T12:00:00Z")
    repetidas = sistema.procesar_noticias_nuevas(noticias_nuevas_demo(), "2026-05-25T12:05:00Z")
    sistema.guardar_historial("data/ac10_historial_alertas.json")

    print(f"Consultas persistidas: {len(sistema.consultas)}")
    print(f"Ejecucion sin noticias nuevas: {len(sin_nuevas)} alertas")
    print(f"Ejecucion con cinco noticias nuevas: {len(con_nuevas)} alertas")
    print(f"Reprocesamiento de las mismas noticias: {len(repetidas)} alertas duplicadas")
    print(sistema.documentar_deduplicacion())
    print()


def ejecutar_ac11() -> None:
    print("=== AC-11: Estudio de Usabilidad ===\n")
    estudio = estudio_demo()
    ruta = estudio.exportar_csv("data/ac11_resultados_usabilidad.csv")

    print("Tareas del guion:")
    for idx, tarea in enumerate(estudio.tareas, start=1):
        print(f"  {idx}. {tarea}")
    print("\nPromedios del cuestionario:")
    for item, promedio in estudio.promedios().items():
        print(f"  {item}: {promedio}")
    print("\nProblemas y mejoras:")
    for item in estudio.problemas_y_mejoras():
        print(f"  - {item['problema']} -> {item['mejora']}")
    print(f"\nResultados exportados: {ruta}")
    print(estudio.reflexion_consentimiento())
    print()


def ejecutar_ac12() -> None:
    print("=== AC-12: Trazabilidad y Reproducibilidad ===\n")
    traza = trazabilidad_demo()
    archivos = {
        "rastreo_paginado": "data/ac1_noticias_paginadas.json",
        "calidad": "data/ac8_informe_calidad.json",
        "tendencias": "data/ac9_tendencias.csv",
        "consultas_guardadas": "data/ac10_consultas_guardadas.json",
        "historial_alertas": "data/ac10_historial_alertas.json",
        "usabilidad": "data/ac11_resultados_usabilidad.csv",
    }
    ruta_manifest = traza.guardar_manifiesto("data/ac12_manifiesto.json", archivos)
    ruta_log = traza.guardar_log_jsonl("data/ac12_log.jsonl")

    print(f"Manifiesto: {ruta_manifest}")
    print(f"Log estructurado: {ruta_log}")
    print(traza.procedimiento_reproducible())
    print("\nChecklist:")
    print(traza.checklist_firmado("Alumno SIMANW"))
    print("\nAnexo de limitaciones:")
    print(traza.anexo_limitaciones())
    print()


def ejecutar_ac13() -> None:
    print("=== AC-13: Publicacion Semantica y Validacion RDF ===\n")
    kg = KnowledgeGraphSIMANW()
    noticias_kg = []
    for indice, noticia in enumerate(NOTICIAS_AC9_DEMO[:6], start=1):
        noticias_kg.append(
            {
                **noticia,
                "autor": f"Autor {indice % 3}",
                "fuente": "https://demo.test",
                "url": f"https://demo.test/kg/{indice}",
                "sentimiento": {
                    "etiqueta": "positivo" if indice % 2 else "negativo",
                    "compound": 0.4 if indice % 2 else -0.3,
                },
            }
        )
    kg.construir_desde_noticias(noticias_kg)
    enlaces = kg.agregar_enlaces_externos_basicos()
    rutas = kg.exportar_rdf("data/ac13_simanw")
    validacion = kg.validar_formas()

    print(f"Triples RDF: {kg.total_triples()}")
    print(f"Exportaciones: {rutas['turtle']} y {rutas['json-ld']}")
    print(f"Enlaces externos documentados: {len(enlaces)}")
    print(f"Validacion conforme: {validacion['conforme']} | Violaciones: {len(validacion['violaciones'])}")
    print("\nConsultas SPARQL propias:")
    for nombre, query in [
        ("Autores productivos", QUERY_AC13_AUTORES_PRODUCTIVOS),
        ("Sentimiento por categoria", QUERY_AC13_SENTIMIENTO_POR_CATEGORIA),
        ("Noticias negativas recientes", QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS),
    ]:
        print(f"  {nombre}: {len(kg.consultar(query))} fila(s)")
    print("\nFragmento JSON-LD de ejemplo:")
    print(kg.fragmento_jsonld_noticia(1))
    print("\nReutilizacion externa:")
    print(kg.nota_reutilizacion_datos())
    print()


def main() -> None:
    ejecutar_ac1()
    ejecutar_ac2()
    ejecutar_ac3()
    ejecutar_ac4()
    ejecutar_ac5()
    ejecutar_ac6()
    ejecutar_ac7()
    ejecutar_ac8()
    ejecutar_ac9()
    ejecutar_ac10()
    ejecutar_ac11()
    ejecutar_ac12()
    ejecutar_ac13()


if __name__ == "__main__":
    main()
