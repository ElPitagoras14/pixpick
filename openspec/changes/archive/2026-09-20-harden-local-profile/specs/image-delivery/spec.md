## ADDED Requirements

### Requirement: La dirección de una variante apunta al almacenamiento activo, y una combinación incoherente no arranca

La dirección de una variante SHALL identificar el original en el almacenamiento que está activo. SHALL NOT quedar fijada a un proveedor concreto mientras la aplicación opera contra otro.

Cuando la combinación de proveedor de almacenamiento y proveedor de imágenes seleccionada no pueda producir variantes —porque el transformador no alcanza el almacenamiento donde viven los originales— el arranque SHALL fallar nombrando la incompatibilidad. SHALL NOT arrancar y descubrirlo recién cuando alguien pida una imagen: cada puerto valida hoy solo el grupo de credenciales del proveedor que él mismo selecciona, así que una combinación imposible pasa las dos validaciones por separado y deja el sistema sirviendo direcciones que no resuelven.

#### Scenario: La dirección nombra el almacenamiento activo

- **WHEN** se construye la dirección de una variante
- **THEN** el original que identifica es el del almacenamiento activo

#### Scenario: Una combinación incompatible detiene el arranque

- **WHEN** se selecciona una combinación de proveedores en la que el transformador no puede leer los originales
- **THEN** el arranque falla nombrando la incompatibilidad
- **AND** la aplicación no atiende ninguna petición

#### Scenario: Cada combinación admitida queda comprobada

- **WHEN** se ejecuta la suite de pruebas
- **THEN** cada combinación de proveedores que el proyecto declara admitida queda ejercitada
- **AND** cada combinación que no admite falla el arranque de forma comprobada

### Requirement: El transformador declara qué está dispuesto a procesar y desde dónde

El transformador SHALL declarar techos explícitos para lo que acepta procesar —al menos el tamaño y la resolución del original, y la dimensión del resultado— y SHALL declarar desde qué espacio del almacenamiento admite leer. Un original o un resultado por encima de un techo SHALL rechazarse sin procesarse.

Producir una variante cuesta CPU y memoria del propio entorno, y una dirección válida se construye para cualquier original del almacenamiento: sin estos techos, alcanzar el transformador es alcanzar un recurso sin fondo, y el alcance de una firma filtrada es todo el almacenamiento en lugar del espacio donde viven las fotos.

#### Scenario: Un original demasiado grande se rechaza

- **WHEN** se pide una variante de un original que supera el techo declarado
- **THEN** la petición se rechaza sin producir la variante

#### Scenario: Leer fuera del espacio declarado se rechaza

- **WHEN** se pide una variante de un objeto que está fuera del espacio desde el que el transformador admite leer
- **THEN** la petición se rechaza

#### Scenario: Los techos están declarados y no son los del producto

- **WHEN** se inspecciona la configuración del transformador
- **THEN** cada techo está declarado explícitamente
- **AND** ninguno queda librado al valor por omisión del producto
