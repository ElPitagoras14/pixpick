## 1. La comprobación automática, primero

Va primero a propósito: su salida enumera el trabajo de las fases siguientes y sirve de medidor de avance. Queda en rojo hasta la tarea 8.1, que es cuando tiene que pasar.

- [x] 1.1 Crear `backend/tests/test_documentation_conventions.py` con la derivación de nombres prohibidos: capabilities desde los directorios de `openspec/specs/`, changes desde los de `openspec/changes/archive/` con el prefijo de fecha quitado. Verificar en una corrida que la lista derivada contiene las 27 capabilities y los 24 changes archivados, y que el archivo de la prueba no contiene ninguna de esas cadenas escrita a mano.
- [x] 1.2 Agregar la extracción de comentarios por tipo de archivo: Python con `tokenize` más docstrings con `ast`, TypeScript quitando literales de cadena antes de tomar `//` y `/* */`, YAML/`.conf`/`.env`/Dockerfile por línea que empieza con `#`, Markdown entero. Verificar con un caso por tipo que una URL con `//` dentro de una cadena no se toma como comentario y que un comentario de bloque multilínea sí se extrae completo.
- [x] 1.3 Agregar las tres búsquedas —nombre de capability y nombre de change sobre el archivo entero, `D<n>` solo sobre el texto de comentarios— y las exclusiones de `openspec/`, `local/`, `CLAUDE.md`, `.claude/`, `.agents/`, `frontend/AGENTS.md`, `node_modules`, `.venv`, `__pycache__`, `dist` y `dbmate/schema.sql`. Verificar que el mensaje de fallo nombra archivo, línea y la cadena que disparó.
- [x] 1.4 Correr la prueba y guardar su salida como lista de trabajo. Verificar que enumera del orden de 850 apariciones repartidas en `backend/src`, `backend/tests`, `frontend/src`, los dos compose, `nginx/`, `dbmate/` y `.env.example`, y que no señala ningún archivo excluido.

## 2. `.env.example`

- [x] 2.1 Reescribir el archivo en dos bloques, `MUST CONFIGURE` y `OPTIONAL`, con los seis grupos adentro de cada uno: red, base de datos, identidad, object storage, variantes de imagen y límites. Ubicar cada variable según las tres condiciones del criterio y verificar el resultado contra el reparto nominal escrito en el diseño, variable por variable.
- [x] 2.2 Dejar una sola nota por variable, solo donde el nombre y el valor de ejemplo no alcanzan, con los valores enumerados en las de conjunto cerrado y un puntero corto al README en `STORAGE_PUBLIC_URL`. Verificar que ninguna explicación del archivo se repite en el README y que el archivo queda en inglés.
- [x] 2.3 Verificar que la configuración efectiva no cambió: `docker compose -f compose.dev.yaml config` y `docker compose config` resuelven los mismos valores que antes del cambio, comparando las dos salidas.
- [x] 2.4 Verificar el arranque desde cero: `cp .env.example .env` y `docker compose -f compose.dev.yaml up --build` levantan el proyecto sin completar ninguna variable a mano, y `http://localhost:8080` responde.

## 3. `README.md`

- [x] 3.1 Podar las tres secciones que argumentan en vez de instruir —el rate limit frente a un CDN, por qué importa el reconciler, y las tres páginas de `STORAGE_PUBLIC_URL`— dejando la regla que el lector necesita para operar. Verificar que cada una sigue respondiendo qué hacer, y que lo que se fue es la justificación y no el procedimiento.
- [x] 3.2 Corregir el castellano suelto en el texto en inglés (`plazo`, en la sección del reconciler) y verificar que no queda ninguna otra palabra fuera de idioma leyendo el archivo entero.
- [x] 3.3 Verificar que el documento sigue cumpliendo su requirement vigente: alguien que nunca vio el proyecto puede levantarlo, correr las pruebas y ubicar dónde tocar cada cosa sin abrir ninguna spec.

