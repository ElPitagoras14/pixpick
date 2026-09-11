## ADDED Requirements

### Requirement: La identidad se obtiene por una comunicación directa con el proveedor, y no se retransmite

El canje del código SHALL realizarse en una comunicación directa entre el sistema y el proveedor, cifrada y autenticada con las credenciales de la aplicación, sin que ningún intermediario participe — en particular, sin que el navegador de la persona transporte la identidad. Lo único que SHALL atravesar el navegador es el código, que por sí solo no sirve sin las credenciales de la aplicación.

La identidad SHALL tomarse únicamente de lo que llegue por esa comunicación directa, y SHALL consumirla el mismo proceso que la obtuvo. SHALL NOT reenviarse a otro componente. Si alguna vez tuviera que reenviarse, el componente que la reciba SHALL verificar por su cuenta su autenticidad antes de usarla, porque fuera de ese canal la garantía que lo respalda deja de valer.

#### Scenario: Por el navegador solo pasa el código

- **WHEN** se recorre el ciclo de autorización completo
- **THEN** lo único que el navegador transporta de vuelta es el código
- **AND** la identidad llega al sistema por la comunicación directa con el proveedor

#### Scenario: Una identidad que no vino por ese canal no se usa

- **WHEN** el sistema recibe algo que afirma ser una identidad por un camino distinto del canje directo
- **THEN** no se usa para establecer una sesión

#### Scenario: La credencial del proveedor no se propaga

- **WHEN** se inspecciona qué hace el sistema con lo que el proveedor entregó en el canje
- **THEN** lo consume el mismo proceso que lo obtuvo
- **AND** no lo envía a ningún otro componente

#### Scenario: Un canje que no se puede autenticar no produce identidad

- **WHEN** la comunicación directa con el proveedor no puede autenticarse con las credenciales de la aplicación
- **THEN** no se obtiene ninguna identidad
- **AND** no se establece ninguna sesión

### Requirement: Un proveedor que requiere configuración externa impide el arranque si no la tiene

Cuando el proveedor de identidad activo requiera credenciales o parámetros emitidos por un sistema externo, su ausencia SHALL impedir el arranque del servicio y el error SHALL nombrar qué falta. Un valor presente pero vacío SHALL tratarse igual que uno ausente. El servicio SHALL NOT arrancar en esa condición para después manifestar el problema como un inicio de sesión que falla para todas las personas.

Esta exigencia SHALL evaluarse únicamente sobre el proveedor activo: los requisitos de un proveedor que no está seleccionado SHALL NOT condicionar el arranque.

#### Scenario: Sin credenciales el servicio no arranca

- **WHEN** el proveedor activo requiere credenciales y no están configuradas
- **THEN** el arranque falla
- **AND** el error nombra las credenciales que faltan

#### Scenario: Una credencial vacía equivale a una ausente

- **WHEN** la credencial está declarada pero su valor es vacío
- **THEN** el arranque falla igual que si no estuviera declarada

#### Scenario: Los requisitos de un proveedor inactivo no estorban

- **WHEN** el proveedor activo no requiere credenciales externas y las de otro proveedor no están configuradas
- **THEN** el servicio arranca normalmente

### Requirement: La dirección de retorno se deriva de la configuración y es conocible sin adivinarla

La dirección a la que el proveedor devuelve a la persona SHALL derivarse de la dirección pública configurada del sitio, y SHALL ser observable al arrancar, de modo que pueda compararse con la que se declaró en el proveedor sin tener que deducirla del código.

El motivo es que esa dirección tiene que coincidir exactamente con la declarada en un sistema que el proyecto no controla, y una discrepancia produce un error que reporta el proveedor y que la aplicación no puede anticipar ni explicar.

#### Scenario: La dirección de retorno es observable al arrancar

- **WHEN** el servicio arranca con un proveedor que requiere una dirección de retorno declarada externamente
- **THEN** la dirección que el sistema va a usar queda registrada de forma legible
- **AND** puede compararse con la declarada en el proveedor sin inspeccionar el código

#### Scenario: La dirección de retorno cambia con la dirección pública

- **WHEN** se cambia la dirección pública configurada del sitio
- **THEN** la dirección de retorno que el sistema usa cambia en consecuencia
- **AND** no hay una segunda configuración que mantener en correspondencia
