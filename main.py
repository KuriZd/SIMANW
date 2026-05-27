import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.busqueda_natural import BusquedaNatural
from src.control_calidad import ControlCalidadCorpus
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
from src.exportador import guardar_csv, guardar_json, guardar_markdown
from src.extractor import ExtractorNoticias
from src.html_demo import html_portal_noticias
from src.knowledge_graph import (
    QUERY_AUTORES_PRODUCTIVIDAD,
    QUERY_AC13_SENTIMIENTO_POR_CATEGORIA,
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
from src.rastreador_rss import RastreadorRSS
from src.recomendacion import SistemaRecomendacion
from src.representacion_vectorial import RepresentacionVectorial
from src.reportes import GeneradorReportes, resumen_pipeline_completo
from src.sentimientos import AnalizadorSentimientos
from src.similitud import CalculadorSimilitud
from src.tendencias_temporales import TendenciasTemporales
from src.trazabilidad import TrazabilidadPipeline


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


def ejecutar_control_calidad(noticias: list[dict]) -> list[dict]:
    print("=== AC-8: Control de Calidad del Corpus ===\n")

    ctrl = ControlCalidadCorpus()
    corpus_depurado = ctrl.validar(noticias)
    informe = ctrl.generar_informe()

    print(f"  Total registros       : {informe['total_registros']}")
    print(f"  Registros válidos     : {informe['registros_validos']}")
    print(f"  Registros rechazados  : {informe['registros_rechazados']}")
    print(f"  Inválidos/incompletos : {informe['invalidos_o_incompletos']}")
    print(f"  Duplicados exactos    : {informe['duplicados_exactos_url']}")
    print(f"  Duplicados similares  : {informe['duplicados_casi_identicos_titulo']}")

    if informe["detalle_rechazados"]:
        print("\n  Registros rechazados:")
        for entrada in informe["detalle_rechazados"]:
            print(f"    - '{entrada['titulo'][:50]}' → {'; '.join(entrada['motivos'])}")

    ruta = ctrl.guardar_informe("data/informe_calidad.json")
    print(f"\n  Informe guardado en: {ruta}")
    print(f"\n  Resumen:\n  {ctrl.parrafo_resumen()}\n")

    return corpus_depurado


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


def seleccionar_consultas_fase4(consultas_demo: list[str], usar_predefinidas: bool = False) -> list[str]:
    if usar_predefinidas:
        return consultas_demo

    while True:
        opcion = input("Usar consultas predefinidas de fase 4? (Y/N): ").strip().upper()
        if opcion in {"Y", "N"}:
            break
        print("Opcion no valida. Presiona Y para usar el arreglo o N para ingresar una consulta.")

    if opcion == "Y":
        return consultas_demo

    while True:
        consulta = input("Ingresa tu consulta de busqueda: ").strip()
        if consulta:
            return [consulta]
        print("La consulta no puede estar vacia.")


def seleccionar_preguntas_fase5(preguntas_demo: list[str], usar_predefinidas: bool = False) -> list[str]:
    if usar_predefinidas:
        return preguntas_demo

    while True:
        opcion = input("Usar preguntas predefinidas de fase 5? (Y/N): ").strip().upper()
        if opcion in {"Y", "N"}:
            break
        print("Opcion no valida. Presiona Y para usar el arreglo o N para ingresar una pregunta.")

    if opcion == "Y":
        return preguntas_demo

    preguntas = []
    while True:
        pregunta = input("Ingresa tu pregunta o presiona S para continuar: ").strip()
        if pregunta.upper() == "S":
            return preguntas
        if pregunta:
            preguntas.append(pregunta)
            continue
        print("La pregunta no puede estar vacia.")


def ejecutar_motor_busqueda(noticias: list[dict], usar_predefinidas: bool = False) -> MotorBusqueda:
    print("=== FASE 4.1: Motor de Busqueda ===\n")

    motor = MotorBusqueda()
    motor.indexar(noticias)
    info = motor.info_indice()

    print("Indice construido:")
    print(f"  Documentos: {info['documentos_indexados']}")
    print(f"  Terminos unicos: {info['terminos_en_indice']}")
    print(f"  Postings promedio: {info['tamano_promedio_posting']:.2f}")

    consultas = seleccionar_consultas_fase4([
        "inteligencia artificial tecnologia",
        "mercados financieros economia",
        "datos abiertos gobierno semantica",
        "Python programacion desarrollo",
        "cambio climatico investigacion cientifica",
    ], usar_predefinidas=usar_predefinidas)

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


def ejecutar_busqueda_natural(motor: MotorBusqueda, usar_predefinidas: bool = False) -> BusquedaNatural:
    print("=== FASE 4.3: Busqueda en Lenguaje Natural ===\n")

    busqueda_nl = BusquedaNatural(motor)
    consultas = seleccionar_consultas_fase4([
        "Muestrame noticias positivas sobre tecnologia",
        "Que noticias hay sobre datos del gobierno?",
        "Busco informacion preocupante sobre el clima",
        "Hay algo nuevo de programacion en Python?",
    ], usar_predefinidas=usar_predefinidas)

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


def ejecutar_chatbot(noticias: list[dict], usar_predefinidas: bool = False) -> ChatbotSIMANW:
    print("=== FASE 5.1: Chatbot del SIMANW ===\n")

    chatbot = ChatbotSIMANW(noticias)
    preguntas_usuario = seleccionar_preguntas_fase5([
        "Que noticias hay sobre inteligencia artificial?",
        "Cual es el tono de la noticia de los mercados financieros?",
        "Hay algo sobre datos abiertos del gobierno?",
        "Que noticias de tecnologia tienen sentimiento positivo?",
        "Cual es la capital de Francia?",
    ], usar_predefinidas=usar_predefinidas)

    for pregunta in preguntas_usuario:
        respuesta, confianza = chatbot.responder(pregunta)
        print(f"  Usuario: {pregunta}")
        print(f"  Bot [{confianza:.3f}]: {respuesta[:100]}...")
        print()

    print(f"Resumen: {chatbot.resumen_interaccion()}\n")
    return chatbot


def ejecutar_sistema_qa(noticias: list[dict], motor: MotorBusqueda, usar_predefinidas: bool = False) -> SistemaQA:
    print("=== FASE 5.2: Sistema Question/Answering ===\n")

    qa_system = SistemaQA(noticias, motor)
    preguntas_qa = seleccionar_preguntas_fase5([
        "Cuantas noticias tienes?",
        "Cual es el sentimiento general de las noticias?",
        "Que categorias de noticias hay?",
        "Dame un resumen de las noticias",
        "Recomiendame algo sobre tecnologia",
        "Que dice la noticia sobre Python?",
    ], usar_predefinidas=usar_predefinidas)

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline reproducible SIMANW")
    parser.add_argument("--source", choices=["demo", "rss", "archivo"], default="demo")
    parser.add_argument("--url", help="URL RSS cuando --source rss")
    parser.add_argument("--input", help="Archivo JSON cuando --source archivo")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Permite capturar consultas manuales. Por defecto usa preguntas demo para reproducibilidad.",
    )
    return parser.parse_args()


