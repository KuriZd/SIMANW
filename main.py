from collections import Counter

from src.busqueda_natural import BusquedaNatural
from src.chatbot_qa import ChatbotSIMANW, SistemaQA
from src.clasificador_noticias import (
    ETIQUETAS_ENTRENAMIENTO,
    TEXTOS_ENTRENAMIENTO,
    ClasificadorNoticias,
)
from src.control_rastreo import ControlRastreo
from src.detector_publicidad import DetectorTemasPublicidad
from src.evaluador_irs import EvaluadorIRS
from src.exportador import ExportadorNoticias
from src.extractor import ExtractorNoticias
from src.html_demo import html_portal_noticias
from src.knowledge_graph import (
    QUERY_AUTORES_PRODUCTIVIDAD,
    QUERY_CONTEO_CATEGORIA,
    QUERY_DBPEDIA_HERRAMIENTAS_NLP,
    QUERY_NOTICIAS_METADATA,
    QUERY_SENTIMIENTO_NEGATIVO,
    QUERY_WIKIDATA_SOFTWARE_IA_PYTHON,
    ConectorDatosAbiertos,
    KnowledgeGraphSIMANW,
    cargar_datasets_demo,
    endpoints_sparql_disponibles,
)
from src.motor_busqueda import MotorBusqueda
from src.parser_dom import analizar_dom
from src.pipeline_nlp import PipelineNLP
from src.recomendacion import SistemaRecomendacion
from src.representacion_vectorial import RepresentacionVectorial
from src.reportes import GeneradorReportes, resumen_pipeline_completo
from src.sentimientos import AnalizadorSentimientos
from src.similitud import CalculadorSimilitud


def ejecutar_parser_dom() -> None:
    print("=== FASE 1.1: Parsing del DOM ===\n")
    resultado = analizar_dom(html_portal_noticias)

    print(f"Título del portal: {resultado['titulo_portal']}")
    print(f"Secciones de navegación: {resultado['navegacion']}")
    print(f"Total de artículos: {resultado['total_articulos']}")
    print(f"Tendencias: {resultado['tendencias']}")
    print(f"Estructura detectada: {resultado['estructura']}\n")


def ejecutar_extraccion() -> list[dict]:
    print("=== FASE 1.2: Extracción de Noticias ===\n")

    extractor = ExtractorNoticias()
    noticias = extractor.extraer_de_html(
        html_portal_noticias,
        url_base="https://portal-noticias.com",
    )
    resumen = extractor.resumen_extraccion()

    print(f"Noticias extraídas: {resumen['total_extraidas']}")
    print(f"Errores: {resumen['errores']}")
    print(f"Categorías encontradas: {resumen['categorias']}")
    print(f"Rango de fechas: {resumen['rango_fechas']}\n")

    for indice, noticia in enumerate(noticias, start=1):
        print(f"{indice}. [{noticia['fecha']}] [{noticia['categoria_original']}] {noticia['titulo']}")
        print(f"   Autor: {noticia['autor']}")
        print(f"   URL: {noticia['url']}\n")

    if resumen["detalle_errores"]:
        print("Errores encontrados:")
        for error in resumen["detalle_errores"]:
            print(f"- {error}")

    return noticias


def ejecutar_control_rastreo() -> None:
    print("=== FASE 1.3: Control de Rastreo ===\n")

    control = ControlRastreo(
        "https://portal-noticias.com/noticias/",
        modo="directorio",
        max_paginas=10,
        delay=2,
    )

    enlaces_descubiertos = [
        "/noticias/pagina/2",
        "/noticias/tecnologia/ia-2026",
        "/deportes/futbol-liga",
        "https://otro-sitio.com/articulo",
        "/noticias/economia/mercados",
        "/noticias/ciencia/clima",
        "/contacto",
    ]

    agregados = control.agregar_enlaces(enlaces_descubiertos)
    print(f"URL semilla: {control.url_semilla}")
    print(f"Modo: {control.modo}")
    print(f"Máximo de páginas: {control.max_paginas}")
    print(f"Delay entre peticiones: {control.delay}s")
    print(f"Enlaces descubiertos: {len(enlaces_descubiertos)}")
    print(f"Agregados a cola: {agregados}")
    print(f"Rechazados: {len(control.rechazadas)}\n")

    print("Simulación de rastreo:")
    while True:
        url = control.siguiente()
        if url is None:
            break
        print(f"Visitando: {url}")

    print(f"\nEstado final: {control.estado()}\n")


