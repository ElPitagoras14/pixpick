## Why

Cada explicación del repositorio arrastra la procedencia de su decisión: `(api-conventions spec, added by add-albums-and-upload)`, `(D10 in harden-local-profile's design)`, `(task 6.3 in harden-local-profile)`. Son unas 850 marcas repartidas por `backend/src`, `backend/tests`, `frontend/src`, los dos archivos de compose, `nginx/` y `.env.example`. Sirvieron mientras el change se escribía; ahora le cobran a quien lee el código un salto a un artefacto archivado para entender una línea que casi siempre se explica sola, y alrededor de la referencia creció el hábito de argumentar la alternativa descartada, que es material de decisión y no de lectura. En paralelo, `.env.example` marca `Required` treinta y pico de variables sin distinguir la que no arranca sin un valor propio de la que trae un default con el que se trabaja sin tocarla, así que la pregunta más básica —qué tengo que llenar antes de levantar esto— no tiene respuesta en el archivo que existe para responderla.

## What Changes

- Ninguna explicación del repositorio nombra una spec, un change ni una decisión numerada. El detalle de cada decisión sigue donde corresponde, en `openspec/specs/` y en `openspec/changes/archive/`, y el código deja de duplicarlo.
- Un comentario sobrevive solo si dice algo que el código no dice: lo contraintuitivo, el acoplamiento que no se ve desde el archivo, o la consecuencia de cambiar el valor. Se va la paráfrasis del código y la argumentación de alternativas descartadas.
- `README.md` deja de argumentar. Las tres secciones que hoy defienden una decisión en vez de instruir —el rate limit frente a un CDN, por qué el reconciler importa, y las tres páginas de `STORAGE_PUBLIC_URL`— quedan en la regla que el lector necesita para operar.
- `.env.example` se reordena en dos bloques, el que hay que configurar y el opcional, cada uno agrupado por área: red, base de datos, identidad, object storage, variantes de imagen y límites. Cada variable de opciones cerradas lista sus valores, y las que el nombre no explica conservan cómo llenarlas.
- Una comprobación automática en la suite falla si una referencia a una spec, a un change o a una decisión numerada vuelve a aparecer en cualquier archivo del repositorio.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `project-documentation`: gana dos requirements. Uno generaliza a todo el repositorio la prohibición que hoy pesa solo sobre el documento de entrada: ninguna explicación, viva donde viva, remite a una spec, a un change ni a una decisión numerada. El otro gobierna la forma del archivo de ejemplo de variables de entorno, que hoy ninguna capability cubre: `local-environment` exige que exista y que esté completo, no que se pueda leer.
- `code-conventions`: gana un requirement sobre cuándo existe un comentario. Es exactamente el tipo de regla que esta capability declara gobernar —la que ninguna herramienta trae resuelta y que hoy se decide imitando el archivo de al lado—, y cae bajo su requirement vigente de que toda regla suya tenga comprobación automática.

## Impact

- `README.md` y `.env.example`.
- `compose.yaml`, `compose.dev.yaml`, `nginx/` y `dbmate/`.
- `backend/src` (69 de 89 archivos), `backend/tests` (incluido el docstring de `test_code_conventions.py`, que hoy tiene una línea duplicada y a medio escribir) y `frontend/src` (36 de 55 archivos).
- La suite gana una comprobación que recorre el repositorio, del mismo tipo que las de `test_code_conventions.py` y `test_compose_conventions.py`, que ya leen archivos fuera de `backend/`.
- Ningún cambio de comportamiento: no se toca lógica, ni firmas, ni configuración efectiva. `docker compose config` resuelve los mismos valores antes y después.
- Quedan fuera `openspec/specs/`, `openspec/changes/archive/`, `CLAUDE.md`, `local/`, `.claude/`, `.agents/` y `frontend/AGENTS.md`, que es generado.