def cargar_noticias_configuradas(args: argparse.Namespace) -> list[dict]:
    if args.source == "demo":
        ejecutar_parser_dom()
        noticias = ejecutar_extraccion()
        ejecutar_control_rastreo()
        return [_normalizar_noticia(noticia, idx) for idx, noticia in enumerate(noticias, start=1)]

    if args.source == "rss":
        if not args.url:
            raise ValueError("Debes proporcionar --url cuando usas --source rss")
        rastreador = RastreadorRSS(args.url, max_noticias=25)
        noticias = rastreador.extraer()
        if not noticias:
            raise ValueError(f"No se extrajeron noticias RSS: {rastreador.errores}")
        print(f"Noticias RSS extraidas: {len(noticias)} desde {args.url}")
        return [_normalizar_noticia(noticia, idx) for idx, noticia in enumerate(noticias, start=1)]

    if not args.input:
        raise ValueError("Debes proporcionar --input cuando usas --source archivo")
    ruta = Path(args.input)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, list):
        raise ValueError("El archivo JSON debe contener una lista de noticias")
    print(f"Noticias cargadas desde archivo: {len(datos)} ({ruta})")
    return [_normalizar_noticia(noticia, idx) for idx, noticia in enumerate(datos, start=1)]


def guardar_salidas_iniciales(noticias_raw: list[dict]) -> dict[str, str]:
    rutas = {
        "raw_json": guardar_json(noticias_raw, "data/raw/noticias.json"),
        "raw_csv": guardar_csv(noticias_raw, "data/raw/noticias.csv"),
    }
    return {clave: str(ruta) for clave, ruta in rutas.items()}


