## Context

La instancia corre hoy con `STORAGE_PROVIDER=local` e `IMAGE_PROVIDER=local`: MinIO guarda los originales, imgproxy produce las variantes, y nginx reparte `/api/`, `/images/` y todo lo demás. Delante de nginx hay un proxy de plataforma que termina TLS, y delante del dominio hay una CDN. El backend corre en un único proceso de uvicorn, sin workers, contra un pool de veinte conexiones.

Tres piezas de ese cuadro condicionan todo lo que sigue. La primera es que el navegador escribe los bytes de cada foto directamente contra MinIO con una concesión firmada, sin pasar por la API ni por nginx: la firma cubre el objeto y el tipo de contenido, nunca el tamaño, porque ningún esquema de firma por URL puede expresar un rango de tamaño de forma portable. La segunda es que nginx, tal como está, no distingue un cliente de otro: no declara de qué proxy acepta una dirección reenviada, y uvicorn tampoco, así que ambos ven la dirección del contenedor que tienen delante para todas las peticiones. La tercera es que la limpieza de subidas abandonadas es un comando que nadie ejecuta, y una fila cuyo permiso venció deja de contar en las tres cuotas aunque su objeto siga ocupando disco.

Sobre ese cuadro hay dos asimetrías que no existían mientras el almacenamiento era externo. Como MinIO, Postgres y la caché de variantes comparten disco, llenarlo no encarece nada: apaga la instancia entera. Y como el transformador es propio, el costo de producir una variante es CPU que compite con la base, no una factura de un tercero.

## Goals / Non-Goals

**Goals:**

- Que ninguna petición pueda dejar las cuotas describiendo algo distinto de lo que hay en disco.
- Que exista una cota sobre los bytes que efectivamente se escriben, y no solo sobre los que el cliente declara.
- Que la instancia pueda decir "no puedo ahora, volvé en tanto" en lugar de agotarse en silencio o responder un fallo interno.
- Que una combinación de proveedores que no funciona falle al arrancar y no en la primera imagen.

**Non-Goals:**

- Optimizar la suma del consumo de la instancia. Sigue siendo un recorrido completo bajo un lock global; lo que este change agrega son techos de tiempo y una limpieza que evita que la tabla crezca sin fondo, no un contador materializado.
- Paginar las lecturas. El techo de fotos por álbum acota la respuesta de la galería; el listado de álbumes queda sin techo, y acotarlo -- paginándolo o limitando cuántos álbumes puede tener una cuenta -- es trabajo que ninguna de estas exposiciones exige: inflarlo requiere una cuenta autenticada martillando durante días contra el límite de tasa, y el único listado que se degrada es el suyo.
- Cambiar la forma en que el cliente sube. La cola sigue pidiendo una concesión y aplicándola tal como llega.
- Endurecer el perfil cloud. La firma de ImageKit, la exigencia de firma en su panel y la expiración de las direcciones de variante quedan sin tocar.
- Acotar las credenciales del almacenamiento por consumidor. La redacción original de este design incluía un servicio de inicialización que le daba al backend y al transformador una cuenta de servicio propia cada uno, con la administrativa quedando solo en MinIO; se descartó durante la implementación porque el costo de un servicio de aprovisionamiento nuevo no se justificaba frente al resto de este change. El backend y el transformador siguen usando la credencial administrativa de MinIO, como hoy. Queda como deuda conocida, en la misma categoría que el endurecimiento del perfil cloud.

## Decisions

### D1: El almacenamiento se alcanza por un hostname propio que atiende el punto de entrada

La concesión se firma con SigV4, que cubre el método, la ruta, la query y el Host. El navegador pide exactamente la URL que recibió, y el que verifica es el almacenamiento, sin nadie en el medio que pueda recomponer la cadena firmada. De ahí sale toda la restricción: lo que llegue al almacenamiento tiene que coincidir con lo que el backend firmó, y el primer segmento de la ruta tiene que seguir siendo el bucket.

