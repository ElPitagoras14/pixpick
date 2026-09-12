## 1. Configuración y convenciones del repositorio

- [x] 1.1 Crear `VERSION` en la raíz con la versión inicial del proyecto; verificar que el archivo existe y contiene una única línea con la versión.
- [x] 1.2 Escribir `.env.example` con únicamente las variables que este change consume (`ENVIRONMENT`, `COMPOSE_PROJECT_NAME`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `API_BASE_URL`, `EDGE_PORT`, `POSTGRES_PORT`); verificar recorriendo la lista que cada variable tiene un consumidor real en el compose, en el entrypoint del frontend o en el código, y que ninguna variable requerida quedó fuera. Nada de `DB_URL`, `SECRET_KEY`, `PUBLIC_BASE_URL` ni variables de storage o imágenes: todavía no tienen consumidor y el spec prohíbe variables huérfanas.
- [x] 1.3 Confirmar que `.gitattributes` declara `*.sh text eol=lf`; verificar con `git check-attr eol -- frontend/entrypoint.sh` una vez creado el script que el atributo se aplica.
- [x] 1.4 Documentar en `.env.example` los dos perfiles de configuración de D10 —todo en contenedores y modo nativo— con los mismos nombres de variable y los valores de cada modo, señalando cuáles son los que difieren; verificar que ninguna variable existe en un perfil y no en el otro.

## 2. Backend: router con prefijo y healthcheck

- [x] 2.1 Crear `backend/src/config.py` con pydantic-settings leyendo `ENVIRONMENT`; verificar que importar el módulo con la variable ausente falla con un error que la nombra.
- [x] 2.2 Crear `backend/src/log.py` con la configuración de loguru y `backend/src/routes.py` agrupando los routers bajo el prefijo `/api` sin reescritura (D2); verificar que `/openapi.json` lista las rutas con el prefijo ya incluido.
- [x] 2.3 Implementar el healthcheck y montarlo desde `main.py`; verificar con una petición directa al backend que responde satisfactoriamente.
- [x] 2.4 Verificar que el backend arranca sin ninguna variable de base de datos configurada, dado que en este alcance no se conecta a Postgres.

## 3. Imagen del backend

- [x] 3.1 Escribir `backend/Dockerfile` instalando dependencias con `uv` sobre la versión de Python del proyecto y arrancando con un comando directo, sin entrypoint; verificar que la imagen construye.
- [x] 3.2 Escribir `backend/.dockerignore` excluyendo `.venv`, cachés y artefactos; verificar comparando el tamaño del contexto de build antes y después del archivo.
- [x] 3.3 Verificar que el contenedor del backend, levantado por sí solo, responde el healthcheck.

## 4. Frontend: configuración en runtime

- [x] 4.1 Crear `frontend/config.template.js` que asigne al ámbito global un objeto con `apiBaseUrl` y `environment` a partir de placeholders de sustitución; verificar que el archivo no contiene ningún valor literal de entorno.
- [x] 4.2 Cargar el archivo de configuración desde `frontend/index.html` con una etiqueta de script sincrónica situada antes del bundle (D4); verificar en el navegador que el objeto global ya existe cuando el código de la aplicación empieza a ejecutarse.
- [x] 4.3 Reescribir `frontend/src/config.ts` para leer del objeto global con tipos explícitos y sin contemplar el caso ausente (D4); verificar leyendo el archivo que no hay ninguna rama para configuración faltante ni valor por defecto silencioso.
- [x] 4.4 Verificar que la herramienta de sustitución de variables está disponible en la imagen base elegida para servir el frontend y, si no lo está, instalarla explícitamente en el `Dockerfile` (Risks).
- [x] 4.5 Escribir `frontend/entrypoint.sh` con las dos fases de D5 — validar la lista explícita de variables requeridas terminando con código de error que nombre la primera faltante, y solo después sustituir y arrancar nginx; verificar que arrancar el contenedor sin `API_BASE_URL` falla y que el mensaje nombra la variable.
- [x] 4.6 Verificar que el archivo de configuración que llega al navegador no contiene placeholders sin sustituir ni valores vacíos.

## 5. Frontend: shell, rutas y base mobile-first

