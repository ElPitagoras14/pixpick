## Why

Todo el dominio que viene necesita saber quién está pidiendo. Un álbum tiene dueño, una calificación pertenece a alguien, y el link compartido concede acceso a una persona identificada, no a cualquiera que tenga la URL. La identidad es entonces la primera pieza de dominio y condiciona la forma de todas las siguientes.

La decisión de fondo es que la identidad entre por un puerto desde el día uno, aunque el único proveedor de este change sea local. El proveedor real va a ser Google, pero empezar por él obligaría a tener credenciales de OAuth configuradas para poder desarrollar, y haría que cada verificación manual pase por la pantalla de consentimiento de un tercero. El adapter local recorre exactamente el mismo ciclo —una URL de autorización a la que se redirige y un código que se canjea por una identidad—, así que el change que agregue Google es un archivo de adapter más configuración, y no una reescritura del flujo de sesión.

## What Changes

- **`AuthPort` con selección de proveedor por variable de entorno**: la aplicación consume el puerto y no sabe cuál es el proveedor. Un valor desconocido en la variable falla en el arranque, no en el primer intento de login.
- **Adapter local**: una pantalla de desarrollo sin contraseña que emite el código, atravesando el mismo ciclo de redirección y canje que atravesará Google. Es el proveedor de la fase local y el que permitirá verificar el resto del proyecto sin depender de un tercero.
- **Tabla de usuarios** con la identidad externa —proveedor más sujeto— como clave única, más el correo, el nombre y el avatar que el proveedor entrega.
- **Tabla de sesiones** que guarda el hash del token de sesión y nunca el token, de modo que un volcado de la base no entregue sesiones utilizables.
- **Sesión en cookie httpOnly** con su ciclo de vida completo: se establece al completar el login, se valida en cada petición, y el cierre de sesión elimina la fila y no solo la cookie.
- **Endpoints de inicio de sesión, retorno del proveedor, cierre de sesión e identidad actual**, bajo el prefijo de la API.
- **El destino de retorno viaja en el estado del ciclo de autorización**, para que abrir un link compartido sin sesión termine en el álbum y no en la portada. El destino se valida como una ruta del propio sitio antes de usarse.
- **Convenciones de respuesta de la API**: la forma de los cuerpos y la correspondencia entre situaciones de error y códigos de estado, que a partir de acá gobiernan todos los endpoints del proyecto.
- **Constructores compartidos de datos de prueba**, que con las primeras entidades ya tienen algo que construir.
- **Frontend**: la vista de inicio de sesión, el contexto de sesión, el guard del layout autenticado, y el tratamiento de la respuesta no autorizada en el cliente HTTP.

### Fuera de alcance

- Google como proveedor: es el change de la fase cloud y no cambia nada de lo que este establece.
- Roles y permisos. No hay más de un tipo de usuario: que alguien sea dueño de un álbum se determina por pertenencia, no por un rol asignado.
- Credenciales propias del sistema, y con ellas registro, contraseñas, recuperación y verificación de correo. La identidad siempre viene de un proveedor.
- Álbumes, fotos, compartir, swipe, galería y estadísticas, junto con los puertos de storage e imágenes.
- Del proyecto en general: comentarios en fotos, notificaciones por email, coautores de álbum, PWA/offline y pruebas end-to-end.

## Capabilities

### New Capabilities

- `identity-provider`: cómo el sistema obtiene la identidad de una persona desde un proveedor externo, qué se le exige a un proveedor para ser intercambiable con otro, y cómo se elige cuál está activo.
- `session-management`: cómo se establece, se transporta, se valida y se termina una sesión, y cómo se representa el usuario autenticado ante el resto del sistema.
- `api-conventions`: qué forma tienen los cuerpos que la API devuelve y qué código de estado corresponde a cada situación, incluida la deliberada indistinción entre "no existe" y "no tenés acceso".

### Modified Capabilities

- `backend-testing`: incorpora el requirement de que los datos de prueba se construyan con constructores compartidos. Quedó fuera de `add-backend-data-layer` porque allí no existía ninguna entidad que construir, y este change trae las primeras. El delta asume que los changes se archivan en el orden en que fueron planificados.

## Impact

**Archivos nuevos**

- `dbmate/migrations/0002_create_users_and_sessions.sql`
- `backend/src/identity/port.py`, `factory.py`, `config.py`, `adapters/local.py`
- `backend/src/models.py` y `backend/src/responses.py`: base compartida de los modelos de respuesta y el envelope de la API
- `backend/src/packages/auth/router.py`, `service.py`, `repository.py`, `dependencies.py`, `schemas.py`, `responses.py`, `config.py`
- `backend/tests/factories.py` y las pruebas de identidad y sesión
- `frontend/src/auth.tsx`, `frontend/src/features/auth/api.ts` y su vista de inicio de sesión

**Archivos modificados**

- `dbmate/schema.sql`: regenerado con las dos tablas nuevas.
- `backend/src/routes.py`: montaje del router de autenticación.
- `backend/src/handlers.py`: manejo de los errores que este change introduce.
- `.env.example`: proveedor de identidad activo y URL pública del sitio.
- `frontend/src/api.ts`: envío de credenciales y tratamiento del no autorizado.
- `frontend/src/routes/login.tsx` y `frontend/src/routes/_app/route.tsx`: la vista deja de ser un placeholder y el layout gana su guard.
- `README.md`: cómo entrar con el proveedor local.

**Dependencias**

Ninguna nueva. El canje del código en el adapter local no sale de la aplicación, y el cliente HTTP que necesitará el adapter de Google ya viene con las dependencias del backend.

Tampoco hace falta un secreto de firma: el token de sesión es opaco y aleatorio, y la defensa del ciclo de autorización compara el estado recibido contra el que viaja en una cookie, sin firmar nada.

**Precedencia**

Depende de `add-backend-data-layer`: necesita las migraciones, la capa de acceso y la suite de pruebas que ese change establece.