def ejecutar_tendencias(noticias: list[dict]) -> dict:
    print("=== AC-9: Tendencias Temporales ===\n")
    tendencias = TendenciasTemporales(granularidad="mes")
    tendencias.cargar_noticias(noticias)
    ruta_csv = tendencias.exportar_csv("outputs/tendencias.csv")
    ruta_png = tendencias.exportar_png("outputs/tendencias.png")
    tabla = tendencias.tabla_resumen()
    print(f"Tendencias CSV: {ruta_csv}")
    print(f"Tendencias PNG: {ruta_png}\n")
    return {
        "granularidad": "mes",
        "tabla": tabla,
        "conclusion": tendencias.conclusion(),
        "csv": str(ruta_csv),
        "png": str(ruta_png),
    }


def consultas_reproducibles(motor: MotorBusqueda) -> list[dict]:
    consultas = [
        "inteligencia artificial tecnologia",
        "mercados financieros economia",
        "datos abiertos gobierno semantica",
        "Python programacion desarrollo",
        "cambio climatico investigacion cientifica",
    ]
    return [{"consulta": consulta, "resultados": motor.buscar_vectorial(consulta, top_k=3)} for consulta in consultas]


def respuestas_chatbot_reproducibles(qa_system: SistemaQA) -> list[dict]:
    preguntas = [
        "Cuantas noticias tienes?",
        "Cual es el sentimiento general de las noticias?",
        "Que categorias de noticias hay?",
        "Recomiendame algo sobre tecnologia",
    ]
    respuestas = []
    for pregunta in preguntas:
        respuesta, tipo, confianza = qa_system.conversar(pregunta)
        respuestas.append(
            {
                "pregunta": pregunta,
                "respuesta": respuesta,
                "tipo": tipo,
                "confianza": confianza,
            }
        )
    return respuestas


def escribir_documentacion_reproducible(rutas: dict[str, str], args: argparse.Namespace) -> Path:
    lineas = [
        "# Reproducibilidad SIMANW",
        "",
        "## Procedimiento",
        "",
        "1. Crear entorno virtual: `python -m venv .venv`.",
        "2. Activarlo en PowerShell: `.\\.venv\\Scripts\\Activate.ps1`.",
        "3. Instalar dependencias: `pip install -r requirements.txt`.",
        "4. Preparar NLTK: `python -m src.nltk_setup`.",
        "5. Ejecutar el pipeline:",
        "   - Demo: `python main.py --source demo`.",
        "   - RSS: `python main.py --source rss --url <url>`.",
        "   - Archivo: `python main.py --source archivo --input data/raw/noticias.json`.",
        "",
        "## Fuente usada en esta ejecucion",
        "",
        f"- Source: `{args.source}`",
        f"- URL: `{args.url or 'N/A'}`",
        f"- Input: `{args.input or 'N/A'}`",
        "",
        "## Artefactos generados",
        "",
    ]
    for nombre, ruta in sorted(rutas.items()):
        lineas.append(f"- {nombre}: `{ruta}`")
    lineas.extend(
        [
            "",
            "## Limitaciones",
            "",
            "El rastreo real depende de conectividad, disponibilidad del sitio, cambios de estructura, RSS incompletos y reglas de robots.txt. "
            "Los modelos locales de clasificacion y sentimiento son ligeros y deben recalibrarse con corpus amplio para uso productivo.",
            "",
            "## Checklist",
            "",
            "- [x] Dependencias declaradas.",
            "- [x] Recursos NLTK documentados.",
            "- [x] Datos crudos guardados.",
            "- [x] Corpus depurado y procesado guardado.",
            "- [x] Reporte, tendencias, grafo, manifiesto y log generados.",
        ]
    )
    return guardar_markdown("\n".join(lineas), "docs/reproducibilidad.md")


