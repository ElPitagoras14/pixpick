# request-throttling Specification

## Purpose
Gobierna cuánta carga admite la instancia por cliente y qué hace cuando no puede admitir más: el techo de peticiones, en qué punto del ciclo de una petición se aplica, cómo se identifica al cliente cuando hay un proxy delante, y cómo se distingue una petición rechazada por carga de una rechazada por su contenido. No se solapa con `account-quota` ni `instance-quota`, que gobiernan cuánto espacio se puede ocupar y no a qué ritmo se puede pedir.

## Requirements

### Requirement: La cantidad de peticiones que un cliente puede hacer tiene un techo fijo

El sistema SHALL limitar cuántas peticiones admite de un mismo cliente por unidad de tiempo, con un techo fijo en el código y no declarado en la configuración del entorno: ningún despliegue de este proyecto ha necesitado un valor distinto del otro. SHALL existir un techo general y un techo propio, más estricto, para las operaciones que consumen recursos del almacenamiento o del transformador. Superar un techo SHALL rechazar la petición sin ejecutarla.

El límite SHALL estar siempre activo. SHALL NOT existir una forma de desactivarlo por configuración: quien necesite ejercitar el sistema sin él edita el valor fijo en el código en vez de apagarlo por una variable de entorno.

#### Scenario: Un cliente por debajo del techo no se ve afectado

- **WHEN** un cliente hace peticiones a un ritmo menor que el techo
- **THEN** todas se atienden normalmente

#### Scenario: Superar el techo rechaza la petición

- **WHEN** un cliente supera el techo de peticiones declarado
- **THEN** la petición se rechaza sin ejecutarse
- **AND** la respuesta indica que el motivo es la carga y no el contenido de la petición

#### Scenario: Conceder subidas tiene su propio techo

- **WHEN** un cliente pide concesiones de subida a un ritmo que respeta el techo general pero supera el propio de esa operación
- **THEN** la petición se rechaza
- **AND** las peticiones de otro tipo del mismo cliente siguen atendiéndose

### Requirement: El límite se aplica antes de tomar cualquier recurso escaso

El rechazo por carga SHALL decidirse antes de que la petición tome una conexión a la base de datos y antes de que se resuelva la sesión. Una petición rechazada por carga SHALL NOT haber consumido ninguno de los recursos que el límite existe para proteger.

#### Scenario: Una petición rechazada no toma conexión

- **WHEN** una petición se rechaza por superar el techo
- **THEN** no llegó a tomar una conexión a la base de datos

#### Scenario: El límite alcanza a las peticiones sin sesión

- **WHEN** un cliente sin sesión supera el techo pidiendo un recurso que requiere sesión
- **THEN** la petición se rechaza por carga
- **AND** el rechazo ocurre sin haber consultado la sesión

### Requirement: El cliente se identifica por su dirección real y no por la del proxy

Cuando el tráfico llegue a través de un proxy, el sistema SHALL identificar al cliente por la dirección que el proxy declara y no por la del proxy mismo. SHALL declararse explícitamente de qué proxies se acepta esa declaración, y una dirección declarada por un origen no declarado SHALL ignorarse.

Sin esta identificación un límite por cliente agrupa a todo internet en un solo cliente, de modo que la identificación SHALL estar resuelta en cualquier despliegue que aplique un límite.

#### Scenario: Dos clientes detrás del mismo proxy se cuentan por separado

- **WHEN** dos clientes distintos hacen peticiones a través del mismo proxy
- **THEN** cada uno consume su propio cupo
- **AND** el consumo de uno no rechaza las peticiones del otro

#### Scenario: Una dirección declarada por un origen no confiable se ignora

- **WHEN** una petición llega desde un origen no declarado afirmando venir de otra dirección
- **THEN** esa afirmación no se usa para identificar al cliente

#### Scenario: Lo que se registra es la dirección real

- **WHEN** se revisa el registro de una petición atendida
- **THEN** la dirección que figura es la del cliente y no la del proxy

### Requirement: Una instancia sin capacidad lo dice y sugiere cuándo volver

Cuando el sistema no pueda atender una petición por falta de capacidad —el techo de peticiones, el agotamiento del pool de conexiones o cualquier otro recurso compartido saturado— la respuesta SHALL indicar que se trata de una condición transitoria y SHALL incluir cuánto conviene esperar antes de reintentar. SHALL NOT presentarse como un fallo interno ni como un error de validación, porque las tres condiciones piden reacciones distintas de quien llama.

#### Scenario: El agotamiento del pool se presenta como falta de capacidad

- **WHEN** una petición no consigue conexión a la base porque el pool está agotado
- **THEN** la respuesta indica una condición transitoria
- **AND** no se presenta como un fallo interno

#### Scenario: La respuesta dice cuándo reintentar

- **WHEN** una petición se rechaza por falta de capacidad
- **THEN** la respuesta incluye cuánto esperar antes de reintentar

#### Scenario: La interfaz distingue esperar de fallar

- **WHEN** la interfaz recibe un rechazo por falta de capacidad
- **THEN** informa que el sistema está ocupado y que conviene reintentar
- **AND** no lo presenta como un error del contenido que se envió
