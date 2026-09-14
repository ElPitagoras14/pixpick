## ADDED Requirements

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
