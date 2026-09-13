## Why

Este change es el momento de la verdad del puerto de identidad. El proyecto decidió meter la identidad detrás de un puerto desde el primer change de autenticación, con un argumento explícito: agregar Google sería escribir un adapter y cambiar una variable, sin tocar el flujo de sesión ni los endpoints ni la interfaz. Acá ese argumento se cobra o se desmiente, y la medida es verificable — si al implementarlo aparece la necesidad de modificar algo fuera del adapter y su configuración, el puerto estaba mal diseñado y conviene decirlo.

Y el producto lo necesita. El link de un álbum se comparte con gente que no va a crear una cuenta en nada: entrar con la cuenta que ya tiene es la diferencia entre que califique el álbum y que cierre la pestaña.

## What Changes

- **Un adapter del proveedor de identidad** que implementa las dos operaciones que el puerto declara: producir la dirección de autorización y canjear el código por una identidad.
- **El intercambio del código ocurre directamente contra el proveedor**, servidor a servidor, autenticándose con las credenciales de la aplicación. La identidad llega en ese intercambio y no pasa por el navegador.
- **Los ámbitos que se piden son los mínimos**: identidad y correo. Nada de acceso a datos del proveedor más allá de quién es la persona.
- **Las credenciales viven en la configuración del entorno**, y su ausencia impide el arranque cuando este proveedor está activo, en vez de manifestarse como un login que falla para todo el mundo.
- **El adapter local sigue existiendo y sigue siendo el de desarrollo.** La variable que elige el proveedor sigue eligiendo uno por entorno, así que desarrollar y probar no pasa a depender de credenciales de un tercero ni de una pantalla de consentimiento.
- **Documentación de la configuración externa**: qué hay que crear en la consola del proveedor, qué dirección de retorno declarar y cómo se deriva de la dirección pública del sitio.

### Fuera de alcance

- **Verificación criptográfica del token de identidad.** El proveedor documenta explícitamente que, cuando el token se recibe en el intercambio directo por un canal cifrado y autenticado con el secreto de la aplicación, no hace falta validar su firma: el canal es la garantía. La validación sí sería obligatoria si ese token se pasara a otros componentes, y en este diseño no se pasa a ninguno — lo consume el mismo proceso que lo obtuvo.
- Vincular cuentas entre proveedores, que sigue siendo un no-goal del proyecto.
- Otros proveedores de identidad.
- Pedir permisos adicionales o consumir cualquier dato del proveedor que no sea la identidad.
- **Cualquier cambio en la sesión, los endpoints, la interfaz o el esquema.** No es solo que no estén en el alcance: si alguno hiciera falta, es un hallazgo sobre el diseño del puerto y corresponde tratarlo como tal antes de seguir.

## Capabilities

### New Capabilities

Ninguna. Este change no agrega una forma de comportamiento nueva: agrega una implementación de una que ya está especificada.

### Modified Capabilities

- `identity-provider`: se le agregan dos requirements que hasta ahora no tenían razón de existir, porque el único proveedor era local y no hablaba con nadie. El primero es sobre la confianza en el canal por el que llega la identidad: qué garantiza que lo que el sistema recibe viene efectivamente del proveedor. El segundo es sobre la configuración externa: un proveedor que requiere credenciales tiene que impedir el arranque si no las tiene, del mismo modo que el adapter local impide el arranque fuera de desarrollo.

Esa capability se materializa al archivar `add-auth-port-and-local-provider`, así que este delta asume que los changes se archivan en el orden en que fueron planificados.

## Impact

**Archivos nuevos**

- `backend/src/identity/adapters/google.py`
- Pruebas del adapter: construcción de la dirección de autorización, forma de la identidad que produce el canje, y comportamiento ante un rechazo del proveedor

**Archivos modificados**

- `backend/src/identity/factory.py` y `config.py`: registro del proveedor y sus credenciales.
- `.env.example`: las credenciales de la aplicación, en los dos perfiles de configuración.
- `README.md`: cómo obtener las credenciales, qué dirección de retorno declarar en la consola del proveedor, y por qué en desarrollo conviene seguir usando el proveedor local.

**Dependencias**

**Ninguna nueva.** El intercambio del código es una petición HTTP servidor a servidor, y el cliente que hace falta ya viene con las dependencias del backend. Al no verificar firmas tampoco hace falta una biblioteca de criptografía ni obtener y refrescar claves públicas rotativas, que era la única complejidad que este change parecía traer.

**Configuración fuera del repositorio**

Es el primer change del proyecto que necesita configuración en un sistema que no controlamos: la aplicación registrada en la consola del proveedor, con su dirección de retorno declarada. Esa dirección tiene que coincidir exactamente con la que el sistema construye a partir de la dirección pública configurada, y no coincidir produce un error que reporta el proveedor y que la aplicación no puede anticipar.

**Precedencia**

Depende de `add-auth-port-and-local-provider`, que define el puerto que este change implementa. No depende de ningún otro: los changes de álbumes, compartir y galería no participan.