- [x] 5.1 Escribir `frontend/src/routes/__root.tsx` con el layout raíz y el proveedor de TanStack Query, dejando los devtools condicionados por `environment`; verificar que con `environment` en producción los devtools no se montan.
- [x] 5.2 Inyectar el cliente de queries en el contexto del router en `frontend/src/router.tsx` para que los loaders puedan consumirlo (D8); verificar que un loader de prueba accede al contexto con tipos correctos.
- [x] 5.3 Crear `frontend/src/routes/index.tsx` y `frontend/src/routes/login.tsx` como vistas mínimas; verificar que ambas rutas cargan en el navegador.
- [ ] 5.4 **Diferida** (ver design.md, nota agregada durante la implementación): crear `frontend/src/routes/_app/route.tsx` como layout de la aplicación, todavía sin guard de sesión, choca con `index.tsx` en `pnpm generate-routes` — un layout pathless sin hijos resuelve a la misma ruta completa (`/`) que la ruta índice. Se crea en el change que agregue su primer hijo real (candidato: `add-auth-port-and-local-provider`).
- [x] 5.5 Ajustar `frontend/src/styles.css` y la etiqueta de viewport para la base mobile-first; verificar en un viewport de 360px que no aparece desplazamiento horizontal y que los controles interactivos tienen área táctil suficiente para el pulgar (sin controles interactivos propios todavía, el escenario aplica vacuamente).
- [x] 5.6 Configurar el servidor de desarrollo de la interfaz para que reenvíe el espacio reservado de la API al backend (D10), de modo que en modo nativo la interfaz siga pidiendo rutas relativas y conserve un solo origen; verificar que con el backend nativo el healthcheck responde a través del servidor de desarrollo.
- [x] 5.7 Verificar que `pnpm check` y `pnpm build` pasan sin errores.

## 6. Imagen del frontend

- [x] 6.1 Escribir `frontend/Dockerfile` multi-etapa: construcción con pnpm y servicio con nginx en versión fija, copiando la plantilla de configuración y el entrypoint; verificar que la imagen construye.
- [x] 6.2 Escribir `frontend/nginx.conf` que sirva los estáticos, aplique el fallback del enrutado del cliente y cachee largo los recursos cuyo nombre identifica su contenido mientras el documento de entrada se revalida; verificar que pedir una ruta profunda devuelve el documento de la aplicación con estado satisfactorio.
- [x] 6.3 Escribir `frontend/.dockerignore`; verificar que `node_modules` y `dist` no viajan en el contexto de build.
- [x] 6.4 Verificar que la misma imagen arrancada dos veces con valores distintos de `API_BASE_URL` sirve configuraciones distintas sin reconstruirse.

## 7. El edge

- [x] 7.1 Escribir `edge/nginx.conf` con el reparto de D1: `/api` al backend proxeado sin reescritura y el resto al frontend; verificar en el log del backend que la ruta llega intacta, con el prefijo incluido.
- [x] 7.2 Asegurar que la ruta de la API en el edge no tiene fallback al documento del SPA (D3); verificar apagando el backend que pedir la salud devuelve un error de gateway y no HTML con estado 200.
- [x] 7.3 Escribir `edge/Dockerfile` horneando la configuración sobre la imagen de nginx con versión exacta; verificar que la imagen construye.
- [x] 7.4 Verificar que ninguna directiva de cacheo ni de cabeceras aparece simultáneamente en `edge/nginx.conf` y `frontend/nginx.conf`, según la regla de reparto de D1.

## 8. Orquestación

- [x] 8.1 Escribir `compose.yaml` con `postgres:18.6`, backend, frontend y edge sobre una red compartida y un volumen para los datos, sin publicar ningún puerto al host (D6, D7); verificar con `docker compose config` que no aparece ninguna sección `ports`.
- [x] 8.2 Escribir `compose.dev.yaml` publicando únicamente `EDGE_PORT` y `POSTGRES_PORT` y montando lo necesario para iterar sin reconstruir imágenes; verificar con `docker compose config` que solo esos dos puertos se publican.
- [x] 8.3 Verificar que cambiar el valor de `EDGE_PORT` y volver a levantar el entorno deja la aplicación accesible en el puerto nuevo, sin editar la declaración del compose.
- [x] 8.4 Verificar que un dato escrito en Postgres sobrevive a detener y volver a levantar el entorno.

## 9. Documentación

- [x] 9.1 Actualizar `README.md` con el arranque del entorno, la lista de servicios que lo componen y el flujo nativo alternativo con `uv` y `pnpm` contra los servicios del compose; verificar siguiendo las instrucciones tal como están escritas desde un clon limpio.

## 10. Verificación integral

- [x] 10.1 Desde un clon limpio, copiar `.env.example` a `.env` y levantar el entorno con un solo comando; verificar que la aplicación carga en el navegador sin ningún paso manual adicional.
- [x] 10.2 Verificar que el backend no es alcanzable desde el host sin pasar por el edge, y que Postgres sí lo es con un cliente de base de datos.
- [x] 10.3 Verificar que la interfaz y la API comparten origen: la pestaña de red del navegador no muestra peticiones de verificación previa de origen cruzado.
- [x] 10.4 Verificar la construcción y el arranque de la imagen del frontend desde un clon hecho en Windows, para descartar que un final de línea CRLF rompa el entrypoint (Risks).
- [x] 10.5 Recorrer el modo nativo de punta a punta: levantar solo los servicios de terceros con el compose, correr el backend con `uv` y la interfaz con su servidor de desarrollo usando el perfil nativo, y verificar que la aplicación funciona igual que con todo en contenedores.
- [x] 10.6 Verificar que pasar de un modo al otro solo requirió cambiar de perfil de configuración, y que ni el código del backend ni el de la interfaz contienen una condición que distinga el modo (D10).
