## Context

El repositorio no tiene ningún workflow de integración continua, ningún tag y ninguna imagen publicada. `compose.yaml` referencia `ghcr.io/elpitagoras14/pixpick-backend`, `-frontend`, `-migrate` y `-nginx` en su etiqueta móvil, y las cuatro responden que no están disponibles ante una consulta anónima al registro. `VERSION` en la raíz dice `0.1.0` y ningún archivo del proyecto lo lee.

Cuatro condiciones del repositorio determinan el margen de este diseño.

Los cuatro contextos de build son independientes. `backend/Dockerfile` copia `pyproject.toml`, `uv.lock` y `src`; `frontend/Dockerfile` copia todo su directorio y se queda con `dist` más tres archivos de arranque; `dbmate/Dockerfile` copia `migrations` y `schema.sql`; `nginx/Dockerfile` copia su plantilla y su entrypoint. Ninguno toma archivos de la raíz ni de otro servicio, así que el directorio de cada servicio es una señal honesta de si su imagen cambió.

Dos de esos contextos versionan material que no llega a la imagen: `backend/tests`, que el Dockerfile ni siquiera copia, y `frontend/AGENTS.md`, `frontend/biome.json` y `frontend/.cta.json`, que entran al contexto de build pero no influyen en lo que `vite build` produce. `dbmate` y `nginx` no tienen sobras: todo lo que versionan se hornea.

Ningún Dockerfile acepta una versión como argumento de build, y el frontend resuelve su configuración en runtime mediante `config.template.js` y `envsubst` en su entrypoint. Ninguna imagen lleva adentro nada que dependa de la versión ni del entorno de despliegue.

Las imágenes base están fijadas de forma dispareja: `nginx:1.30.4`, `ghcr.io/amacneil/dbmate:2.35.1` y `ghcr.io/astral-sh/uv:0.10.9` señalan una versión concreta, mientras que `python:3.13-slim` y `node:22-slim` son etiquetas que reciben parches sin cambiar de nombre.

## Goals / Non-Goals

**Goals:**

- Que el trabajo de construir se pague una sola vez por servicio y por cambio real, no una vez por release.
- Que una imagen reutilizada sea verificablemente la misma, y no una reconstrucción que se le parece.
- Que un release interrumpido se recupere solo, sin que nadie tenga que inspeccionar el registro ni borrar tags a mano.
- Que quien consume las imágenes nunca observe un estado intermedio del release.
- Que el criterio de reconstrucción falle hacia construir de más y nunca hacia publicar una imagen que no corresponde al código.

**Non-Goals:**

- Reconstruir imágenes para incorporar parches de sus bases. Este diseño elige explícitamente lo contrario, y compensa fijando las bases para que actualizarlas sea un cambio visible en el repositorio.
- Atomicidad literal de la publicación. Las imágenes de una versión aparecen en el registro a medida que cada una termina; lo que el diseño garantiza es que nada las consuma hasta que estén todas.
- Optimizar el tiempo de construcción por debajo de lo que la reutilización ya ahorra.

## Decisions

### El punto de comparación es el tag más alto, no el commit anterior

Un release compara `VERSION` contra el tag semver más alto del repositorio, y compara los directorios de cada servicio contra ese mismo tag.

La alternativa natural sería comparar contra el commit anterior de la rama principal, que es más barato de calcular. Se descarta porque convierte cualquier fallo en corrupción silenciosa: si una corrida publica tres imágenes y muere antes de crear el tag, la corrida siguiente vería el commit anterior como referencia, concluiría que ya no hay cambios pendientes y publicaría una versión incompleta. Con el tag como referencia, un intento fallido no deja huella y el siguiente rehace el trabajo entero.

Ese razonamiento es también lo que obliga a crear el tag al final, después de publicar las imágenes y mover la etiqueta móvil. El tag es la constancia de que el release terminó, así que asentarlo antes lo convertiría en una promesa en lugar de un hecho.

### La comparación de versiones es numérica

La comparación usa `sort -V`, que ordena por precedencia numérica de cada tramo. Alfabéticamente `0.1.10` queda por debajo de `0.1.9`, y un release se saltearía sin aviso en cuanto un tramo llegue a dos dígitos.

Se descarta `git describe --tags --abbrev=0`, que devuelve el tag alcanzable más reciente por topología del historial y no el de mayor precedencia. Son lo mismo mientras los tags se creen en orden, y dejan de serlo apenas alguien etiquete fuera de orden o rehaga historia.

