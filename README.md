# TactiSpace

TactiSpace es una aplicacion Streamlit desarrollada como parte de un TFG para
el analisis visual, contextual y espacial de eventos de futbol a partir de
datos de StatsBomb Euro 2024.

## Descripcion

La aplicacion trabaja sobre datasets procesados offline y permite explorar
eventos, perdidas, metricas especificas, comparativas y analisis espaciales
con una interfaz orientada a uso academico y defensa del proyecto.

## Funcionalidades principales

La app incluye las siguientes vistas:

- `Inicio`
- `Resumen`
- `Metricas especificas`
- `Comparativa`
- `Perdidas`
- `Analisis espacial`
- `Eventos`
- `Mapa de calor`
- `Secuencias`
- `Datos brutos`

## Modulo espacial

El modulo `Analisis espacial` trabaja sobre datos `360` normalizados y combina
varias capas:

- `freeze-frame` del evento seleccionado
- diagramas de `Voronoi`
- triangulacion de `Delaunay`
- recomendacion basada en conectividad local mediante `Delaunay`
- recomendacion basada en `scoring` espacial interpretable

Ademas, la vista permite inspeccionar el diagnostico del evento y exportar un
resumen ligero del caso seleccionado.

## Arquitectura de datos

La arquitectura general del proyecto sigue este flujo:

```text
raw -> scripts offline -> parquets normalizados -> app Streamlit
```

Datasets principales:

- `data/processed/events_normalized.parquet`
- `data/processed/lineups_normalized.parquet`
- `data/processed/three_sixty_normalized.parquet`

La app consume estos parquets ya preparados y evita recalcular la normalizacion
en cada arranque.

## Ejecucion

Instalacion de dependencias:

```bash
pip install -r requirements.txt
```

Construccion del pipeline normalizado:

```bash
python scripts/build_all_normalized.py
```

Arranque de la app:

```bash
streamlit run app.py
```

## Validacion offline con statsbombpy

El proyecto incluye una validacion offline para contrastar los parquets
normalizados con `statsbombpy`, sin usar `statsbombpy` dentro de la app
Streamlit.

Ejemplo rapido:

```bash
python scripts/validate_statsbombpy_data.py --limit 3
```

Mas detalle en [docs/data_pipeline.md](docs/data_pipeline.md).

## Estructura resumida

```text
.
|-- app.py
|-- README.md
|-- requirements.txt
|-- data/
|   |-- raw/
|   `-- processed/
|-- docs/
|   |-- data_pipeline.md
|   `-- spatial_methodology.md
|-- scripts/
|-- src/
`-- tests/
```

## Documentacion relacionada

- [docs/data_pipeline.md](docs/data_pipeline.md)
- [docs/spatial_methodology.md](docs/spatial_methodology.md)