def ejecutar_exportacion(noticias: list[dict]) -> None:
    print("=== FASE 1.4: Exportación de Datos ===\n")

    exportador = ExportadorNoticias("data")
    ruta_json = exportador.guardar_json(noticias)
    ruta_csv = exportador.guardar_csv(noticias)

    print(f"Archivo JSON generado: {ruta_json}")
    print(f"Archivo CSV generado: {ruta_csv}\n")


def ejecutar_pipeline_nlp(noticias: list[dict]) -> list[dict]:
    print("=== FASE 2.1: Pipeline NLP ===\n")
    print("Procesando noticias extraidas...\n")

    pipeline = PipelineNLP()
    noticias_procesadas = pipeline.procesar_noticias(noticias)

    for noticia in noticias:
        resultado = noticia["nlp"]
        print(f"  [{noticia['categoria_original']}] {noticia['titulo'][:50]}...")
        print(
            "    Tokens: "
            f"{len(resultado['tokens'])}  "
            f"Sin SW: {len(resultado['sin_stopwords'])}  "
            f"Stems: {len(resultado['stems'])}"
        )
        print(f"    Riqueza lexica: {resultado['riqueza_lexica']:.3f}\n")

    stats = pipeline.estadisticas_corpus(noticias_procesadas)
    print("--- Estadisticas del Corpus ---")
    for clave, valor in stats.items():
        if clave != "palabras_frecuentes":
            print(f"  {clave}: {valor}")

    print("\n  Palabras mas frecuentes:")
    for palabra, frecuencia in stats["palabras_frecuentes"]:
        print(f"    '{palabra}': {frecuencia}")
    print()

    return noticias_procesadas


def ejecutar_representacion_vectorial(noticias: list[dict]) -> RepresentacionVectorial:
    print("=== FASE 2.2: Representacion Vectorial TF-IDF ===\n")

    textos_para_vectorizar = [" ".join(noticia["nlp"]["sin_stopwords"]) for noticia in noticias]
    representacion = RepresentacionVectorial()
    representacion.construir_matriz(textos_para_vectorizar)

    info = representacion.info_matriz()
    print(f"Matriz TF-IDF: {info['documentos']} docs  {info['features']} features")
    print(f"Densidad: {info['densidad']:.4f}")
    print(f"Terminos promedio por documento: {info['terminos_promedio_doc']:.1f}")
    print(f"\nVocabulario (muestra): {list(representacion.vocabulario()[:15])}")

    print("\nTerminos mas relevantes por noticia:")
    for indice, noticia in enumerate(noticias):
        print(f"\n  [{noticia['categoria_original']}] {noticia['titulo'][:45]}...")
        for termino, peso in representacion.top_terminos_documento(indice, n=5):
            print(f"    {termino:<20} = {peso:.4f}")
    print()

    return representacion


