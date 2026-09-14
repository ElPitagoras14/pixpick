# object-storage Specification

## Purpose

Gobierna cómo el sistema guarda archivos binarios y cómo llegan ahí: cómo se concede una subida directa desde el navegador, cómo se nombran los objetos, cómo se verifica lo que efectivamente llegó, cómo se eliminan, y qué se le exige a un proveedor de almacenamiento para ser intercambiable con otro. No se solapa con `image-delivery`, que gobierna cómo se entregan al navegador las variantes de lo que acá se guardó.

## Requirements

### Requirement: El contenido sube directo al almacenamiento y no pasa por la API

La subida SHALL ir del navegador al almacenamiento sin atravesar la API. La API SHALL limitarse a conceder el permiso de escritura, y SHALL NOT recibir, reenviar ni retener el contenido.

#### Scenario: El contenido no atraviesa la API

- **WHEN** el navegador sube un archivo
- **THEN** el contenido viaja al almacenamiento
- **AND** no pasa por la API

#### Scenario: La API concede sin ver el contenido

- **WHEN** la API concede una subida
- **THEN** lo hace conociendo únicamente lo que se declaró sobre el archivo
- **AND** no necesita el contenido para conceder

### Requirement: La concesión de subida está acotada en objeto, tiempo y tipo, y el tamaño se verifica al confirmar

Una concesión SHALL habilitar la escritura de un único objeto, SHALL vencer, y SHALL declarar el tipo de contenido admitido. El tamaño declarado SHALL validarse antes de emitir la concesión, y el tamaño real del objeto SHALL verificarse contra lo declarado una vez subido -- ninguna de las dos comprobaciones SHALL depender de que el almacenamiento la imponga al recibir, porque ningún esquema de firma por URL puede expresar un rango de tamaño de forma portable entre proveedores.

#### Scenario: Un tamaño declarado por encima del límite se rechaza antes de conceder

- **WHEN** se pide una concesión para un archivo cuyo tamaño declarado excede el límite
- **THEN** no se emite la concesión

#### Scenario: Un objeto que no coincide con lo declarado se rechaza al confirmar

- **WHEN** el objeto subido con una concesión válida no coincide en tamaño con lo declarado
- **THEN** se rechaza al confirmarlo
- **AND** el objeto se elimina del almacenamiento

#### Scenario: Una concesión vencida ya no habilita

- **WHEN** se intenta usar una concesión cuyo vencimiento pasó
- **THEN** la escritura se rechaza

#### Scenario: Una concesión no habilita escribir otro objeto

- **WHEN** se intenta usar una concesión para escribir un objeto distinto del que habilitaba
- **THEN** la escritura se rechaza

### Requirement: El nombre de un objeto no depende del proveedor, y cambiar de proveedor es copiar contenido

El nombre con el que se guarda un objeto SHALL ser válido en cualquier proveedor de almacenamiento y SHALL NOT incluir nada que identifique a uno en particular. En consecuencia, mover el sistema de un proveedor a otro SHALL requerir únicamente copiar el contenido: los datos que refieren a esos objetos SHALL seguir siendo correctos sin modificación alguna.

El sistema SHALL permitir comprobar, antes de cambiar el proveedor activo, cuáles de los objetos que tiene registrados no están todavía en el proveedor de destino. Esa comprobación SHALL usar la misma operación de consulta que el puerto ya ofrece, y SHALL poder hacerse mientras el sistema sigue funcionando contra el proveedor anterior, porque comprobarlo después del cambio sería comprobarlo tarde.

#### Scenario: El nombre no menciona al proveedor

- **WHEN** se inspecciona el nombre con el que se guardó un objeto
- **THEN** no contiene nada que identifique al proveedor donde está

#### Scenario: Copiar el contenido alcanza para cambiar de proveedor

- **WHEN** se copian todos los objetos a otro proveedor y se cambia el proveedor activo
- **THEN** todas las referencias existentes siguen resolviendo
- **AND** no hubo que modificar ningún dato almacenado

#### Scenario: Antes de cambiar se puede saber qué falta

- **WHEN** se consulta el proveedor de destino con los nombres que el sistema tiene registrados
- **THEN** se puede determinar cuáles no están todavía
- **AND** la comprobación se hace sin dejar de operar contra el proveedor vigente

#### Scenario: Un objeto faltante se detecta antes y no después

- **WHEN** la copia quedó incompleta y se ejecuta la comprobación
- **THEN** los objetos que faltan quedan identificados
- **AND** el proveedor activo todavía no cambió

### Requirement: La concesión se describe de forma que el cliente la aplique sin conocer el proveedor

