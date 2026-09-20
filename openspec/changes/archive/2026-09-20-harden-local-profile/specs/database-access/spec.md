## ADDED Requirements

### Requirement: Toda consulta y toda espera de lock tienen un techo de tiempo

El acceso a la base SHALL declarar un techo de duración por sentencia, un techo de espera para adquirir un lock y un techo para una transacción que quedó abierta sin actividad. SHALL NOT quedar librados a que la base no imponga ninguno.

Una sola consulta sin techo retiene su conexión indefinidamente, y como el pool tiene un máximo declarado, suficientes consultas lentas simultáneas dejan al servicio sin conexiones para nada más. El caso concreto que lo hace alcanzable es la suma del consumo de la instancia, que recorre la tabla entera y corre bajo un lock global tomado en cada concesión: a medida que la tabla crece, la ventana durante la que ese lock está tomado crece con ella.

#### Scenario: Una consulta que se pasa del techo se interrumpe

- **WHEN** una consulta supera el techo de duración declarado
- **THEN** se interrumpe
- **AND** la conexión queda liberada

#### Scenario: Esperar un lock no es indefinido

- **WHEN** una operación espera un lock por más del techo declarado
- **THEN** la espera termina con un error en lugar de continuar

#### Scenario: Los techos están declarados

- **WHEN** se inspecciona la construcción del acceso a la base
- **THEN** el techo por sentencia, el de espera de lock y el de transacción inactiva están declarados

### Requirement: La conexión se toma después de autorizar la petición

Una petición SHALL obtener su conexión a la base recién después de haberse resuelto que está autorizada a ejecutarse. SHALL NOT tomarse una conexión para después descubrir que la petición no tenía sesión, o que fue rechazada por carga.

De lo contrario el recurso más escaso del servicio queda al alcance de cualquiera sin credenciales: bastan tantas peticiones sin sesión como conexiones tenga el pool para dejar al resto esperando.

#### Scenario: Una petición sin sesión no consume conexión

- **WHEN** llega una petición sin sesión a un recurso que la requiere
- **THEN** se rechaza sin haber tomado una conexión

#### Scenario: Una petición rechazada por carga no consume conexión

- **WHEN** una petición se rechaza por superar el techo de peticiones
- **THEN** se rechaza sin haber tomado una conexión

#### Scenario: Un flujo de peticiones sin sesión no agota el pool

- **WHEN** llegan simultáneamente más peticiones sin sesión que conexiones tiene el pool
- **THEN** las peticiones autenticadas que llegan al mismo tiempo se siguen atendiendo
