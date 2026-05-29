"""AC-11: Estudio de Usabilidad del Sistema."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.usabilidad import (
    CUESTIONARIO_USABILIDAD,
    TAREAS_USABILIDAD,
    EstudioUsabilidad,
    estudio_demo,
)
from src.ui_streamlit import aplicar_estilo_global, encabezado  # noqa: E402

st.set_page_config(page_title="SIMANW | AC-11: Usabilidad", page_icon="🧪", layout="wide")
aplicar_estilo_global()

_RUTA_PARTICIPANTES = Path("data/ac11_participantes.json")


def _cargar_participantes() -> list[dict]:
    if not _RUTA_PARTICIPANTES.exists():
        return []
    try:
        return json.loads(_RUTA_PARTICIPANTES.read_text(encoding="utf-8"))
    except Exception:
        return []


def _guardar_participante(codigo: str, respuestas: dict, problemas: list[str]) -> None:
    participantes = _cargar_participantes()
    codigos_existentes = {p["codigo"] for p in participantes}
    if codigo in codigos_existentes:
        participantes = [p for p in participantes if p["codigo"] != codigo]
    participantes.append({"codigo": codigo, "respuestas": respuestas, "problemas": problemas})
    _RUTA_PARTICIPANTES.parent.mkdir(parents=True, exist_ok=True)
    _RUTA_PARTICIPANTES.write_text(
        json.dumps(participantes, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _construir_estudio(participantes: list[dict]) -> tuple[EstudioUsabilidad, bool]:
    """Devuelve (estudio, usando_demo)."""
    if participantes:
        estudio = EstudioUsabilidad()
        for p in participantes:
            estudio.registrar_participante(p["codigo"], p["respuestas"], p["problemas"])
        return estudio, False
    return estudio_demo(), True


def main() -> None:
    encabezado(
        "AC-11 | Estudio de Usabilidad",
        "Estudio de Usabilidad del Sistema",
        "Evaluación de la interfaz SIMANW mediante guión de tareas y cuestionario de satisfacción.",
    )

    participantes = _cargar_participantes()
    estudio, usando_demo = _construir_estudio(participantes)

    if usando_demo:
        st.warning(
            "Mostrando datos de demostración (3 participantes ficticios). "
            "Usa la pestaña **Registrar participante** para añadir respuestas reales."
        )
    else:
        st.caption(f"Datos reales — {len(participantes)} participante(s) registrado(s).")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Guión de tareas",
        "Registrar participante",
        "Resultados por participante",
        "Promedios y análisis",
        "Mejoras y ética",
    ])

    with tab1:
        st.subheader("Tareas del guión de usabilidad")
        for i, tarea in enumerate(estudio.tareas, 1):
            st.markdown(
                f"""<div style="background:#F9FAFB; border-left:3px solid #4F46E5;
                padding:0.5rem 0.8rem; border-radius:5px; margin-bottom:0.4rem;">
                <b>Tarea {i}</b> — {tarea}</div>""",
                unsafe_allow_html=True,
            )
        st.subheader("Ítems del cuestionario (escala 1–5)")
        for i, item in enumerate(estudio.items, 1):
            st.markdown(f"**{i}.** {item}")

    with tab2:
        st.subheader("Registrar respuestas de un participante")
        st.caption(
            "Cada participante recibe un código anónimo (ej. P4, P5…). "
            "Sus respuestas se guardan en `data/ac11_participantes.json`."
        )

        with st.form("form_participante"):
            codigo = st.text_input("Código del participante", placeholder="P4")
            st.markdown("**Cuestionario** — escala 1 (muy en desacuerdo) a 5 (muy de acuerdo)")
            respuestas: dict[str, int] = {}
            cols = st.columns(2)
            for idx, item in enumerate(estudio.items):
                with cols[idx % 2]:
                    respuestas[item] = st.slider(
                        item, min_value=1, max_value=5, value=3,
                        key=f"item_{idx}",
                    )
            problemas_txt = st.text_area(
                "Problemas observados (uno por línea)",
                placeholder="El botón de búsqueda no era visible al inicio.",
            )
            enviado = st.form_submit_button("Guardar respuestas", type="primary", use_container_width=True)

        if enviado:
            if not codigo.strip():
                st.error("Ingresa un código de participante.")
            else:
                problemas = [p.strip() for p in problemas_txt.splitlines() if p.strip()]
                _guardar_participante(codigo.strip(), respuestas, problemas)
                st.success(f"Respuestas de **{codigo.strip()}** guardadas. Recarga la página para ver los resultados actualizados.")
                st.cache_data.clear()

        if participantes:
            st.divider()
            st.caption(f"Participantes registrados: {', '.join(p['codigo'] for p in participantes)}")
            if st.button("Borrar todos los participantes reales", type="secondary"):
                _RUTA_PARTICIPANTES.unlink(missing_ok=True)
                st.rerun()

    with tab3:
        st.subheader("Resultados por participante (anonimizados)")
        tabla = estudio.tabla_anonimizada()
        if tabla:
            df_p = pd.DataFrame(tabla)
            st.dataframe(df_p, use_container_width=True, hide_index=True)
            fig = px.imshow(
                df_p.set_index("participante"),
                color_continuous_scale="Blues",
                zmin=1, zmax=5,
                template="plotly_white",
                title="Heatmap de respuestas por participante",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)
            csv_bytes = df_p.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Descargar CSV", data=csv_bytes,
                               file_name="ac11_resultados_usabilidad.csv", mime="text/csv")

    with tab4:
        st.subheader("Puntuaciones promedio por ítem")
        promedios = estudio.promedios()
        df_prom = pd.DataFrame(list(promedios.items()), columns=["Ítem", "Promedio"]).sort_values(
            "Promedio", ascending=True
        )
        fig = px.bar(
            df_prom, x="Promedio", y="Ítem", orientation="h",
            color="Promedio", color_continuous_scale="Blues",
            range_color=[1, 5], template="plotly_white",
        )
        fig.add_vline(x=3.0, line_dash="dot", line_color="#EF4444", annotation_text="umbral mínimo")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
        puntuacion_global = sum(promedios.values()) / len(promedios) if promedios else 0
        st.metric("Puntuación global promedio", f"{puntuacion_global:.2f} / 5.0")

    with tab5:
        st.subheader("Problemas detectados y mejoras propuestas")
        mejoras = estudio.problemas_y_mejoras()
        df_m = pd.DataFrame(mejoras)
        st.dataframe(df_m, use_container_width=True, hide_index=True)
        st.subheader("Reflexión sobre consentimiento informado")
        st.info(estudio.reflexion_consentimiento())
        with st.expander("Formato de registro de participante"):
            st.markdown("""
**Código del participante:** `P___ ` (no se registran nombres reales)

**Instrucción:** Lee cada ítem y asigna un valor del 1 al 5.
- 1 = Muy en desacuerdo
- 3 = Neutral
- 5 = Muy de acuerdo

Los datos se reportan de forma **agregada** y no permiten identificar a ningún participante.
""")


if __name__ == "__main__":
    main()