### Reutilizar es copiar el manifiesto, no reconstruir

Un servicio sin cambios se publica con `docker buildx imagetools create --tag <imagen>:<nueva> <imagen>:<anterior>`. El registro guarda un solo manifiesto y le cuelga dos nombres: mismo digest, ninguna capa subida, ningún almacenamiento adicional, y nada que descargar para quien ya tiene la versión anterior.

La alternativa era reconstruir confiando en el cache de capas. Se descarta porque el cache no garantiza bits idénticos —basta un `ADD` con timestamp, una base que se movió o una entrada evictada para que el resultado difiera— y porque un cache miss termina reconstruyendo todo de todas formas. La copia de manifiesto no tiene modo de fallo parcial: o el nombre nuevo apunta al manifiesto viejo o la operación falla.

### El criterio de cambio se define por exclusión

Cada servicio declara una pathspec que parte de su directorio y resta lo que no entra en la imagen:

```
backend    backend :!backend/tests
frontend   frontend :!frontend/AGENTS.md :!frontend/biome.json :!frontend/.cta.json
migrate    dbmate
nginx      nginx
```

La alternativa era enumerar los archivos que sí afectan la imagen, que es más preciso hoy y peligroso mañana. Ante un archivo nuevo que nadie sumó a la lista, enumerar concluye que el servicio no cambió y publica la imagen anterior bajo el nombre de la versión nueva: el registro pasa a mentir sobre qué código contiene una imagen, en silencio. Excluyendo, ese mismo archivo provoca una reconstrucción innecesaria, que cuesta minutos y se ve en el log.

`components.json` queda deliberadamente del lado que cuenta, aunque solo lo lea la herramienta de componentes del frontend y no influya en el build. Ahorra un rebuild que casi nunca va a ocurrir y obligaría a rehacer ese razonamiento en cada revisión futura.

Un detalle de implementación con trampa: la pathspec se expande sin comillas para que el shell la separe en argumentos. Escribirla con comillas simples dentro del YAML no funciona, porque el shell no reinterpreta las comillas que provienen de expandir una variable y git recibiría un path que empieza con comilla; la exclusión se evaporaría sin error. En un script no interactivo `!` no necesita escape.

### Ninguna imagen lleva la versión adentro

Como ninguna imagen hornea la versión, las cuatro se pueden reutilizar por copia de manifiesto sin más. Un proyecto donde alguna imagen llevara la versión dentro necesitaría, para esa imagen, una tercera vía entre construir y copiar: armar una capa que estampe el valor nuevo sobre la imagen anterior. Este diseño no la incluye porque no la necesita, y esa ausencia depende de que la versión siga sin ser observable en runtime.

### Multi-arquitectura por emulación, no por runners nativos

Cada leg construye `linux/amd64,linux/arm64` en un mismo runner, con `docker/setup-qemu-action` declarado explícitamente en lugar de confiar en que la imagen del runner traiga `binfmt` configurado.

La alternativa es partir cada servicio en dos legs —una en `ubuntu-latest` y otra en `ubuntu-24.04-arm`, gratis en repositorios públicos— que publican por digest, más un job que fusiona los digests en un índice multiplataforma. Es sensiblemente más rápido y bastante más complejo: la decisión de construir o reutilizar tiene que subir al job que detecta, para poder generar la matriz con `fromJSON`; el cache se parte por arquitectura para que dos runners no se pisen; y un job con matriz vacía se saltea arrastrando en cascada a todo lo que dependa de él, que es exactamente lo que ocurre en el release donde nada cambió y hay que contener con condiciones explícitas.

Se elige la emulación porque de los cuatro servicios solo dos tienen algo caro que emular, y solo en los releases donde cambian. Migrar después es un cambio contenido en el job que publica: detectar, mover la etiqueta móvil y registrar el release no se tocan.

### El cache de capas vive en el registro

`cache-from` y `cache-to` apuntan a una etiqueta `buildcache` del propio paquete, con `mode=max`, y solo para backend y frontend.

La alternativa es el almacenamiento de cache de Actions. Se descarta por el patrón de uso: este pipeline no construye en cada integración sino cuando sube la versión, y GitHub borra las entradas de cache que no se acceden en una semana. Con releases espaciados el cache llegaría frío casi siempre. El del registro no expira por inactividad ni compite por la cuota de diez gigabytes que el repositorio comparte entre todas sus caches.

