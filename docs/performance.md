# Rendimiento

## Datasets normalizados

La app prioriza los parquets normalizados para evitar repetir trabajo en cada arranque:

- `data/processed/events_normalized.parquet`
- `data/processed/lineups_normalized.parquet`
- `data/processed/three_sixty_normalized.parquet`

Generacion offline:

```bash
python scripts/build_all_normalized.py
```

## Que se calcula offline

- normalizacion base de eventos
- columnas derivadas reutilizables
- metadatos de jugador y posicion desde lineups
- normalizacion de freeze-frame / 360
- optimizacion de tipos

## Que se calcula bajo demanda

- percentiles
- comparativa avanzada
- secuencias
- freeze-frame y Voronoi

## Carga diferida de datos 360

Los datos 360 no se cargan al iniciar la app. `three_sixty_normalized.parquet` se usa solo cuando el usuario entra en `Analisis espacial`.
