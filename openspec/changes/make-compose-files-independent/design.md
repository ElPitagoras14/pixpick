## Context

El entorno se declara hoy en dos archivos de tamaños muy distintos. `compose.yaml` tiene 171 líneas y declara los siete servicios completos: imagen publicada, `environment` entero, `depends_on`, healthchecks, volúmenes y la red `pixpick`. `compose.dev.yaml` tiene 72 y declara, para seis de esos siete, solo tres cosas: `build:` en lugar de la imagen, los puertos que se publican al host, y qué variables recibe cada uno. No declara imágenes, ni dependencias, ni healthchecks, ni volúmenes, ni la red. Levantado solo no produce nada utilizable.

`.env` trae `COMPOSE_FILE=compose.yaml:compose.dev.yaml` y `COMPOSE_PATH_SEPARATOR=:`, así que `docker compose` sin argumentos fusiona los dos. La segunda variable existe porque el separador por omisión de Compose es `;` en Windows y `:` en el resto. Trae además `COMPOSE_PROFILES`, que decide si `storage` y `transformer` forman parte del proyecto: los dos llevan `profiles: ["local"]`, y por eso el `depends_on` del backend hacia `storage` lleva `required: false` —sin esa marca, su ausencia sería un error en lugar de un caso previsto.

Dos valores no salen de `.env` sino que los compone `compose.yaml`: `DATABASE_URL`, armada con los `POSTGRES_*` y el host `postgres`, y `MINIO_SERVER_ENDPOINT`, fijada en `http://storage:9000`. En `.env` esos dos nombres guardan a propósito el valor con el que se alcanza cada servicio desde el host, que es el que sirve cuando el backend corre fuera de los contenedores. Otros dos servicios reciben variables con otro nombre: `storage` toma las credenciales de MinIO como `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD`, y `transformer` las del transformador como `IMGPROXY_KEY`/`IMGPROXY_SALT`.

Del lado de las pruebas, el backend ya tiene una suite que comprueba convenciones del repositorio en lugar de comportamiento —`backend/tests/test_code_conventions.py`, que recorre el código fuente y falla ante una importación o un literal que rompa la regla—, y ese es el precedente para cualquier comprobación nueva de este tipo.

## Goals / Non-Goals

**Goals:**

- Que abrir cualquiera de los dos archivos alcance para saber qué levanta, sin tener el otro al lado.
- Que elegir una de las dos formas se lea en el comando, no en una variable de `.env`.
- Que los valores sigan escritos una sola vez, aunque las definiciones de servicio queden escritas dos.
- Que la divergencia entre los dos archivos se detecte sola, porque es el riesgo que este diseño introduce a cambio de la independencia.

**Non-Goals:**

- Reducir la duplicación entre los dos archivos. Es el costo aceptado, no un problema a resolver: cualquier mecanismo que la elimine vuelve a acoplarlos.
- Cambiar qué levanta cada forma. Las dos declaran los mismos siete servicios; lo que difiere es de dónde sale la imagen y qué puertos se publican.
- Convertir `compose.yaml` en un archivo de despliegue real. Sigue nombrando imágenes que ningún workflow publica todavía, igual que hoy.

## Decisions

### D1 - Dos declaraciones completas, elegidas con un `-f` explícito

`compose.dev.yaml` pasa a declarar los siete servicios enteros y se levanta con `docker compose -f compose.dev.yaml up`. `compose.yaml` queda igual de completo y se levanta con `docker compose up`. Ninguna variable decide cuál se usa.

Se consideraron dos alternativas. La primera, renombrar el archivo a `compose.override.yaml`: Compose lo fusiona por convención, sin variable ni flag, y se comprobó que funciona. Se descarta porque sigue siendo una fusión —el archivo sigue sin poder leerse solo— y porque el default sigue siendo implícito, que es exactamente lo que se quiere sacar. La segunda, dejar `COMPOSE_FILE` como está, es el estado actual: convierte la fusión en el significado de `docker compose` dentro del directorio, de modo que el mismo comando hace cosas distintas según qué `.env` haya al lado.

### D2 - Los valores siguen viniendo de `.env`, no escritos adentro

