## Context

El repositorio explica sus decisiones citando de dónde vienen. Un comentario típico de `backend/src` dice `(api-conventions spec, added by add-albums-and-upload)`; uno de `compose.yaml`, `(local-environment spec, task 6.3 in harden-local-profile)`; uno de `frontend/src`, `(D7)` a secas. Son unas 850 marcas: 377 en `backend/src` (69 de 89 archivos), 179 en `frontend/src` (36 de 55), 157 en `backend/tests`, 141 entre los dos compose, `nginx/` y `dbmate/`, y el resto en `.env.example`.

Alrededor de la cita creció una segunda capa: el comentario no solo dice de dónde sale la decisión, también defiende por qué no se tomó la otra. `images/factory.py` dedica cinco líneas a explicar que parametrizar el transformer para alcanzar un proveedor externo quedó fuera de alcance; `exceptions.py` compara las tres reacciones posibles de un cliente ante un 503, un 422 y un 500. Es material de decisión, y ya está escrito en las specs y en los changes archivados.

`.env.example` marca `Required` treinta y pico de variables. La marca no distingue `DATABASE_URL`, que no tiene default y sin la cual el backend no arranca, de `MINIO_PORT`, que trae `9000` y no se toca nunca. Las variables tampoco están agrupadas: `NGINX_PORT` y `POSTGRES_PORT` viven juntas en un bloque de puertos, pero `MINIO_PORT` aparece cien líneas más abajo, entre las de storage.

Dos restricciones enmarcan el trabajo. La primera: `code-conventions` ya exige que toda regla suya tenga una comprobación automática que forme parte de lo que valida el proyecto, así que la regla nueva sobre comentarios nace incumplida si no llega con la suya. La segunda: `backend/tests/test_code_conventions.py` y `test_compose_conventions.py` ya establecen el precedente de una prueba que lee archivos fuera de `backend/` —el segundo levanta los dos compose desde la raíz del repositorio—, así que la comprobación tiene dónde vivir sin inventar una categoría nueva.

## Goals / Non-Goals

**Goals:**

- Que un comentario se entienda sin abrir nada más, y que exista solo cuando aporta algo que el código no dice.
- Que `.env.example` responda en su primer bloque qué hay que llenar antes de levantar el proyecto.
- Que la limpieza no dependa de que alguien la recuerde: una referencia nueva tiene que hacer fallar la suite.
- Que la comprobación siga valiendo cuando se archive el próximo change, sin editarla.

**Non-Goals:**

- Renombrar, extraer o reordenar código. Si un comentario existe porque el nombre de una función es malo, en este change se va el comentario y el nombre queda como está: cambiarlo es otro trabajo, con otro riesgo.
- Reducir la cantidad de comentarios como objetivo propio. El criterio es si aporta, no cuántos quedan; un archivo puede terminar con más líneas de comentario que antes si las que tenía no servían y la que falta sí.
- Tocar `openspec/specs/` ni `openspec/changes/archive/`. Son el destino al que se delega el detalle.
- Verificar que el comentario que queda sea cierto. Se asume correcto lo que está escrito; corregir una afirmación desactualizada es un hallazgo aparte, y si aparece se reporta, no se arregla en silencio.

## Decisions

### D1. El criterio de supervivencia son tres preguntas, no una impresión

Un comentario se queda si responde a alguna de tres: por qué no se hizo lo que el lector esperaría, con qué otro archivo o servicio tiene que coincidir este valor, o qué se rompe si se cambia. Si no responde a ninguna, se va.

La alternativa era un criterio por volumen —"ningún comentario de más de N líneas"— o por posición —"solo comentarios de una línea sobre una asignación"—. Se descartan porque miden la forma y no el aporte: el comentario de `database/config.py` que explica que los tres timeouts están en milisegundos porque esa es la unidad de los GUC de Postgres ocupa dos líneas y es exactamente el acoplamiento invisible que hay que conservar, mientras que el de `port.py` que dice que la interfaz es la que el resto de la aplicación usa ocupa una y no dice nada.

