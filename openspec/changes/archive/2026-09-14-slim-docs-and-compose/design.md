## Context

El proyecto arranca hoy con `docker compose -f compose.yaml -f compose.dev.yaml up --build`, y esa cadena se repite en cada comando del README. `compose.yaml` declara los siete servicios con su `environment` completo; `compose.dev.yaml` solo agrega `build:` y `ports:`, sin `environment` ni `volumes`. Los valores llegan de `.env`, que Compose lee por estar en el directorio del proyecto, no porque ningún archivo lo declare.

Dos de esas variables no se copian de `.env` sino que las arma `compose.yaml`: `DATABASE_URL`, compuesta de los `POSTGRES_*` con el host `postgres`, y `MINIO_SERVER_ENDPOINT`, fijada en `http://storage:9000`. Las dos existen porque el servicio corre dentro de la red de Docker, y en `.env` el mismo nombre guarda a propósito el valor del modo native, que apunta al host. Otras dos parejas de servicios reciben variables renombradas: `storage` toma las credenciales de MinIO bajo los nombres que MinIO espera (`MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`), y `transformer` hace lo mismo con las del transformador (`IMGPROXY_KEY`, `IMGPROXY_SALT`).

El bucket lo crea `storage-init`: un servicio del perfil local que monta `storage/init.sh`, corre `mc mb --ignore-existing` contra el almacenamiento sano y termina. El backend y el `transformer` esperan a que ese servicio complete. En modo native nadie lo ejecuta, así que trabajar así depende de haber levantado el entorno completo alguna vez.

Del lado del backend, `src/storage/port.py` define tres operaciones (`grant_upload`, `get_object`, `delete_objects`), `src/storage/factory.py` construye el puerto **en tiempo de import** (`storage_port: StoragePort = build_storage_port()`), y `src/main.py` tiene un `lifespan` que ya falla el arranque cuando la base de datos no responde. Existe una suite de contrato que corre sin modificaciones contra el doble de pruebas y contra cada proveedor real.

## Goals / Non-Goals

**Goals:**

- Que el espacio de objetos exista sin un servicio dedicado a crearlo, y que el modo native quede cubierto por el mismo mecanismo que el modo containers.
- Que abrir `compose.dev.yaml` diga qué recibe cada servicio, sin que ningún valor quede escrito dos veces.
- Que cada variable de `.env.example` se pueda completar leyendo solo lo que tiene al lado.
- Que los comandos del README sean cortos: un comando que se lee de una vez es parte del nivel de lectura exigido, no un detalle cosmético.

**Non-Goals:**

- Cambiar cómo se eligen o configuran los proveedores. Los grupos de variables y la variable que selecciona cada proveedor quedan como están; lo que cambia es cómo se documentan.
- Convertir el nivel de lectura en una verificación automática. La spec lo bajó a dos reglas comprobables a ojo y con eso alcanza.
- Tocar el orden de arranque más allá de lo que la salida de `storage-init` obliga.

## Decisions

### D1 - Preparar el almacenamiento es una operación del puerto, invocada en el `lifespan`

El puerto gana una cuarta operación —dejar el almacenamiento listo— y el `lifespan` la invoca junto a la comprobación de conectividad de la base que ya vive ahí. Es asíncrona y delega en un hilo, como las otras dos operaciones de red del puerto.

Se consideraron dos alternativas. La primera, que el arranque llamara directo al adaptador de MinIO, obliga a preguntar qué proveedor está activo en un punto del código que hoy no lo sabe, y la spec de `object-storage` lo prohíbe explícitamente. La segunda, hacerlo en el constructor del adaptador, es peor de lo que parece: el factory construye el puerto en tiempo de import, así que importar el módulo abriría una conexión de red — y todo test que importe cualquier cosa que dependa del puerto quedaría exigiendo un MinIO levantado.

### D2 - Comprobar siempre, crear solo el proveedor que el proyecto opera

Los dos adaptadores empiezan igual: preguntan si el espacio existe. Si existe, terminan. Si no, el de MinIO lo crea y el de R2 falla, porque el bucket de R2 se crea una vez en el panel de Cloudflare y su ausencia es un error de configuración, no algo que la aplicación deba resolver sola.

La alternativa era crear siempre y tolerar el "ya existe". Se descarta porque exige permiso de creación en cada arranque incluso cuando no hace falta, y porque en el proveedor externo convertiría un error de configuración en un intento silencioso de crear un recurso de pago.

Comprobar la existencia alcanza: no se escribe un objeto de prueba. Un objeto así deja basura o exige limpiarla, y una credencial con permiso de lectura pero no de escritura falla igual en la primera subida, de forma igual de visible.

### D3 - Un espacio ausente no es un almacenamiento caído