`migrate` y `nginx` quedan fuera porque no tienen nada caro que cachear: su construcción es descargar una base y superponer un par de capas triviales. Lo que el cache sí recupera es `uv sync` en el backend y `pnpm install` en el frontend, que se invalidan solo cuando cambian sus archivos de dependencias, y que son justamente lo que la emulación vuelve lento. Lo que nunca va a acertar es `vite build`, que se invalida con cualquier cambio en `frontend/src` —o sea, con la razón misma por la que el frontend se está reconstruyendo.

### La etiqueta móvil se mueve en un paso aparte

Un job posterior a la matriz recorre los cuatro servicios y apunta `latest` a la versión recién publicada. Corre en un solo runner, porque cada operación tarda segundos y levantar cuatro para esto sería desproporcionado.

Que sea un paso aparte es lo que hace que la publicación sea atómica para quien la consume: las imágenes `:<versión>` aparecen de a una, pero nadie las pide por ese nombre. `compose.yaml` pide `latest`, que hasta ese momento sigue apuntando a la versión anterior completa.

### Fijar las bases es lo que hace honesta a la reutilización

`python:3.13-slim` pasa a una versión de parche explícita, y `node:22-slim` también.

Sin eso, reutilizar tiene una consecuencia que nadie eligió: un servicio que no se toca durante meses se sigue publicando con la base que bajó la primera vez, porque no existe ningún evento que fuerce su reconstrucción. Con las bases fijadas, actualizar una es editar su Dockerfile, y esa edición cae dentro de la pathspec del servicio y dispara el build por el mismo mecanismo que cualquier otro cambio.

Se consideró un disparo manual con reconstrucción forzada. Se descarta porque no cierra: o republica un nombre de versión ya publicado, y entonces ese nombre pasa a significar dos contenidos distintos según el día, o exige subir `VERSION` antes, pero ese cambio ya dispara por su cuenta una corrida que reutiliza todo y asienta el tag, dejando al disparo manual sin nada que hacer.

### La matriz aborta al primer fallo

`fail-fast` queda en `true`, que es el valor por defecto, declarado de forma explícita porque acá es una decisión y no una inercia. Si un servicio rompe, el release no va a salir igual, así que cancelar las legs en vuelo deja menos imágenes huérfanas sin nombre de release que la corrida siguiente tenga que sobrescribir.

## Risks / Trade-offs

**Una imagen reutilizada no incorpora parches de su base** → Es el precio de garantizar bits idénticos; las dos cosas no pueden ser verdad a la vez. Se mitiga fijando las cinco bases, de modo que actualizarlas sea una decisión explícita y visible en el historial en lugar de algo que llega solo y sin registro.

**La emulación hace lento el release cuando cambia el frontend** → El cache de registro cubre `pnpm install`, que es la parte que más sufre la emulación. El empaquetado en sí no tiene mitigación posible y se paga cada vez que el frontend cambia; el techo es del orden de diez a quince minutos en el peor caso, contra cuatro o cinco con runners nativos, y ocurre solo en releases.

**Mover la etiqueta móvil no es una operación atómica** → No existe forma de reapuntar varias etiquetas transaccionalmente en un registro OCI. La ventana dura lo que tardan cuatro llamadas, del orden de segundos, y solo la observaría alguien que descargue exactamente en ese instante.

**Los tags se acumulan en el registro** → Cada release suma cuatro nombres. Como los reutilizados son referencias al mismo manifiesto, no duplican almacenamiento; lo que crece es la lista de nombres. Sin mitigación por ahora, por decisión de alcance.

**El despliegue depende de un servicio externo** → El paso de despliegue no interrumpe el release si falla. Las imágenes y el tag son válidos por sí mismos y el despliegue se puede reintentar sin rehacerlos.

**La exclusión provoca reconstrucciones innecesarias** → Es el modo de fallo elegido a propósito, y cuesta minutos de runner que en un repositorio público no se facturan.

## Migration Plan

El proyecto no tiene nada publicado, así que no hay migración de un estado anterior sino una puesta en marcha.

Antes de integrar: crear el proyecto en Dokploy y anotar su identificador, cargar `DOKPLOY_API_KEY` como secreto del repositorio y `DOKPLOY_COMPOSE_ID` como variable.