def escribir_documentacion_ontologia(kg: KnowledgeGraphSIMANW) -> Path:
    glosario = kg.glosario_ontologia()
    lineas = ["# Ontologia SIMANW", "", "## Prefijos", ""]
    for prefijo, uri in glosario["prefijos"].items():
        lineas.append(f"- `{prefijo}`: `{uri}`")

    lineas.extend(["", "## Clases", ""])
    for clase, descripcion in glosario["clases"].items():
        lineas.append(f"- `{clase}`: {descripcion}")

    lineas.extend(["", "## Propiedades", ""])
    for prop, descripcion in glosario["propiedades"].items():
        lineas.append(f"- `{prop}`: {descripcion}")

    lineas.extend(
        [
            "",
            "## Ejemplo de triples",
            "",
            "```turtle",
            "\n".join([linea for linea in kg.serializar("turtle").splitlines() if linea.strip()][:20]),
            "```",
            "",
            "## Consultas SPARQL",
            "",
            "### Noticias con metadatos",
            "",
            "```sparql",
            QUERY_NOTICIAS_METADATA.strip(),
            "```",
            "",
            "### Conteo por categoria",
            "",
            "```sparql",
            QUERY_CONTEO_CATEGORIA.strip(),
            "```",
            "",
            "### Sentimiento por categoria",
            "",
            "```sparql",
            QUERY_AC13_SENTIMIENTO_POR_CATEGORIA.strip(),
            "```",
            "",
            "## Validacion",
            "",
            "El proyecto incluye validacion estructural equivalente en `KnowledgeGraphSIMANW.validar_formas()` "
            "y validacion SHACL formal con `pyshacl` mediante `KnowledgeGraphSIMANW.validar_con_shacl()` "
            "usando `shapes/simanw_shapes.ttl`.",
        ]
    )
    return guardar_markdown("\n".join(lineas), "docs/ontologia_simanw.md")


def registrar_trazabilidad(
    args: argparse.Namespace,
    rutas: dict[str, str],
    conteos: dict[str, int],
) -> dict[str, str]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path("outputs/runs") / run_id
    traza = TrazabilidadPipeline(fuente_noticias=_fuente_trazabilidad(args))
    etapas = [
        ("rastreo", 0, conteos["raw"], rutas["raw_json"]),
        ("calidad", conteos["raw"], conteos["depurado"], rutas["corpus_depurado"]),
        ("procesamiento", conteos["depurado"], conteos["procesado"], rutas["corpus_procesado"]),
        ("tendencias", conteos["procesado"], conteos["tendencias"], rutas["tendencias_csv"]),
        ("grafo", conteos["procesado"], conteos["procesado"], rutas["grafo_ttl"]),
        ("reporte", conteos["procesado"], 1, rutas["reporte_final"]),
    ]
    for etapa, entrada, salida, artefacto in etapas:
        traza.registrar_etapa(etapa, entrada, salida, artefacto)

    manifest = traza.guardar_manifiesto(run_dir / "manifest.json", rutas)
    log = traza.guardar_log_jsonl(run_dir / "pipeline_log.jsonl")
    return {"manifest": str(manifest), "pipeline_log": str(log)}


def _normalizar_noticia(noticia: dict, indice: int) -> dict:
    titulo = str(noticia.get("titulo") or noticia.get("title") or f"Noticia {indice}").strip()
    cuerpo = str(
        noticia.get("cuerpo")
        or noticia.get("resumen")
        or noticia.get("summary")
        or noticia.get("descripcion")
        or titulo
    ).strip()
    fecha = str(noticia.get("fecha") or noticia.get("published") or "2026-01-01")[:10]
    autor = str(noticia.get("autor") or noticia.get("author") or "Autor desconocido").strip()
    categoria = str(
        noticia.get("categoria_original")
        or noticia.get("categoria")
        or noticia.get("category")
        or "general"
    ).strip()
    url = str(noticia.get("url") or noticia.get("link") or f"https://simanw.local/noticia/{indice}").strip()
    fuente = str(noticia.get("fuente") or _fuente_desde_url(url)).strip()
    return {
        **noticia,
        "titulo": titulo,
        "cuerpo": cuerpo,
        "fecha": fecha,
        "autor": autor,
        "categoria_original": categoria,
        "url": url,
        "fuente": fuente,
    }