Cada declaración nombra variables con `${VAR}` y no copia sus valores. El proyecto que sirvió de referencia hace lo contrario: su archivo de desarrollo lleva los valores literales adentro y no lee `.env` para nada.

No se copia esa parte porque las dos configuraciones de desarrollo no son comparables. Ahí los valores de desarrollo son `SECRET_KEY=secret` y `postgres:postgres`, que no son secretos de nadie. Acá el juego de proveedores cloud se usa en desarrollo con credenciales reales de R2, ImageKit y Google, y un archivo versionado no es lugar para eso.

El costo es que `compose.dev.yaml` no se levanta sin `.env`. Es el mismo costo que ya tiene `compose.yaml`, y el archivo de ejemplo sigue siendo lo único que hay que copiar para arrancar.

### D3 - Sin `profiles`: los dos archivos declaran los siete servicios siempre

`storage` y `transformer` pierden su `profiles: ["local"]` y quedan declarados en las dos formas. Con eso el `depends_on` del backend hacia `storage` pierde su `required: false`, porque ya no hay ninguna configuración en la que el servicio no forme parte del proyecto, y `COMPOSE_PROFILES` deja de tener algo que activar.

El razonamiento es que declarar un servicio no cuesta nada y sirve de referencia: el archivo muestra cómo se configura MinIO aunque esa corrida use R2. A qué proveedor apunta la aplicación lo deciden `STORAGE_PROVIDER` e `IMAGE_PROVIDER`, no qué contenedores existen, así que un servicio levantado que nadie consulta simplemente no participa.

Tiene una consecuencia medible: con el juego cloud activo, el backend igual espera a que `storage` esté sano antes de arrancar, porque el `depends_on` ya no es condicional. Son los pocos segundos que MinIO tarda en responder su healthcheck, contra un contenedor que después no se consulta. Se acepta: la alternativa es sacarle al backend esa dependencia, y entonces con proveedores locales podría arrancar antes que MinIO y fallar en la preparación del almacenamiento, que es un fallo real a cambio de evitar una espera que no lo es.

### D4 - Las dos declaraciones difieren en exactamente dos cosas

`compose.dev.yaml` usa `build:` donde `compose.yaml` usa `image:`, y publica puertos al host donde `compose.yaml` no publica ninguno. Todo lo demás —`environment`, `depends_on`, healthchecks, volúmenes, red, `command`, `entrypoint`— es idéntico, incluidos los dos valores compuestos y los dos mapeos de nombres renombrados.

Definirlo así de estrecho es lo que hace comprobable el requirement de que las dos no se separen: no hay que decidir caso por caso si una diferencia es legítima, porque solo dos lo son.

### D5 - La coincidencia se comprueba en la suite, no en revisión

Una prueba nueva lee los dos archivos y falla si difieren en algo que no sea `image`/`build` o `ports`. Vive junto a `backend/tests/test_code_conventions.py`, que es el precedente del repositorio para una regla que ninguna herramienta trae configurada.

La alternativa era comparar las dos salidas de `docker compose config`. Se descarta porque exigiría Docker corriendo para ejecutar la suite, que hoy no hace falta para las pruebas que no tocan servicios, y porque esa salida incluye rutas absolutas de la máquina.

La prueba necesita un parser de YAML. `yaml` se importa hoy en el entorno del backend, pero como dependencia transitiva de `fastapi[standard]`, no declarada: se agrega `pyyaml` al grupo de dependencias de desarrollo, porque una prueba que se apoya en una dependencia que nadie pidió se rompe el día que el grafo cambie, sin que nada lo anuncie.

### D6 - El README presenta dos formas, no una con un agregado

La sección de arranque pasa a nombrar las dos y a decir cuándo se usa cada una: la que construye desde el código fuente, que es la de desarrollo, y la que consume imágenes publicadas. Los comandos de desarrollo llevan `-f compose.dev.yaml`, uno solo, y los otros ninguno.

## Risks / Trade-offs

**Las definiciones de servicio quedan escritas dos veces** → Es el costo central de este diseño y no se mitiga escondiéndolo, sino comprobándolo: la prueba de D5 falla ante cualquier diferencia que no sea imagen o puertos, así que las dos no pueden separarse sin que alguien se entere en el acto.