La concesión SHALL entregarse al cliente descrita en términos de qué petición hacer, de modo que el cliente la aplique tal como la recibió. SHALL NOT exigirle al cliente conocer qué proveedor está detrás ni ramificar según cuál sea.

#### Scenario: El cliente aplica la concesión tal como llega

- **WHEN** el cliente recibe una concesión y sube el archivo
- **THEN** usa lo que la concesión describe
- **AND** su código no contiene condicionales por proveedor

#### Scenario: Cambiar de proveedor no cambia el cliente

- **WHEN** se cambia el proveedor de almacenamiento activo
- **THEN** el código del cliente que sube archivos no se modifica

### Requirement: Los nombres de objeto se derivan del dominio y agrupan por álbum

El nombre de un objeto SHALL construirse a partir de identificadores del dominio ya conocidos al momento de conceder la subida, con un prefijo que agrupe los objetos de un mismo álbum. SHALL NOT derivarse del nombre de archivo que el cliente declaró, ni depender de ningún dato que el cliente controle.

#### Scenario: El nombre no depende del archivo original

- **WHEN** se concede una subida
- **THEN** el nombre del objeto se deriva de identificadores del dominio
- **AND** el nombre de archivo declarado por el cliente no lo determina

#### Scenario: Los objetos de un álbum comparten prefijo

- **WHEN** se comparan los nombres de dos objetos del mismo álbum
- **THEN** comparten un prefijo común a ese álbum
- **AND** eliminar todo lo del álbum es eliminar ese prefijo

#### Scenario: Dos archivos con el mismo nombre no colisionan

- **WHEN** se suben dos archivos que se llaman igual
- **THEN** ocupan objetos distintos

### Requirement: Lo que llegó se verifica contra lo que se declaró

El sistema SHALL poder consultar un objeto ya subido y obtener su tamaño y su tipo de contenido reales, y SHALL distinguir un objeto presente de uno ausente. SHALL NOT darse por válido lo que el cliente declaró sin comprobarlo contra el objeto.

#### Scenario: Un objeto ausente se distingue de uno presente

- **WHEN** se consulta un objeto que nunca se subió
- **THEN** el resultado indica que no está
- **AND** no se confunde con un objeto de tamaño cero

#### Scenario: El tamaño real es comparable con el declarado

- **WHEN** se consulta un objeto que sí se subió
- **THEN** se obtiene su tamaño y su tipo de contenido reales

### Requirement: Eliminar objetos admite varios a la vez y es idempotente

La eliminación SHALL aceptar varios objetos en una sola operación, y eliminar algo que no existe SHALL NOT ser un error.

#### Scenario: Eliminar lo que no existe no falla

- **WHEN** se elimina un objeto que no está
- **THEN** la operación termina satisfactoriamente

#### Scenario: Varios objetos se eliminan juntos

- **WHEN** se eliminan varios objetos
- **THEN** una sola operación los cubre

### Requirement: El puerto no ofrece leer el contenido

El puerto de almacenamiento SHALL NOT ofrecer ninguna operación que devuelva el contenido de un objeto. Quien necesita el contenido es el transformador de imágenes, que lo lee del almacenamiento por su cuenta, así que ningún byte de imagen SHALL pasar por la memoria de la aplicación.

#### Scenario: No existe operación de lectura de contenido

- **WHEN** se inspecciona el puerto de almacenamiento
- **THEN** ninguna de sus operaciones devuelve el contenido de un objeto

#### Scenario: El contenido nunca pasa por la aplicación

- **WHEN** se recorre el ciclo de vida completo de un archivo, desde subirlo hasta entregarlo
- **THEN** sus bytes nunca atraviesan la aplicación

### Requirement: El almacenamiento declara desde qué orígenes se puede escribir

Como el navegador escribe directamente contra el almacenamiento y este vive en un origen distinto del de la aplicación, el almacenamiento SHALL declarar qué orígenes tienen permitido escribir y qué encabezados y métodos admite en esa negociación. SHALL NOT admitirse cualquier origen, y la declaración SHALL formar parte de la preparación del entorno y no ser un ajuste manual posterior.

#### Scenario: Un origen declarado puede subir

- **WHEN** el navegador, cargado desde un origen declarado, sube un archivo con una concesión válida
- **THEN** la escritura se acepta

#### Scenario: Un origen no declarado no puede subir

- **WHEN** se intenta subir desde un origen que no está declarado
- **THEN** el navegador no completa la escritura

#### Scenario: La declaración se aplica al preparar el entorno

- **WHEN** se levanta el entorno desde cero
- **THEN** los orígenes admitidos ya están declarados
- **AND** nadie tuvo que configurarlos a mano

### Requirement: La dirección con la que se firma para el navegador puede diferir de la que usa el servidor

