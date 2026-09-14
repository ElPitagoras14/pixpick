## Why

Hoy lo único que limita cuánto ocupa una persona es indirecto: 50 fotos por álbum y 20 MiB por archivo. Nada limita cuántos álbumes crea, así que el techo real de una cuenta es "50 por la cantidad de álbumes que se le ocurra crear" — es decir, no hay techo. Con el proveedor de almacenamiento cloud eso se factura, y con el local llena el disco de quien lo hospeda.

Y del otro lado falta lo mismo pero para quien usa el producto: no hay forma de saber cuánto se está ocupando. Ni en total, ni por álbum, ni por foto. Alguien que quiera hacer lugar no tiene con qué decidir qué borrar.

Las dos cosas son la misma: un límite que nadie puede ver no es un límite, es una sorpresa el día que se alcanza.

## What Changes

- **Cada persona tiene un límite de almacenamiento**, de 150 MiB, declarado en la configuración del entorno como ya lo está el máximo de fotos por álbum.
- **Lo que cuenta son los originales de las fotos de sus álbumes.** Las variantes no ocupan lugar propio: el transformador las produce al pedido y lo que las conserva es un cache, que se vacía sin consecuencias.
- **El consumo lo paga el dueño del álbum.** Una foto que alguien califica en un álbum compartido ocupa lugar en la cuenta de quien lo posee, que es quien decidió subirla y quien puede borrarla.
- **El límite se evalúa al conceder el permiso de subida**, antes de transferir un solo byte, exactamente donde ya se evalúa el máximo de fotos del álbum.
- **Un lote que no entra entero se concede en parte.** Se recorren los archivos en el orden en que se pidieron, se concede permiso a cada uno que entre en los dos límites, y el que no entra se devuelve sin permiso con el motivo y cuánto espacio queda. Quien elige veinte fotos cuando entran doce ve doce subiendo y ocho explicadas, en lugar de un rechazo total que lo obliga a volver a elegir cuáles doce.
- **Eso cambia también el máximo de fotos por álbum**, que hoy rechaza el lote completo. Los dos límites son de capacidad y pasan a comportarse igual: quedarse sin lugar no es un error de quien pide, es un hecho del estado de la cuenta, y las dos formas de quedarse sin lugar no tienen por qué responder distinto.
- **Un archivo inadmisible sigue rechazando el lote entero.** Ahí la distinción se mantiene y con el argumento que la spec ya trae: el cliente conoce el tipo y el tamaño de sus propios archivos antes de pedir, así que un rechazo por eso indica una inconsistencia y no un caso normal de uso. La capacidad es lo contrario — el cliente no puede saberla con certeza, porque cambia desde otra sesión, otro dispositivo o un borrado.
- **Las fotos a la espera de confirmación ocupan su tamaño declarado**, igual que hoy ocupan un lugar del álbum. Sin eso, pedir concesiones repetidamente permite superar el límite entre varios lotes simultáneos.
- **El consumo se puede consultar en tres niveles**: el total de la persona contra su límite, lo que ocupa cada álbum, y lo que ocupa cada foto. Los tres son información del dueño y de nadie más.
- **Se muestra en los tres lugares donde se decide algo con él**: en la home el total contra el límite, en cada álbum lo que ocupa, y en la grilla el tamaño de cada foto junto a los contadores de calificaciones que el dueño ya ve ahí.

### Fuera de alcance

- **Cobrar, vender más espacio o tener planes distintos por persona.** El límite es uno solo, igual para todas las cuentas, y vive en la configuración del entorno.
- **Bloquear la lectura al alcanzar el límite.** Estar lleno impide subir y nada más: los álbumes se siguen viendo, calificando y compartiendo. Un límite que además rompe lo ya guardado castiga dos veces por lo mismo.
- **Borrar nada automáticamente al llegar al tope.** Qué se borra lo decide quien lo subió; el producto le da los números para decidirlo, no la decisión.
- **Contar lo que ocupan las variantes derivadas.** No es una simplificación: no ocupan lugar nuestro, y contar bytes de un cache haría que el consumo de una persona cambiara sin que ella hiciera nada.
- **Avisar cuando falte poco.** El número va a estar a la vista en la home; un aviso adicional es una decisión de producto propia, con su propio umbral que discutir.

## Capabilities

### New Capabilities

