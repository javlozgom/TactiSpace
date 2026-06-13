from __future__ import annotations

import streamlit as st

from src.ui.components import render_info_box, render_page_header, render_section_header


COMMON_LABELS = [
    (
        "Eventos / Eventos filtrados / Eventos mostrados",
        "Número de filas de evento que quedan dentro del contexto activo. No representa jugadas completas, sino registros individuales del dataset.",
    ),
    (
        "Partidos",
        "Cantidad de encuentros distintos presentes en el subconjunto filtrado. Si aparece `1`, toda la lectura corresponde a un único partido.",
    ),
    (
        "Equipos",
        "Número de equipos distintos presentes en el subconjunto visible. Normalmente será `1` o `2` según el filtro.",
    ),
    (
        "Jugadores",
        "Número de jugadores con al menos un evento visible en el contexto actual.",
    ),
    (
        "Tipos de evento",
        "Número de categorías de acción distintas presentes en el subconjunto: pase, tiro, regate, recuperación, etc.",
    ),
    (
        "Eventos con 360 / Freeze-frames",
        "Eventos que tienen contexto espacial adicional de StatsBomb 360. Son los únicos que permiten el análisis espacial completo.",
    ),
    (
        "Límite visual / MAX_PLOT_EVENTS",
        "Restricción de rendimiento aplicada en algunas visualizaciones. La app puede mostrar solo una parte de los puntos sin dejar de usar el contexto filtrado para el resto del análisis.",
    ),
    (
        "Percentil",
        "Posición relativa de un jugador respecto al resto del conjunto comparado. Un percentil alto significa que está por encima de la mayoría en esa métrica.",
    ),
    (
        "Métricas de riesgo",
        "Son métricas donde un valor alto suele significar peor comportamiento: más pérdidas, más pases fallidos o más acciones negativas.",
    ),
    (
        "Unidades espaciales",
        "En Voronoi y Delaunay, las distancias se leen en unidades de campo StatsBomb y las áreas en unidades cuadradas del mismo sistema. Solo pueden interpretarse como metros o metros cuadrados de forma aproximada si se asume adicionalmente un campo estándar.",
    ),
]


APP_TERMS_GLOSSARY = [
    (
        "KPI",
        "Siglas de `Key Performance Indicator`. En la app se usa para nombrar un indicador-resumen que condensa rápidamente una parte del contexto.",
    ),
    (
        "Filtro global",
        "Conjunto principal de filtros de la app: partido, equipo, jugador y rango de minutos. Define el subconjunto de datos sobre el que trabajan las vistas.",
    ),
    (
        "Contexto filtrado",
        "Subconjunto exacto de eventos que queda después de aplicar el filtro global. Es la base real del análisis visible.",
    ),
    (
        "Evento",
        "Unidad básica del dataset. Cada fila representa una acción registrada en el partido: un pase, un tiro, una presión, una recuperación, etc.",
    ),
    (
        "Tipo de evento",
        "Categoría de la acción registrada. Se usa para agrupar y analizar comportamientos concretos como pases, tiros o duelos.",
    ),
    (
        "Volumen",
        "Cantidad de veces que ocurre una acción. Un volumen alto indica mucha participación o frecuencia, no necesariamente mejor calidad.",
    ),
    (
        "Eficiencia",
        "Relación entre resultados positivos y volumen total de intentos. Suele aparecer en métricas porcentuales como acierto o conversión.",
    ),
    (
        "Percentil",
        "Posición relativa de un jugador respecto al resto del conjunto comparado. Un percentil 90 significa que está por encima de la mayoría en esa métrica concreta.",
    ),
    (
        "Freeze-frame",
        "Instantánea espacial de StatsBomb 360 asociada a un evento. Muestra a los jugadores visibles alrededor de la acción en ese momento.",
    ),
    (
        "StatsBomb 360",
        "Capa de datos adicional que aporta contexto espacial alrededor de ciertos eventos. Es necesaria para el análisis espacial avanzado.",
    ),
    (
        "Voronoi",
        "Modelo geométrico que divide el campo en regiones de influencia aproximadas según proximidad a cada jugador visible.",
    ),
    (
        "Delaunay",
        "Triangulación dual de Voronoi. En la app se usa para estudiar vecindad geométrica y conectividad local entre jugadores visibles.",
    ),
    (
        "Unidades de campo StatsBomb",
        "Sistema de coordenadas normalizado del dataset, representado sobre un campo 120x80. En este marco, las distancias y áreas de Voronoi/Delaunay son consistentes internamente, pero no equivalen por defecto a metros reales del estadio.",
    ),
    (
        "Scoring heurístico",
        "Sistema de puntuación aproximado que ordena alternativas de pase combinando criterios como progresión, espacio y presión cercana. No es una probabilidad real.",
    ),
    (
        "Heatmap",
        "Visualización de densidad espacial. Resalta las zonas donde un tipo de evento se repite con más frecuencia.",
    ),
    (
        "Datos normalizados",
        "Datos ya procesados y homogeneizados para que la app pueda analizarlos de forma consistente entre vistas.",
    ),
]


