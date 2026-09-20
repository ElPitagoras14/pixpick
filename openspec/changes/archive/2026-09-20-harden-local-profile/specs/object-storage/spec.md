## MODIFIED Requirements

### Requirement: La concesión de subida está acotada en objeto, tiempo y tipo, y el tamaño se verifica al confirmar

Una concesión SHALL habilitar la escritura de un único objeto, SHALL vencer, y SHALL declarar el tipo de contenido admitido. El tamaño declarado SHALL validarse antes de emitir la concesión -- SHALL exigirse un valor positivo y por debajo del máximo, porque un valor que no lo sea no describe ningún archivo posible y, al restarse de lo disponible, agranda el espacio libre en lugar de consumirlo. El tamaño real del objeto SHALL verificarse contra lo declarado una vez subido.

Ninguna de las dos comprobaciones SHALL depender de que el almacenamiento la imponga al recibir, porque ningún esquema de firma por URL puede expresar un rango de tamaño de forma portable entre proveedores. Cuando el despliegue interponga un punto de entrada entre el navegador y el almacenamiento, ese punto SHALL acotar además el tamaño del cuerpo que acepta, de modo que lo efectivamente escrito quede acotado y no solo lo declarado; esa cota SHALL derivarse del mismo máximo que valida la concesión, para que las dos no puedan divergir.

#### Scenario: Un tamaño declarado por encima del límite se rechaza antes de conceder

- **WHEN** se pide una concesión para un archivo cuyo tamaño declarado excede el límite
- **THEN** no se emite la concesión

#### Scenario: Un tamaño declarado que no es positivo se rechaza antes de conceder

- **WHEN** se pide una concesión declarando un tamaño de cero o negativo
- **THEN** no se emite la concesión
- **AND** el espacio disponible de la cuenta y el de la instancia quedan como estaban

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

#### Scenario: Escribir más de lo permitido se corta en el punto de entrada

- **WHEN** el navegador escribe a través del punto de entrada un cuerpo mayor que el máximo admitido
- **THEN** la escritura se rechaza ahí
- **AND** el objeto no llega al almacenamiento

### Requirement: Eliminar objetos admite varios a la vez y es idempotente

La eliminación SHALL aceptar varios objetos en una sola operación, y eliminar algo que no existe SHALL NOT ser un error.

La cantidad de objetos que se le pida eliminar SHALL NOT estar acotada por quien la invoca: cuando supere lo que el protocolo del proveedor admite en una sola petición, el puerto SHALL repartirla en las peticiones que hagan falta. Dejar que el exceso llegue al proveedor haría fallar la operación entera, y quien la invoca -- la limpieza periódica y la eliminación de un álbum -- no tiene forma de conocer ese tope sin saber qué proveedor está activo.

#### Scenario: Eliminar lo que no existe no falla

- **WHEN** se elimina un objeto que no está
- **THEN** la operación termina satisfactoriamente

#### Scenario: Varios objetos se eliminan juntos

- **WHEN** se eliminan varios objetos
- **THEN** una sola operación los cubre

#### Scenario: Una cantidad mayor que la que el proveedor admite se reparte

- **WHEN** se pide eliminar más objetos de los que el proveedor acepta en una petición
- **THEN** todos quedan eliminados
- **AND** quien lo pidió no tuvo que repartirlos