Las tres preguntas dan además un criterio de reescritura y no solo de borrado: un comentario que hoy mezcla las tres capas —qué hace, de dónde sale la decisión, por qué no la otra— se reduce a la parte que responde, en vez de desaparecer entero.

### D2. La comprobación lee los nombres prohibidos del propio `openspec/`, no de una lista escrita

La prueba construye lo que busca en el momento de correr: los nombres de capability salen de los directorios de `openspec/specs/`, y los nombres de change de los directorios de `openspec/changes/archive/` con el prefijo de fecha quitado. No hay una lista literal en el código de la prueba.

La alternativa era una lista de literales, que es más simple de leer. Se descarta porque envejece exactamente igual que lo que la regla quiere evitar: al archivar el próximo change, su nombre no estaría en la lista y podría citarse sin que nada avise, que es el fallo que la comprobación existe para tapar. Leerlos del sistema de archivos hace que archivar un change extienda la comprobación solo con archivarlo.

Efecto lateral buscado: la prueba no contiene ninguna de las cadenas que prohíbe, así que no tiene que excluirse a sí misma del recorrido.

### D3. Los nombres se buscan en el archivo entero; `D<n>` solo dentro de comentarios

Un nombre de capability (`api-conventions`) o de change (`harden-local-profile`) es una cadena kebab-case lo bastante distintiva como para buscarla en el texto completo de cada archivo sin riesgo: ningún archivo ni identificador del proyecto se llama así hoy, y ninguno tendría por qué. La decisión numerada es otra cosa: `D6` es dos caracteres y aparece legítimamente en datos de un path SVG o en una constante. Para esa sola forma, la comprobación extrae primero el texto de los comentarios y busca ahí.

La extracción va por tipo de archivo: en Python con `tokenize` para los comentarios y `ast` para los docstrings, que es lo que ya usa `test_code_conventions.py` y no inventa una dependencia; en TypeScript quitando primero los literales de cadena y tomando después `//` y `/* */`, con lo que una URL con `//` no se confunde con un comentario; en YAML, `.conf`, `.env` y Dockerfile por línea que empieza con `#`; en Markdown, el archivo entero, porque todo él es texto de lectura.

La alternativa era buscar `D<n>` también en el archivo entero. Hoy daría cero falsos positivos —lo verifiqué: no hay una sola aparición fuera de un comentario—, pero la prueba quedaría atada a esa casualidad y fallaría el día que alguien escriba un SVG en línea. La alternativa opuesta, extraer comentarios también para los nombres de capability y de change, agrega trabajo sin ganar nada: si uno de esos nombres aparece en una cadena del código, es una cita igual.

### D4. La comprobación vive en la suite del backend, en un archivo propio

Va a `backend/tests/test_documentation_conventions.py`, junto a las otras dos pruebas de convención, y recorre desde la raíz del repositorio como ya hace `test_compose_conventions.py`.

La alternativa era un script aparte en `nginx/` o en la raíz, o un hook de pre-commit. Se descarta por lo mismo que ya está escrito en los docstrings de las dos pruebas vecinas: un script hay que acordarse de correrlo. Un archivo propio en vez de sumarla a `test_code_conventions.py` porque su alcance es distinto —todo el repositorio, no `backend/src`— y porque sirve a dos capabilities, no a una.

La prueba excluye `openspec/`, `local/`, `CLAUDE.md`, `.claude/`, `.agents/`, `frontend/AGENTS.md`, los directorios generados (`node_modules`, `.venv`, `__pycache__`, `dist`) y `dbmate/schema.sql`, que lo escribe dbmate.

### D5. El corte de `.env.example` sale del código, no del criterio de quien edita

Una variable va al bloque obligatorio si se cumple alguna de tres condiciones verificables: no tiene default en su clase de settings de Pydantic, su default es una credencial apta solo para desarrollo, o queda exigida por el valor activo de un selector de proveedor. Todo lo demás va al opcional.

