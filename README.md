# TactiSpace

TactiSpace es una aplicacion Streamlit desarrollada como parte de un TFG para
el analisis visual, contextual y espacial de eventos de futbol a partir de
datos de StatsBomb Euro 2024.

La aplicacion se apoya en una arquitectura modular por capas, datasets
normalizados generados offline y una suite de tests orientada a cubrir la
logica principal del sistema.

## Estructura funcional de la aplicacion

La interfaz se estructura en tres vistas principales:

- `Vista general`: espacio de contexto con `Inicio`, `Resumen` y `Guia`.
- `Sistema de analisis`: bloque principal de trabajo con `Metricas especificas`,
  `Eventos`, `Mapa de calor`, `Comparativa`, `Voronoi/Delaunay` y `Perdidas`.
- `Datos y depuracion`: vista tecnica para inspeccionar el subconjunto filtrado
  y validar el contexto aplicado.

Los filtros globales de partido, equipo, jugador y tramo temporal se comparten
entre vistas. La app tambien muestra indicadores de contexto filtrado y aplica
carga diferida para los datos `360`, que solo se leen cuando el usuario entra
en el analisis espacial.

## Capacidades principales

- Exploracion de eventos filtrados por partido, equipo, jugador y minutos.
- Calculo de metricas basicas y metricas especificas por tipo de accion.
- Comparativa entre contextos de juego.
- Analisis de perdidas y pases fallidos.
- Visualizaciones espaciales con `freeze-frame`, diagramas de `Voronoi`,
  triangulacion de `Delaunay` y recomendacion interpretable de pase.
- Vista de datos y depuracion para revisar las filas reales que sostienen cada
  conclusion.

## Arquitectura del proyecto

La estructura del proyecto separa responsabilidades de forma explicita:

- `src/repositories`: acceso a datos y cache de lectura.
- `src/services`: orquestacion de contexto, filtros, exportacion y analisis.
- `src/core`: logica de dominio para metricas, reglas, modelos y espacial.
- `src/state`: gestion del estado de sesion y navegacion.
- `src/ui`: vistas, componentes, estilos y presentadores de Streamlit.
- `scripts`: construccion offline de datasets y validaciones externas.

El punto de entrada es `app.py`, que inicializa la sesion, carga los eventos,
construye el contexto comun y enruta la navegacion principal.

## Datos y pipeline

La app prioriza datasets normalizados generados offline para reducir el trabajo
en cada arranque:

```text
datos raw -> scripts offline -> parquets normalizados -> app Streamlit
```

Archivos principales usados por la aplicacion:

- `data/processed/events_normalized.parquet`
- `data/processed/lineups_normalized.parquet`
- `data/processed/three_sixty_normalized.parquet`

Fuentes auxiliares del dataset:

- `data/raw/statsbomb/euro_2024/matches.json`
- `data/raw/statsbomb/euro_2024/lineups/`
- `data/raw/statsbomb/euro_2024/three_sixty/`

La aplicacion puede apoyarse en `data/processed/events.parquet` como origen
base, aunque el flujo recomendado consiste en trabajar con los datasets
normalizados.

## Puesta en marcha

Crear y activar un entorno virtual:

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Construir el pipeline normalizado:

```bash
python scripts/build_all_normalized.py
```

Lanzar la aplicacion:

```bash
streamlit run app.py
```

Validar offline los datos normalizados frente a `statsbombpy`:

```bash
python scripts/validate_statsbombpy_data.py --limit 3
python scripts/validate_statsbombpy_data.py --all
```

`statsbombpy` se utiliza como herramienta de contraste offline y no forma parte
del flujo interactivo de la aplicacion en Streamlit.

## Testing

El repositorio incluye una suite de tests organizada por capas:

- `tests/compat`
- `tests/core`
- `tests/repositories`
- `tests/services`
- `tests/state`
- `tests/ui`

Comandos utiles:

```bash
python -m pytest
python -m pytest --cov=src --cov-report=term-missing
```

Estado verificado en este repositorio:

- `216` tests superados.
- `90%` de cobertura sobre `src` con la configuracion actual de `.coveragerc`.

## Estructura resumida

```text
.
|-- app.py
|-- README.md
|-- requirements.txt
|-- data/
|   |-- processed/
|   |-- raw/
|   `-- sample/
|-- docs/
|   |-- data_pipeline.md
|   |-- performance.md
|   `-- spatial_methodology.md
|-- notebooks/
|-- scripts/
|-- sql/
|-- src/
|   |-- config/
|   |-- core/
|   |-- repositories/
|   |-- services/
|   |-- state/
|   `-- ui/
`-- tests/
```

## Documentacion relacionada

- [docs/data_pipeline.md](docs/data_pipeline.md)
- [docs/performance.md](docs/performance.md)
- [docs/spatial_methodology.md](docs/spatial_methodology.md)

## Fuente de datos y atribucion

<p align="center">
  <img
    src="https://raw.githubusercontent.com/statsbomb/open-data/master/img/SB%20-%20Icon%20Lockup%20-%20Colour%20positive.png"
    alt="StatsBomb logo"
    width="260"
  />
</p>

Los datos utilizados en este proyecto proceden de `StatsBomb Open Data`. En la
memoria, la documentacion y cualquier publicacion o presentacion derivada de
este trabajo, la fuente de datos se citara expresamente como `StatsBomb`.

Cuando sea necesario incluir identidad visual asociada a esa fuente, se
utilizara el logo oficial y los recursos de marca publicados por StatsBomb en
su [Media Pack](https://statsbomb.com/media-pack/).
