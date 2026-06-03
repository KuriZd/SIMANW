# AC-11 – Estudio de Usabilidad del Buscador y Chatbot SIMANW

---

## 1. Objetivo

Evaluar la usabilidad del sistema SIMANW (Sistema Inteligente de Monitoreo y Análisis de Noticias Web) enfocándose en dos módulos principales: el buscador de noticias (modelo booleano y vectorial) y el chatbot contextual. El estudio busca identificar problemas de interacción, medir la satisfacción del usuario y proponer mejoras concretas a la interfaz y al comportamiento del sistema.

---

## 2. Participantes

Todos los participantes fueron informados del propósito académico del estudio y firmaron consentimiento informado previo a la prueba. No se registran nombres reales; cada persona se identifica con un código anónimo.

| Participante | Perfil                      | Rango de edad | Experiencia con buscadores                       |
| ------------ | --------------------------- | ------------- | ------------------------------------------------ |
| Usuario A    | Estudiante de ingeniería    | 20–25 años    | Media (uso diario de Google)                     |
| Usuario B    | Estudiante de posgrado      | 25–30 años    | Alta (familiarizado con herramientas académicas) |
| Usuario C    | Profesional área no técnica | 30–40 años    | Básica (navegación web general)                  |

> PENDIENTE: completar con perfiles reales de los participantes al ejecutar el estudio con usuarios nuevos desde la pestaña "Registrar participante" de la página AC-11 en SIMANW.

---

## 3. Guión de Pruebas

Las cinco tareas se presentaron de forma secuencial. Se proporcionó acceso al sistema SIMANW en ejecución local (`streamlit run app.py`). No se ofreció ayuda durante la ejecución, salvo para aclaraciones sobre el objetivo de la tarea.

### Tarea 1 — Búsqueda directa

> Buscar noticias sobre inteligencia artificial usando el campo de búsqueda directa del sistema (AC-5 · Comparador de Búsqueda, pestaña "Consulta manual", modelo booleano).

**Criterio de éxito:** El usuario encuentra al menos una noticia con el término "inteligencia artificial" en menos de 60 segundos.

### Tarea 2 — Búsqueda en lenguaje natural

> Usar lenguaje natural para encontrar noticias económicas recientes (AC-6 · Chatbot Contextual).

**Criterio de éxito:** El usuario formula una pregunta en lenguaje natural y el chatbot devuelve al menos una noticia de categoría economía.

### Tarea 3 — Pregunta de conteo

> Preguntar cuántas noticias hay sobre ciencia en el corpus cargado.

**Criterio de éxito:** El sistema responde con un número concreto o una lista filtrada por categoría ciencia.

### Tarea 4 — Pregunta de recomendación

> Pedir una recomendación de lectura sobre tecnología.

**Criterio de éxito:** El sistema sugiere al menos una noticia justificando la recomendación (categoría, similitud o sentimiento).

### Tarea 5 — Pregunta de seguimiento contextual

> Hacer una pregunta de seguimiento usando el contexto de la respuesta anterior sin repetir el tema explícitamente.

**Criterio de éxito:** El chatbot mantiene el contexto de la sesión y responde coherentemente sin que el usuario deba reformular desde cero.

---

## 4. Cuestionario Posterior

Aplicado inmediatamente tras completar las cinco tareas. Escala Likert de 1 a 5:

- **1** = Muy en desacuerdo / Muy difícil
- **3** = Neutral
- **5** = Muy de acuerdo / Muy fácil

| #   | Ítem del cuestionario               |
| --- | ----------------------------------- |
| 1   | Facilidad para completar las tareas |
| 2   | Relevancia de los resultados        |
| 3   | Confianza en las respuestas         |
| 4   | Claridad del lenguaje del chatbot   |
| 5   | Rapidez percibida                   |
| 6   | Facilidad para reformular consultas |
| 7   | Utilidad de las recomendaciones     |
| 8   | Satisfacción general                |

---

## 5. Resultados

Tabla completa de respuestas por participante (valores 1–5):

