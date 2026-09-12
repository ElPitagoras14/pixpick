## Why

Ningún change del dominio puede escribirse sin una forma acordada de evolucionar el esquema y de consultarlo. Los que vienen —usuarios y sesiones, álbumes, fotos, compartir, calificaciones— crean tablas y consultas en cada paso, así que las reglas de cómo se declara una migración, cómo viaja la conexión y cómo se delimita una transacción tienen que estar fijadas antes. Si no, cada change las reinventa y la capa de datos termina con tres estilos conviviendo.

Hay además una decisión de fondo que conviene tomar de una vez, porque condiciona todo lo que se escriba después: el esquema se declara en SQL con dbmate y no hay ORM. Un ORM paga su costo cuando los modelos declarativos son la única fuente de verdad y las migraciones se derivan de ellos, y con dbmate eso es imposible por construcción — agregar modelos declarativos significaría mantener el esquema dos veces sin nada que verifique que las dos versiones coinciden. Y las consultas que definen a este producto son justamente donde un ORM estorba: conteos agregados por foto, upsert de calificación, y un anti-join para saber qué le falta calificar a cada usuario.

## What Changes

- **Migraciones con dbmate**: directorio propio en la raíz, imagen con versión exacta y las migraciones horneadas dentro, y `schema.sql` versionado como retrato del esquema vigente.
- **La migración inicial establece las piezas compartidas**, no tablas de dominio: la función que mantiene `updated_at` y cualquier extensión que el esquema requiera. Cada tabla posterior la reutiliza en vez de repetir la actualización de ese campo en cada sentencia.
- **El servicio de migraciones entra al compose** y las migraciones se aplican antes de que el backend atienda peticiones. Esto trae consigo el healthcheck de Postgres y el arranque ordenado que `add-local-environment` dejó fuera precisamente porque todavía no existía un servicio que dependiera de la base.
- **Acceso a datos en SQL crudo**: consultas escritas como SQL con parámetros por nombre sobre un conjunto reducido de helpers, la conexión como parámetro explícito de toda función de acceso, límites de pool declarados, y verificación de conectividad durante el arranque.
- **Los repositories devuelven modelos Pydantic**, no filas crudas, para que el tipado exista en la frontera de la capa de datos y no se disuelva en el resto de la aplicación.
- **Los fallos de la capa de datos se traducen a errores de dominio** y no filtran detalle del driver ni de la capa de acceso, lo que requiere una base mínima de excepciones y su manejo.
- **El healthcheck se extiende** para cubrir la conectividad con la base, que en el change anterior quedó explícitamente sin cubrir.
- **`.env.example` gana la variable de conexión**, que a partir de este change tiene consumidor.
- **Pruebas de backend con pytest** contra un Postgres real migrado por dbmate, con fixtures de conexión y de transacción, factories y utilidades de base de datos.

### Fuera de alcance

- Toda tabla de dominio: usuarios, sesiones, álbumes, fotos, compartir y calificaciones llegan con los changes que las usan.
- Cualquier endpoint que no sea el healthcheck, y con ello el envelope de respuestas de la API, que espera al primer endpoint real.
- Los puertos de storage e imágenes, y los adapters cloud.
- Pruebas end-to-end y pruebas de frontend.
- Del proyecto en general: comentarios en fotos, notificaciones por email, coautores de álbum y PWA/offline.

## Capabilities

### New Capabilities

- `database-migrations`: cómo evoluciona el esquema, cómo se declara una migración, cómo se aplica y cómo se garantiza que el esquema esté al día antes de que la aplicación atienda.
- `database-access`: cómo se expresan las consultas, cómo viaja la conexión, cómo se delimita una unidad de trabajo, cómo se configura el pool y qué forma tienen los resultados que la capa de datos entrega.
- `backend-testing`: contra qué se prueba el backend, cómo se aísla cada prueba y qué garantías ofrece la suite.

### Modified Capabilities

Ninguna. Este change toca archivos que `add-local-environment` introdujo —el compose y `.env.example`—, pero no contradice ninguno de sus requirements: agregar una variable que tiene consumidor es exactamente lo que su spec pide, y sus requirements no prohíben healthchecks ni arranque ordenado. Lo que sí especifica este change es que las migraciones se apliquen antes de atender, y eso pertenece a `database-migrations`.

## Impact

**Archivos nuevos**

- `dbmate/Dockerfile`, `dbmate/migrations/0001_create_initial_schema.sql`, `dbmate/schema.sql`
- `backend/src/database/__init__.py`, `client.py`, `config.py`, `utils.py`
- `backend/src/exceptions.py`, `backend/src/handlers.py`
- `backend/tests/conftest.py`, `dbutils.py`, `factories.py` y las pruebas de la capa de datos

**Archivos modificados**

- `compose.yaml` y `compose.dev.yaml`: servicio de migraciones, healthcheck de Postgres y arranque ordenado.
- `.env.example`: variable de conexión a la base.
- `backend/src/main.py`: ciclo de vida de la conexión y healthcheck extendido.
- `backend/pyproject.toml`: dependencias de desarrollo para las pruebas.
- `README.md`: cómo crear y aplicar una migración, y cómo correr las pruebas.

**Dependencias**

- Nuevas de desarrollo en Python para el marco de pruebas y su soporte asincrónico.
- Imagen de dbmate con versión exacta, declarada en un único lugar del que dependen el compose, las pruebas y el README.
- Sin dependencias nuevas de npm.

**Precedencia**

Depende de `add-local-environment`: necesita el compose, la red y el servicio de Postgres que ese change introduce.