**Un `.env` que conserve `COMPOSE_FILE` produce una tercera forma, y silenciosa** → Con los dos archivos completos, fusionarlos no da error: se comprobó que Compose acepta `image:` y `build:` en el mismo servicio, construye, y deja ganar los valores del archivo de dev. O sea que quien no borre esas líneas obtiene algo que arranca y funciona, pero que no es ninguna de las dos formas previstas. El plan de migración lo cubre, y es la razón por la que sacar las variables del `.env` propio no es opcional.

**Con proveedores cloud se levantan dos contenedores que nadie consulta** → Buscado (D3). MinIO e imgproxy arrancan, responden sus healthchecks y ahí quedan. Cuestan memoria, no corrección.

**Las dos formas comparten `COMPOSE_PROJECT_NAME`** → Son el mismo proyecto visto de dos maneras, así que levantar una después de la otra reemplaza los contenedores y conserva los volúmenes. Es el comportamiento buscado —los datos no dependen de con cuál se levantó—, pero conviene saber que alternar no deja los dos juegos conviviendo.

## Migration Plan

No hay datos que migrar y los volúmenes se conservan. Para un `.env` existente hay un paso obligatorio: borrar `COMPOSE_FILE`, `COMPOSE_PATH_SEPARATOR` y `COMPOSE_PROFILES`. Las dos primeras porque si no `docker compose` sigue fusionando, ahora dos archivos completos, sin avisar; la tercera porque ya no activa nada y queda como variable sin consumidor, que es lo que el archivo de ejemplo prohíbe.

Quien parte de un clon limpio copia el ejemplo y no hace nada especial.

El rollback es revertir el commit. Los contenedores levantados con la versión nueva no estorban a la anterior: son los mismos servicios con la misma red y los mismos volúmenes, y quien vuelva atrás tiene que volver a poner las tres variables en su `.env` para recuperar los comandos cortos.

## Open Questions

Ninguna. Las tres decisiones que podían cambiar los specs —si los archivos se fusionan o no, si los valores van literales o desde `.env`, y cómo se reparten `storage` y `transformer`— las respondió el usuario antes de escribir el diseño, y el resto se pudo medir en esta máquina.

### Resueltas durante la redacción

- **¿Alcanza con renombrar el archivo a `compose.override.yaml`? (D1)** Funciona: probado contra Compose 29.7.2, `docker compose config` sin `-f` ni variables fusiona los dos, y `-f compose.yaml` sigue dando el base solo. Se descarta igual porque sigue siendo una fusión y el default sigue sin leerse en el comando. *Fuente: prueba directa en esta máquina.*
- **¿Los valores de desarrollo van escritos adentro del archivo, como en el proyecto de referencia? (D2)** No. *Fuente: respuesta del usuario, sobre el dato de que el juego cloud se usa en desarrollo con credenciales reales.*
- **¿`storage` y `transformer` quedan detrás de `profiles`, o declarados siempre? (D3)** Declarados siempre, en las dos formas, sin `profiles`. *Fuente: respuesta del usuario: el servicio se deja definido como referencia, y si se lo levanta sin que nada lo apunte no pasa nada, porque el apuntamiento depende de las variables de entorno.*
- **¿Fusionar dos archivos completos falla de forma visible? (Risks)** No: Compose acepta `image:` y `build:` juntos, construye, y el archivo de dev gana en `environment`. El resultado arranca, así que el error no se nota. *Fuente: prueba directa con dos archivos completos.*
- **¿Hay parser de YAML para la comprobación de D5?** Sí, `yaml` 6.0.3 importa en el entorno del backend, pero llega por `fastapi[standard]` y no está declarado. Se declara explícito en el grupo de desarrollo. *Fuente: `uv run python -c "import yaml"` y `backend/pyproject.toml`.*
- **¿Qué difiere legítimamente entre las dos declaraciones? (D4)** Solo la imagen y los puertos publicados. Sale de comparar los dos archivos actuales: `compose.dev.yaml` no agrega hoy nada más que eso y el bloque `environment`, que en la versión nueva pasa a ser idéntico al del otro archivo. *Fuente: los dos archivos en su estado actual.*
