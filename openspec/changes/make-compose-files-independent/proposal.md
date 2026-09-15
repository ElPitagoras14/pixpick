## Why

`compose.dev.yaml` no es una definición del entorno: son treinta y dos líneas que solo tienen sentido apiladas sobre `compose.yaml`. Declara `build:`, `ports:` y qué variables recibe cada servicio, y nada más — ni imágenes, ni healthchecks, ni `depends_on`, ni volúmenes, ni la red. Abrirlo no dice qué levanta; hay que abrir el otro archivo y fusionarlos mentalmente.

Para que esa fusión ocurriera sin escribir dos `-f` en cada comando, el change anterior declaró `COMPOSE_FILE` y `COMPOSE_PATH_SEPARATOR` en `.env`. Eso convirtió la fusión en el comportamiento por omisión del directorio: `docker compose` a secas dejó de significar `compose.yaml`. Dos variables de configuración existen únicamente para sostener que un archivo esté incompleto.

## What Changes

- **`compose.dev.yaml` pasa a ser una declaración completa del entorno.** Sus siete servicios llevan todo lo que cada uno necesita para arrancar solo: de dónde sale la imagen, qué variables recibe, qué puertos publica, de qué depende, qué healthcheck tiene, qué volúmenes monta y en qué red vive. Se levanta con `docker compose -f compose.dev.yaml up` y no se combina con nada.
- **`compose.yaml` queda como la otra declaración completa**, la que consume imágenes ya publicadas en lugar de construirlas. Sigue levantándose con `docker compose up` y vuelve a significar exactamente lo que dice el archivo.
- **Los valores siguen viniendo de `.env`.** Cada declaración nombra variables con `${VAR}`, no copia sus valores. Lo que queda escrito dos veces son las definiciones de servicio, no la configuración.
- **Los servicios se declaran siempre, en las dos.** `storage` y `transformer` pierden su `profiles: ["local"]`, y el `depends_on` del backend pierde su `required: false`. Un servicio declarado que nadie consulta no molesta: a qué proveedor apunta la aplicación lo deciden `STORAGE_PROVIDER` e `IMAGE_PROVIDER`, no qué contenedores están levantados. Declararlo siempre hace además que cada archivo muestre cómo se configura ese servicio, sirva o no en esa corrida.
- **Salen tres variables de `.env.example`.** `COMPOSE_FILE` y `COMPOSE_PATH_SEPARATOR` ya no tienen nada que sostener. `COMPOSE_PROFILES` tampoco, porque no queda ningún `profiles` que activar.
- **Los comandos de desarrollo del README llevan `-f compose.dev.yaml`**, uno solo. Los de producción siguen sin ninguno.
- **BREAKING para un `.env` existente**: quien tenga `COMPOSE_FILE` declarada la sigue teniendo, y con ella `docker compose` a secas seguiría fusionando los dos archivos — ahora el de dev completo sobre el de producción, que no es ninguna de las dos formas previstas. Hay que borrar esas líneas del `.env` propio, no solo del ejemplo.

### Fuera de alcance

- **Escribir los valores de desarrollo literalmente dentro del archivo**, como hace el proyecto que sirvió de referencia. Ahí la configuración de desarrollo no tiene secretos; acá sí puede tenerlos —se desarrolla contra R2 e ImageKit con credenciales reales—, y un archivo versionado no es lugar para eso. Los valores siguen en `.env`.
- **Un tercer archivo.** Dos declaraciones cubren las dos formas que el proyecto tiene de levantarse; una combinación más sería una tercera definición completa que mantener.
- **Cambiar cómo se eligen los proveedores.** `STORAGE_PROVIDER` e `IMAGE_PROVIDER` siguen decidiendo lo mismo que hoy, y los grupos de variables quedan como están.
- **Unificar las dos declaraciones con anclas de YAML.** Sería volver al acoplamiento por otra vía: un archivo dejaría de leerse entero por sí mismo, que es justo lo que este change persigue.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `local-environment`: el requirement «Cada servicio declara qué variables recibe» exige hoy que un valor compuesto —el que depende de cómo se alcanzan los servicios entre sí— se declare **en un único lugar**, y esa exigencia se apoya en que haya una sola definición del entorno. Con dos definiciones independientes, cada una compone los suyos, así que ese párrafo pasa a exigir que el valor se componga dentro de la declaración que lo usa, que no se tome del archivo de ejemplo, y que las dos declaraciones digan lo mismo cuando componen el mismo valor. Se le agrega un requirement nuevo: cada forma de levantar el proyecto está declarada completa y por separado, y un servicio se declara en cada forma que pueda usarlo aunque una configuración concreta no lo consulte.

## Impact

**Archivos modificados**

- `compose.dev.yaml`: reescrito. Pasa de 32 líneas de superposición a una declaración completa de los siete servicios.
- `compose.yaml`: se van los dos `profiles: ["local"]` y el `required: false` del `depends_on` del backend; el comentario de cabecera deja de describirlo como la mitad de un par.
- `.env.example`: tres variables menos.
- `README.md`: los comandos de desarrollo ganan `-f compose.dev.yaml` y el documento explica que hay dos formas de levantar el proyecto, no una con un agregado.
- `backend/tests/images/test_variant_contract.py`: su docstring todavía nombra la forma vieja con dos `-f`.

**Archivos nuevos**

- Una comprobación de que las dos declaraciones no se separan: mismos servicios, y mismo valor donde las dos componen uno. Sin ella, la única defensa contra que se separen es que alguien lo note revisando.

**Consecuencia al alternar entre las dos formas**

Las dos declaraciones comparten `COMPOSE_PROJECT_NAME`, así que son el mismo proyecto visto de dos maneras. Levantar una después de la otra reemplaza los contenedores y conserva los volúmenes, que es el comportamiento buscado: los datos no dependen de con cuál se levantó.

**Precedencia**

Depende de `slim-docs-and-compose`, ya archivado: este change modifica el requirement que aquel agregó y retira las dos variables que aquel introdujo.
