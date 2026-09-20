## 1. nginx

- [x] 1.1 En `nginx/nginx.conf.template`, reemplazar `${API_RATE_LIMIT_PER_MINUTE}`, `${API_RATE_LIMIT_BURST}`, `${GRANTS_RATE_LIMIT_PER_MINUTE}`, `${GRANTS_RATE_LIMIT_BURST}`, `${API_MAX_CONNECTIONS_PER_IP}` y `${RATE_LIMIT_RETRY_AFTER_SECONDS}` por sus valores literales actuales (600, 50, 30, 5, 20, 5 respectivamente) en cada lugar donde aparecen, y ajustar los comentarios que describen el mecanismo de `RATE_LIMIT_ENABLED=false` para que reflejen que el techo ya es fijo. Verificar con `grep -n 'RATE_LIMIT\|API_RATE\|GRANTS_RATE\|API_MAX_CONNECTIONS' nginx/nginx.conf.template` que no queda ningún `${...}` de los seis.
- [x] 1.2 En `nginx/entrypoint.sh`, quitar las siete variables de `required_vars` (dejando solo `STORAGE_PUBLIC_URL`), eliminar todo el bloque `if [ "$RATE_LIMIT_ENABLED" = "false" ]; then ... fi`, y reducir la lista de `envsubst` a `'${STORAGE_PUBLIC_HOSTNAME}'`. Verificar que el script sigue siendo válido con `sh -n nginx/entrypoint.sh`.

## 2. compose

- [x] 2.1 En `compose.yaml` y `compose.dev.yaml`, quitar del bloque `environment` del servicio `nginx` las siete claves `RATE_LIMIT_ENABLED`, `API_RATE_LIMIT_PER_MINUTE`, `API_RATE_LIMIT_BURST`, `GRANTS_RATE_LIMIT_PER_MINUTE`, `GRANTS_RATE_LIMIT_BURST`, `API_MAX_CONNECTIONS_PER_IP` y `RATE_LIMIT_RETRY_AFTER_SECONDS`, dejando `STORAGE_PUBLIC_URL` como única entrada. Verificar con `docker compose -f compose.dev.yaml config` que el servicio `nginx` ya no las lista.
- [x] 2.2 Levantar `docker compose -f compose.dev.yaml up -d --build postgres storage transformer nginx` y confirmar manualmente que `nginx` arranca sin errores (`docker compose -f compose.dev.yaml logs nginx` no muestra el error de variable faltante de `entrypoint.sh`).

## 3. Documentación de entorno

- [x] 3.1 En `.env.example`, borrar la sección "Rate limiting" completa (las siete variables y su comentario introductorio). Verificar con `grep -n RATE_LIMIT .env.example` que no queda nada.
- [x] 3.2 En `README.md`, quitar la frase que sugiere `RATE_LIMIT_ENABLED=false` para "hammer the API during development" (reemplazarla por una nota de que el techo es fijo y se edita en `nginx/nginx.conf.template` si hace falta un valor distinto), y en la sección "The rate limit and your CDN" quitar la referencia a que los valores viven en `.env` (ya no es cierto). Verificar con `grep -n 'RATE_LIMIT_ENABLED\|API_RATE_LIMIT_PER_MINUTE\|GRANTS_RATE_LIMIT_PER_MINUTE' README.md` que solo queda, si acaso, el nombre del concepto sin implicar que sea configuración de `.env`.

## 4. Tests

- [x] 4.1 Actualizar el docstring de `backend/tests/test_rate_limiting.py` para que ya no diga "requires ... running with RATE_LIMIT_ENABLED=true and the default limits from .env.example", sino que los límites son fijos en `nginx/nginx.conf.template` (mismos valores: 600/50 general, 30/5 grants).
- [x] 4.2 Correr `docker compose -f compose.dev.yaml up -d --build postgres storage transformer nginx` seguido de `cd backend && uv run pytest tests/test_rate_limiting.py` y confirmar que las tres pruebas siguen pasando sin cambios de comportamiento.

## 5. Verificación final

- [x] 5.1 Correr `grep -rn "RATE_LIMIT_ENABLED\|API_RATE_LIMIT_PER_MINUTE\|API_RATE_LIMIT_BURST\|GRANTS_RATE_LIMIT_PER_MINUTE\|GRANTS_RATE_LIMIT_BURST\|API_MAX_CONNECTIONS_PER_IP\|RATE_LIMIT_RETRY_AFTER_SECONDS" --include=*.yaml --include=*.sh --include=*.template --include=*.md --include=*.py .` desde la raíz del repo (excluyendo `openspec/changes` y `.venv`) y confirmar que no queda ninguna referencia fuera de este change y de `openspec/specs/request-throttling` una vez archivado.
