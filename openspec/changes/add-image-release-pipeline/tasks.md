## 1. Fijar las imágenes base

- [x] 1.1 Fijar `python:3.13-slim` a su versión de parche vigente en `backend/Dockerfile` y verificar que `docker build backend/` completa
- [x] 1.2 Fijar `node:22-slim` a su versión de parche vigente en `frontend/Dockerfile` y verificar que `docker build frontend/` completa y que la etapa final recibe `dist`
- [x] 1.3 Verificar que ningún `FROM` ni `COPY --from` del repositorio queda apuntando a una etiqueta móvil, recorriendo los cuatro Dockerfiles

## 2. Detección del release

- [x] 2.1 Crear `.github/workflows/release.yml` con disparo en push a `main`, permisos de escritura sobre contenidos y paquetes, concurrencia sin cancelación en curso, y el prefijo de imagen como variable de entorno; verificar que `actionlint` no reporta errores
- [x] 2.2 Implementar el job de detección que lee `VERSION`, obtiene el tag semver más alto y decide si hay release comparando con `sort -V`; verificar extrayendo el script a un shell local y cubriendo cinco casos: sin tags, versión mayor, igual, menor, y `0.1.10` contra `0.1.9`
- [x] 2.3 Verificar que el checkout usa `fetch-depth: 0`, comprobando que sin esa opción la detección no ve ningún tag y con ella los ve todos

## 3. Publicación de imágenes

- [x] 3.1 Declarar la matriz de los cuatro servicios con su directorio, su pathspec de exclusión y `fail-fast: true`; verificar que cada entrada nombra el contexto de build que le corresponde
- [x] 3.2 Implementar la decisión entre construir y reutilizar por servicio; verificar cada pathspec con `git diff --quiet` sobre rangos reales del historial, comprobando que un commit que solo toca `backend/tests` no marca al backend como cambiado y que uno que toca `backend/src` sí
- [x] 3.3 Verificar que la pathspec se expande sin comillas y que la exclusión efectivamente excluye, comprobando que `git diff` no interpreta el patrón como un path que empieza con comilla
- [x] 3.4 Configurar QEMU y buildx, y construir `linux/amd64,linux/arm64` con el cache de registro en backend y frontend; verificar que la imagen resultante declara las dos arquitecturas con `imagetools inspect`
- [x] 3.5 Implementar la reutilización con `imagetools create` para el servicio sin cambios, y la caída a construir cuando no exista imagen del release anterior; verificar que el nombre nuevo resuelve al mismo digest que el anterior

## 4. Etiqueta móvil, registro y despliegue

- [x] 4.1 Implementar el job que mueve `latest` en los cuatro servicios, dependiente de la matriz completa; verificar que no arranca si una leg falla
- [x] 4.2 Implementar el job que crea el tag y registra el release con notas generadas, posterior al movimiento de la etiqueta móvil; verificar que el nombre del tag es idéntico al de las etiquetas de imagen
- [x] 4.3 Implementar el job de despliegue contra la API de Dokploy, con `continue-on-error`; verificar que un fallo suyo deja el release marcado como exitoso

## 5. Puesta en marcha

- [ ] 5.1 Crear el proyecto en Dokploy, cargar `DOKPLOY_API_KEY` como secreto del repositorio y `DOKPLOY_COMPOSE_ID` como variable; verificar que ambos figuran en la configuración del repositorio antes de integrar
- [ ] 5.2 Integrar y verificar la primera corrida: los cuatro paquetes existen con las etiquetas `0.1.0` y `latest`, el tag `0.1.0` está en el repositorio, y el despliegue recibió la llamada
- [ ] 5.3 Verificar que los cuatro paquetes son públicos con una consulta anónima al registro, sin credenciales

## 6. Verificación del comportamiento de reutilización

- [ ] 6.1 En el primer release posterior que toque un solo servicio, verificar que los otros tres publicaron su etiqueta de versión con el mismo digest que tenían en la versión anterior, comparando con `imagetools inspect`
- [ ] 6.2 Verificar que una integración que no toca `VERSION` no publica imágenes ni crea tag, comprobando que la corrida termina sin ejecutar la matriz
