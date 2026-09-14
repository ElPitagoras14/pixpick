## Why

La documentación del proyecto creció como registro de sus nueve changes, no como material de lectura. El README tiene 295 líneas y dedica buena parte a justificar decisiones internas; `.env.example` ocupa 10 KB para explicar unas treinta variables, y varias de esas notas citan decisiones de changes por su identificador (`D4 en add-cloud-media-adapters`) en lugar de decir qué valor poner; `compose.yaml` vuelve a explicar las mismas variables una tercera vez. Quien llega al proyecto lee tres versiones del mismo texto y termina eligiendo un valor con información que no necesitaba para elegirlo.

El README además está en inglés, que no es la lengua materna de quienes trabajan aquí. Hoy exige un nivel alto para leerse; la vara correcta es que lo entienda alguien de nivel B1.

Y hay un contenedor entero, `storage-init`, cuya única función es crear el bucket una vez. Es un servicio, un archivo de script, un volumen montado y dos `depends_on` para una llamada que el backend puede hacer con el cliente que ya tiene abierto contra ese mismo almacenamiento.

## What Changes

- **El README se reescribe para la persona que va a trabajar en el proyecto**, no para quien quiere entender por qué se decidió cada cosa. Responde qué es pixpick, cómo levantarlo, cómo correr las pruebas y dónde vive cada parte. En inglés simple, legible con nivel B1: frases cortas, y ninguna palabra técnica que no sea el nombre real de algo que la persona va a escribir o ver en pantalla.
- **Cada variable de `.env.example` queda acompañada solo de lo que hace falta para elegir su valor**: qué controla, qué valores admite y qué pasa si se cambia. Sin alternativas descartadas, sin referencias a decisiones de changes, sin historia.
- **Cada variable dice además si hay que darle un valor.** Son tres casos y hoy hay que deducirlos leyendo prosa: la que siempre necesita valor, la que puede quedar vacía, y la que pertenece a un grupo de alternativas donde solo el grupo que nombra el proveedor activo necesita valores. El proyecto tiene tres de esos grupos —identidad, almacenamiento e imágenes— y llenar el equivocado no produce ningún error hasta que algo se usa.
- **Los comentarios de `compose.yaml` dejan de explicar variables.** Lo que ya está en `.env.example` no se repite; quedan los comentarios que solo tienen sentido leyendo el compose, como por qué existe un servicio o por qué se publica un puerto.
- **`compose.dev.yaml` declara, servicio por servicio, qué recibe cada uno.** Deja de ser un archivo que solo construye imágenes y publica puertos: cada servicio lista las variables que le llegan, así que abrirlo alcanza para saber qué necesita cada pieza. Sin comentarios explicativos — la explicación de cada variable vive en `.env.example`, en un solo lugar.
- **Esa declaración nombra variables, no repite valores.** Compose resuelve cada nombre contra `.env`, de modo que el valor sigue escrito una sola vez. La única excepción son las direcciones que existen porque el servicio corre dentro de la red de Docker (`DATABASE_URL` y `MINIO_SERVER_ENDPOINT`, que apuntan a `postgres` y a `storage`): esas las arma `compose.yaml` y no se declaran aquí, porque declararlas por nombre las reemplazaría por el valor de modo native que guarda `.env` y el contenedor quedaría buscando la base en su propio localhost. Qué variable es de qué tipo se explica en `.env.example`, junto a cada una.
- **El README documenta cómo ver el entorno ya resuelto de cada servicio** (`docker compose config`). Es lo único de esta lista que no puede quedar desactualizado, porque lo imprime Compose a partir de los archivos y el `.env` reales.
- **El servicio `storage-init` desaparece, junto con `storage/init.sh`.** El backend garantiza al arrancar que el espacio donde guarda los objetos existe, usando la operación que el protocolo ya ofrece. El `transformer` pasa a depender del almacenamiento sano, que es lo único que necesita.

### Fuera de alcance