Aplicado queda así. Obligatorio: `ENVIRONMENT`, `PUBLIC_URL`, `DATABASE_URL`, `IDENTITY_PROVIDER`, `STORAGE_PROVIDER`, `IMAGE_PROVIDER` (sin default en las settings); `POSTGRES_PASSWORD`, `MINIO_SECRET_ACCESS_KEY`, `MINIO_ACCESS_KEY_ID`, `IMAGE_SIGNING_KEY`, `IMAGE_SIGNING_SALT` (secreto de desarrollo); `GOOGLE_CLIENT_ID`/`SECRET`, los cuatro `R2_*`, los dos `IMAGEKIT_*`, `MINIO_BROWSER_ENDPOINT`, `MINIO_SERVER_ENDPOINT` y `STORAGE_PUBLIC_URL` (condicionados al proveedor activo). Opcional: `COMPOSE_PROJECT_NAME`, `API_BASE_URL`, `NGINX_PORT`, `POSTGRES_PORT`, `MINIO_PORT`, `POSTGRES_USER`, `POSTGRES_DB`, `MINIO_BUCKET`, `MINIO_ALLOWED_ORIGINS`, `ALBUM_MAX_PHOTOS`, `ACCOUNT_MAX_BYTES`, `INSTANCE_MAX_BYTES`, `ALBUM_RETENTION_DAYS`.

`POSTGRES_USER` y `POSTGRES_DB` quedan del lado opcional aunque `POSTGRES_PASSWORD` no: los dos primeros son nombres, no credenciales, y el entorno arranca con los que trae. La condición del secreto mira si el valor tiene que cambiar para salir de una máquina de desarrollo, no si pertenece al mismo servicio.

Dentro de cada bloque, seis grupos: red, base de datos, identidad, object storage, variantes de imagen y límites. Una variable condicionada a un proveedor queda en el grupo de su proveedor, con la condición escrita en su línea.

### D6. Una nota por variable, y solo cuando el nombre no alcanza

`NGINX_PORT=8080` no lleva nota. `STORAGE_PUBLIC_URL` sí, porque ni el nombre ni el valor dicen que tiene que ser un hostname y no una IP. Las de conjunto cerrado llevan sus valores en la misma línea (`local | google`). El archivo sigue en inglés, como el resto del código.

Esto achica `.env.example` de forma marcada, y el detalle que se va no se reescribe en el README: la explicación larga de `STORAGE_PUBLIC_URL` ya existe ahí, y `project-documentation` exige que cada cosa se explique en un solo lugar. Lo que queda en `.env.example` es un puntero corto al README para esa variable.

### D7. Se corrigen dos defectos que aparecen al pasar por los archivos

El docstring de `backend/tests/test_code_conventions.py` tiene una línea duplicada y cortada a la mitad: dice `The first one, in detail: a module living under the importing file's` y la línea siguiente vuelve a empezar la misma frase. Y `identity/adapters/google.py:56` y `identity/adapters/local.py:65` tienen su docstring en castellano, contra la convención del repositorio de que el código va en inglés.

Se arreglan acá en vez de dejarlos para otro change porque este pasa por esos tres archivos de todas formas, y porque el primero es justamente un comentario que no dice lo que pretende decir, que es lo que este change corrige.

## Risks / Trade-offs

**Borrar un comentario que sí aportaba** → El riesgo real del change: 850 decisiones tomadas de a una, y un borrado de más no lo señala ninguna prueba. Mitigación: las tres preguntas de D1 se aplican por archivo y no por lote, y el trabajo se reparte en fases por área para que el diff de cada una se pueda revisar entero. Un comentario dudoso se conserva: el costo de dejar uno de más es una línea, el de borrar uno de menos es una decisión perdida.

**La comprobación da un falso positivo y estorba** → Un nombre de capability como `album-management` podría aparecer algún día en un contexto legítimo. Mitigación: el mensaje de fallo nombra archivo, línea y qué cadena disparó, así que el diagnóstico es inmediato; y si el caso legítimo aparece, la excepción se agrega con su motivo escrito.