EVENT_GLOSSARY = [
    ("Pass", "Pase realizado por un jugador hacia un compañero. Puede acabar completado o fallido."),
    ("Carry", "Conducción del balón por parte de un jugador entre un punto inicial y uno final."),
    ("Shot", "Remate o intento de finalización hacia portería."),
    ("Pressure", "Acción defensiva de presión sobre rival con balón o con recepción cercana."),
    ("Ball Recovery", "Recuperación de la posesión por parte del equipo."),
    ("Duel", "Disputa individual por balón o posición entre dos jugadores."),
    ("Dribble", "Intento de regate o desborde frente a un rival."),
    ("Ball Receipt*", "Recepción del balón por parte de un jugador."),
    ("Miscontrol", "Control defectuoso que degrada o compromete la posesión."),
    ("Dispossessed", "Pérdida de balón provocada por el rival."),
    ("Interception", "Intercepción de un pase o acción del rival."),
    ("Clearance", "Despeje defensivo para alejar el balón de una zona peligrosa."),
    ("Block", "Bloqueo de tiro, pase o acción rival."),
    ("Goal Keeper", "Acción específica registrada para el portero."),
    ("Own Goal For", "Gol en propia favorable al equipo analizado."),
    ("Own Goal Against", "Gol en propia en contra del equipo analizado."),
    ("Offside", "Acción sancionada por fuera de juego."),
]