Un hostname propio cumple las dos cosas sin esfuerzo: la ruta viaja intacta y solo hace falta reenviar el Host original, que ya es lo que hacen los tres bloques existentes. Es además la práctica establecida -- `cdn.`, `files.`, `uploads.` son el patrón habitual -- y la documentación de MinIO para desplegarlo detrás de un reverse proxy pide exactamente eso: preservar el Host, precisamente porque la firma se valida contra el que recibe. Un paso intermedio de esta decisión probó un puerto propio en lugar de un hostname, específicamente para el caso de una IP privada sin dominio (uso personal o por VPN); se revirtió porque un puerto propio le exige a quien despliega con un proxy de plataforma (Dokploy u otro) asignarle un puerto distinto al mismo contenedor, cuando lo habitual en esas plataformas es asignar varios dominios a un mismo puerto -- el hostname es el mecanismo que ya esperan. Lo que cierra el caso sin dominio no es el puerto: es un hostname que resuelve solo, sin DNS propio que correr -- `storage.localhost` en desarrollo, y un servicio como sslip.io/nip.io (`storage.192-168-1-50.sslip.io` para 192.168.1.50) cuando el dominio es una IP privada o de VPN. Los dos casos terminan usando el mismo mecanismo que un despliegue con dominio real, y `STORAGE_PUBLIC_URL` es lo único que cambia entre ellos.

Tres razones lo eligen por encima de las alternativas que también funcionan. Aísla la cookie: en un origen compartido cada escritura llevaría la cookie de sesión a un servicio que no la necesita y que podría registrarla. Acompaña la dirección del ecosistema: el direccionamiento por ruta está deprecado en S3 en favor del bucket en el hostname. Y conserva la paridad con el modo cloud en lugar de romperla, que es lo que el requisito original buscaba proteger: en cloud el almacenamiento vive en otro origen y la escritura negocia origen cruzado, de modo que un modo local que no lo ejercite dejaría ese camino probándose únicamente en producción.

Conviene decir por qué `/images/` sí puede vivir en un prefijo: ahí la firma la calcula imgproxy sobre la ruta que recibe *después* del rewrite, y el adapter firma exactamente esa ruta y le antepone el prefijo recién al final. Es una coordinación deliberada entre las dos puntas, posible porque el que firma y el que verifica son el mismo par bajo nuestro control.

Lo que no cambia respecto de hoy es que el almacenamiento tiene su propio origen; lo que cambia es que ese origen lo atiende el punto de entrada en lugar de publicarse el servicio. Nada más que el punto de entrada queda publicado, y lo alcanzable de MinIO se reduce al espacio de objetos de un bucket: su API de administración, su consola y cualquier otro bucket quedan fuera porque no hay ruta que los alcance.

**Alternativas descartadas:**

- *El nombre del bucket como prefijo de ruta en el origen de la aplicación.* Funciona —la ruta firmada ya empieza por el bucket, así que nginx la reenvía sin tocarla— y evita la negociación de origen cruzado. Se descarta porque evitarla es un defecto disfrazado: en cloud esa negociación existe igual, de modo que suprimirla en local deja el camino sin ejercitar. Además ata el espacio de rutas públicas al nombre del bucket y manda la cookie de sesión en cada escritura.
- *Un prefijo de ruta genérico.* No funciona de ninguna de las dos formas: quitándolo, el almacenamiento recalcula sobre una ruta distinta de la firmada y rechaza; conservándolo, lee el prefijo como nombre de bucket.
- *Concesión por POST con policy en lugar de PUT.* Es la respuesta canónica de S3 para acotar el tamaño, porque la policy firmada admite `content-length-range` y la impone el propio almacenamiento. Se descarta por dos motivos: el proveedor externo no implementa POST prefirmado, así que la concesión tendría forma distinta según el proveedor; y con la cota puesta en el punto de entrada no agrega nada que no esté cubierto.
- *Que el punto de entrada firme por su cuenta.* Dejaría el almacenamiento completamente inalcanzable desde afuera, pero exige implementar SigV4 dentro de nginx, una subpetición de autorización por subida, y solo existiría en el modo local.
- *Subir a través de la API.* Es la que más complejidad elimina —sin prefirma, sin origen cruzado, sin dos direcciones, sin concesión y confirmación, sin objetos huérfanos, y con la cuota exacta en lugar de declarada— pero contradice el requisito más cargado de `object-storage`, que pide que ningún byte de imagen atraviese la aplicación, y pondría hasta veinte mebibytes por foto y tres subidas concurrentes por cliente a través de un backend de un solo proceso. Queda anotada como no elegida y no como mala: si alguna vez el perfil cloud deja de importar, es un rediseño que simplifica el sistema entero.

### D2: La cota del cuerpo en el punto de entrada se deriva del mismo máximo que valida la concesión