- **Montar el código fuente en los contenedores para editar en caliente.** El proyecto ya tiene un camino para eso: el modo native, donde el backend corre con `uv` y la interfaz con su dev server contra los mismos contenedores de terceros. Agregar montajes daría un segundo camino para lo mismo, con su propio conjunto de fallos (dependencias instaladas en la imagen que no coinciden con las del host).
- **Traducir el README al español.** El código, los comentarios y el README son en inglés por convención del repositorio; lo que cambia es el nivel exigido, no la lengua.
- **Crear el espacio de objetos en un proveedor externo.** El del proveedor cloud se crea una vez en el panel de Cloudflare, porque es un servicio de pago y ajeno: la garantía nueva cubre al proveedor que el proyecto opera dentro de su propio compose.
- Cualquier cambio en endpoints, dominio o interfaz. Este change no toca comportamiento de producto.

## Capabilities

### New Capabilities

- `project-documentation`: gobierna qué documenta el repositorio para quien va a trabajar en él y qué no. Fija la audiencia del README y su nivel de lectura, delimita qué preguntas responde, y establece que cada cosa se explica en un solo lugar — el archivo donde se la va a usar. Es la capability que hoy falta: el proyecto especifica su entorno, su API y sus pruebas, pero nada dice qué tiene que poder hacer alguien después de leer el README, así que su contenido creció sin criterio para decidir qué sacar.

### Modified Capabilities

- `local-environment`: el requirement «El entorno declara su configuración en un archivo de ejemplo» gana qué tiene que acompañar a cada variable. Hoy exige que todas estén presentes, con valor por defecto y sin huérfanas — nada sobre qué se dice de ellas. Se le agrega que lo que acompaña a una variable SHALL ser lo suficiente para elegir su valor y SHALL indicar si necesita uno, distinguiendo la que siempre lo requiere, la que puede quedar vacía y la que pertenece a un grupo de alternativas del que solo uno aplica; y que ese texto vive en el archivo de ejemplo y no se duplica en los archivos que la consumen. Se le agrega también que cada servicio del entorno SHALL declarar qué variables consume, sin que eso implique declarar sus valores más de una vez.
- `object-storage`: gana un requirement sobre el espacio donde el proveedor guarda los objetos. Hasta ahora ninguna spec decía que ese espacio tiene que existir — la garantía estaba implícita en «un solo comando levanta el entorno completo» de `local-environment`, y materializada en un servicio de compose. Pasa a ser explícita y del puerto: preparar el almacenamiento SHALL formar parte del arranque, y para un proveedor que el proyecto no opera SHALL bastar con comprobar que el espacio ya está. Así el resto del código sigue sin ramificar según el proveedor activo, que es la regla que esta capability ya impone.

## Impact

**Archivos eliminados**

- `storage/init.sh` y, con él, el directorio `storage/`.

**Archivos modificados**

- `README.md`: reescrito completo.
- `.env.example`: cada bloque de comentario reducido a lo necesario para elegir el valor.
- `compose.yaml`: se van los comentarios que explican variables y el servicio `storage-init` entero; el `depends_on` del backend hacia él y el del `transformer` se reemplazan por una dependencia del almacenamiento sano.
- `compose.dev.yaml`: cada servicio gana su bloque `environment` con lo que recibe. Los dos servicios cuyas variables el compose renombra (`storage`, que recibe las credenciales de MinIO bajo los nombres que MinIO espera, y `transformer`, igual con las del transformador) declaran ese mapeo, que es de uno a uno y no se compone de nada.
- `backend/src/storage/port.py`: una operación más, para dejar el almacenamiento listo antes de usarlo.
- `backend/src/storage/adapters/minio.py` y `r2.py`: la implementan. La del proveedor local crea el espacio si falta; la del cloud comprueba que está y falla con un error de dominio si no, que es la única forma de que la suite de contrato siga corriendo igual contra los dos.
- `backend/src/main.py`: la llamada entra en el `lifespan`, junto a la comprobación de conectividad de la base que ya vive ahí. Un almacenamiento sin espacio falla el arranque con un error explícito, en lugar de la primera subida.
- La suite de contrato del almacenamiento gana el caso correspondiente, sin adaptarse por proveedor.

**Consecuencia en el modo native**

Hoy el bucket lo crea un servicio del compose, así que trabajar en modo native depende de haber levantado el entorno completo alguna vez. Con la creación en el backend, el modo native queda cubierto por sí solo.

**Precedencia**

Ninguna. Es el primero de los siete changes que salen de esta ronda de observaciones y no depende de los otros seis.