El almacenamiento SHALL poder alcanzarse por dos direcciones distintas: la que el navegador usa y la que usa el servidor. Lo que se conceda al navegador SHALL ser válido cuando el navegador lo use, sin importar que el servidor alcance el almacenamiento por otro camino.

#### Scenario: La concesión sirve desde el navegador

- **WHEN** el navegador usa una concesión emitida para la dirección que le corresponde
- **THEN** la escritura se acepta

#### Scenario: Las operaciones del servidor usan su propia dirección

- **WHEN** el servidor consulta o elimina objetos
- **THEN** alcanza el almacenamiento por la dirección que le corresponde
- **AND** no depende de que la dirección del navegador sea alcanzable desde donde corre

### Requirement: Un fallo del almacenamiento llega como error de dominio

Cuando el almacenamiento no responda o rechace una operación, el resto de la aplicación SHALL recibir un error de dominio. SHALL NOT propagarse el error original del proveedor, y ninguna respuesta al cliente SHALL revelar qué proveedor está detrás.

#### Scenario: Un almacenamiento caído llega como error de dominio

- **WHEN** el almacenamiento no responde y se intenta una operación
- **THEN** el consumidor recibe un error de dominio

#### Scenario: La respuesta no revela el proveedor

- **WHEN** un fallo del almacenamiento se traduce en una respuesta al cliente
- **THEN** la respuesta no identifica al proveedor ni incluye su mensaje original

### Requirement: Todo proveedor cumple el mismo contrato verificable

El comportamiento exigido a un proveedor SHALL estar expresado como una suite ejecutable, y esa misma suite SHALL correr sin modificaciones contra el doble usado en pruebas y contra cada proveedor real. Un proveedor nuevo SHALL considerarse aceptable solo si la pasa completa.

#### Scenario: La misma suite corre contra el doble y contra el proveedor real

- **WHEN** se ejecuta la suite de contrato
- **THEN** se ejecuta contra el doble y contra el proveedor real
- **AND** su código es el mismo en los dos casos

#### Scenario: Un proveedor nuevo se acepta solo si pasa la suite

- **WHEN** se agrega un proveedor de almacenamiento
- **THEN** se lo somete a la suite de contrato sin adaptarla
- **AND** no se considera utilizable hasta que la pase completa

### Requirement: El almacenamiento queda listo como parte del arranque

Antes de que la aplicación atienda su primera petición, el espacio donde el proveedor guarda los objetos SHALL existir y estar listo para recibirlos. Dejarlo listo SHALL formar parte del arranque de la aplicación, y SHALL NOT depender de un paso manual ni de un servicio del entorno dedicado a eso.

La operación SHALL ofrecerse por el puerto, como el resto de las operaciones de almacenamiento, de modo que quien la invoca no conozca ni pregunte qué proveedor está activo. Para un proveedor que el proyecto opera dentro de su propio entorno, dejarlo listo SHALL incluir crear el espacio cuando falte; para un proveedor externo, cuyo espacio se crea una vez en el proveedor mismo, SHALL bastar con comprobar que existe.

La operación SHALL ser idempotente: repetirla sobre un espacio que ya está listo SHALL terminar sin error y SHALL NOT alterar su contenido. Cuando el almacenamiento no pueda quedar listo, el arranque SHALL fallar con un error de dominio que lo diga, y la aplicación SHALL NOT pasar a atender peticiones.

#### Scenario: Un clon limpio no necesita preparar nada a mano

- **WHEN** se levanta el entorno por primera vez, sin estado previo, y se sube una foto
- **THEN** la subida se completa
- **AND** nadie tuvo que crear el espacio de objetos

#### Scenario: Trabajar fuera del entorno queda igualmente cubierto

- **WHEN** la aplicación se ejecuta contra el almacenamiento sin haber levantado el entorno completo antes
- **THEN** el espacio de objetos queda listo igual

#### Scenario: Arrancar de nuevo no altera lo que ya está

- **WHEN** la aplicación arranca contra un almacenamiento cuyo espacio ya existe y tiene objetos
- **THEN** el arranque termina normalmente
- **AND** los objetos que había siguen estando

#### Scenario: Un espacio ausente en un proveedor externo detiene el arranque

- **WHEN** el proveedor activo es externo y su espacio de objetos no existe
- **THEN** el arranque falla con un error de dominio que identifica el problema
- **AND** la aplicación no atiende ninguna petición

#### Scenario: Quien la invoca no distingue proveedores

- **WHEN** se deja el almacenamiento listo durante el arranque
- **THEN** se lo hace a través del puerto
- **AND** el código que lo invoca es el mismo sea cual sea el proveedor activo
