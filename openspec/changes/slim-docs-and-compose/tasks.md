## 1. Línea base

- [x] 1.1 Guardar la salida de `docker compose -f compose.yaml -f compose.dev.yaml config` del estado actual en un archivo fuera del repositorio, y verificar que contiene el bloque `environment` de los siete servicios: es la referencia contra la que se compara al final, y sin ella no hay forma de demostrar que declarar el entorno en el archivo dev no cambió ningún valor.

## 2. El almacenamiento queda listo al arrancar

- [x] 2.1 Agregar `StorageNotReadyError` a `backend/src/storage/exceptions.py`, derivada de `StorageError` (D3), y verificar con un test que un consumidor que capture `StorageError` la atrapa.
- [x] 2.2 Agregar al Protocol `StoragePort` la operación que deja el almacenamiento listo, asíncrona como las otras dos de red (D1), y verificar que `backend/tests/storage/test_port.py` comprueba que está en el contrato.
- [x] 2.3 Implementarla en `backend/src/storage/adapters/minio.py`: comprobar si el espacio existe y crearlo cuando falte (D2). Verificar con `backend/tests/storage/test_minio_adapter.py` que sobre un espacio ausente lo crea y sobre uno existente no lo toca.
- [x] 2.4 Implementarla en `backend/src/storage/adapters/r2.py`: comprobar y levantar `StorageNotReadyError` si el espacio no está, sin intentar crearlo (D2, D3). Verificar con un test que el caso ausente levanta esa excepción y no otra.
- [x] 2.5 Implementarla en el doble de `backend/tests/fakes.py`, y verificar que la suite existente sigue pasando sin cambios en sus casos actuales.
- [x] 2.6 Extender `backend/tests/storage/test_contract.py` con el caso nuevo —tras invocarla el espacio está listo, y repetirla no falla ni altera el contenido—, y verificar que corre sin modificaciones contra el doble y contra MinIO real.
- [x] 2.7 Invocarla en el `lifespan` de `backend/src/main.py`, después de la comprobación de conectividad de la base (D1). Verificar arrancando el backend contra un almacenamiento sin espacio con el proveedor externo activo: el proceso no llega a atender peticiones y el error nombra el problema.
- [x] 2.8 Correr `ruff format` y `ruff check` en `backend/`, y la suite completa con `pytest`, y verificar que ambas terminan limpias.

## 3. El entorno deja de crear el bucket

- [x] 3.1 Eliminar el servicio `storage-init` de `compose.yaml` y borrar `storage/init.sh` junto con el directorio `storage/` (D5). Verificar que `docker compose config` ya no lista el servicio y no reporta referencias rotas.
- [x] 3.2 Cambiar el `depends_on` de `transformer` para que espere al almacenamiento sano en vez del servicio eliminado (D5), y verificar que el entorno levanta con el perfil local.
- [x] 3.3 Cambiar el `depends_on` del backend a las migraciones completas más el almacenamiento sano, conservando `required: false` (D5). Verificar con el perfil cloud —sin `COMPOSE_PROFILES`— que el proyecto resuelve sin el servicio `storage` y sin error.
- [x] 3.4 Quitar de `compose.yaml` los comentarios que explican variables, dejando los que solo se entienden leyendo ese archivo. Verificar que ningún comentario restante describe qué valores admite una variable ni por qué se eligió el suyo.
- [x] 3.5 Verificar el ciclo completo de un clon limpio: con volúmenes borrados, levantar el entorno y subir una foto, sin crear el bucket a mano.

## 4. El archivo dev declara qué recibe cada servicio