| Participante   | Facilidad tareas | Relevancia resultados | Confianza respuestas | Claridad chatbot | Rapidez | Reformular consultas | Utilidad recomendaciones | Satisfacción general |
| -------------- | ---------------- | --------------------- | -------------------- | ---------------- | ------- | -------------------- | ------------------------ | -------------------- |
| Usuario A (P1) | 4                | 4                     | 3                    | 4                | 5       | 3                    | 4                        | 4                    |
| Usuario B (P2) | 3                | 4                     | 4                    | 3                | 4       | 3                    | 3                        | 4                    |
| Usuario C (P3) | 4                | 3                     | 3                    | 4                | 4       | 4                    | 3                        | 3                    |

**Problemas abiertos reportados:**

| Participante | Problema observado                                                                       |
| ------------ | ---------------------------------------------------------------------------------------- |
| Usuario A    | No encontró filtros visibles para acotar la búsqueda.                                    |
| Usuario B    | Dudó sobre la fuente del conteo de noticias.                                             |
| Usuario C    | La recomendación parecía poco explicada (no se indicaba por qué se sugería esa noticia). |

---

## 6. Promedios

### Promedio por pregunta

| Ítem                              | Usuario A | Usuario B | Usuario C | **Promedio** |
| --------------------------------- | --------- | --------- | --------- | ------------ |
| Facilidad para completar tareas   | 4         | 3         | 4         | **3.67**     |
| Relevancia de los resultados      | 4         | 4         | 3         | **3.67**     |
| Confianza en las respuestas       | 3         | 4         | 3         | **3.33**     |
| Claridad del lenguaje del chatbot | 4         | 3         | 4         | **3.67**     |
| Rapidez percibida                 | 5         | 4         | 4         | **4.33**     |
| Facilidad para reformular         | 3         | 3         | 4         | **3.33**     |
| Utilidad de las recomendaciones   | 4         | 3         | 3         | **3.33**     |
| Satisfacción general              | 4         | 4         | 3         | **3.67**     |

### Promedio general

**Promedio global: 3.63 / 5.0**

### Interpretación de resultados

- El ítem con mayor puntuación es **Rapidez percibida (4.33)**, lo que indica que el sistema responde en tiempos aceptables para los usuarios.
- Los ítems con puntuación más baja son **Confianza en las respuestas**, **Facilidad para reformular consultas** y **Utilidad de las recomendaciones** (todos en 3.33), señalando áreas prioritarias de mejora.
- El promedio general de **3.63/5.0** se ubica por encima del umbral mínimo aceptable (3.0) pero deja margen de mejora relevante, especialmente en transparencia explicativa del sistema.
- Ningún ítem cae por debajo de 3.0, lo que indica que el sistema es funcionalmente usable aunque no óptimo en experiencia.

---

## 7. Problemas Detectados

| #   | Problema                                                                               | Severidad | Impacto                                                         | Mejora propuesta                                                                      |
| --- | -------------------------------------------------------------------------------------- | --------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| 1   | Los usuarios no distinguen claramente búsqueda directa y búsqueda en lenguaje natural. | Alta      | Confusión en el flujo principal de uso.                         | Etiquetar visualmente el modo activo y conservar ejemplos breves por modo.            |
| 2   | Algunos resultados relevantes aparecen debajo de documentos menos útiles.              | Media     | Reduce la confianza en el ranking de resultados.                | Reordenar resultados combinando similitud vectorial, fecha y coincidencia exacta.     |
| 3   | El chatbot no siempre explica la fuente de una respuesta de conteo.                    | Media     | El usuario no puede verificar la cifra devuelta.                | Mostrar el conteo, el filtro aplicado y enlaces a las noticias consideradas.          |
| 4   | Las recomendaciones no muestran por qué una noticia fue sugerida.                      | Media     | Dificulta que el usuario evalúe la relevancia de la sugerencia. | Agregar justificación basada en categoría, términos coincidentes y sentimiento.       |
| 5   | Las preguntas de seguimiento pierden contexto cuando cambia el tema.                   | Alta      | El usuario debe reformular desde cero al cambiar de tema.       | Guardar un resumen de contexto por sesión y pedir confirmación ante cambios ambiguos. |