`client_max_body_size` pasa a existir y a componerse del mismo valor que `MAX_FILE_SIZE`, más el margen que el protocolo agrega sobre el contenido. Dos números distintos para la misma cosa se separan: uno se cambia y el otro queda, y el síntoma sería que las subidas fallan con un error de nginx en lugar de con la validación de la aplicación.

Esto convierte una validación que solo podía ser declarativa en una que se impone. La aplicación sigue validando lo declarado antes de conceder y verificando lo real al confirmar; el punto de entrada agrega la tercera, que es la única que actúa mientras los bytes viajan.

Se descarta `proxy_request_buffering on` (el valor por omisión): obligaría a nginx a escribir cada subida entera a disco antes de reenviarla, con la cola del cliente subiendo de a tres en paralelo.

### D3: El rate limit vive en el punto de entrada, con la CDN como capa exterior

nginx está en el camino de toda petición de producción, ve la dirección real del cliente una vez resuelto D4, y rechaza antes de que la petición llegue al backend -- o sea antes de cualquier recurso escaso, sin que haya que cuidar en qué orden se resuelven las dependencias. Un techo general sobre el espacio de la API y uno más estricto sobre la concesión de subidas, que es la operación cara, se expresan con dos zonas y un bloque por operación. La CDN queda por fuera como configuración, no como código.

Se descarta un middleware en el backend. Lo único que podría aportar por encima de nginx es limitar por cuenta en vez de por dirección, y eso exige resolver la sesión, que exige consultar la base: exactamente el recurso que el límite existe para proteger. Sin eso limitaría por dirección igual que nginx, en un segundo lugar que mantener y afinar. El otro argumento a su favor -- que nginx no devuelve el cuerpo de error común de la API -- se resuelve con una página de error propia.

Los umbrales siguen siendo variables de entorno: la imagen parte de la oficial de nginx, que sustituye plantillas al arrancar, y el proyecto ya tiene ese patrón en el entrypoint de la interfaz, con validación explícita de lo requerido antes de sustituir. La sustitución SHALL restringirse a la lista de variables declaradas, porque la configuración de nginx está llena de `$` que no hay que tocar.

El contador vive en la memoria compartida de nginx y se reinicia cuando el servicio reinicia. Es aceptable: un reinicio solo devuelve cupo, nunca lo amplía.

### D4: Antes de cualquier límite por dirección, el sistema tiene que saber cuál es

nginx declara de qué proxy acepta una dirección reenviada y uvicorn declara lo propio para el que tiene delante. Sin eso, un límite por dirección agrupa a todo internet bajo la dirección del proxy y corta a todos los usuarios como si fueran uno. Es la única tarea de este change que no puede quedar para después de las que dependen de ella, y por eso ordena el reparto.

### D5: La cota inferior del tamaño se sostiene en dos lugares

La validación de entrada rechaza un tamaño que no sea positivo, y el esquema lo rechaza también con una restricción. Duplicarlo es deliberado: de esa suma dependen tres límites, y hoy el esquema no tiene ninguna restricción que sostenga ninguno. La validación de entrada protege del caso normal y da un mensaje que nombra el campo; la del esquema es la que sigue valiendo si mañana otro camino escribe esa columna.

### D6: La limpieza pasa a correr sola, en un servicio propio del entorno

`add-instance-quota` dejó escrito que su limpieza podía seguir siendo manual porque el margen entre el techo de la instancia y el del proveedor absorbía la diferencia. Esa premisa valía mientras lo no contado fuera espacio facturable en un tercero. Con el almacenamiento en el mismo disco que la base, lo no contado es la distancia entre el techo declarado y el momento en que el disco se llena y el servicio se cae.

El mecanismo es un servicio del entorno que invoca el comando existente cada cierto intervalo. Se prefiere sobre un planificador dentro del proceso del backend porque no agrega una dependencia, porque queda declarado donde se lee el resto del entorno, y porque recibe sus propios techos de recursos. Se prefiere sobre un cron del host porque el host no está en el repositorio.

Esto revierte una parte explícita del requisito anterior, que pedía que descartar los restos no exigiera un proceso permanente. La razón de aquella decisión era que lo descartado era invisible para todos; ahora es visible como disco lleno.

### D7: Repartir la eliminación es responsabilidad del puerto, no de quien lo llama