TAB_GUIDES = [
    {
        "name": "🏟️ Vista general > 🏠 Inicio",
        "purpose": (
            "Es la puerta de entrada a la app. Está pensada para ubicar rápidamente al usuario en el contexto actual antes de entrar en vistas más analíticas."
        ),
        "data": (
            "Maneja el subconjunto filtrado globalmente y muestra su tamaño, jugadores visibles, partidos, volumen de pases y número de eventos con soporte 360 cuando existen."
        ),
        "what_you_see": [
            "KPIs generales del contexto filtrado.",
            "Resumen visual del proyecto y flujo recomendado de uso.",
            "Mapa general de eventos y mapa de calor agregado.",
            "Resumen por jugador para una lectura rápida del reparto del volumen.",
        ],
        "how_to_use": [
            "Úsala al principio de cada análisis para confirmar que el filtro global es correcto.",
            "Si los números no cuadran con lo esperado, corrige antes partido, equipo, jugador o minutos.",
            "Sirve también como vista introductoria para una persona externa al desarrollo.",
        ],
        "how_to_read": [
            "Los KPIs aquí son de contexto, no de evaluación fina.",
            "Un volumen alto de eventos o pases no implica automáticamente mejor rendimiento.",
            "El resumen por jugador ayuda a identificar protagonistas, pero debe contrastarse después con métricas específicas o comparativas.",
        ],
    },
    {
        "name": "🏟️ Vista general > 📊 Resumen",
        "purpose": (
            "Sintetiza el contexto activo y permite entender qué tipo de partido, jugador o equipo estás viendo antes de profundizar."
        ),
        "data": (
            "Trabaja sobre el dataframe filtrado globalmente. Agrega eventos por tipo, calcula tasas básicas de éxito y construye mapas prioritarios según posición o perfil del jugador."
        ),
        "what_you_see": [
            "KPIs de eventos, pases, conducciones y tiros.",
            "Contexto activo: jugador, equipos, partidos y tipos de evento visibles.",
            "Tabla de acierto por acción.",
            "Eventos especiales como fuera de juego o goles en propia.",
            "Resumen agregado por jugador y mapas prioritarios.",
        ],
        "how_to_use": [
            "Empieza aquí cuando quieras una lectura descriptiva del subconjunto filtrado.",
            "Usa la tabla de acierto por acción para detectar qué tipos de evento merecen una revisión posterior.",
            "Si seleccionas un jugador, los mapas prioritarios ayudan a centrar la lectura en las acciones más relevantes para su perfil.",
        ],
        "how_to_read": [
            "Las tasas de éxito deben leerse junto al volumen.",
            "Los eventos especiales suelen ser escasos, así que conviene tratarlos como señales contextuales, no como base estadística.",
            "Los mapas muestran dónde se producen acciones, no si fueron correctas táctica o técnicamente.",
        ],
    },
    {
        "name": "🏟️ Vista general > 📘 Guía",
        "purpose": (
            "Documenta el funcionamiento actual de la app, su terminología y la forma correcta de interpretar los resultados."
        ),
        "data": (
            "No introduce un análisis nuevo, sino que organiza explicaciones metodológicas y de uso basadas en la arquitectura actual de la aplicación."
        ),
        "what_you_see": [
            "Explicación general de la app.",
            "Glosarios de términos y eventos.",
            "Guía detallada por vistas y subapartados.",
            "Advertencias metodológicas y pautas de validación.",
        ],
        "how_to_use": [
            "Consúltala cuando necesites interpretar correctamente una métrica o una visualización.",
            "Úsala como apoyo para presentar la app a una persona que no ha participado en el desarrollo.",
        ],
        "how_to_read": [
            "Debe entenderse como documentación metodológica, no como una vista de análisis de datos.",
        ],
    },
    {
        "name": "🎯 Sistema de análisis > 📏 Métricas específicas",
        "purpose": (
            "Permite estudiar a fondo un único tipo de acción. Es la pestaña adecuada para responder preguntas concretas."
        ),
        "data": (
            "Parte del subconjunto filtrado y aplica filtros internos por tipo de evento. Según el evento, calcula métricas como pases totales, pases completados, tiros, duelos ganados, regates exitosos, recuperaciones o presiones."
        ),
        "what_you_see": [
            "Selector del tipo de evento a analizar.",
            "Filtros internos específicos del tipo de acción.",
            "KPIs del evento seleccionado.",
            "Mapa espacial de ese evento.",
            "Resumen tabular de métricas y tabla detallada de registros.",
        ],
        "how_to_use": [
            "Escoge primero el evento que responde a tu pregunta: pase, tiro, duelo, regate, recuperación, etc.",
            "Afina después con los filtros internos de la propia pestaña.",
            "Usa la tabla final para validar que los registros visibles coinciden con lo que estás interpretando en el mapa.",
        ],
        "how_to_read": [
            "Las métricas cambian según el evento. No compares directamente KPIs de pase con KPIs de tiro como si significaran lo mismo.",
            "El mapa aporta distribución espacial; la tabla y los KPIs aportan magnitud y resultado.",
            "Cuando veas porcentajes de éxito, considera siempre cuántos eventos los sostienen.",
        ],
    },
    {
        "name": "🎯 Sistema de análisis > 📋 Eventos",
        "purpose": (
            "Permite explorar visual y tabularmente varios tipos de acción dentro del contexto filtrado."
        ),
        "data": (
            "Parte del subconjunto filtrado y deja seleccionar uno o varios tipos de evento. El mapa muestra solo eventos con representación espacial útil; la tabla conserva más detalle."
        ),
        "what_you_see": [
            "Selector múltiple de tipos de evento.",
            "Resumen de cuántos eventos visibles hay frente al total filtrado.",
            "Mapa de eventos seleccionados.",
            "Tabla de eventos y guía de lectura por tipo.",
        ],
        "how_to_use": [
            "Úsala para localizar dónde aparecen determinadas acciones o para cruzar varios tipos de evento en un mismo mapa.",
            "Si necesitas precisión, revisa siempre la tabla después del mapa.",
        ],
        "how_to_read": [
            "Cuando mezclas varios tipos, el gráfico representa coexistencia espacial, no orden temporal.",
            "Algunos eventos administrativos no se dibujan en el mapa porque no tienen representación espacial útil.",
        ],
    },
    {
        "name": "🎯 Sistema de análisis > 🌡️ Mapa de calor",
        "purpose": (
            "Resume la concentración espacial de un único tipo de evento mediante densidad visual."
        ),
        "data": (
            "Usa el subconjunto filtrado y un único tipo de evento elegido localmente. El heatmap se construye con los eventos visibles de ese tipo."
        ),
        "what_you_see": [
            "Selector del evento del heatmap.",
            "Barra de contexto con evento, número de eventos usados y límite visual.",
            "Mapa de calor y una breve interpretación.",
        ],
        "how_to_use": [
            "Elige el tipo de acción y revisa dónde se concentra territorialmente.",
            "Úsalo como complemento a `Eventos` cuando quieras menos detalle puntual y más patrón agregado.",
        ],
        "how_to_read": [
            "Las zonas más calientes significan repetición, no éxito.",
            "Una concentración alta puede deberse a estilo de juego, zona táctica habitual o simplemente mayor volumen de muestra.",
        ],
    },
    {
        "name": "🎯 Sistema de análisis > ⚖️ Comparativa",
        "purpose": (
            "Sirve para contrastar rendimientos entre contextos: jugador frente a equipo, jugador frente a otro jugador o perfiles relativos por percentiles."
        ),
        "data": (
            "Usa el contexto filtrado para la comparativa básica y percentiles, y el dataset cargado para la comparativa avanzada entre contextos distintos."
        ),
        "what_you_see": [
            "Jugador vs equipo.",
            "Comparativa avanzada entre dos contextos.",
            "Percentiles para lectura relativa de perfil, con presets identificados por la pareja de métricas comparadas.",
        ],
        "how_to_use": [
            "Usa la comparativa básica para ver si un jugador está por encima o por debajo de su equipo en un tipo de acción.",
            "Usa la comparativa avanzada cuando necesites contrastar dos contextos concretos.",
            "Usa percentiles para detectar perfiles destacados dentro del conjunto comparado.",
        ],
        "how_to_read": [
            "Comparar contextos distintos exige prudencia: rival, muestra, fase del partido y volumen pueden sesgar la lectura.",
            "En percentiles, un valor alto significa posición relativa alta, no necesariamente rendimiento absoluto mejor en cualquier situación.",
            "Las métricas de riesgo deben invertirse mentalmente: más alto puede significar más volumen negativo.",
        ],
    },
    {
        "name": "🎯 Sistema de análisis > 🗺️ Voronoi/Delaunay",
        "purpose": (
            "Explica espacialmente un pase fallido mediante geometría, proximidad y heurísticas de recomendación."
        ),
        "data": (
            "Combina eventos filtrados con datos StatsBomb 360. Solo analiza acciones con freeze-frame disponible, es decir, eventos en los que se conoce la disposición visible de jugadores alrededor de la acción."
        ),
        "what_you_see": [
            "Selector de un pase fallido concreto con freeze-frame.",
            "Módulo `Voronoi` con subapartados de `Vista`, `Métricas` y `Alternativas`.",
            "Módulo `Delaunay` con subapartados de `Red`, `Conexiones` y `Alternativas`.",
            "Visualizaciones de freeze-frame, Voronoi, Delaunay y combinación de ambas.",
            "Tablas de áreas, vecindades, distancias entre puntos y comparación entre métodos.",
        ],
        "how_to_use": [
            "Selecciona un caso con freeze-frame y recorre primero la visualización real del pase fallido.",
            "Después añade Voronoi o Delaunay para entender espacio, influencia y conectividad local.",
            "Usa las alternativas para discutir opciones de pase, no para imponer una solución única.",
        ],
        "how_to_read": [
            "Voronoi representa zonas de influencia aproximadas, no control real garantizado del espacio.",
            "Delaunay modela conectividad geométrica local, no líneas de pase automáticamente viables.",
            "En esta pestaña, las distancias deben leerse como unidades de campo StatsBomb y las áreas como unidades cuadradas del mismo sistema.",
            "Solo tiene sentido hablar de metros o metros cuadrados como equivalencia aproximada si se adopta expresamente el supuesto de un campo estándar.",
            "Las recomendaciones son interpretables y útiles para argumentar, pero no sustituyen orientación corporal, velocidad, timing o ejecución técnica.",
        ],
    },
    {
        "name": "🎯 Sistema de análisis > ⚠️ Pérdidas",
        "purpose": (
            "Integra el análisis de pérdidas de balón y pases fallidos en una única vista para localizar acciones negativas y decidir si merece la pena revisarlas espacialmente."
        ),
        "data": (
            "Parte del subconjunto filtrado y agrega pérdidas generales, pérdidas por tipo y pases fallidos dentro del mismo contexto."
        ),
        "what_you_see": [
            "KPIs y tablas de pérdidas.",
            "Bloque integrado de pases fallidos.",
            "Acceso directo al caso espacial cuando el evento tiene soporte 360.",
        ],
        "how_to_use": [
            "Úsala para localizar errores con impacto potencial y decidir después si conviene llevar un caso concreto a Voronoi/Delaunay.",
            "Si aparece acceso al análisis espacial, úsalo para saltar directamente al evento seleccionado.",
        ],
        "how_to_read": [
            "Una pérdida no tiene siempre la misma gravedad táctica; el contexto del partido y la zona del campo importan.",
            "Los pases fallidos deben leerse junto a su localización, volumen y contexto de riesgo.",
        ],
    },
    {
        "name": "🗂️ Datos y depuración",
        "purpose": (
            "Permite inspeccionar directamente el subconjunto de datos que la app está usando en el contexto filtrado."
        ),
        "data": (
            "Muestra el dataframe procesado ya filtrado por partido, equipo, jugador y minutos según el filtro global. No enseña el dataset completo si el contexto ya ha sido reducido."
        ),
        "what_you_see": [
            "KPIs de filas, columnas y partidos del subconjunto activo.",
            "Rutas y descripción de los ficheros principales usados por la app.",
            "Tabla del subconjunto actualmente visible para la aplicación.",
        ],
        "how_to_use": [
            "Úsala para validar que una conclusión de otra pestaña se apoya en los datos que crees estar viendo.",
            "Si sospechas que un filtro no está actuando bien, esta es la vista de comprobación.",
        ],
        "how_to_read": [
            "Cada fila representa un evento del subconjunto filtrado.",
            "No es una vista interpretativa, sino una vista de verificación y trazabilidad.",
            "Si aquí los datos no coinciden con tu expectativa, el problema está en el contexto o en la selección, no en la visualización final.",
        ],
    },
]