## 4. Entorno: compose, nginx y dbmate

- [x] 4.1 Limpiar `compose.yaml` y `compose.dev.yaml`, incluido el bloque del techo de memoria que se repite ocho veces en cada uno, conservando el porqué y quitando la procedencia. Verificar que los dos archivos siguen difiriendo solo en lo que `test_compose_conventions.py` permite, corriendo esa prueba.
- [x] 4.2 Limpiar `nginx/` y `dbmate/`. Verificar que `docker compose -f compose.dev.yaml up nginx` sigue levantando y que el healthcheck responde por el punto de entrada.

## 5. `backend/src`

Por subárbol, para que cada diff se revise entero. En cada uno se aplican las tres preguntas del criterio archivo por archivo.

- [x] 5.1 Raíz del paquete: `config.py`, `main.py`, `models.py`, `exceptions.py`, `handlers.py`. Verificar que `uv run pytest` sigue pasando y que la comprobación de la fase 1 ya no señala estos archivos.
- [x] 5.2 `database/`. Conservar el acoplamiento de los tres timeouts con la unidad que toman los GUC de Postgres. Verificar con `uv run pytest tests/test_database_timeouts.py tests/test_data_access.py`.
- [x] 5.3 `identity/`. Verificar con `uv run pytest tests/identity`.
- [x] 5.4 `images/` y `storage/`. Conservar el acoplamiento de `IMAGE_SIGNING_KEY`/`SALT` con `IMGPROXY_KEY`/`IMGPROXY_SALT` del servicio transformer. Verificar con `uv run pytest tests/images tests/storage`.
- [x] 5.5 `maintenance/` y `packages/`. Verificar con `uv run pytest tests/maintenance tests/packages`.
- [x] 5.6 Verificar el subárbol completo: la comprobación de la fase 1 no señala ningún archivo de `backend/src`, y `uv run ruff format .` y `uv run ruff check .` pasan limpios.

## 6. `backend/tests`

- [x] 6.1 Limpiar los archivos de prueba conservando el comentario que describe el escenario, que es lo que el código de la prueba no dice. Verificar que `uv run pytest` sigue pasando y que ninguna prueba cambió de comportamiento.
- [x] 6.2 Reescribir el docstring de `test_code_conventions.py`, que hoy tiene una línea duplicada y cortada a la mitad. Verificar que el docstring resultante describe las dos reglas que el archivo comprueba y se lee de corrido.

## 7. `frontend/src`

- [x] 7.1 `api.ts`, `config.ts`, `router.tsx` y el resto de la raíz. Verificar con `pnpm lint` y `pnpm build`.
- [x] 7.2 `features/`, subcarpeta por subcarpeta. Verificar con `pnpm lint` después de cada una.
- [x] 7.3 `routes/` y `components/`. Verificar con `pnpm build` y abriendo la aplicación.
- [x] 7.4 Verificar el subárbol completo: la comprobación de la fase 1 no señala ningún archivo de `frontend/src`, y `pnpm format` y `pnpm lint` pasan limpios.

## 8. Cierre

- [x] 8.1 Traducir al inglés los dos docstrings en castellano de `identity/adapters/google.py` y `identity/adapters/local.py`, y verificar que no queda ningún otro comentario fuera de idioma en `backend/src` ni en `frontend/src`.
- [x] 8.2 Verificar que la comprobación de la fase 1 pasa en verde sobre el repositorio entero, que es lo que cierra el change.
- [x] 8.3 Verificar la suite completa y los linters: `uv run pytest`, `uv run ruff format .` y `uv run ruff check .` en `backend/`, `pnpm format` y `pnpm lint` en `frontend/`.
- [x] 8.4 Verificar de punta a punta con un clon limpio del árbol de trabajo: `cp .env.example .env`, `docker compose -f compose.dev.yaml up --build`, crear un álbum, subir una foto y calificarla.
