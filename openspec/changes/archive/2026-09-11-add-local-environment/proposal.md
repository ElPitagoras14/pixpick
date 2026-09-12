## Why

pixpick tiene que funcionar íntegramente en local o contra servicios cloud según variables de entorno. Esa simetría no se puede agregar después: depende de que el navegador entre siempre por una única puerta —un edge— porque en modo cloud esa puerta será un CDN. Si el desarrollo local empieza con el SPA hablándole directo al backend en otro puerto, más adelante hay que rehacer el ruteo, el CORS y los supuestos de cacheo, y las diferencias entre local y cloud aparecen recién en producción, que es justo lo que el diseño por puertos intenta evitar.

Hoy el repositorio es un scaffold sin infraestructura declarada: el backend expone un único `main.py`, el frontend una sola ruta, y no hay forma de levantar el proyecto con un comando. Este change establece esa base y nada más, para que los changes siguientes agreguen comportamiento sobre un entorno que ya se levanta y se verifica.

## What Changes

- **Orquestación local**: `compose.yaml` con Postgres 18 y nginx como edge, más `compose.dev.yaml` con los ajustes de desarrollo (puertos publicados al host, recarga).
- **Edge como única puerta**: nginx rutea `/api` al backend y `/` al SPA. Ningún otro servicio publica puerto al host salvo Postgres, que lo hace solo para poder inspeccionarlo en desarrollo.
- **Imágenes de backend y frontend**: un `Dockerfile` por servicio. El frontend además lleva un `entrypoint.sh`, porque es el mecanismo que inyecta la configuración en runtime antes de arrancar su nginx; el backend no lo necesita y arranca con un comando directo.
- **Configuración del SPA en runtime**: el frontend recibe su configuración al arrancar el contenedor, no al construirlo, para que la misma imagen sirva en cualquier entorno sin rebuild.
- **`.env.example` mínimo**: solo las variables que este change necesita, con un bloque explícito de puertos locales. Cada change posterior agrega las suyas.
- **Shell del frontend**: `__root.tsx`, ruta índice y `login.tsx` como placeholder, con tipografía, tema y estructura mobile-first.
- **Healthcheck**: un endpoint que el edge expone y que permite verificar la cadena completa navegador → nginx → backend.
- **Convenciones del repositorio**: archivo `VERSION` en la raíz.

### Fuera de alcance

- **El layout `_app`**: se descarta para este change. TanStack Router calcula la ruta completa de un layout pathless quitándole el segmento con guion bajo, así que un `_app/route.tsx` sin ningún hijo queda con la misma ruta completa (`/`) que `index.tsx`, y `pnpm generate-routes` lo rechaza como conflicto — se verificó tanto en la forma de archivo (`_app.tsx`) como en la de directorio (`_app/route.tsx`). El layout solo deja de chocar cuando tiene al menos un hijo real, así que se crea en el change que agregue su primera ruta protegida (candidato: `add-auth-port-and-local-provider`, que suma el guard de sesión).

Estos puntos quedan explícitamente fuera y pertenecen a changes posteriores o al no-goal del proyecto:

- Autenticación, sesiones y usuarios.
- Migraciones, acceso a datos y pruebas de backend.
- MinIO, imgproxy y el cacheo de imágenes en el edge: se incorporan cuando nazcan sus puertos, para no dejar servicios levantados sin consumidor.
- Adapters cloud (Google OAuth, R2, ImageKit).
- Álbumes, fotos, compartir, swipe, galería y estadísticas.
- Del proyecto en general: comentarios en fotos, notificaciones por email, coautores de álbum, PWA/offline y pruebas end-to-end.

## Capabilities

### New Capabilities

- `local-environment`: cómo se levanta el proyecto completo en una máquina de desarrollo, qué servicios lo componen, por dónde entra el tráfico y qué se expone al host.
- `frontend-delivery`: cómo se construye el SPA y cómo se sirve, incluida la resolución de rutas del lado del cliente.
- `frontend-runtime-config`: cómo el SPA obtiene su configuración sin volver a construirse.

### Modified Capabilities

Ninguna. `openspec/specs/` está vacío: este es el primer change del proyecto.

## Impact

**Archivos nuevos**

- `compose.yaml`, `compose.dev.yaml`, `.env.example`, `VERSION`
- `edge/Dockerfile`, `edge/nginx.conf`
- `backend/Dockerfile`, `backend/.dockerignore`
- `frontend/Dockerfile`, `frontend/.dockerignore`, `frontend/entrypoint.sh`, `frontend/nginx.conf`, `frontend/config.template.js`

**Archivos modificados**

- `backend/src/main.py`: healthcheck y montaje del router bajo el prefijo del edge.
- `frontend/src/routes/`: `__root.tsx`, `index.tsx`, `login.tsx`.
- `frontend/src/config.ts`: lectura de la configuración inyectada en runtime.
- `frontend/index.html`: carga del archivo de configuración.
- `README.md`: instrucciones de arranque del proyecto.

**Dependencias**

- Sin dependencias nuevas de Python ni de npm.
- Imágenes de terceros con versión fijada: `postgres:18` y una imagen `nginx` estable.

**Sistemas afectados**

Ninguno en producción: el proyecto no está desplegado. El único impacto es sobre el flujo de trabajo local, que pasa a requerir Docker para levantar el entorno completo.