def _render_markdown_list(items: list[str]) -> None:
    """Render a flat markdown bullet list."""
    if not items:
        return
    st.markdown("\n".join(f"- {item}" for item in items))


def render_guide_view() -> None:
    """Render a user-facing guide aligned with the current app state."""
    render_page_header(
        "Guía de uso",
        "Manual orientado a una persona externa al desarrollo: qué hace la app, cómo manejar cada vista y cómo interpretar correctamente los datos y resultados.",
        eyebrow="Ayuda",
    )
    st.divider()

    render_section_header(
        "Qué es esta app",
        "Contexto general para entender qué tipo de herramienta estás usando y qué no debes esperar de ella.",
    )
    render_info_box(
        "Marco de lectura",
        (
            "TactiSpace es una aplicación de análisis sobre datos de eventos de fútbol de StatsBomb Euro 2024. "
            "La app no toma decisiones por sí sola: organiza, resume, compara y visualiza un subconjunto de datos "
            "definido por el filtro global. Su valor está en ayudarte a formular y justificar lecturas analíticas "
            "con apoyo visual, tabular y espacial."
        ),
        tone="info",
    )
    st.divider()

    render_section_header(
        "Cómo se usa correctamente",
        "Flujo recomendado para una persona que llega por primera vez a la herramienta.",
    )
    with st.container(border=True):
        st.markdown(
            "\n".join(
                [
                    "1. Ajusta primero el `filtro global`: partido, equipo, jugador y rango de minutos.",
                    "2. Comprueba en `🏟️ Vista general` que el subconjunto visible tiene sentido.",
                    "3. Profundiza después en la vista principal que responde a tu pregunta: `🎯 Sistema de análisis` o `🗂️ Datos y depuración`.",
                    "4. Contrasta siempre una conclusión en más de una vista si es importante.",
                    "5. Revisa `🗂️ Datos y depuración` cuando necesites confirmar qué registros exactos están sosteniendo un resultado.",
                ]
            )
        )
    st.divider()

    render_section_header(
        "Cómo interpretar los datos visibles",
        "Significado de los nombres, contadores y etiquetas que aparecen de forma repetida en la app.",
    )
    with st.container(border=True):
        for label, description in COMMON_LABELS:
            st.markdown(f"**{label}:** {description}")
    st.divider()

    render_section_header(
        "Diccionario de términos de la app",
        "Definiciones de la terminología específica que aparece repetidamente en la interfaz y en las interpretaciones.",
    )
    with st.container(border=True):
        for term, description in APP_TERMS_GLOSSARY:
            st.markdown(f"**{term}:** {description}")
    st.divider()

    render_section_header(
        "Significado de los eventos",
        "Glosario mínimo para usuarios que no están familiarizados con la nomenclatura de StatsBomb.",
    )
    with st.container(border=True):
        for event_name, description in EVENT_GLOSSARY:
            st.markdown(f"**`{event_name}`**: {description}")
    st.divider()

    render_section_header(
        "Guía detallada por vista y subapartado",
        "Qué hace cada bloque funcional, qué datos usa, qué muestra y cómo deben leerse sus resultados dentro de la arquitectura actual de la app.",
    )
    for guide in TAB_GUIDES:
        with st.container(border=True):
            st.markdown(f"### {guide['name']}")
            st.markdown(f"**Qué hace este apartado:** {guide['purpose']}")
            st.markdown(f"**Qué datos maneja:** {guide['data']}")
            st.markdown("**Qué se ve en pantalla:**")
            _render_markdown_list(guide["what_you_see"])
            st.markdown("**Cómo usarla:**")
            _render_markdown_list(guide["how_to_use"])
            st.markdown("**Cómo interpretar sus resultados:**")
            _render_markdown_list(guide["how_to_read"])
    st.divider()

    render_section_header(
        "Advertencias metodológicas",
        "Qué errores de lectura son más comunes al trabajar con esta app.",
    )
    with st.container(border=True):
        st.markdown(
            "\n".join(
                [
                    "- Un volumen alto de acciones no significa automáticamente mejor rendimiento.",
                    "- Un porcentaje alto con pocas acciones puede no ser robusto.",
                    "- Una comparación solo es útil si los contextos comparados son razonablemente homogéneos.",
                    "- Un mapa espacial indica localización y densidad, no calidad por sí mismo.",
                    "- Un percentil alto expresa posición relativa dentro del conjunto comparado, no excelencia universal.",
                    "- Un resultado espacial sugerido no implica que el pase fuera técnicamente ejecutable en la realidad.",
                    "- En Voronoi y Delaunay, las medidas son coherentes dentro del sistema StatsBomb, pero no deben presentarse como metros exactos si no se ha fijado antes una equivalencia física explícita.",
                ]
            )
        )
    st.divider()

    render_section_header(
        "Cómo validar una conclusión",
        "Forma recomendable de pasar de una observación a una lectura mínimamente defendible.",
    )
    with st.container(border=True):
        st.markdown(
            "\n".join(
                [
                    "1. Identifica una señal en `🏟️ Vista general` o en algún subapartado de `🎯 Sistema de análisis`.",
                    "2. Comprueba si esa señal también aparece en otros subapartados, por ejemplo `📋 Eventos`, `🌡️ Mapa de calor` o `⚖️ Comparativa`.",
                    "3. Si la conclusión depende de un caso concreto, revísalo en `🎯 Sistema de análisis > 🗺️ Voronoi/Delaunay` si existe soporte 360.",
                    "4. Confirma en `🗂️ Datos y depuración` que el subconjunto visible es realmente el que querías estudiar.",
                    "5. Expresa siempre tu conclusión junto al contexto del filtro usado.",
                ]
            )
        )
