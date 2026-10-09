## Why

`README.md` lo lee principalmente quien va a levantar pixpick con `docker compose`, y está escrito para quien va a desarrollarlo. El propio repositorio ya lo delata: `.env.example` —el archivo que solo abre quien despliega— remite al README cuatro veces, por los pasos de Google OAuth, por el hostname del storage, por R2 y por ImageKit. Las cuatro apuntan a material de operación; ninguna apunta a las secciones de desarrollo. Pero la estructura dice lo contrario: "Start it" encabeza con `compose.dev.yaml ... --build`, que construye desde el código, y el camino que consume imágenes publicadas queda como una fila de tabla en la línea 37. Lo que el operador necesita está repartido entre cinco secciones separadas por material que no le toca, y un tercio del documento —113 de 340 líneas— es una sección que mezcla la tabla de servicios y el hostname del storage, que sí son suyos, con tres tablas de stack que no va a abrir nunca.

Sobre esa estructura se acumulan dos deudas. La primera es duplicación: cuatro explicaciones de configuración están escritas dos veces, en el README y en `.env.example`, una de ellas casi palabra por palabra. La segunda son ausencias que solo se ven desde la silla del operador: los volúmenes `postgres-data` y `storage-data` guardan la base y las fotos de alguien y el documento los menciona una sola vez, para explicar cómo borrarlos; no hay nada sobre subir la instancia a una versión nueva; y no se dice qué espera el stack del entorno para ser alcanzable, cuando los archivos de compose son una referencia de cómo componer los servicios y no la forma final en que cada operador los va a correr. El troubleshooting, además, le habla a su lector principal con comandos que ese lector no puede ejecutar: pide `cd backend` y `uv` a quien solo tiene contenedores.

## What Changes

- El documento se reordena por el momento en que cada cosa hace falta, con quien despliega como lector principal: levantar, iniciar sesión, elegir dónde viven las fotos, poner el proyecto en un servidor, mantenerlo andando, y la tabla de servicios.
- "Start it" pasa a encabezar con la forma que consume imágenes publicadas. La forma que construye desde el código deja de ser el primer comando del documento.
- Todo el material de desarrollo queda agrupado en una sola sección al final: correr desde el código, las pruebas, el linting, dónde vive cada parte, las tablas de stack y la actualización de dependencias. El documento sigue respondiendo cómo ejecutar las pruebas y dónde tocar cada cosa, en un solo lugar en vez de repartido.
- El README deja de explicar qué es una variable y qué valores admite. Eso vive en `.env.example`, que ya lo hace agrupado por área. El README conserva lo que ese archivo no puede cargar y por eso le delega: los procedimientos fuera del repositorio que hay que completar para conseguir un valor, que quedan juntos en una sola sección.
- Aparece qué espera el stack del entorno de quien lo adapte: un único punto de entrada, dos hostnames públicos, TLS terminado afuera y el límite de peticiones que importa al poner una CDN delante. No se prescribe una plataforma ni una topología.
- Aparece cómo mantener la instancia: qué volúmenes respaldar y qué se pierde sin ellos, y cómo pasar a una versión nueva.
- Los comandos de mantenimiento del troubleshooting pasan a ejecutarse contra los contenedores, sin suponer un clon del repositorio ni herramientas de desarrollo en la máquina.
- Se corrigen dos datos: la lista de servicios que enumera siete cuando el entorno declara ocho, y la diferencia sin explicar entre los dos comandos que levantan un subconjunto de servicios.
- Se resuelven las dos explicaciones que hoy aparecen dos veces dentro del propio README, el límite de peticiones y cómo consultar la configuración efectiva, dejando cada una donde el lector la va a buscar.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `project-documentation`: cambia el requirement que fija a quién se dirige el documento de entrada. Hoy dice que se dirige a quien va a desarrollar sobre el proyecto, y eso ya no describe a su lector principal ni al orden en que el documento tiene que estar escrito. Pasa a nombrar a las dos audiencias con una prioridad —primero quien levanta el proyecto, después quien lo desarrolla— y a exigir que el material de desarrollo quede agrupado, sin perder ninguna de las preguntas que el documento ya tenía que responder. Gana además un requirement que fija el reparto entre el documento de entrada y el archivo de ejemplo de variables: el ejemplo explica qué es cada variable y qué valor toma, y el documento de entrada explica los procedimientos externos para conseguir ese valor. Hoy ese reparto existe de hecho —el archivo de ejemplo delega cuatro veces— pero no está escrito en ninguna parte, y por eso las cuatro duplicaciones vigentes no las detiene nada.

## Impact

- `README.md`, reordenado por completo. Ninguna de las secciones de operación se reescribe desde cero: el hostname del storage, el límite de peticiones frente a una CDN, la tabla de servicios y el runbook de migración entre proveedores ya están bien escritos y cambian de lugar, no de contenido.
- `openspec/specs/project-documentation/spec.md`, con un requirement modificado y uno nuevo.
- `.env.example` no se modifica. Sus cuatro remisiones al README siguen siendo válidas y aterrizan todas en la misma sección nueva.
- `compose.yaml` y `compose.dev.yaml` no se modifican. El change describe lo que ya son; no cambia qué publican ni cómo se componen.
- Ningún cambio de comportamiento. No se toca código, ni configuración efectiva, ni la suite.
- Este change se integra después de que existan las imágenes publicadas, porque "Start it" pasa a encabezar con el comando que las consume.