- `account-quota`: gobierna cuánto almacenamiento puede ocupar una persona y cómo lo conoce. Define el límite y de dónde sale su valor, qué bytes se cuentan y cuáles no, a quién se le imputan los de un álbum compartido, y que el consumo se pueda consultar en los tres niveles en que sirve para decidir —cuenta, álbum y foto—, siempre y solo para el dueño. Es una capability propia y no un requirement más de `photo-upload` porque el límite existe fuera del acto de subir: se consulta sin subir nada, y lo que lo hace bajar es eliminar, que es otro flujo.

### Modified Capabilities

- `photo-upload`: dos cambios. Gana un requirement hermano del que hoy gobierna el máximo de fotos por álbum, que dice que al conceder se evalúan dos límites y no uno, y que los dos rechazos se distinguen entre sí —quedarse sin lugar en el álbum se resuelve creando otro álbum, y quedarse sin espacio en la cuenta no—.

  Y modifica el requirement del máximo por álbum, que hoy exige rechazar el lote completo: pasa a conceder lo que entra y devolver el resto sin permiso, con su motivo. Es un cambio de comportamiento sobre algo ya implementado, y entra en este change porque la alternativa es peor: dos límites de capacidad que responden distinto a la misma acción, sin nada en la pantalla que explique por qué una vez subieron doce fotos y otra vez ninguna.

  El requirement que rechaza el lote entero por un archivo inadmisible **no** se toca. Su justificación escrita —el cliente conoce el tipo y el tamaño antes de pedir, así que un rechazo señala una inconsistencia y no un uso normal— sigue valiendo, y es justamente la que no vale para la capacidad.

`album-stats` no se modifica, aunque el tamaño por foto vaya a mostrarse junto a los contadores que esa capability provee. Esa capability gobierna la información agregada sobre las **calificaciones** de un álbum, y unos bytes no son una calificación: meterlos ahí obligaría a ensanchar su propósito para que abarcara dos cosas sin relación. Que las dos se muestren en el mismo lugar de la pantalla es una decisión de presentación, y no una razón para mezclarlas en el mismo contrato.

## Impact

**Base de datos**

Ninguna columna nueva y ninguna migración. El tamaño real de cada foto ya se guarda al confirmarla, y el declarado desde que se concede el permiso: el consumo de una persona es una suma sobre las fotos de sus álbumes. Queda por resolver en el diseño si esa suma se calcula al momento o se mantiene acumulada, y la respuesta depende de cuánto cuesta la consulta en el peor caso realista, no de una preferencia.

**Concurrencia**

Es el punto delicado del change. Hoy conceder bloquea la fila del álbum, lo que alcanza para un límite que es del álbum. Un límite de la persona abarca todos sus álbumes, así que dos lotes simultáneos en dos álbumes distintos del mismo dueño hoy no se verían entre sí: cada uno bloquearía el suyo y ambos leerían el mismo total. El punto de exclusión tiene que pasar a ser la persona.

**Backend**

- `packages/photos/config.py` y `.env.example`: el límite nuevo, junto al máximo por álbum.
- `packages/photos/service.py`: la segunda evaluación al conceder, el recorrido que concede lo que entra en lugar de rechazar el lote, y el bloqueo por persona en lugar del bloqueo por álbum.
- `packages/photos/responses.py`: la respuesta al pedido de permisos de subida —el primer paso del flujo, donde el cliente declara qué archivos quiere subir y recibe una dirección firmada por cada uno— deja de ser una lista plana de permisos y pasa a llevar también los archivos que no se concedieron, cada uno con su motivo. Es el cambio de contrato de este change, y alcanza a todo cliente que hoy asuma que pidió N y recibió N.
- Un recurso nuevo para consultar el consumo, con su repositorio, su servicio y su router.
- `packages/albums`: lo que ocupa cada álbum, para que la lista pueda mostrarlo.

**Interfaz**

- La home, hoy vacía, muestra el total contra el límite.
- La lista de álbumes muestra lo que ocupa cada uno.
- La grilla muestra el tamaño de cada foto en la tira que el dueño ya ve, sin agregar una tira nueva.
- La cola de subida gana un estado por archivo para el que se pidió y no se concedió, con el motivo al lado. La estructura ya lleva estado por archivo, así que es un valor más y no un mecanismo nuevo.
- La vista de subida deja de traducir el álbum lleno como un error del lote y pasa a mostrarlo por archivo, junto al de cuenta llena.

**Precedencia**

Depende de que el máximo por álbum ya exista, que es el caso. Va antes de `add-landing-and-home`: si la home se construye primero, hay que volver a tocarla para meter el consumo.
