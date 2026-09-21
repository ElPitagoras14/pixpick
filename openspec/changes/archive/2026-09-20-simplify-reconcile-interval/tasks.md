## 1. Confirmar que la implementación ya es la que el delta describe

Este change no escribe código: alinea la spec con lo que `6e26e40` dejó. Las tareas de esta fase son comprobaciones, no cambios, y si alguna falla el change necesita código además del delta.

- [x] 1.1 Verificar que el intervalo está fijo en el código y en los dos archivos a la vez: `grep -n "sleep 300" compose.yaml compose.dev.yaml` devuelve una línea por archivo, dentro del `command` del servicio `reconciler`.
- [x] 1.2 Verificar que no queda ningún rastro de un intervalo configurable: buscar `RECONCILE_INTERVAL` en el código, en los dos compose, en `.env.example` y en `README.md` no devuelve nada fuera de `openspec/`.
- [x] 1.3 Verificar que la limpieza sigue siendo invocable a mano, que es lo único del requirement que este change no toca: `cd backend && uv run python -m src.maintenance.reconcile` corre y termina sin error con el entorno arriba.
- [x] 1.4 Verificar que los dos compose siguen declarando lo mismo: `cd backend && uv run pytest tests/test_compose_conventions.py` pasa.

## 2. Cerrar el change

- [x] 2.1 Verificar que el delta aplica sobre el requirement vigente sin perder nada: el bloque de `MODIFIED Requirements` conserva los cinco scenarios que el requirement ya tenía, agrega el de que cambiar el ritmo exige tocar el código, y solo cambia el texto de la frecuencia y el de «La limpieza ocurre sola».
- [x] 2.2 Verificar que `openspec validate simplify-reconcile-interval --strict` pasa.
