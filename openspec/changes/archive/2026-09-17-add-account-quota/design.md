## Context

Conceder permisos de subida hoy hace, dentro de una transacción: bloquear la fila del álbum con `select ... for update` —que a la vez comprueba la pertenencia—, contar las fotos ocupadas del álbum, comparar contra el máximo, calcular la posición siguiente, firmar un permiso por archivo e insertar las filas pendientes. Si el lote no entra, levanta un conflicto de estado y no concede nada.

La firma de un permiso no sale a la red en ninguno de los dos proveedores: es un cálculo local sobre las credenciales. Por eso esa transacción dura milisegundos aunque el lote tenga cincuenta archivos.

Los tamaños ya están en la base. `declared_size` se escribe al conceder y `size` al confirmar, y la confirmación compara el objeto real contra lo declarado: si no coinciden, la foto se rechaza y el objeto se elimina. De ahí que para toda foto disponible el tamaño registrado sea el real, y que una suma sobre esas columnas no pueda desfasarse de lo que hay en el almacenamiento.

El esquema tiene los índices que esta suma necesita: `albums_owner_id_idx` sobre `albums (owner_id)` y `photos_album_id_idx` sobre `photos (album_id)`. La única escritura sobre `users` en todo el backend es el alta o actualización al iniciar sesión.

El pedido de concesión no lleva el nombre de los archivos: cada uno viaja con su tipo, su tamaño y sus dimensiones, y la respuesta devuelve los permisos en el mismo orden, que es cómo el cliente los vuelve a asociar con sus archivos.

## Goals / Non-Goals

**Goals:**

- Que el límite de la persona no se pueda superar por dos pedidos simultáneos, en el mismo álbum o en álbumes distintos.
- Que el consumo que se muestra no pueda mentir, ni siquiera transitoriamente.
- Que un lote que no entra entero suba lo que sí entra, y que quede claro por archivo qué no entró y por qué.

**Non-Goals:**

- Optimizar la consulta de consumo antes de tener un caso que lo pida. El límite acota el tamaño del problema por construcción, y esa cota se calcula en D2.
- Unificar los dos límites en uno. Son dos y siguen siendo dos: dan mensajes distintos porque se resuelven distinto.

## Decisions

### D1 - El punto de exclusión pasa a ser la persona, y reemplaza al bloqueo del álbum

La transacción de concesión pasa a bloquear la fila de la persona dueña del álbum, en lugar de la fila del álbum.

No es un bloqueo más sino uno en vez del otro, y eso es lo que lo hace barato: como todo álbum tiene exactamente un dueño, serializar por persona ya serializa por álbum. Lo que el bloqueo del álbum protegía —que dos lotes no calculen la misma posición siguiente ni cuenten la misma ocupación— queda protegido igual. La comprobación de pertenencia, que hoy viaja pegada a ese bloqueo, se mantiene como consulta aparte.

La alternativa era conservar el bloqueo del álbum y agregar uno consultivo por persona. Se descarta porque son dos mecanismos para una misma exclusión, con dos órdenes de adquisición posibles y por lo tanto con la posibilidad de un abrazo mortal entre dos transacciones que los tomen en orden distinto.

El riesgo de ensanchar el bloqueo a la persona es contender con otras escrituras sobre esa fila. Son una sola en todo el backend, el alta o actualización al iniciar sesión, y la transacción que sostiene el bloqueo no hace entrada/salida de red, así que la espera posible es de milisegundos y solo contra una sesión de esa misma persona.

### D2 - El consumo se suma al momento y no se mantiene acumulado

El consumo de una persona se calcula con una consulta que suma, sobre las fotos de sus álbumes, el tamaño real de las disponibles y el declarado de las que esperan confirmación con permiso vigente.

La alternativa —una columna acumulada que se actualiza en cada movimiento— es más rápida de leer y peor en todo lo demás. Habría que mantenerla en cinco flujos distintos: conceder, confirmar, eliminar una foto, eliminar un álbum entero y descartar las esperas vencidas. Cada uno es un lugar donde olvidarla, y el resultado de olvidarla no es un error visible sino un número equivocado que nadie nota hasta el día que bloquea una subida legítima o deja pasar una que no debía.

