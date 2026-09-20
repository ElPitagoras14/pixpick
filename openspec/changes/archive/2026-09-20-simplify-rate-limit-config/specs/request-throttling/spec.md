## REMOVED Requirements

### Requirement: La cantidad de peticiones que un cliente puede hacer tiene un techo configurable

**Reason**: el techo nunca varió por despliegue en la práctica, y el único uso real del interruptor de desactivación era ejercitar el sistema en desarrollo y en la suite de pruebas sin tropezar con un límite pensado para tráfico real.

**Migration**: ver el nuevo requirement "La cantidad de peticiones que un cliente puede hacer tiene un techo fijo" — el techo sigue existiendo, con los mismos valores, pero ya no se declara por configuración ni se puede desactivar. Quien necesite un valor distinto en desarrollo edita la constante en `nginx/nginx.conf.template` en vez de una variable de entorno.

## ADDED Requirements

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