def ejecutar_similitud(noticias: list[dict], representacion: RepresentacionVectorial) -> CalculadorSimilitud:
    print("=== FASE 2.3: Similitud entre Noticias ===\n")

    calculador = CalculadorSimilitud(representacion.matriz)

    print("Matriz de similitud coseno:")
    print(f"{'':>5}", end="")
    for indice in range(len(noticias)):
        print(f"{'N' + str(indice + 1):>7}", end="")
    print()

    for fila in range(len(noticias)):
        print(f"N{fila + 1:>3}", end=" ")
        for columna in range(len(noticias)):
            print(f"{calculador.similitud_par(fila, columna):>7.3f}", end="")
        print()

    print("\nNoticias mas similares entre si:")
    for indice, noticia in enumerate(noticias):
        similares = calculador.documentos_similares(indice, top_n=1)
        if similares:
            similar_idx, similitud = similares[0]
            if similitud > 0.05:
                print(f"  N{indice + 1}  N{similar_idx + 1} (sim={similitud:.3f})")
                print(f"    '{noticia['titulo'][:40]}...'")
                print(f"    '{noticias[similar_idx]['titulo'][:40]}...'")

    print("\nGrupos tematicos detectados:")
    grupos = calculador.agrupar_por_similitud(umbral=0.1)
    for grupo_idx, grupo in enumerate(grupos):
        print(f"  Grupo {grupo_idx + 1}: {['N' + str(indice + 1) for indice in grupo]}")
        for indice in grupo:
            print(f"    - {noticias[indice]['titulo'][:50]}")
    print()

    return calculador


def ejecutar_clasificador(noticias: list[dict]) -> ClasificadorNoticias:
    print("=== FASE 3.1: Clasificador de Noticias ===\n")

    clasificador = ClasificadorNoticias()
    resultado = clasificador.entrenar(TEXTOS_ENTRENAMIENTO, ETIQUETAS_ENTRENAMIENTO)

    print("Entrenamiento completado:")
    print(f"  Muestras: {resultado['n_muestras']}")
    print(f"  Categorias: {resultado['categorias']}")
    print(f"  Accuracy (CV): {resultado['accuracy_cv']:.3f}")

    print("\nClasificacion automatica de noticias del SIMANW:")
    clasificador.clasificar_noticias(noticias)

    for noticia in noticias:
        print(f"\n  Titulo: {noticia['titulo'][:55]}...")
        print(
            "  Cat. original: "
            f"{noticia['categoria_original']} | "
            f"Predicha: {noticia['categoria_predicha']}"
        )
        top_scores = sorted(noticia["scores_categoria"].items(), key=lambda item: item[1], reverse=True)[:3]
        print(f"  Scores: {', '.join(f'{categoria}={score:.2f}' for categoria, score in top_scores)}")
    print()

    return clasificador


def ejecutar_sentimientos(noticias: list[dict]) -> AnalizadorSentimientos:
    print("=== FASE 3.2: Analisis de Sentimientos ===\n")

    analizador = AnalizadorSentimientos()
    resultados, resumen = analizador.analizar_noticias(noticias)

    for noticia, sentimiento in zip(noticias, resultados):
        print(f"  [{sentimiento['compound']:+.3f}] {noticia['titulo'][:55]} ({sentimiento['etiqueta']})")

    print("\n--- Resumen de Sentimiento del Corpus ---")
    print(f"  Distribucion: {resumen['distribucion']}")
    print(f"  Promedio: {resumen['sentimiento_promedio']:+.3f}")
    print(f"  Tono general: {resumen['tono_general'].upper()}\n")

    return analizador


def ejecutar_recomendacion(noticias: list[dict], calculador: CalculadorSimilitud) -> SistemaRecomendacion:
    print("=== FASE 3.3: Sistema de Recomendacion ===\n")

    recomendador = SistemaRecomendacion(noticias, calculador.sim_matrix)

    print("Si leiste esta noticia, te recomendamos:")
    for indice, noticia in enumerate(noticias):
        recomendaciones = recomendador.recomendar(indice, top_n=2)
        print(f"\n  Leiste: '{noticia['titulo'][:50]}...'")
        for recomendada_idx, similitud in recomendaciones:
            print(f"     [{similitud:.3f}] {noticias[recomendada_idx]['titulo'][:50]}...")

    print("\n\nRecomendacion por perfil (si leyo noticias 1 y 4 - tecnologia):")
    for indice, score in recomendador.recomendar_por_perfil([0, 3], top_n=2):
        print(f"   [{score:.3f}] {noticias[indice]['titulo'][:55]}")
    print()

    return recomendador


