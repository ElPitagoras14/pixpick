## Context

`README.md` tiene 340 líneas en un solo documento ordenado por tema. Lo que necesita quien despliega está repartido entre cinco secciones de nivel `##` separadas por material que no le toca, y la sección más grande —113 líneas, un tercio del documento— mezcla la tabla de servicios y el hostname del storage, que son suyos, con tres tablas de stack que no va a abrir. El primer comando del documento construye desde el código.

`.env.example` ya está resuelto y no se toca: 139 líneas divididas en un bloque `CONFIGURE` y uno `TUNE`, agrupadas por área, cada variable con qué controla y qué valores admite. Delega en el README cuatro veces, por los pasos de Google OAuth, por el hostname del storage, por R2 y por ImageKit.

Los dos archivos de compose son una referencia de cómo se componen los servicios, no la forma final en que cada operador los va a correr. `compose.yaml` no publica ningún puerto; `compose.dev.yaml` publica `NGINX_PORT`, `POSTGRES_PORT` y `MINIO_PORT`. El entorno declara ocho servicios y tres volúmenes: `postgres-data`, `storage-data` y `nginx-cache`.

Las imágenes de `ghcr.io` que consume `compose.yaml` van a existir antes de que este documento se integre.

## Goals / Non-Goals

**Goals:**

- Un mapa de secciones donde cada cosa tiene un solo hogar, y ese hogar es donde su lector la va a buscar.
- Una línea escrita entre el documento de entrada y el archivo de ejemplo de variables, que hoy existe de hecho pero no está declarada en ninguna parte.
- Que todo comando dirigido a quien opera sea ejecutable con lo que esa persona tiene.

**Non-Goals:**

- Partir el documento en dos archivos. El material de desarrollo se agrupa, no se muda.
- Reescribir las secciones de operación que ya están bien. El hostname del storage, el límite de peticiones frente a una CDN, la tabla de servicios y el runbook de migración cambian de lugar, no de contenido.
- Prescribir una plataforma de despliegue, un proxy concreto o una forma de terminar TLS.
- Agregar una captura o un diagrama de la aplicación.

## Decisions

### D1 - Un documento, con el material de desarrollo agrupado al final

La alternativa era un segundo archivo que se llevara todo lo de desarrollo, y quedó descartada para este change. Agruparlo en un solo bloque de nivel `##` con subsecciones adentro consigue lo mismo para el lector —ninguna de las dos audiencias atraviesa el material de la otra— y deja el corte hecho: si más adelante ese bloque se muda a su propio archivo, se mueve entero y no hay que reescribir nada alrededor.

### D2 - El orden lo fija el momento en que cada cosa hace falta

La alternativa era conservar el agrupamiento temático y limitarse a mover el bloque de desarrollo al final, que es menos trabajo y deja a quien despliega saltando entre secciones igual. El mapa resultante:

```
# Pixpick                      que es
## What you need               el runtime de contenedores
## Start it                    el comando que consume imagenes publicadas
## Get the values you need     los cuatro procedimientos externos
    ### Google
    ### R2
    ### ImageKit
    ### The storage hostname
## Put it on a server          que espera el stack del entorno
## Keep it running             backups, subir de version, mantenimiento, logs
## Move the photos elsewhere   el runbook de migracion entre proveedores
## The services                la tabla de los ocho
## Work on the code
    ### Run it from source
    ### Run the tests
    ### Where each part lives
    ### Upgrade the dependencies
```

### D3 - Los cuatro procedimientos externos van juntos en una sección, no sueltos donde cada uno caería

Sueltos se escanean mejor, y fue la alternativa considerada. Juntos ganan dos cosas que pesan más: las cuatro remisiones de `.env.example` aterrizan todas en el mismo lugar, y quien está llenando `.env` hace una sola pasada en vez de cuatro saltos.

### D4 - Lo que sale del README por duplicación

Cuatro pasajes explican lo que `.env.example` ya explica: qué valores toma `IDENTITY_PROVIDER` y qué hace `local` (líneas 81 y 83, casi palabra por palabra), que `STORAGE_PROVIDER` e `IMAGE_PROVIDER` eligen proveedor (96), que cada `POSTGRES_DB` guarda sus propios álbumes (117) y qué es `PUBLIC_URL` (77). De cada uno queda lo que el archivo de ejemplo no puede cargar: los pasos en la consola del proveedor. Aplicar la regla achica el documento en vez de agrandarlo.

### D5 - La sección de servidor describe lo que el stack espera, no cómo montarlo

Un punto de entrada único, dos hostnames públicos, TLS terminado afuera y el límite de peticiones que importa al poner una CDN delante. La alternativa era un instructivo para una plataforma concreta, que envejece con esa plataforma y deja afuera a todas las demás. Ahí se absorben el hostname del storage, que hoy vive en la sección de estructura, y el límite de peticiones frente a una CDN.