Al integrar, la primera corrida encuentra `VERSION` en `0.1.0` y ningún tag. Sin tag anterior no hay con qué comparar ni de dónde reutilizar, así que los cuatro servicios se construyen, la etiqueta móvil queda apuntando a `0.1.0` y el tag nace al final. No hace falta modificar `VERSION` para que esto ocurra: el número que ya está declarado es el del primer release.

Los cuatro paquetes se crean en esa corrida. Al publicarse desde el workflow con la credencial del propio repositorio, que es público, quedan públicos sin configuración adicional.

Rollback: volver a una versión anterior es apuntar la etiqueta móvil a ella con la misma operación de copia de manifiesto que usa la reutilización. Las imágenes de todas las versiones anteriores siguen publicadas bajo su propio nombre, así que no hay nada que reconstruir. Revertir el pipeline entero es borrar el workflow; las imágenes ya publicadas no dependen de él para seguir sirviendo.

## Open Questions

Ninguna. Las decisiones que quedaban por tomar dependían de información que estaba disponible —en los Dockerfiles, en el registro o en la documentación de la plataforma— o de una preferencia del usuario que se consultó antes de cerrar el diseño.

### Resueltas durante la redacción

**¿Alguna imagen necesita llevar la versión adentro?** No. Se verificó que ningún Dockerfile declara un argumento de build para la versión y que ningún archivo del proyecto lee `VERSION`; el endpoint de salud del backend devuelve solo un estado. El usuario confirmó además que no quiere la versión observable en runtime. Eso es lo que permite que las cuatro imágenes se reutilicen por copia de manifiesto sin una tercera vía de estampado.

**¿Los paquetes publicados nacen públicos o privados?** Públicos. La documentación de GitHub se contradice entre dos páginas: una afirma que un paquete creado por un workflow con la credencial del repositorio hereda su visibilidad, y otra que hereda los permisos de acceso pero no la visibilidad. Se resolvió empíricamente contra los paquetes de otro proyecto del mismo propietario, publicados por un workflow equivalente: los cuatro responden a una consulta anónima al registro. Por eso el plan de puesta en marcha no incluye ningún paso manual de visibilidad ni credenciales de registro para el desplegador.

**¿El nombre de la versión lleva prefijo?** No. Se verificó contra los tags publicados de ese mismo proyecto, que van de `1.0.0` a `2.0.21` sin prefijo. El nombre tiene que ser idéntico en el tag del repositorio y en la etiqueta de la imagen, porque el release siguiente usa ese nombre como referencia para reutilizar.

**¿Emulación o runners nativos por arquitectura?** Emulación, por respuesta del usuario tras ver el costo de cada camino. La estimación del costo se derivó de la forma del proyecto: sesenta y seis paquetes en el lock del backend, todos con distribuciones precompiladas para ARM de 64 bits en las dependencias que suelen requerir compilación, y treinta y una dependencias más cincuenta y seis archivos de código en el frontend.

**¿Cómo se refrescan las imágenes base?** Fijándolas. La primera propuesta fue un disparo manual con reconstrucción forzada; se descartó al escribirla porque reutilizaría un nombre de versión ya publicado o exigiría un bump previo que ya dispara su propia corrida. Fijar las dos bases móviles resuelve el mismo problema con el mecanismo que el pipeline ya tiene.

**¿Qué se excluye del contexto de cada servicio?** Se derivó leyendo cada Dockerfile contra la lista de archivos versionados de su directorio, y quedó asimétrico: `backend` excluye sus pruebas, `frontend` excluye tres archivos de documentación y configuración de herramientas, y `dbmate` y `nginx` no excluyen nada porque todo lo que versionan se hornea.

**¿El release se apoya en pruebas o linters?** No, por decisión del usuario: ejecutarlos queda a cargo de quien desarrolla. Es separable, así que no condiciona nada de este diseño.

**¿Dónde vive el requisito de fijar las bases?** En `local-environment`, extendiendo el requisito que ya fija las versiones de las imágenes de terceros, en lugar de crear uno nuevo en `release-pipeline`. El motivo que justifica ese requisito —que reconstruir en otro momento no traiga silenciosamente una versión distinta— es exactamente el que aplica a las bases bajo la forma que construye desde el código fuente. El requisito existente no las alcanzaba solo porque su texto habla de la declaración del entorno.