def ejecutar_detector_publicidad() -> DetectorTemasPublicidad:
    print("=== FASE 3.4: Deteccion de Temas + Publicidad ===\n")

    detector = DetectorTemasPublicidad()
    conversacion = [
        ("Laura", "Vieron la noticia sobre la nueva IA de Google?"),
        ("Miguel", "Si, dicen que puede programar mejor que muchos desarrolladores"),
        ("Laura", "Me preocupa el futuro del trabajo en tecnologia"),
        ("Roberto", "Yo creo que es una oportunidad, hay que aprender machine learning"),
        ("Miguel", "Cambiando de tema, como ven la economia este trimestre?"),
        ("Laura", "Los mercados estan muy volatiles, mis inversiones bajaron"),
        ("Roberto", "El banco central anuncio que subira las tasas de interes"),
        ("Miguel", "Mejor hay que diversificar, quiza invertir en fondos indexados"),
    ]

    print("Simulacion de chat con publicidad dirigida:")
    resultados = detector.simular_chat(conversacion)

    for resultado in resultados:
        print(f"  [{resultado['usuario']}]: {resultado['mensaje']}")
        print(f"    Tema: {resultado['tema'].upper()} (confianza: {resultado['confianza']:.3f})")
        print(f"    Ad: {resultado['publicidad']}\n")

    temas = Counter(resultado["tema"] for resultado in resultados)
    print(f"Resumen de temas en la conversacion: {dict(temas)}\n")

    return detector


def ejecutar_motor_busqueda(noticias: list[dict]) -> MotorBusqueda:
    print("=== FASE 4.1: Motor de Busqueda ===\n")

    motor = MotorBusqueda()
    motor.indexar(noticias)
    info = motor.info_indice()

    print("Indice construido:")
    print(f"  Documentos: {info['documentos_indexados']}")
    print(f"  Terminos unicos: {info['terminos_en_indice']}")
    print(f"  Postings promedio: {info['tamano_promedio_posting']:.2f}")

    consultas = [
        "inteligencia artificial tecnologia",
        "mercados financieros economia",
        "datos abiertos gobierno semantica",
        "Python programacion desarrollo",
        "cambio climatico investigacion cientifica",
    ]

    print("\n--- Resultados de Busqueda ---")
    for consulta in consultas:
        resultados = motor.buscar_vectorial(consulta, top_k=2)
        print(f"\n  Consulta: '{consulta}'")
        for resultado in resultados:
            print(f"    [{resultado['relevancia']:.3f}] {resultado['titulo'][:50]}...")
            print(f"      Cat: {resultado['categoria']} | Sent: {resultado['sentimiento']}")
    print()

    return motor


def ejecutar_evaluacion_busqueda(noticias: list[dict]) -> EvaluadorIRS:
    print("=== FASE 4.2: Evaluacion del Motor de Busqueda ===\n")

    evaluador = EvaluadorIRS()
    evaluaciones = [
        {"consulta": "inteligencia artificial", "relevantes": [0, 3], "recuperados": [0, 3, 1]},
        {"consulta": "economia mercados", "relevantes": [1], "recuperados": [1, 4, 2]},
        {"consulta": "datos gobierno", "relevantes": [4], "recuperados": [4, 2]},
    ]

    print(f"{'Consulta':<25} {'Precision':>10} {'Recall':>10} {'F1':>10} {'AP':>10}")
    print("-" * 67)

    for evaluacion in evaluaciones:
        metricas = evaluador.evaluar_consulta(
            evaluacion["recuperados"],
            evaluacion["relevantes"],
            len(noticias),
        )
        print(
            f"{evaluacion['consulta']:<25} "
            f"{metricas['precision']:>10.3f} "
            f"{metricas['recall']:>10.3f} "
            f"{metricas['f1']:>10.3f} "
            f"{metricas['average_precision']:>10.3f}"
        )

    map_score = evaluador.mean_average_precision(evaluaciones)
    print(f"\n  MAP (Mean Average Precision): {map_score:.3f}")

    print("\n--- Precision@K para 'inteligencia artificial' ---")
    ranking = [0, 3, 1, 2, 4]
    relevantes = [0, 3]
    for k in range(1, 6):
        pk = evaluador.precision_at_k(ranking, relevantes, k)
        print(f"  P@{k} = {pk:.3f}")
    print()

    return evaluador


