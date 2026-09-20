## 1. Cotas de entrada y restricciones de esquema

- [x] 1.1 Acotar `GrantPhotoRequest.size` a un entero positivo que no supere el máximo por archivo, y acotar `width`/`height`, verificando con un test de router que un tamaño negativo, uno de cero y uno excesivo se rechacen como error de validación nombrando el campo
- [x] 1.2 Ajustar la validación del servicio para que el rechazo por tamaño no positivo identifique el archivo del lote, verificando con un test que el lote completo se rechaza y que ni el consumo de la cuenta ni el de la instancia cambian
- [x] 1.3 Escribir la migración que agrega la restricción de esquema sobre `declared_size`, verificando que aplica sobre la base de desarrollo y que revertirla y reaplicarla funciona
- [x] 1.4 Acotar `ConfirmPhotosRequest.photo_ids` al mismo techo que el lote de concesión, verificando con un test que un lote mayor se rechaza como validación y que no se consulta el almacenamiento
- [x] 1.5 Acotar la longitud de `title` y `description` al crear y al renombrar un álbum, con los máximos declarados en configuración, verificando con tests que un valor más largo se rechaza nombrando el campo

## 2. Identificación del cliente real

- [x] 2.1 Declarar en nginx de qué proxy se acepta la dirección reenviada y de qué encabezado se lee, verificando que el log de acceso de una petición externa muestra la dirección del cliente y no la del contenedor de la plataforma
- [x] 2.2 Declarar en uvicorn de qué origen acepta los encabezados reenviados, verificando que el registro del backend muestra la dirección del cliente y no la del contenedor de nginx
- [x] 2.3 Comprobar que una dirección afirmada por un origen no declarado se ignora, verificando con una petición que envía el encabezado por su cuenta que la dirección registrada no es la afirmada

## 3. El almacenamiento detrás del punto de entrada

- [x] 3.1 Agregar en nginx el bloque que atiende el hostname del almacenamiento y lo reenvía sin reescribir ruta ni destino, preservando el Host original, verificando que una petición de lectura firmada a través de ese hostname es aceptada por el almacenamiento
- [x] 3.2 Fijar explícitamente el estilo de direccionamiento por ruta en el cliente del adapter de MinIO, verificando que la suite de contrato del puerto sigue pasando
- [x] 3.3 Apuntar la dirección del navegador del almacenamiento al hostname del punto de entrada en ambos archivos de entorno y en el archivo de ejemplo, verificando que una subida completa de extremo a extremo funciona con el entorno levantado
- [x] 3.4 Componer `client_max_body_size` a partir del máximo por archivo más el margen del protocolo, verificando que un cuerpo dentro del máximo se acepta y uno por encima se rechaza en el punto de entrada sin llegar al almacenamiento
- [x] 3.5 Desactivar el buffering de la petición en ese bloque, verificando que una subida grande no deja archivos temporales en el volumen de nginx mientras transcurre
- [x] 3.6 Ajustar los orígenes admitidos por el almacenamiento al origen real de la aplicación, verificando que una subida desde el origen declarado se acepta y desde otro no

## 4. Rate limit y backpressure

- [x] 4.1 Convertir la configuración de nginx en plantilla sustituida al arrancar, con la lista de variables restringida y validada como hace el entrypoint de la interfaz, verificando que el entorno levanta y que cambiar una variable cambia el valor efectivo
- [x] 4.2 Agregar en nginx los límites de tasa y de conexiones concurrentes por dirección, con un techo general sobre el espacio de la API y uno más estricto sobre la concesión de subidas, verificando que una ráfaga por encima del techo recibe rechazos, que un ritmo normal no se ve afectado y que el techo de concesiones no afecta a otras operaciones
- [x] 4.3 Servir el rechazo por tasa con el cuerpo de error común de la API y su indicación de reintento, verificando que la respuesta tiene la misma forma que la de cualquier otro error
- [x] 4.4 Rechazar sin tomar conexión la petición que no trae cookie de sesión hacia un recurso que la requiere, verificando con un test que el pool queda intacto ante una ráfaga de peticiones sin cookie y que una petición autenticada simultánea se sigue atendiendo
- [x] 4.5 Agregar al cuerpo común de error la indicación de reintento, verificando con un test de esquema que la estructura la admite y que las respuestas que no la usan no cambian
- [x] 4.6 Traducir el agotamiento del pool a una respuesta de falta de capacidad con indicación de reintento, verificando con un test que fuerza el agotamiento que la respuesta no es un fallo interno y que no se registra una traza por petición
- [x] 4.7 Declarar los techos de tiempo por sentencia, por espera de lock y por transacción inactiva, más la validación y el reciclado de conexiones del pool, verificando con un test que una sentencia deliberadamente lenta se interrumpe y libera su conexión
- [x] 4.8 Mostrar en la interfaz el rechazo por falta de capacidad como estado transitorio con sugerencia de reintentar, verificando que se distingue visualmente de un error de validación y de un fallo