- [x] 4.1 Agregar a cada servicio de `compose.dev.yaml` su bloque `environment` nombrando las variables que recibe, sin valores (D4), y dejando fuera `DATABASE_URL` y `MINIO_SERVER_ENDPOINT`.
- [x] 4.2 Declarar en `storage` y `transformer` el mapeo de nombres que cada uno espera, con la variable de `.env` de la que sale (D4). Verificar que el entorno levanta y que MinIO acepta las credenciales.
- [x] 4.3 Verificar contra la línea base de 1.1 que el entorno resuelto de cada servicio es idéntico al anterior salvo por el servicio eliminado: en particular que `DATABASE_URL` sigue apuntando al host `postgres` y `MINIO_SERVER_ENDPOINT` al host `storage`, y no a los valores de modo native.

## 5. El archivo de ejemplo

- [x] 5.1 Agregar `COMPOSE_FILE` y `COMPOSE_PATH_SEPARATOR` a `.env.example` (D7), y verificar que `docker compose config` y `docker compose up` funcionan desde la raíz sin pasar ningún `-f`.
- [x] 5.2 Reescribir el comentario de cada variable dejando solo qué controla, qué valores admite y qué cambia al cambiarla (D6). Verificar con una búsqueda en el archivo que no queda ninguna referencia a un change por su nombre ni ninguna marca de decisión del tipo `D<n>`.
- [x] 5.3 Marcar cada variable como obligatoria, opcional, u obligatoria bajo condición nombrando la variable y el valor que la activan (D6). Verificar recorriendo el archivo que toda variable tiene exactamente una marca.
- [x] 5.4 Agrupar los tres conjuntos de alternativas —identidad, almacenamiento e imágenes— bajo un encabezado que nombre la variable que decide cuál aplica (D6), y verificar que desde las credenciales de un proveedor se ve sin desplazarse cuál es la variable que las activa.
- [x] 5.5 Reducir la cabecera del archivo a lo que las marcas por variable no cubren, y verificar que lo que queda no repite lo que ya dice cada variable al lado.
- [x] 5.6 Verificar copiando `.env.example` a un `.env` limpio y levantando el entorno: arranca, y lo único que hubo que ajustar fueron secretos.

## 6. El documento de entrada

- [x] 6.1 Reescribir `README.md` con las secciones de D8, en el orden en que alguien las necesita, y verificar que cada una responde una pregunta y no dos.
- [x] 6.2 Actualizar todos los comandos a la forma sin `-f` (D7), y verificar ejecutando cada comando del documento tal como está escrito.
- [x] 6.3 Documentar `docker compose config` como la forma de ver qué recibe cada servicio ya resuelto (D8), y verificar que lo que el documento indica produce esa salida.
- [x] 6.4 Quitar todo párrafo que justifique una decisión y toda referencia a un change por su nombre, y verificar con una búsqueda que no queda ninguna.
- [x] 6.5 Revisar el documento oración por oración contra las dos reglas del spec: una idea por oración, y ninguna palabra técnica que no nombre algo que la persona escribe, ejecuta o ve. Verificar corrigiendo las que no pasen.
- [x] 6.6 Comparar el documento anterior con el nuevo y verificar que ningún procedimiento se perdió: lo que salió son justificaciones, y cualquier procedimiento que no entre en las secciones de D8 es un hallazgo a resolver, no algo que se borra.

## 7. Verificación final

- [x] 7.1 Verificar el modo native sin haber levantado el entorno completo: arrancar solo los servicios de terceros, correr el backend con `uv` contra ellos, y comprobar que el espacio de objetos queda listo y una subida se completa.
- [x] 7.2 Verificar la salida y vuelta de un entorno preexistente: con contenedores de la versión anterior corriendo, aplicar el change, correr `docker compose down --remove-orphans` y levantar de nuevo, comprobando que no queda ningún contenedor huérfano y que las fotos que ya estaban siguen viéndose.
- [x] 7.3 Correr `openspec validate --changes slim-docs-and-compose --strict` y verificar que pasa.
- [x] 7.4 Correr la suite completa del backend junto con `ruff format` y `ruff check` sobre `backend/`, y verificar que todo termina limpio.