Lo que vuelve innecesaria esa optimización es que **el propio límite acota el tamaño del problema**. Con 150 MiB por persona, el peor caso realista —fotos de unos 10 KB, el piso práctico de una imagen— da unas quince mil filas por persona; con fotos de tamaño corriente, unos cientos. Es una agregación sobre un conjunto acotado, alcanzable por los dos índices que ya existen, y ocurre una vez por lote y no una vez por archivo.

Si algún día el límite deja de acotar —planes distintos, cuentas grandes—, el acumulado se puede introducir sin tocar ninguna spec, porque ninguna dice cómo se calcula el número.

### D3 - El consumo viaja por recursos propios y no agregado a los que ya existen

Se agregan dos recursos: el de la cuenta, que devuelve el total, el límite y el desglose por álbum, y el del álbum, que devuelve su total y el tamaño de cada una de sus fotos. Los dos son del dueño y de nadie más.

La alternativa tentadora era sumar el dato a lo que ya se pide: lo ocupado por álbum en la lista de álbumes, el tamaño por foto en la galería. Se descarta por una asimetría de visibilidad concreta. La lista de álbumes es solo de los propios, así que ahí sería seguro; pero el detalle de un álbum y su galería los ve también quien recibió el álbum compartido, y el tamaño no es información suya. Meterlo ahí obligaría a filtrar campos según quién pregunta —algo que hoy el proyecto no hace en ninguna respuesta— y a repetir esa decisión en cada campo nuevo. Con recursos propios la regla de visibilidad se escribe una vez, en la puerta.

El costo es una petición más en la vista del álbum. Es el mismo costo que ya se paga por las estadísticas, y se paga igual: se pide junto con la galería y no se espera antes de dibujarla.

### D4 - La respuesta al pedido de permisos identifica cada archivo por su posición en el pedido

Se trata del primer paso del flujo de subida: el cliente declara qué archivos quiere subir —tipo, tamaño y dimensiones, sin el contenido— y recibe por cada uno una dirección firmada contra la que el navegador escribe directo en el almacenamiento. Hoy esa respuesta es una lista plana de permisos, tantos como archivos se pidieron.

Pasa a llevar dos listas: los permisos concedidos y los archivos sin permiso, cada uno con su motivo y con cuánto espacio o lugar quedaba. Cada entrada, de una lista o de la otra, lleva el índice que el archivo tenía en el pedido.

Ese índice no es decorativo. Hoy el cliente vuelve a asociar cada permiso con su archivo por el orden, porque pide N y recibe N; en cuanto la respuesta puede tener menos permisos que archivos, el orden deja de alcanzar. El pedido no lleva nombres de archivo —solo tipo, tamaño y dimensiones—, así que el índice es el único identificador disponible, y hacerlo explícito evita que el cliente reconstruya la correspondencia contando.

### D5 - El recorrido saltea lo que no entra y sigue

Los archivos se evalúan en el orden pedido, y el que no entra se saltea sin detener el recorrido: uno más chico que venga después puede entrar igual.

La alternativa era cortar en el primero que no entra y no conceder nada de lo que sigue. Es más simple de explicar pero desperdicia espacio por un accidente de orden: una foto grande al principio dejaría afuera a diez chicas que entraban. Saltear no cambia el orden de las que sí entran ni reordena nada, así que lo que se pierde en simplicidad se gana en que la selección de quien sube se respeta lo más posible.

Con el límite de cantidad del álbum la distinción no existe: cuando no queda lugar, no queda para ninguna y el recorrido termina por sí solo. Solo importa para el límite de espacio.

### D6 - La vista de subida muestra el espacio disponible antes de elegir

La pantalla de subida muestra cuánto espacio le queda a la persona antes de que elija archivos, no solo después de que el servidor rechace algunos.

Es barato —el dato ya está en el recurso de la cuenta— y cambia el carácter del límite: deja de ser algo que se descubre al chocar y pasa a ser algo que se ve antes de decidir. Es la diferencia que el propio motivo de este change plantea entre un límite y una sorpresa.

## Risks / Trade-offs

**Ensanchar el bloqueo de álbum a persona serializa todas las subidas de alguien (D1)** → Es lo que la corrección exige: un límite de la cuenta no se puede evaluar viendo un álbum. El efecto práctico es nulo porque una persona sube desde un lugar a la vez, y la transacción no espera red.

