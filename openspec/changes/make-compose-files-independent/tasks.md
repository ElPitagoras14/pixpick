## 1. Línea base

- [x] 1.1 Guardar fuera del repositorio la salida de `docker compose -f compose.yaml -f compose.dev.yaml config` del estado actual, con el juego local de proveedores activo, y verificar que contiene los siete servicios con su bloque `environment`: es la referencia contra la que se compara el archivo nuevo, y sin ella no hay forma de demostrar que reescribirlo no cambió ningún valor.

## 2. El archivo de desarrollo declara el entorno entero

- [x] 2.1 Escribir en `compose.dev.yaml` los siete servicios completos: copiar de `compose.yaml` el `environment`, el `depends_on`, los healthchecks, los volúmenes, el `command`, el `entrypoint` y la red, reemplazar `image:` por `build:` en los cuatro que se construyen, y conservar los puertos que ya publicaba (D1, D4). Verificar que `docker compose -f compose.dev.yaml config` lista los siete y no reporta referencias rotas.
- [x] 2.2 Verificar contra la línea base de 1.1 que el entorno resuelto es idéntico salvo por la imagen de los cuatro servicios que se construyen: en particular que `DATABASE_URL` sigue apuntando al host `postgres`, que `MINIO_SERVER_ENDPOINT` sigue siendo `http://storage:9000`, y que los nombres renombrados de `storage` y `transformer` llegan con los mismos valores.
- [x] 2.3 Verificar que el archivo se levanta solo: con volúmenes borrados, `docker compose -f compose.dev.yaml up --build`, la aplicación responde en el navegador y una subida se completa, sin nombrar `compose.yaml` en ningún comando.

## 3. El archivo de producción deja de tener perfiles

- [x] 3.1 Quitar `profiles: ["local"]` de `storage` y de `transformer`, y el `required: false` del `depends_on` del backend hacia `storage` (D3). Verificar que `docker compose config`, sin ninguna variable de perfil, lista los siete servicios y que el `depends_on` del backend queda en `required: true`.
- [x] 3.2 Reescribir los comentarios de `compose.yaml` que lo describen como la mitad de un par o que explican el perfil local (D6). Verificar que ningún comentario del archivo remite a `compose.dev.yaml` para completar lo que declara, ni menciona perfiles.
- [x] 3.3 Verificar la consecuencia de declarar siempre los dos servicios locales: con `STORAGE_PROVIDER=r2` e `IMAGE_PROVIDER=imagekit`, levantar el entorno y comprobar que el backend arranca, que `storage` y `transformer` quedan levantados, y que nada falla por que nadie los consulte.

## 4. Las dos declaraciones no se separan

- [x] 4.1 Agregar `pyyaml` al grupo de dependencias de desarrollo de `backend/pyproject.toml` (D5), y verificar que `uv sync` lo instala y que deja de ser una dependencia transitiva sin declarar.
- [x] 4.2 Escribir en `backend/tests/` la comprobación que lee los dos archivos y falla ante cualquier diferencia que no sea `image` contra `build`, o los puertos publicados (D4, D5), junto a la de convenciones de código que ya existe. Verificar que pasa sobre los dos archivos ya corregidos.
- [x] 4.3 Verificar que la comprobación detecta una divergencia real y no solo pasa: cambiar a mano un valor compuesto en uno de los dos archivos, comprobar que falla nombrando el servicio y el campo que difieren, y deshacer el cambio.

## 5. El archivo de ejemplo

- [x] 5.1 Quitar `COMPOSE_FILE`, `COMPOSE_PATH_SEPARATOR` y `COMPOSE_PROFILES` de `.env.example` (D1, D3). Verificar recorriendo el archivo que cada variable restante sigue teniendo un consumidor en alguna de las dos declaraciones, y que ninguna que el entorno requiera quedó fuera.
- [x] 5.2 Verificar que las marcas por variable siguen siendo ciertas después de quitar esas tres: ninguna debe seguir condicionada a `COMPOSE_PROFILES`, que ya no existe.
- [x] 5.3 Verificar copiando `.env.example` a un `.env` limpio y levantando con `docker compose -f compose.dev.yaml up --build`: arranca, y lo único que hubo que ajustar fueron secretos.

## 6. El documento de entrada

- [x] 6.1 Reescribir la sección de arranque del README para que presente las dos formas de levantar el proyecto y diga cuándo se usa cada una (D6). Verificar que queda dicho, sin abrir ningún otro archivo, cuál es la de desarrollo y cuál la que consume imágenes publicadas.
- [x] 6.2 Actualizar cada comando del documento a la forma que corresponda —`-f compose.dev.yaml` para los de desarrollo, ninguno para los otros— y verificar ejecutando cada comando tal como está escrito.
- [x] 6.3 Quitar del README lo que se apoyaba en las variables que se van: la frase que dice que ningún comando lleva `-f`, y la nota de la tabla de servicios sobre `COMPOSE_PROFILES`. Verificar con una búsqueda que no queda ninguna mención a las tres.
- [x] 6.4 Actualizar el docstring de `backend/tests/images/test_variant_contract.py`, que todavía indica levantar los servicios con dos `-f`, y verificar que el comando que indica funciona tal como está escrito.
- [x] 6.5 Revisar las oraciones nuevas del README contra las dos reglas del spec de documentación —una idea por oración, y ninguna palabra técnica que no nombre algo que la persona escribe, ejecuta o ve— y corregir las que no pasen.

## 7. Verificación final

- [x] 7.1 Verificar la migración de un `.env` existente: con las tres variables todavía declaradas, comprobar que `docker compose` a secas fusiona los dos archivos completos sin dar error —que es el fallo silencioso que el plan de migración previene—, borrarlas, y comprobar que el mismo comando vuelve a significar la forma que consume imágenes publicadas.
- [x] 7.2 Verificar que alternar entre las dos formas conserva los datos: levantar con una, subir una foto, levantar con la otra, y comprobar que la foto sigue viéndose.
- [x] 7.3 Verificar el trabajo fuera de los contenedores con la forma nueva: levantar solo los servicios de terceros con `-f compose.dev.yaml`, correr el backend con `uv` contra ellos, y comprobar que una subida se completa.
- [x] 7.4 Correr `openspec validate --changes make-compose-files-independent --strict` y verificar que pasa.
- [x] 7.5 Correr la suite completa del backend junto con `ruff format` y `ruff check` sobre `backend/`, y verificar que todo termina limpio.
