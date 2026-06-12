# Spatial Methodology

Este documento resume la metodología del módulo `Análisis espacial` de la app.

## 1. Freeze-frame

El punto de partida es el `freeze-frame` asociado a un evento concreto, normalmente un pase fallido dentro del contexto filtrado.

Un freeze-frame aporta una instantánea espacial del evento y permite observar:

- posición del actor
- posición de compañeros visibles
- posición de rivales visibles
- localización de inicio y destino del pase

Sin freeze-frame no se ejecuta el análisis espacial completo.

## 2. Voronoi

La capa de `Voronoi` divide el espacio visible del campo en regiones de influencia.

Interpretación:

- cada región representa el área más cercana a un jugador respecto al resto
- permite aproximar cuánto espacio controla cada jugador en ese instante
- sirve como apoyo para el scoring espacial

La app muestra esta información de forma visual y, cuando es posible, también resume áreas por jugador.

## 3. Delaunay

La triangulación de `Delaunay` es la estructura dual de Voronoi y conecta jugadores espacialmente próximos.

Interpretación:

- modela relaciones locales de vecindad
- ayuda a detectar opciones de pase cercanas y conectadas
- proporciona una lectura complementaria a la ocupación de espacio

## 4. Recomendación por conectividad

La recomendación basada en `Delaunay` propone una alternativa de pase usando la conectividad local observada en el freeze-frame.

Idea general:

- parte del actor del evento
- considera compañeros conectados por la triangulación
- prioriza una opción interpretable de proximidad y conectividad

No es un modelo predictivo supervisado; es una heurística espacial explicable.

## 5. Scoring espacial

La recomendación por `scoring` mantiene la heurística principal del proyecto y combina varios factores espaciales.

Según el estado actual de la app, el desglose puede incluir componentes como:

- progresión del pase
- distancia al rival más cercano
- área asociada al espacio disponible
- penalización por distancia del pase
- score final

La app expone este desglose cuando está disponible para facilitar la interpretabilidad.

## 6. Limitaciones

El módulo espacial debe interpretarse como una ayuda analítica, no como una verdad táctica absoluta.

Limitaciones principales:

- depende de la disponibilidad de freeze-frame
- no modela orientación corporal
- no modela velocidad o aceleración
- no garantiza que un pase sea técnicamente ejecutable
- la lectura espacial depende del instante capturado en el snapshot
- las recomendaciones son heurísticas interpretables, no predicciones entrenadas

## 7. Uso dentro del proyecto

Este módulo está integrado en la app Streamlit, pero su cálculo se apoya en datos `360` ya normalizados offline.

No utiliza `statsbombpy` durante la interacción de la app. La validación con `statsbombpy` se realiza fuera de Streamlit mediante scripts offline. 