def ejecutar_busqueda_natural(motor: MotorBusqueda) -> BusquedaNatural:
    print("=== FASE 4.3: Busqueda en Lenguaje Natural ===\n")

    busqueda_nl = BusquedaNatural(motor)
    consultas = [
        "Muestrame noticias positivas sobre tecnologia",
        "Que noticias hay sobre datos del gobierno?",
        "Busco informacion preocupante sobre el clima",
        "Hay algo nuevo de programacion en Python?",
    ]

    for consulta in consultas:
        resultados = busqueda_nl.buscar_natural(consulta, top_k=2)
        print(f'  Usuario: "{consulta}"')
        if resultados:
            for resultado in resultados:
                print(f"     [{resultado['relevancia']:.3f}] {resultado['titulo'][:50]}...")
        else:
            print("     Sin resultados relevantes")
        print()

    return busqueda_nl


def ejecutar_chatbot(noticias: list[dict]) -> ChatbotSIMANW:
    print("=== FASE 5.1: Chatbot del SIMANW ===\n")

    chatbot = ChatbotSIMANW(noticias)
    preguntas_usuario = [
        "Que noticias hay sobre inteligencia artificial?",
        "Cual es el tono de la noticia de los mercados financieros?",
        "Hay algo sobre datos abiertos del gobierno?",
        "Que noticias de tecnologia tienen sentimiento positivo?",
        "Cual es la capital de Francia?",
    ]

    for pregunta in preguntas_usuario:
        respuesta, confianza = chatbot.responder(pregunta)
        print(f"  Usuario: {pregunta}")
        print(f"  Bot [{confianza:.3f}]: {respuesta[:100]}...")
        print()

    print(f"Resumen: {chatbot.resumen_interaccion()}\n")
    return chatbot


def ejecutar_sistema_qa(noticias: list[dict], motor: MotorBusqueda) -> SistemaQA:
    print("=== FASE 5.2: Sistema Question/Answering ===\n")

    qa_system = SistemaQA(noticias, motor)
    preguntas_qa = [
        "Cuantas noticias tienes?",
        "Cual es el sentimiento general de las noticias?",
        "Que categorias de noticias hay?",
        "Dame un resumen de las noticias",
        "Recomiendame algo sobre tecnologia",
        "Que dice la noticia sobre Python?",
    ]

    for pregunta in preguntas_qa:
        respuesta, tipo, confianza = qa_system.conversar(pregunta)
        print(f"  Pregunta: {pregunta}")
        print(f"  [{tipo}][{confianza:.2f}] {respuesta[:120]}")
        print()

    return qa_system


def ejecutar_knowledge_graph(noticias: list[dict]) -> KnowledgeGraphSIMANW:
    print("=== FASE 6.1: Knowledge Graph ===\n")

    kg = KnowledgeGraphSIMANW()
    kg.construir_desde_noticias(noticias)

    print("Knowledge Graph construido:")
    print(f"  Total de triples: {kg.total_triples()}")
    print(f"  Noticias almacenadas: {len(noticias)}")

    print("\nOntologia (fragmento en Turtle):")
    turtle = kg.serializar("turtle")
    lineas = [linea for linea in turtle.split("\n") if linea.strip()][:25]
    for linea in lineas:
        print(f"  {linea}")
    print()

    return kg