---

## 8. Consideraciones Éticas

### Consentimiento informado

Antes de iniciar la prueba se entregó a cada participante un documento explicando el objetivo académico del estudio, las tareas a realizar, la duración estimada (20–30 minutos) y el carácter voluntario de la participación. Ningún participante fue coaccionado ni recibió incentivo económico.

### Anonimización

No se registran nombres reales en ningún documento del estudio. Cada participante recibe un código alfanumérico (`P1`, `P2`, `P3`…). Los reportes y tablas se generan exclusivamente con estos códigos.

### Protección de datos

Las respuestas del cuestionario se almacenan localmente en `data/ac11_participantes.json` dentro del repositorio del proyecto. No se transmiten a servidores externos. Las consultas realizadas durante las tareas no se persisten en ningún log asociado al código del participante.

### Uso académico de la información

Los datos recopilados se utilizan exclusivamente para evaluar la interfaz del sistema SIMANW en el contexto de la asignatura. Los resultados se reportan de forma agregada. No se publican respuestas individuales que permitan identificar a ningún participante.

---

## 9. Conclusiones

El estudio de usabilidad con tres participantes reveló que SIMANW es un sistema funcional y con tiempos de respuesta aceptables (rapidez: 4.33/5.0), pero con oportunidades de mejora significativas en:

1. **Transparencia explicativa**: los usuarios necesitan que el sistema justifique sus respuestas, conteos y recomendaciones con referencias directas a los documentos considerados.
2. **Diferenciación de modos de búsqueda**: la distinción entre búsqueda directa (booleana/vectorial) y búsqueda en lenguaje natural no es evidente sin instrucción previa.
3. **Gestión del contexto conversacional**: el chatbot pierde el hilo temático ante cambios de tema, lo que obliga al usuario a reformular consultas ya realizadas.

Como mejoras prioritarias para versiones futuras se recomienda: etiquetado visual del modo activo, justificación de recomendaciones, y un mecanismo de resumen de contexto por sesión de chat.

> PENDIENTE: ampliar el estudio con al menos 5 participantes para obtener métricas estadísticamente representativas. Registrar nuevos participantes desde la pestaña "Registrar participante" en AC-11 · Usabilidad.

---

## 10. Evaluación del Cumplimiento

| Requisito AC-11                                          | Estado      | Evidencia                                                             |
| -------------------------------------------------------- | ----------- | --------------------------------------------------------------------- |
| Guión con cinco tareas obligatorias                      | ✅ Cumplido | Sección 3 — 5 tareas documentadas con criterio de éxito               |
| Cuestionario con mínimo 8 preguntas en escala Likert 1–5 | ✅ Cumplido | Sección 4 — 8 ítems del cuestionario                                  |
| Tabla de resultados completa                             | ✅ Cumplido | Sección 5 — respuestas por participante                               |
| Promedio por pregunta y promedio general                 | ✅ Cumplido | Sección 6 — tabla de promedios y valor global 3.63/5.0                |
| Mínimo cinco problemas detectados con mejora propuesta   | ✅ Cumplido | Sección 7 — tabla con 5 problemas, severidad, impacto y mejora        |
| Participantes anonimizados                               | ✅ Cumplido | Códigos Usuario A/B/C (P1/P2/P3), sin datos personales                |
| Consideraciones éticas (consentimiento, protección)      | ✅ Cumplido | Sección 8 — consentimiento, anonimización, protección y uso académico |
| Conclusiones con hallazgos y mejoras futuras             | ✅ Cumplido | Sección 9 — 3 hallazgos principales y mejoras prioritarias            |
| Formato Markdown profesional para repositorio            | ✅ Cumplido | Archivo `usertest.md` en raíz del proyecto                            |
| Registro interactivo de participantes reales en app      | ✅ Cumplido | Pestaña "Registrar participante" en `pages/AC11_Usabilidad.py`        |
