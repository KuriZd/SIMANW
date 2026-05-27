"""AC-6: Chatbot con Memoria de Contexto."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chatbot_contextual import CONVERSACION_AC6, ChatbotContextual
from src.motor_busqueda import MotorBusqueda
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

NOTICIAS_DEMO = [
    {"titulo": "Avances en inteligencia artificial generativa",
     "cuerpo": "La inteligencia artificial y el aprendizaje automatico impulsan nuevas aplicaciones de software.",
     "categoria_predicha": "tecnologia", "sentimiento": {"etiqueta": "positivo"}},
    {"titulo": "Mercados financieros muestran volatilidad",
     "cuerpo": "La inflacion y las tasas de interes presionan al mercado de valores y a los inversionistas.",
     "categoria_predicha": "economia", "sentimiento": {"etiqueta": "negativo"}},
    {"titulo": "Descubrimiento cientifico sobre cambio climatico",
     "cuerpo": "Investigadores publican datos sobre emisiones de carbono y calentamiento global.",
     "categoria_predicha": "ciencia", "sentimiento": {"etiqueta": "negativo"}},
    {"titulo": "Python mejora herramientas de programacion",
     "cuerpo": "La nueva version de Python ayuda al desarrollo de software e inteligencia artificial.",
     "categoria_predicha": "tecnologia", "sentimiento": {"etiqueta": "positivo"}},
    {"titulo": "Gobierno publica datos abiertos",
     "cuerpo": "El gobierno libera datos abiertos para fortalecer transparencia y politicas publicas.",
     "categoria_predicha": "politica", "sentimiento": {"etiqueta": "positivo"}},
]

st.set_page_config(page_title="SIMANW | AC-6: Chatbot Contextual", page_icon="🤖", layout="wide")
aplicar_estilo_global()



@st.cache_resource
def get_chatbot() -> ChatbotContextual:
    motor = MotorBusqueda()
    motor.indexar(NOTICIAS_DEMO)
    return ChatbotContextual(NOTICIAS_DEMO, motor)


def main() -> None:
    encabezado(
        "AC-6 | Chatbot Contextual",
        "Chatbot con Memoria de Contexto",
        "Chatbot que recuerda temas previos dentro de la sesión y adapta sus respuestas al contexto acumulado.",
    )

    chatbot = get_chatbot()

    if "historial" not in st.session_state:
        st.session_state.historial = []

    col_chat, col_info = st.columns([3, 1])

    with col_chat:
        st.subheader("Conversación")

        # Mostrar historial
        for turno in st.session_state.historial:
            with st.chat_message("user"):
                st.write(turno["pregunta"])
            with st.chat_message("assistant"):
                st.write(turno["respuesta"])
                st.caption(f"Tipo: `{turno['tipo']}` | Confianza: `{turno['confianza']:.2f}`")

        # Input del usuario
        pregunta = st.chat_input("Escribe tu pregunta sobre las noticias…")
        if pregunta:
            with st.spinner("Pensando…"):
                respuesta, tipo, confianza = chatbot.responder(pregunta)
            st.session_state.historial.append({
                "pregunta": pregunta,
                "respuesta": respuesta,
                "tipo": tipo,
                "confianza": confianza,
            })
            st.rerun()

        if st.button("🔄 Reiniciar conversación"):
            st.session_state.historial = []
            st.rerun()

        # Sugerencias rápidas
        st.markdown("**Sugerencias:**")
        sugs = st.columns(len(CONVERSACION_AC6))
        for col, sug in zip(sugs, CONVERSACION_AC6):
            if col.button(sug[:30] + "…" if len(sug) > 30 else sug, key=f"sug_{sug[:10]}"):
                with st.spinner("Respondiendo…"):
                    respuesta, tipo, confianza = chatbot.responder(sug)
                st.session_state.historial.append({
                    "pregunta": sug, "respuesta": respuesta,
                    "tipo": tipo, "confianza": confianza,
                })
                st.rerun()

    with col_info:
        st.subheader("Estadísticas de sesión")
        stats = chatbot.estadisticas_sesion()
        st.metric("Interacciones", stats.get("interacciones", 0))

        temas = stats.get("temas_interes", [])
        if temas:
            st.markdown("**Temas de interés detectados:**")
            for t in temas:
                st.markdown(f"- `{t}`")

        tipos = dict(stats.get("tipos_respuesta", {}))
        if tipos:
            st.subheader("Tipos de respuesta")
            df_tipos = pd.DataFrame(list(tipos.items()), columns=["Tipo", "Cantidad"])
            fig = px.pie(df_tipos, names="Tipo", values="Cantidad",
                         color_discrete_sequence=["#4F46E5", "#7C3AED", "#06B6D4", "#F59E0B"],
                         template="plotly_white", hole=0.3)
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Noticias del corpus")
        for i, n in enumerate(NOTICIAS_DEMO):
            st.markdown(f"**{i}** — {n['titulo'][:40]}…")


if __name__ == "__main__":
    main()