El protocolo admite mil objetos por petición y hoy se mandan todos juntos. Los dos llamadores que pueden superarlo —la limpieza periódica y la eliminación de un álbum— no tienen forma de conocer ese tope sin saber qué proveedor está activo, que es exactamente lo que el puerto existe para ocultarles. Además el fallo actual es del peor tipo: los registros ya se borraron y se confirmaron antes de la llamada al almacenamiento, así que un lote que aborta convierte filas recuperables en objetos huérfanos sin nombre conocido.

### D9: Una petición sin cookie se rechaza sin tocar la base; una con cookie no puede

Resolver una sesión exige consultarla, así que no hay forma de validar una cookie existente sin una conexión. Lo que sí se puede es rechazar antes de pedirla la petición que no trae cookie ninguna, que es el caso del que abusa un flujo automatizado. La ganancia es concreta: hoy la dependencia que resuelve el usuario depende de la que abre la transacción, de modo que hasta una petición sin cookie abre una y la mantiene mientras descubre que no hay nada que resolver.

### D10: La dirección de una variante deja de nombrar un bucket fijo, y el par incoherente no arranca

El adapter de imgproxy compone hoy su origen con el nombre del bucket de MinIO, leído directamente de la configuración de ese proveedor. Con el almacenamiento apuntando a otro proveedor eso produce una dirección que no resuelve, y como cada puerto valida solo el grupo de credenciales del proveedor que él mismo selecciona, la combinación pasa las dos validaciones por separado y el proceso arranca limpio. El puerto de almacenamiento pasa a exponer cuál es su espacio y el adapter lo lee de ahí.

Con eso el código deja de mentir, pero no alcanza: el transformador del entorno está cableado contra el almacenamiento del entorno, así que el par sigue sin funcionar aunque la dirección sea correcta. El arranque lo rechaza nombrando la incompatibilidad. Parametrizar el transformador para que lea de un proveedor externo es trabajo del perfil cloud y queda fuera.

### D11: Todo umbral nuevo es una variable de entorno

Siguiendo lo que ya hacen los límites de cuota. Los valores por omisión propuestos son el techo general de peticiones por minuto y dirección, el techo propio de las concesiones las longitudes máximas de título y descripción, el intervalo de la limpieza, los tres techos de tiempo de la base, y los techos del transformador. Ninguno se elige por medición —todavía no hay tráfico real que medir— sino por ser holgado para el uso previsto y acotado para el abuso; que sean configurables es lo que hace aceptable elegirlos así.

## Risks / Trade-offs

**El contador del rate limit se reinicia cuando reinicia nginx** → La regla de la CDN queda como capa exterior, que no se reinicia con el servicio. El agujero dura lo que tarda un reinicio y solo devuelve cupo, no lo amplía.

**nginx pasa a manejar los bytes de cada subida** → Deja de ser un proxy de peticiones chicas para transportar hasta veinte mebibytes por foto, con tres subidas en paralelo por cliente. Se mitiga desactivando el buffering de la petición, de modo que transmita en lugar de acumular, y con los techos de recursos que cada servicio pasa a declarar.

**El techo de tiempo por sentencia puede cortar la suma del consumo de la instancia** → Esa consulta recorre la tabla completa y su duración crece con ella. El techo tiene que quedar por encima del peor caso observado, y la limpieza periódica es lo que evita que el peor caso crezca sin fondo. Si alguna vez corta, el síntoma es una concesión que falla, no una cuota mal calculada.

**El modo local y el cloud dejan de escribir contra el mismo tipo de origen** → Es la parte del spec que este change restringe. Se mitiga donde importa: la concesión sigue viajando descrita como una petición a ejecutar, el cliente la aplica sin saber a dónde apunta, y la suite de contrato del puerto corre igual contra los dos proveedores.

## Migration Plan

Un despliegue existente del perfil local necesita apuntar la dirección del almacenamiento para el navegador al hostname nuevo del punto de entrada (STORAGE_PUBLIC_URL). Rotar secretos sigue siendo criterio de quien despliega, como hasta ahora; si se rota la clave de firma, las direcciones de variante ya emitidas se vuelven a producir en la primera vista.

Las concesiones emitidas antes del cambio siguen apuntando a la dirección anterior y dejan de valer al vencer, como máximo quince minutos después. No hay migración de datos de objetos: los originales no se tocan.

Marcha atrás: cada pieza es independiente salvo dos. La cota del cuerpo en nginx depende de que el almacenamiento se alcance por el punto de entrada, así que volver atrás lo uno obliga a lo otro. Y el límite por dirección depende de la identificación del cliente real: quitarla dejando el límite puesto corta a todos los usuarios como si fueran uno, de modo que si se revierte, se revierten juntos.