**La suma al momento crece con la cantidad de fotos (D2)** → Acotada por el propio límite: unas quince mil filas en el peor caso realista, con los dos índices que ya existen, una vez por lote. Si el límite deja de acotar, el cambio a un acumulado no toca ninguna spec.

**Una concesión parcial puede pasar inadvertida (D4, D5)** → Quien elige veinte archivos y ve doce subiendo tiene que entender qué pasó con ocho. Por eso el motivo va por archivo y no como un mensaje general del lote, y por eso D6 muestra el espacio antes de elegir: la mayoría de las veces el recorte deja de ser una sorpresa.

**El cambio de forma de la respuesta de concesión rompe a cualquier cliente existente (D4)** → El único cliente es la interfaz del proyecto, y este change la actualiza. No hay versiones publicadas de la API ni consumidores externos.

**Dos recursos nuevos son dos peticiones más (D3)** → Se piden en paralelo, no bloquean el dibujado, y a cambio ninguna respuesta existente cambia de forma ni empieza a filtrar campos por quién pregunta.

## Migration Plan

No hay migración de datos ni cambios de esquema: las dos columnas de tamaño ya existen y ya están pobladas.

Una cuenta que hoy supere los 150 MiB —posible solo en un entorno de desarrollo con datos de prueba— conserva todo y simplemente no puede agregar más hasta liberar espacio. Eso no es un caso a migrar sino el comportamiento que el spec exige.

El rollback es revertir el commit. Nada de lo que este change escribe queda en la base, así que volver atrás no deja residuo: el límite deja de evaluarse y las subidas vuelven a depender solo del máximo por álbum.

## Open Questions

Ninguna. Las dos incógnitas de peso —dónde poner el punto de exclusión y si el consumo se calcula o se acumula— se cerraron con datos del propio proyecto: quién más escribe la fila que se bloquea, y qué cota le impone el límite al tamaño de la suma.

### Resueltas durante la redacción

- **¿El consumo puede desfasarse de lo que hay en el almacenamiento? (D2)** No. La confirmación compara el objeto real contra lo declarado y, si no coinciden, rechaza la foto y elimina el objeto, así que el tamaño registrado de toda foto disponible es el real. *Fuente: el requirement de confirmación en `photo-upload`.*
- **¿Bloquear la fila de la persona interfiere con otra cosa? (D1)** Solo con el alta o actualización de esa misma persona al iniciar sesión, que es la única escritura sobre esa tabla en todo el backend. *Fuente: búsqueda de escrituras sobre `users` en el código.*
- **¿Cuánto puede durar el bloqueo? (D1)** Milisegundos: firmar un permiso es cálculo local en los dos proveedores, así que la transacción no espera respuestas de red aunque el lote tenga cincuenta archivos. *Fuente: los dos adapters de almacenamiento.*
- **¿Hace falta un índice nuevo para la suma? (D2)** No: `albums (owner_id)` y `photos (album_id)` ya están indexados. *Fuente: la migración que crea las dos tablas.*
- **¿Cuán grande puede ser esa suma? (D2)** Unas quince mil filas por persona en el peor caso realista —150 MiB en fotos de unos 10 KB—, y unos cientos con fotos de tamaño corriente. *Fuente: derivación aritmética a partir del límite.*
- **¿Cómo se identifica un archivo que no recibió permiso? (D4)** Por su índice en el pedido: los archivos no viajan con nombre, solo con tipo, tamaño y dimensiones. *Fuente: la forma del pedido de concesión.*
- **¿Se corta en el primero que no entra o se saltea? (D5)** Se saltea, para no desperdiciar espacio por el orden de la selección. Respondida como decisión de producto, no derivada de un dato. *Fuente: decisión tomada al redactar, con la alternativa registrada arriba.*
- **¿Por qué no agregar el dato a las respuestas que ya existen? (D3)** Porque el detalle del álbum y su galería los ve también quien lo recibió compartido, y eso obligaría a filtrar campos según quién pregunta, que es algo que hoy no ocurre en ninguna respuesta del proyecto. *Fuente: el requirement de acceso de `album-sharing` y la forma actual de las respuestas.*
