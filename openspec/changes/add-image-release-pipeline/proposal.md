## Why

El proyecto declara dos formas de levantarse y solo una funciona. `compose.yaml` referencia `ghcr.io/elpitagoras14/pixpick-backend`, `-frontend`, `-migrate` y `-nginx` en su etiqueta móvil, pero ninguna de esas imágenes existe: el repositorio no tiene workflows, no tiene tags y nunca publicó nada. La forma que `local-environment` exige —la que consume imágenes ya publicadas— está declarada pero no es realizable, así que hoy la única manera de levantar el proyecto es construirlo desde el código. Publicar el repositorio sin resolver eso deja a cualquiera que lo clone frente a un `compose.yaml` que no puede satisfacer.

Falta además el paso siguiente: sin un mecanismo que publique imágenes versionadas no hay nada que desplegar, y el despliegue queda como una operación manual que nadie registra.

Construir las cuatro imágenes en cada versión sería la respuesta obvia y sería un desperdicio. Los cuatro contextos de build son independientes —ninguno copia archivos de la raíz ni de otro servicio— y la mayoría de las versiones toca uno o dos. Un servicio cuyo directorio no cambió produciría, al reconstruirlo, una imagen equivalente a la anterior, pagando el build completo para no cambiar nada.

## What Changes

- Aparece un pipeline de release que se dispara al integrar en la rama principal y que decide si hay algo que publicar comparando la versión declarada en el código contra el tag más alto ya publicado. Si la versión no subió, no publica nada ni crea ningún tag.
- Cada release publica las cuatro imágenes bajo el tag de la versión, pero solo construye aquellas cuyo contexto cambió desde el release anterior. Las demás se reetiquetan en el registry sin reconstruirse, de modo que conservan exactamente los mismos bits.
- Qué cuenta como cambio de un servicio se define excluyendo lo que el servicio versiona pero no hornea —las pruebas del backend, la documentación y la configuración de herramientas del frontend— en lugar de enumerar lo que sí entra. Un archivo nuevo no contemplado provoca un build de más, nunca la publicación de una imagen que no corresponde al código.
- Un servicio para el que no exista imagen del release anterior se construye, aunque su contexto no haya cambiado. Cubre el servicio recién agregado y el registry purgado.
- La etiqueta móvil de los cuatro servicios se mueve recién cuando las cuatro imágenes de la versión están publicadas, para que `compose.yaml` nunca resuelva una mezcla de versiones.
- El tag de la versión se crea al final, después de publicar. Un release que falla a mitad de camino no deja el tag creado, así que el intento siguiente vuelve a ver los mismos cambios pendientes y se recupera solo.
- Las imágenes se publican para `linux/amd64` y `linux/arm64`.
- El despliegue lo dispara el propio pipeline al terminar el release, y su fallo no marca el release como fallido.
- Las dos imágenes base que hoy usan etiquetas móviles —`python:3.13-slim` en el backend y `node:22-slim` en el frontend— pasan a versión explícita, como ya hacen `nginx`, `dbmate` y `uv`. Sin eso, un servicio que no se toca durante meses se sigue publicando con la base que bajó la primera vez, porque nada fuerza su reconstrucción.

Queda fuera de alcance la ejecución de pruebas o linters como condición del release: seguirlas corriendo es responsabilidad de quien desarrolla, y sumarlas al pipeline es un change aparte que no depende de este.

Queda fuera de alcance una política de retención en el registry. Cada release suma cuatro tags y, como los no reconstruidos son referencias al mismo manifiesto, no duplican almacenamiento; la acumulación de nombres se atenderá cuando moleste.

## Capabilities

### New Capabilities

- `release-pipeline`: gobierna cómo el proyecto convierte el código integrado en artefactos desplegables —cuándo hay un release, qué se publica y bajo qué nombre, cuándo una imagen se reconstruye y cuándo se reutiliza, en qué orden queda todo visible para quien consume las imágenes, cómo se recupera un release interrumpido, y quién dispara el despliegue.

### Modified Capabilities

- `local-environment`: el requisito que fija las versiones de las imágenes de terceros hoy alcanza solo a las que el entorno declara; se extiende a las imágenes base desde las que se construyen los servicios propios, que son igual de capaces de cambiar en silencio bajo la forma que construye desde el código fuente.

## Impact

Integración continua: `.github/workflows/release.yml`, nuevo y único workflow del repositorio. Requiere permisos de escritura sobre contenidos y paquetes, un secreto con la credencial de la API de despliegue y una variable con el identificador del proyecto desplegado.

Construcción: `backend/Dockerfile` y `frontend/Dockerfile` fijan la versión de su imagen base. No cambia nada más de su contenido.

Entorno: `compose.yaml` no se modifica. Sigue apuntando a la etiqueta móvil de los cuatro servicios, que es lo que el pipeline mantiene al día.

Registro de imágenes: los cuatro paquetes se crean en la primera corrida. Como el repositorio es público y el pipeline publica con la credencial del propio workflow, quedan públicos sin configuración adicional.

Primer release: la versión declarada hoy es `0.1.0` y no hay ningún tag, así que la primera corrida construye los cuatro servicios, mueve la etiqueta móvil y crea `0.1.0`. No hace falta modificar el archivo de versión para que eso ocurra.