def ejecutar_consultas_sparql(kg: KnowledgeGraphSIMANW) -> None:
    print("=== FASE 6.2: Consultas SPARQL ===\n")

    print("Consulta 1: Noticias con metadatos")
    print("-" * 60)
    for row in kg.consultar(QUERY_NOTICIAS_METADATA):
        print(f"  [{row.fecha}] [{row.categoria}] {str(row.titulo)[:45]}... - {row.autor}")

    print("\nConsulta 2: Noticias con sentimiento negativo")
    print("-" * 60)
    for row in kg.consultar(QUERY_SENTIMIENTO_NEGATIVO):
        print(f"  [{float(row.score):+.3f}] {str(row.titulo)[:55]}")

    print("\nConsulta 3: Distribucion por categoria")
    print("-" * 60)
    for row in kg.consultar(QUERY_CONTEO_CATEGORIA):
        print(f"  {row.categoria}: {row.total} noticia(s)")

    print("\nConsulta 4: Productividad por autor")
    print("-" * 60)
    for row in kg.consultar(QUERY_AUTORES_PRODUCTIVIDAD):
        print(f"  {row.autor}: {row.publicaciones} publicacion(es)")
    print()


def ejecutar_datos_abiertos(kg: KnowledgeGraphSIMANW) -> ConectorDatosAbiertos:
    print("=== FASE 6.3: Datos Abiertos Integrados ===\n")

    conector = ConectorDatosAbiertos(kg)
    cargar_datasets_demo(conector)

    print(f"Triples totales en KG (con datos abiertos): {kg.total_triples()}")

    print("\nDatasets de datos abiertos cargados:")
    for row in conector.consultar_datos():
        print(f"  [{row.tema}] {row.titulo} - {row.publicador}")

    print("\nEnlaces noticias - datos abiertos:")
    enlaces = conector.enlazar_noticias_con_datos()
    if enlaces:
        for row in enlaces:
            print(f"  Noticia: {str(row.noticia_titulo)[:40]}...")
            print(f"  Dataset: {row.dataset_titulo}")
            print()
    else:
        print("  (Los enlaces se generan cuando las categorias coinciden con los temas)")
    print()

    return conector


def ejecutar_endpoints_sparql_externos() -> None:
    print("=== FASE 6.4: Endpoints SPARQL Externos ===\n")

    print("Consulta para Wikidata (software de IA en Python):")
    print(QUERY_WIKIDATA_SOFTWARE_IA_PYTHON)

    print("\nConsulta para DBpedia (herramientas NLP):")
    print(QUERY_DBPEDIA_HERRAMIENTAS_NLP)

    print("\nEndpoints SPARQL disponibles para el SIMANW:")
    for nombre, endpoint in endpoints_sparql_disponibles().items():
        print(f"  - {nombre}: {endpoint}")

    print("\n# Para ejecutar estas consultas se requiere internet y SPARQLWrapper.\n")


def ejecutar_reportes(noticias: list[dict], kg: KnowledgeGraphSIMANW) -> GeneradorReportes:
    print("=== FASE 7.1: Generador de Reportes ===\n")

    reportero = GeneradorReportes(noticias, kg)
    print(reportero.reporte_completo())
    print()
    return reportero


def ejecutar_integracion_final() -> None:
    print("=== FASE 7.2: Integracion Final ===")
    print(resumen_pipeline_completo())


def main() -> None:
    ejecutar_parser_dom()
    noticias = ejecutar_extraccion()
    ejecutar_control_rastreo()
    ejecutar_pipeline_nlp(noticias)
    representacion = ejecutar_representacion_vectorial(noticias)
    calculador = ejecutar_similitud(noticias, representacion)
    ejecutar_clasificador(noticias)
    ejecutar_sentimientos(noticias)
    ejecutar_recomendacion(noticias, calculador)
    ejecutar_detector_publicidad()
    motor = ejecutar_motor_busqueda(noticias)
    ejecutar_evaluacion_busqueda(noticias)
    ejecutar_busqueda_natural(motor)
    ejecutar_chatbot(noticias)
    ejecutar_sistema_qa(noticias, motor)
    kg = ejecutar_knowledge_graph(noticias)
    ejecutar_consultas_sparql(kg)
    ejecutar_datos_abiertos(kg)
    ejecutar_endpoints_sparql_externos()
    ejecutar_reportes(noticias, kg)
    ejecutar_integracion_final()
    ejecutar_exportacion(noticias)


if __name__ == "__main__":
    main()