El error que se levanta es propio, distinto del que ya existe para un almacenamiento que no responde. Son dos causas que se arreglan de forma distinta —una se arregla creando un bucket en un panel, la otra revisando la red o el servicio— y compartir el tipo haría que el mensaje de arranque mande a revisar lo que no es.

### D4 - `compose.dev.yaml` declara por nombre, con dos excepciones medidas

Cada servicio lista las variables que recibe por su nombre, sin valor, de modo que Compose las resuelva contra `.env` y ningún valor quede escrito dos veces.

Eso no sirve para las dos variables que `compose.yaml` arma. Medido con `docker compose config`: declarar `DATABASE_URL` por su nombre en el archivo dev hace que gane el valor de `.env` —el del modo native, con host `localhost`— sobre el compuesto con host `postgres`, y el backend en contenedor terminaría buscando la base dentro de sí mismo. Lo mismo vale para `MINIO_SERVER_ENDPOINT`. Las dos se quedan solo en `compose.yaml`, y `.env.example` explica junto a cada una por qué su valor allí es el del modo native.

Se midió también el caso de una variable declarada por nombre que no esté en `.env`: no llega vacía al contenedor, directamente no llega. Es una diferencia respecto de la interpolación de `compose.yaml`, que sí produce una cadena vacía, y es inocua mientras `.env.example` siga listando todas las variables — que es justamente lo que `local-environment` ya exige.

Los servicios cuyas variables se renombran (`storage` y `transformer`) declaran el mapeo completo, con el nombre que el servicio espera y la variable de `.env` de la que sale. Ese mapeo sí queda escrito en los dos archivos, y se acepta porque es de uno a uno, no se compone de nada, y equivocarlo impide que el servicio arranque en el acto en lugar de fallar más tarde.

### D5 - `storage-init` sale, y las dependencias se mueven a lo que cada servicio necesita de verdad

El servicio y su script desaparecen. El `transformer` pasa a depender del almacenamiento sano, que es lo único que necesitaba: lee objetos por petición y no toca nada al arrancar. El backend pasa a depender de las migraciones completas y del almacenamiento sano, conservando el `required: false` que ya tenía — en el perfil cloud el servicio `storage` no forma parte del proyecto resuelto, y sin esa marca su ausencia sería un error en vez de un caso previsto.

### D6 - `.env.example` marca cada variable con una de tres etiquetas

Cada variable lleva, en la primera línea de su comentario, una de tres marcas: obligatoria, opcional, u obligatoria bajo condición, nombrando la variable y el valor que la activan. Los grupos de alternativas quedan agrupados bajo un encabezado que nombra la variable que decide cuál aplica.

La alternativa era describirlo en prosa, que es lo que hay hoy: el archivo ya dice que solo hace falta llenar el grupo del proveedor activo, pero lo dice en un párrafo de cabecera a veinte líneas de distancia de las credenciales. Una marca fija por variable se lee sin buscar y se revisa de un vistazo.

### D7 - Los comandos del README pierden los `-f`

`.env.example` gana `COMPOSE_FILE=compose.yaml:compose.dev.yaml` junto con `COMPOSE_PATH_SEPARATOR=:`, y con eso cada comando del README pasa a ser `docker compose up`, `docker compose config` o `docker compose down`.

La segunda variable no es opcional ni decorativa: el separador por defecto de Compose es `:` en Linux y macOS pero `;` en Windows, verificado en esta máquina, así que sin declararlo el archivo de ejemplo solo funcionaría en la mitad de los sistemas. Declarándolo, el mismo `.env` sirve en todos. Las dos tienen consumidor real —Compose mismo—, así que no violan la regla de no incluir variables huérfanas.

### D8 - El README se ordena por lo que alguien necesita hacer

Las secciones responden preguntas en el orden en que aparecen: qué es pixpick, cómo levantarlo, cómo entrar, dónde mirar cuando algo no anda, cómo correr las pruebas, dónde vive cada parte, y cómo actualizar dependencias. La puesta en marcha de cada proveedor cloud se queda: es un procedimiento, no una justificación. Lo que se va es todo párrafo que explique por qué se decidió algo, incluidas las referencias a changes por su nombre.

Dentro de "cómo levantarlo" entra `docker compose config` como la forma de ver qué recibe cada servicio ya resuelto. Es la única parte de toda la documentación que no puede quedar desactualizada.

## Risks / Trade-offs

**El mapeo renombrado de `storage` y `transformer` queda en dos archivos (D4)** → Es de uno a uno y no se compone de nada, y una credencial mal declarada impide que MinIO arranque de inmediato. El fallo es ruidoso y aparece en el mismo comando que introdujo el error, no tres pasos después.

**El backend pasa a necesitar el almacenamiento sano para arrancar (D1, D5)** → Es intencional: es la misma regla que ya rige para la base de datos. El costo real aparece en modo native, donde nadie garantiza el orden; ahí el error de arranque nombra el problema, que es mejor que la primera subida fallando sin contexto.

