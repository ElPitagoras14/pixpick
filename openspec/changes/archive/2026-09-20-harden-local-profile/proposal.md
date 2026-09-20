## Why

El proyecto va a publicarse como repositorio público y a desplegarse con el perfil local (MinIO e imgproxy) alcanzable desde internet. Una auditoría sobre esa hipótesis encontró que la instancia no resiste a un actor hostil ni a uno simplemente torpe: el tamaño declarado de una foto no tiene cota inferior, así que un valor negativo deja las tres cuotas en negativo para todas las cuentas a la vez y anula la defensa que `instance-quota` acaba de introducir; la confirmación de un lote no tiene cota superior, así que una sola petición dispara miles de consultas al almacenamiento; no existe rate limiting en ninguna capa; el agotamiento del pool de conexiones se presenta como un fallo interno en vez de como una señal de que hay que reintentar más tarde; y la reclamación de subidas abandonadas es un comando manual que nada ejecuta, de modo que los bytes que nadie confirmó ocupan disco sin que ninguna cuota los vea.

El perfil local agrava dos de esos puntos y resuelve un tercero. Los agrava porque el disco que se llena es el mismo donde viven la base y la caché, así que quedarse sin espacio no es un gasto sino una caída total; y porque el transformador que consume CPU es propio, no de un tercero. Lo resuelve porque, al entrar todo el tráfico por el punto de entrada, existe por primera vez un lugar donde acotar el tamaño de lo que el navegador escribe -- algo que con un almacenamiento externo era imposible, porque el navegador escribe directo contra el proveedor y no hay dónde interponerse.

## What Changes

- El tamaño declarado de una foto pasa a tener cota inferior además de superior, respaldada por una restricción en el esquema y no solo por la validación de la aplicación. Las dimensiones declaradas se acotan igual.
- La confirmación de un lote adquiere el mismo techo que ya tiene la concesión, para que una petición no pueda multiplicar consultas al almacenamiento sin límite.
- El punto de entrada pasa a ser el único origen expuesto también para el almacenamiento local, y acota el tamaño del cuerpo que acepta. Esa cota es la primera que se aplica sobre lo que efectivamente se escribe, y no sobre lo que el cliente dijo que iba a escribir. **BREAKING**: `local-environment` admite hoy que un servicio de terceros contra el que el navegador escribe directamente viva en su propio origen; esta excepción se restringe.
- Aparece rate limiting por cliente, aplicado antes de que una petición tome una conexión a la base, y con el punto de entrada capaz de identificar al cliente real en vez de al proxy que tiene delante.
- Una petición rechazada por carga se vuelve distinguible de un error de validación o de un fallo interno, y lleva una indicación de cuándo reintentar.
- El acceso a la base adquiere techos de tiempo por sentencia y por espera de lock, y la conexión se toma recién después de autorizar la petición.
- La reclamación de subidas abandonadas pasa de comando manual a tarea periódica, y la eliminación de varios objetos se reparte en operaciones del tamaño que el protocolo admite, para que un lote grande deje de abortar sin limpiar nada.
- El transformador declara qué está dispuesto a procesar, y cada servicio declara cuánta memoria y CPU puede tomar.
- El arranque se niega a continuar si la combinación de proveedores seleccionada es incoherente.
- Todo umbral nuevo se declara como variable de entorno, siguiendo lo que ya hacen los límites de cuota.

Queda explícitamente fuera de alcance el endurecimiento del perfil cloud: la firma de ImageKit, la exigencia de firma en su panel y la expiración de las direcciones de variante siguen como deuda conocida. La consecuencia es que el par cloud no es un plan de contingencia confiable hasta que se lo atienda, y el guard de coherencia que sí entra en este change hace que esa limitación falle de forma visible en vez de silenciosa.

Queda también fuera de alcance acotar las credenciales del almacenamiento por consumidor: el backend y el transformador siguen usando la credencial administrativa de MinIO, como hoy. Una redacción anterior de este proposal lo incluía; se descartó porque el costo de un servicio de aprovisionamiento de credenciales nuevo no se justificaba frente al resto de este change. Queda como deuda conocida, en la misma categoría que el perfil cloud.

## Capabilities

### New Capabilities

- `request-throttling`: gobierna cuánta carga admite la instancia por cliente y qué hace cuando no puede admitir más -- el límite de peticiones, el punto del ciclo en que se aplica, la identificación del cliente detrás de un proxy, y la forma en que una petición rechazada por carga se distingue de una rechazada por su contenido.

### Modified Capabilities

- `object-storage`: el tamaño declarado pasa a exigirse positivo y no solo por debajo del máximo; la eliminación de varios objetos pasa a repartirse en operaciones del tamaño que el protocolo admite; y se incorpora que, cuando el navegador escribe a través del punto de entrada, el tamaño de lo que escribe se acota ahí.
- `photo-upload`: la confirmación de un lote adquiere un techo de cantidad; el tamaño declarado se exige positivo; y la reclamación de subidas abandonadas pasa de poder ejecutarse a deber ejecutarse periódicamente.
- `local-environment`: se restringe la excepción que permitía a un servicio de terceros vivir en su propio origen, y cada servicio pasa a declarar su techo de memoria y su política de reinicio.
- `image-delivery`: la dirección de una variante pasa a resolverse contra el proveedor de almacenamiento activo y no contra uno fijo, con arranque fallido ante una combinación incoherente; y el transformador pasa a declarar qué está dispuesto a procesar y desde dónde.
- `database-access`: se incorporan techos de tiempo por sentencia y por espera de lock, y la conexión pasa a tomarse después de autorizar la petición y no antes.
- `album-management`: el título y la descripción adquieren longitud máxima.
- `api-conventions`: se incorpora que una petición rechazada por falta de capacidad se distingue de las demás y lleva una indicación de reintento.

## Impact

Backend: `packages/photos` (router y service), `packages/albums`, `storage/adapters/minio.py`, `storage/port.py`, `images/adapters/imgproxy.py`, `images/factory.py`, `database/client.py`, `database/dependencies.py`, `database/utils.py`, `packages/auth/dependencies.py`, `handlers.py`, `responses.py`, `maintenance/reconcile.py`. Migración nueva para las restricciones de esquema.

Entorno: `nginx/nginx.conf` (espacio reservado para el almacenamiento, cota de cuerpo, identificación del cliente real, límites de tasa), `compose.yaml` y `compose.dev.yaml` (límites de recursos, variables del transformador, servicio de reclamación periódica), `.env.example` y `README.md`.

Frontend: sin cambios de comportamiento. La cola de subida sigue aplicando la concesión tal como la recibe; lo que cambia es la dirección que esa concesión contiene.

Compatibilidad: un despliegue existente del perfil local recibe una dirección nueva para el almacenamiento. Las concesiones emitidas antes del cambio dejan de ser válidas al vencer, sin migración de datos.