## Open Questions

**¿Qué valores concretos deberían tener los techos de tasa?** Los propuestos son holgados para el uso previsto y acotados para el abuso, pero ninguno sale de una medición: la instancia todavía no tiene tráfico real. Queda abierta porque es genuinamente diferible: son variables de entorno, ajustarlas no cambia ningún spec, ningún enfoque ni ninguna tarea, y responderla ahora exigiría estimar un perfil de uso que no existe. Lo que sí queda decidido acá es que existan y dónde se aplican.

### Resueltas durante la redacción

- **¿El almacenamiento va en un prefijo de ruta, un hostname propio o un puerto propio?** Hostname propio, con una vuelta por puerto propio en el medio. El primer corte fue la mecánica de SigV4 leída contra el código: el adapter firma con el cliente construido sobre la dirección del navegador (`storage/adapters/minio.py`), y la firma cubre host y ruta, así que cualquier reescritura la invalida. Eso descarta un prefijo de ruta genérico -- funciona solo si el SDK incluye ese prefijo en lo que firma, un comportamiento frágil y no portable entre providers, no algo a depender. Entre hostname propio y puerto propio, los dos evitan tocar la ruta igual de bien, y se probó puerto propio primero pensando en el caso de una IP privada sin dominio (uso personal o por VPN): un puerto no le exige a quien despliega tener ningún nombre que resolver. Se volvió a hostname porque esa ventaja no compensaba el costo del lado de producción: un proxy de plataforma como Dokploy asigna dominios a un puerto, no puertos a un contenedor, así que un puerto propio le pide a esa plataforma algo que no hace de forma natural. Y el caso sin dominio tiene una salida igual de simple sin tocar la estructura: un servicio como sslip.io/nip.io resuelve un hostname inventado (`storage.192-168-1-50.sslip.io`) contra una IP privada sin DNS propio que correr, el mismo mecanismo que ya cubre `storage.localhost` en desarrollo. El aislamiento de la cookie de sesión, la deprecación del direccionamiento por ruta en S3 y la práctica habitual de la industria -- la propia guía de MinIO para desplegarlo detrás de un reverse proxy pide preservar el Host por la misma razón que la firma lo exige -- apuntaron los tres a hostname desde el principio.
- **¿Se puede rechazar una petición sin sesión sin tomar conexión?** Solo la que no trae cookie. Lo cerró la forma en que se resuelve una sesión: el identificador se busca en la base, así que validar una cookie existente exige una conexión por definición. El scenario del spec quedó acotado a ese caso, que es el que un flujo automatizado explota.
- **¿La limpieza tiene que pasar a correr sola?** Sí. La dejó abierta el design de `add-instance-quota`, con el argumento de que el margen entre el techo de la instancia y el del proveedor absorbía lo no contado. Lo que la cierra es que la hipótesis de despliegue cambió: con el almacenamiento en el mismo disco que la base, lo no contado ya no es espacio facturable sino la distancia hasta que el servicio se cae.
- **¿Se soporta el par de almacenamiento externo con transformador propio?** No en este change. Lo cerró leer el cableado del entorno: el transformador está configurado contra el almacenamiento del entorno, así que corregir el bucket que compone el adapter deja la dirección bien formada pero igualmente irresoluble. Hacerlo funcionar es parametrizar el transformador por proveedor activo, que es trabajo del perfil cloud.
- **¿El límite de tasa va en la aplicación o en el punto de entrada?** En el punto de entrada. La primera redacción proponía las dos cosas; al buscar qué aportaba la capa de aplicación quedó que solo podría limitar por cuenta, y que hacerlo exige resolver la sesión contra la base, que es el recurso a proteger. Sin eso limita por dirección, que es lo que nginx ya hace y además antes. Lo que terminó de cerrarlo fue comprobar que la imagen de nginx es la oficial, que sustituye plantillas al arrancar, así que los umbrales pueden seguir siendo variables de entorno sin la capa extra.
- **¿De dónde sale la cota del cuerpo en el punto de entrada?** Del mismo máximo por archivo que ya valida la concesión, más el margen del protocolo. Es una derivación, no una elección: dos números distintos para la misma cosa terminan separándose, y el síntoma sería una subida rechazada por nginx en lugar de por la validación que sabe nombrar el campo.