**Un entorno ya levantado tiene un contenedor `storage-init` que este change deja sin definición (D5)** → Compose lo reporta como huérfano y no lo borra solo. El plan de migración lo cubre.

**Acortar el README puede llevarse algo que alguien estaba usando (D8)** → Lo que se quita son justificaciones, no procedimientos, y el historial conserva el texto anterior completo. Un procedimiento que hoy exista y no aparezca en la lista de secciones es un hallazgo a resolver durante la escritura, no algo que se borra por no estar en la lista.

**`COMPOSE_FILE` en `.env` cambia lo que hace `docker compose` a secas en ese directorio (D7)** → Es el efecto buscado. Quien necesite el archivo base solo —un despliegue— lo pide con `-f compose.yaml` explícito, y el README lo dice donde corresponde.

## Migration Plan

No hay datos que migrar: el bucket existente se conserva y la operación nueva lo encuentra tal cual. Para un entorno ya levantado, el primer arranque después de este change necesita `docker compose down --remove-orphans` para retirar el contenedor de `storage-init`, que queda sin definición. Quien parta de un clon limpio no hace nada especial.

El rollback es revertir el commit. El bucket creado por el backend no estorba a la versión anterior: `mc mb --ignore-existing` lo encuentra y sigue.

## Open Questions

Ninguna. Todas las decisiones de este change dependían de datos que se podían obtener ahora —el comportamiento de Compose al fusionar archivos, el de la imagen de MinIO, y el orden de construcción del puerto en el propio código—, así que no quedó nada cuya respuesta hubiera que adivinar.

### Resueltas durante la redacción

- **¿Puede la imagen oficial de MinIO crear el bucket por sí sola? (D1)** No. No existe variable equivalente a la de Postgres; el pedido se cerró como *working as intended* y el repositorio quedó archivado en abril de 2026. La variable `MINIO_DEFAULT_BUCKETS` que aparece al buscar pertenece a la imagen de Bitnami, que es otra. *Fuente: documentación y el propio issue del proyecto.*
- **¿Sirve crear el directorio dentro del volumen antes de arrancar el servidor? (D1)** Sí, funciona: probado contra `RELEASE.2025-09-07T16-13-09Z`, el bucket aparece listado por la API S3 y acepta escritura y lectura. Se descarta igual, porque se apoya en que MinIO tome cada directorio de primer nivel como un bucket, que no está documentado y podría dejar de ser cierto en una versión siguiente sin aviso. *Fuente: prueba directa contra la imagen fijada.*
- **¿Dónde se invoca la preparación sin que nadie ramifique por proveedor? (D1)** En el `lifespan`, a través del puerto. El constructor del adaptador queda descartado por un dato del propio código: el factory construye el puerto en tiempo de import, así que un efecto de red ahí lo heredaría cualquier test que importe el módulo. *Fuente: `backend/src/storage/factory.py` y la regla de no ramificar que ya impone `object-storage`.*
- **¿Se puede declarar el entorno del archivo dev nombrando variables sueltas? (D4)** Para casi todas sí, pero no para las dos que `compose.yaml` compone: el nombre suelto las resuelve desde `.env` y reemplaza el valor de la red de Docker por el del modo native. Se midió también que una variable ausente de `.env` no llega vacía sino que no llega. *Fuente: `docker compose config` sobre un par de archivos de prueba.*
- **¿Se pueden acortar los comandos del README con `COMPOSE_FILE`? (D7)** Sí, declarando junto a ella `COMPOSE_PATH_SEPARATOR=:`, porque el separador por defecto es `;` en Windows y `:` en Unix. Sin esa segunda línea el archivo de ejemplo solo serviría en un sistema operativo. *Fuente: prueba en esta máquina con los dos separadores.*
- **¿Comprobar que el espacio existe alcanza, o hay que probar que se puede escribir? (D2)** Alcanza. Un objeto de prueba deja basura o exige limpiarla, y una credencial sin permiso de escritura falla igual en la primera subida, con la misma visibilidad. *Fuente: derivado del alcance del requirement, que exige que el espacio esté listo, no que se haya ejercitado.*
- **¿Error nuevo o el que ya existe para un almacenamiento caído? (D3)** Nuevo. El criterio es el que el proyecto ya aplica a sus errores de dominio: dos causas que se arreglan de forma distinta no comparten tipo. *Fuente: convención vigente en `src/storage/exceptions.py` y en el manejo de errores del backend.*
- **¿Qué pasa con el contenedor de `storage-init` en un entorno ya levantado? (D5)** Queda huérfano y Compose no lo retira solo, así que el plan de migración incluye `--remove-orphans`. *Fuente: comportamiento conocido de Compose ante un servicio que desaparece de la definición.*