def _fuente_desde_url(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        partes = url.split("/", 3)
        return "/".join(partes[:3])
    return "https://simanw.local"


def _fuente_trazabilidad(args: argparse.Namespace) -> str:
    if args.source == "rss":
        return args.url or "rss-sin-url"
    if args.source == "archivo":
        return args.input or "archivo-sin-ruta"
    return "demo"


def main() -> None:
    args = parse_args()
    usar_predefinidas = not args.interactive
    rutas_generadas: dict[str, str] = {}

    noticias_raw = cargar_noticias_configuradas(args)
    rutas_generadas.update(guardar_salidas_iniciales(noticias_raw))

    noticias = ejecutar_control_calidad(noticias_raw)
    # Reutilizar el informe real de la ejecucion de calidad.
    ctrl_calidad = ControlCalidadCorpus()
    ctrl_calidad.validar(noticias_raw)
    rutas_generadas["reporte_calidad"] = str(ctrl_calidad.guardar_informe("outputs/reporte_calidad.json"))
    rutas_generadas["corpus_depurado"] = str(guardar_json(noticias, "data/processed/corpus_depurado.json"))

    ejecutar_pipeline_nlp(noticias)
    representacion = ejecutar_representacion_vectorial(noticias)
    calculador = ejecutar_similitud(noticias, representacion)
    ejecutar_clasificador(noticias)
    ejecutar_sentimientos(noticias)
    rutas_generadas["corpus_procesado"] = str(guardar_json(noticias, "data/processed/corpus_procesado.json"))

    ejecutar_recomendacion(noticias, calculador)
    ejecutar_detector_publicidad()
    motor = ejecutar_motor_busqueda(noticias, usar_predefinidas=usar_predefinidas)
    ejecutar_evaluacion_busqueda(noticias)
    ejecutar_busqueda_natural(motor, usar_predefinidas=usar_predefinidas)
    ejecutar_chatbot(noticias, usar_predefinidas=usar_predefinidas)
    qa_system = ejecutar_sistema_qa(noticias, motor, usar_predefinidas=usar_predefinidas)

    tendencias = ejecutar_tendencias(noticias)
    rutas_generadas["tendencias_csv"] = tendencias["csv"]
    rutas_generadas["tendencias_png"] = tendencias["png"]

    kg = ejecutar_knowledge_graph(noticias)
    ejecutar_consultas_sparql(kg)
    ejecutar_datos_abiertos(kg)
    ejecutar_endpoints_sparql_externos()
    rutas_rdf = kg.exportar_rdf("outputs/grafo/simanw_graph")
    rutas_generadas["grafo_ttl"] = str(rutas_rdf["turtle"])
    rutas_generadas["grafo_jsonld"] = str(rutas_rdf["json-ld"])
    validacion_shacl = kg.validar_con_shacl()
    rutas_generadas["grafo_shacl_report"] = str(
        guardar_markdown(str(validacion_shacl), "outputs/grafo/shacl_report.txt")
    )

    consultas = consultas_reproducibles(motor)
    respuestas = respuestas_chatbot_reproducibles(qa_system)
    reportero = ejecutar_reportes(noticias, kg)
    ruta_reporte = reportero.guardar_reporte_markdown(
        "outputs/reportes/reporte_final.md",
        tendencias=tendencias,
        consultas_busqueda=consultas,
        respuestas_chatbot=respuestas,
    )
    rutas_generadas["reporte_final"] = str(ruta_reporte)

    rutas_generadas["docs_reproducibilidad"] = str(escribir_documentacion_reproducible(rutas_generadas, args))
    rutas_generadas["docs_ontologia"] = str(escribir_documentacion_ontologia(kg))

    conteos = {
        "raw": len(noticias_raw),
        "depurado": len(noticias),
        "procesado": len(noticias),
        "tendencias": len(tendencias["tabla"]),
    }
    rutas_generadas.update(registrar_trazabilidad(args, rutas_generadas, conteos))

    ejecutar_integracion_final()
    ejecutar_exportacion(noticias)


if __name__ == "__main__":
    main()
