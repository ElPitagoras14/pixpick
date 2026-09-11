## ADDED Requirements

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