## 5. Reclamación automática de restos

- [x] 5.1 Repartir la eliminación de varios objetos dentro del puerto de almacenamiento según el tope del protocolo, verificando con un test de contrato que una cantidad por encima del tope se elimina completa y que quien llama no la repartió
- [x] 5.2 Agregar el servicio del entorno que invoca la limpieza cada intervalo configurable, declarado en ambos archivos de entorno, verificando que tras el intervalo los registros vencidos y los objetos huérfanos desaparecen sin intervención
- [x] 5.3 Comprobar que la limpieza sigue siendo invocable a mano y que ejecutarla sobre un entorno ya limpio no falla, verificando con una segunda ejecución consecutiva

## 6. Techos de recursos

- [x] 6.1 Desactivar la consola del almacenamiento, verificando que su dirección ya no responde y que la API de objetos sigue funcionando
- [x] 6.2 Declarar los techos del transformador —tamaño y resolución del original, dimensión del resultado, cantidad de trabajadores, tiempo de descarga y espacio desde el que admite leer—, verificando que un original por encima del techo se rechaza sin procesarse y que leer fuera del prefijo declarado se rechaza
- [x] 6.3 Declarar techo de memoria y política de reinicio para cada servicio de ambos archivos de entorno, verificando que el entorno levanta y que inspeccionar la declaración muestra un techo por servicio

## 7. Guards de arranque

- [x] 7.1 Exponer en el puerto de almacenamiento cuál es su espacio y hacer que el adapter del transformador lo lea de ahí en lugar del de un proveedor fijo, verificando con un test que la dirección producida nombra el espacio del proveedor activo
- [x] 7.2 Rechazar en el arranque la combinación de proveedores que el entorno no puede atender, con un error que la nombre, verificando con tests que cada combinación admitida arranca y cada una no admitida falla

## 8. Configuración, documentación y cierre

- [x] 8.1 Declarar en el archivo de ejemplo todas las variables nuevas con su explicación y su marca de obligatoriedad, siguiendo el formato vigente, verificando que no queda ninguna variable sin consumidor ni ningún consumidor sin variable declarada
- [x] 8.2 Declarar servicio por servicio qué variables nuevas recibe cada uno en ambos archivos de entorno, verificando que la comprobación de coincidencia entre ambas declaraciones sigue pasando
- [x] 8.3 Documentar en el README el hostname nuevo del almacenamiento -- incluyendo cómo resolverlo con un dominio real, con `storage.localhost` en desarrollo, y con sslip.io/nip.io para una IP privada o de VPN sin dominio propio -- y la regla de límite de tasa que conviene configurar en la CDN, verificando que un despliegue desde cero siguiendo solo el README queda operativo
- [x] 8.4 Correr `ruff format` y `ruff check` sobre `backend/`, verificando que ambos terminan sin hallazgos
- [x] 8.5 Correr la suite completa del backend y la de la interfaz, verificando que pasan y que la suite de contrato del puerto de almacenamiento corrió contra el doble y contra el proveedor real
- [x] 8.6 Ejercitar de extremo a extremo el flujo completo con el entorno levantado —crear álbum, subir, confirmar, ver galería, calificar y eliminar—, verificando que funciona con el punto de entrada delante del almacenamiento y los límites activos
