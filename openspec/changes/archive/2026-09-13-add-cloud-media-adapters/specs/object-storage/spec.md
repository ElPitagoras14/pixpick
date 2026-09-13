## REMOVED Requirements

### Requirement: La concesión de subida está acotada en objeto, tiempo, tamaño y tipo

Reemplazada por "La concesión de subida está acotada en objeto, tiempo y tipo, y el tamaño se verifica al confirmar" (D9 en este change): ningún esquema de firma por URL puede expresar un rango de tamaño de forma portable entre proveedores, así que esa comprobación deja de ser parte de la concesión.

## ADDED Requirements

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