**La comprobación se vuelve lenta** → Recorre el repositorio entero en cada corrida de la suite. Mitigación: es lectura de archivos de texto con exclusión de los directorios generados, del mismo orden que lo que ya hacen las dos pruebas vecinas. Si midiera de más, se acota a los directorios versionados.

**El corte de `.env.example` envejece** → Si una variable gana o pierde su default en las settings y nadie mueve su línea, el archivo empieza a mentir. Mitigación consciente: no se agrega comprobación para esto. La condición mira tres cosas de las cuales solo una es leíble desde el código, y una prueba que verificara únicamente esa daría una garantía parcial con apariencia de completa. Queda como revisión.

**El diff es enorme y tapa otro trabajo en paralelo** → Toca ~150 archivos sin cambiar comportamiento. Mitigación: el change no toca lógica, así que un conflicto con otra rama se resuelve tomando el lado de la otra y volviendo a aplicar el criterio sobre el archivo resultante.

## Migration Plan

No aplica: no hay cambio de comportamiento, de esquema ni de configuración efectiva. La verificación de que no lo hay es que `docker compose -f compose.dev.yaml config` resuelva los mismos valores antes y después del cambio de `.env.example`, y que la suite pase sin modificaciones salvo la prueba nueva.

El rollback es revertir el commit.

## Open Questions

Ninguna. Las tres decisiones que podían cambiar el reparto de tareas o los specs —qué alcance tiene la limpieza, cómo se estructura `.env.example` y si la comprobación automática entra en este change— las respondió el usuario antes de redactar.

### Resueltas durante la redacción

- **¿El requirement sobre la forma de `.env.example` va en `project-documentation` o en `local-environment`?** En `project-documentation`. Lo cerró leer el requirement vigente de `local-environment` "El entorno declara su configuración en un archivo de ejemplo": gobierna que el archivo exista, que esté completo y que no tenga variables sin consumidor. Nada de eso es cómo se lee, que es lo que gobierna `project-documentation`. El delta lo deja escrito para que el límite no se discuta de nuevo.
- **¿El requirement sobre comentarios va en `project-documentation` o en `code-conventions`?** En `code-conventions`. Lo cerró su propio Purpose: gobierna las convenciones que ninguna herramienta trae resueltas y que sin quedar escritas se deciden imitando el archivo de al lado, que describe exactamente el caso. Y su requirement vigente sobre comprobación automática es lo que obliga a que la regla llegue con su prueba.
- **¿La comprobación puede buscar `D<n>` en el archivo entero?** No, aunque hoy funcionaría. Lo cerró verificarlo sobre el código: no hay una sola aparición de `D<n>` fuera de un comentario, ni en `backend/src` ni en `frontend/src`, así que un recorrido del archivo entero pasaría hoy y quedaría atado a esa casualidad. De ahí la extracción de comentarios de D3, que solo hace falta para esa forma.
- **¿La lista de nombres prohibidos se escribe o se deriva?** Se deriva del sistema de archivos. Lo cerró notar que una lista escrita reproduce el problema que la regla ataca —envejece en silencio al archivar el próximo change— y que derivarla tiene además el efecto de que la prueba no contenga ninguna de las cadenas que prohíbe.
- **¿`POSTGRES_USER` es obligatorio por estar al lado de `POSTGRES_PASSWORD`?** No. Lo cerró aplicar la condición de D5 tal como está escrita: mira si el valor tiene que cambiar para salir de una máquina de desarrollo. Un nombre de usuario y un nombre de base no lo requieren; la contraseña sí.
- **¿El detalle que se saca de `.env.example` se reescribe en el README?** No. Lo cerró el requirement vigente de `project-documentation` "Cada cosa se explica en un solo lugar": la explicación larga de `STORAGE_PUBLIC_URL` ya vive en el README, así que duplicarla sería incumplirlo.
