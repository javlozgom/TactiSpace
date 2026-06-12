# Data Pipeline

La app trabaja preferentemente con datasets normalizados generados offline. El objetivo es desacoplar la preparación de datos del arranque de Streamlit y mantener tiempos de carga razonables.

## Flujo general

```text
datos raw -> scripts offline -> parquets normalizados -> app Streamlit
```

Pipeline recomendado:

```bash
python scripts/build_all_normalized.py
```

## Parquets normalizados

El pipeline genera estos archivos en `data/processed/`:

- `events_normalized.parquet`
- `lineups_normalized.parquet`
- `three_sixty_normalized.parquet`

## Rol de cada parquet

- `events_normalized.parquet`: dataset principal de eventos consumido por la app.
- `lineups_normalized.parquet`: metadatos de jugadores, equipos y posiciones usados para enriquecer el análisis.
- `three_sixty_normalized.parquet`: base para freeze-frames y análisis espacial en la vista `Análisis espacial`.

## Uso dentro de la app

- Streamlit no ejecuta la normalización de datos al arrancar.
- La app lee los parquets ya preparados desde `data/processed/`.
- `three_sixty_normalized.parquet` solo se utiliza cuando se entra en `Análisis espacial`.
- `statsbombpy` no se usa dentro de Streamlit ni forma parte del flujo interactivo de la app.

## Validación offline con statsbombpy

El proyecto incluye un script de validación offline para comparar métricas básicas de los parquets normalizados con datos recuperados mediante `statsbombpy`.

Este paso:

- no modifica los parquets
- no altera el pipeline actual
- no afecta al arranque de Streamlit
- sirve como comprobación externa de consistencia

Comandos disponibles:

```bash
python scripts/validate_statsbombpy_data.py --limit 3
python scripts/validate_statsbombpy_data.py --all
python scripts/validate_statsbombpy_data.py --match-id 3943043
```

El script genera un informe CSV en:

```text
data/processed/validation_statsbombpy_report.csv
```

## Resumen operativo

1. Instalar dependencias:

```bash
pip install -r requirements.txt
```

2. Construir datasets normalizados:

```bash
python scripts/build_all_normalized.py
```

3. Validar offline si se desea:

```bash
python scripts/validate_statsbombpy_data.py --limit 3
```

4. Lanzar la app:

```bash
streamlit run app.py
```
