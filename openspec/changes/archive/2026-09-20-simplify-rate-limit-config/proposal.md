## Why

El rate limit de `nginx` (techos generales, techo de grants, conexiones por IP, retry-after, y el interruptor que lo desactiva entero) vive hoy en siete variables de entorno. Ninguna de las siete se ajusta realmente por despliegue: son ceilings técnicos elegidos una vez (600 rpm, 30 rpm para grants, 20 conexiones, 5 segundos de espera) y el interruptor `RATE_LIMIT_ENABLED` solo existe para que desarrollo y la suite de pruebas puedan machacar la API sin tropezar con un límite pensado para tráfico real. Exponerlos como configuración obliga a validarlos al arrancar, a mantenerlos documentados en `.env.example`, y a sustituirlos con `envsubst` en tiempo de arranque, todo para un valor que en la práctica nunca cambia entre entornos. El caso de uso real de `RATE_LIMIT_ENABLED=false` -- probar la API sin límite -- se cubre igual de bien editando la constante en el código cuando hace falta.

## What Changes

- Fijar los seis valores directamente en `nginx/nginx.conf.template` (los mismos que hoy son el default en `.env.example`): 600 rpm / burst 50 para el techo general, 30 rpm / burst 5 para grants, 20 conexiones por IP, y 5 segundos de retry-after.
- **BREAKING**: eliminar `RATE_LIMIT_ENABLED` sin reemplazo. El rate limit queda siempre activo; ya no existe una forma de desactivarlo por configuración.
- **BREAKING**: eliminar `API_RATE_LIMIT_PER_MINUTE`, `API_RATE_LIMIT_BURST`, `GRANTS_RATE_LIMIT_PER_MINUTE`, `GRANTS_RATE_LIMIT_BURST`, `API_MAX_CONNECTIONS_PER_IP` y `RATE_LIMIT_RETRY_AFTER_SECONDS`: dejan de ser variables de entorno y pasan a ser valores fijos en la plantilla de `nginx`.
- Simplificar `nginx/entrypoint.sh`: ya no valida ni sustituye ninguna de esas siete variables (solo sigue derivando `STORAGE_PUBLIC_HOSTNAME` de `STORAGE_PUBLIC_URL`).
- Quitar esas siete variables de los servicios `nginx` en `compose.yaml` y `compose.dev.yaml`, y de `.env.example`.
- Actualizar `backend/tests/test_rate_limiting.py` y `README.md` para que ya no describan el rate limit como configurable ni mencionen `RATE_LIMIT_ENABLED=false` como vía de escape en desarrollo.

## Capabilities

### Modified Capabilities

- `request-throttling`: el requirement "La cantidad de peticiones que un cliente puede hacer tiene un techo configurable" se reemplaza por "La cantidad de peticiones que un cliente puede hacer tiene un techo fijo" — mismos techos general y de grants, pero ya no declarados en la configuración del entorno ni desactivables por ella. El escenario "El techo se puede desactivar" se elimina junto con el requirement anterior.

## Impact

- `nginx/nginx.conf.template`, `nginx/entrypoint.sh`
- `compose.yaml`, `compose.dev.yaml` (servicio `nginx`)
- `.env.example`
- `backend/tests/test_rate_limiting.py`
- `README.md`
- Ningún cambio en el backend de Python: estas variables nunca las lee, solo las consume `nginx`.