### D6 - Los comandos de mantenimiento se ejecutan contra el contenedor

Hoy piden `cd backend` y `uv run python -m src.maintenance.reconcile`, que supone un clon y herramientas de desarrollo. El servicio `reconciler` corre exactamente `python -m src.maintenance.reconcile` desde `/app`, y su entorno ya trae las variables de base de datos, de storage local, de R2 y de retención, así que es el destino natural: `docker compose exec reconciler python -m src.maintenance.reconcile`, con `--against r2` para la comprobación del runbook de migración. La forma con `uv` se conserva, pero dentro del bloque de desarrollo.

### D7 - Qué volúmenes se respaldan y cuál no

Se respaldan `postgres-data` y `storage-data`, que son la base y las fotos. `nginx-cache` es contenido derivado y se reconstruye solo, así que se dice explícitamente que no hace falta. La única mención actual de los volúmenes es la del `-v` que los borra, que pasa a convivir con la que explica qué se pierde.

### D8 - Las dos duplicaciones internas

El límite de peticiones se explica hoy en el troubleshooting y otra vez en su propia sección: queda completo donde el lector llega con el error en la mano, y la sección de servidor conserva solo lo que agrega, que es la regla en la CDN. Cómo consultar la configuración efectiva aparece dos veces con el mismo comando: queda en el troubleshooting.

### D9 - Las tablas de stack se conservan

Dejan de estar en el camino de quien despliega por estar dentro del bloque de desarrollo, y ahí sirven a quien sí las lee. Achicarlas es una decisión separada que no necesita este change.

## Risks / Trade-offs

- El documento encabeza con un comando que solo funciona una vez publicadas las imágenes → se integra después de que existan; hasta entonces el change queda listo y sin mergear.
- El bloque de desarrollo queda grande, alrededor de la mitad del documento → subsecciones adentro, y su tamaño es precisamente lo que justifica que más adelante sea un archivo aparte.
- Sacar del README lo que `.env.example` explica deja sin respuesta a quien lea solo el README → cada sección que necesita un valor nombra la variable y remite al archivo, que es el sentido de la remisión en la dirección contraria que ya existe.
- La regla nueva no tiene comprobación automática, así que nada impide que la duplicación vuelva a aparecer → queda como riesgo aceptado; una comprobación que compare explicaciones entre dos archivos en prosa es un problema distinto y más caro que el que este change resuelve.
- Mover secciones rompe los anclajes de los títulos que hayan quedado enlazados desde afuera → el repositorio no se enlaza a sí mismo por anclaje, y las cuatro remisiones de `.env.example` nombran el archivo, no una sección.

## Open Questions

Ninguna. Las decisiones que faltaban tocaban el orden de las secciones, el reparto con el archivo de ejemplo y el alcance del documento, y las tres cambian los specs o el reparto de tareas, así que ninguna admitía quedar diferida.

### Resueltas durante la redacción

- **Si el material de desarrollo se muda a un segundo archivo.** No: el usuario lo dejó explícitamente fuera de alcance. Se agrupa en un bloque, que además deja hecho el corte por si más adelante se muda.
- **Si `local-environment` también cambia.** No. Esa capability exige que un solo comando deje el proyecto accesible desde el navegador y que el punto de entrada se exponga al host, y `compose.yaml` no publica nada. La contradicción se disuelve al leerla como lo que su nombre dice, la que gobierna el entorno de desarrollo, que es el que satisface esas exigencias. Se planteó la alternativa de sumarla a las capabilities modificadas y el usuario siguió adelante sin ella.
- **Qué topología de despliegue documentar.** Ninguna. El usuario definió que los archivos de compose son una referencia de cómo se componen los servicios y no la forma final en que cada operador los usa, así que el documento describe lo que el stack espera del entorno y deja la topología a quien lo adapta.
- **Si los cuatro procedimientos externos van en una sección o en cuatro.** En una, con cuatro subsecciones. Decidió el hecho verificado de que `.env.example` remite al README cuatro veces: agrupados, las cuatro remisiones aterrizan en el mismo lugar.
- **Cuál es el comando de mantenimiento correcto contra contenedores.** `docker compose exec reconciler python -m src.maintenance.reconcile`. Lo cerró leer el servicio `reconciler` en `compose.yaml`: corre esa misma línea desde `/app` y su entorno ya incluye las variables de base de datos, storage local, R2 y retención que el comando necesita, incluida la variante `--against r2`.
- **Si el change agrega una captura o un diagrama de la aplicación.** No. Se planteó dos veces durante la exploración y quedó sin respuesta, y el proposal no la incluye; sumarla dependería además de que exista el material. El change se queda en reestructurar lo que ya está escrito.
