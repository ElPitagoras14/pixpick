# identity-provider Specification

## Purpose

Gobierna cómo el sistema obtiene la identidad de una persona desde un proveedor externo: qué ciclo se recorre, qué se le exige a un proveedor para ser intercambiable con otro, cómo se elige el proveedor activo, y cómo una identidad externa se corresponde con un usuario del sistema. No se solapa con `session-management`, que gobierna qué pasa después de que la identidad quedó establecida.

## Requirements

### Requirement: Un solo proveedor está activo y se elige por configuración

El proveedor de identidad activo SHALL declararse en la configuración del entorno. Un valor no reconocido SHALL impedir el arranque del servicio, y SHALL NOT manifestarse como un fallo en el primer intento de inicio de sesión. El código que consume la identidad SHALL NOT ramificar según cuál sea el proveedor activo.

#### Scenario: Un proveedor desconocido impide el arranque

- **WHEN** el entorno declara un proveedor de identidad que el sistema no reconoce
- **THEN** el arranque falla
- **AND** el error nombra la configuración y los valores admitidos

#### Scenario: La aplicación no sabe cuál proveedor está activo

- **WHEN** se inspecciona el código que obtiene la identidad de una persona
- **THEN** no contiene condicionales según el proveedor
- **AND** consume una única interfaz

### Requirement: Todo proveedor expone el mismo ciclo de autorización

Un proveedor SHALL ofrecer dos operaciones: producir la dirección a la que se envía a la persona para que se autentique, y canjear el código que llega en el retorno por una identidad. Cambiar el proveedor activo SHALL NOT alterar los endpoints del sistema ni la secuencia observable de inicio de sesión.

#### Scenario: Iniciar sesión envía a la persona al proveedor

- **WHEN** alguien inicia sesión
- **THEN** el sistema lo redirige a una dirección que el proveedor determinó

#### Scenario: El retorno trae un código que se canjea

- **WHEN** la persona vuelve del proveedor
- **THEN** el retorno incluye un código
- **AND** el sistema lo canjea por una identidad sin intervención de la persona

#### Scenario: Cambiar de proveedor no cambia el flujo observable

- **WHEN** se cambia el proveedor activo y se inicia sesión otra vez
- **THEN** los endpoints involucrados son los mismos
- **AND** la secuencia de redirecciones tiene la misma forma

### Requirement: La identidad que un proveedor entrega tiene una forma fija

La identidad SHALL incluir el proveedor del que proviene y el identificador que ese proveedor asigna a la persona, y ambos SHALL estar siempre presentes. Los datos descriptivos —correo, nombre e imagen— SHALL admitirse ausentes, porque no todo proveedor los entrega, y su ausencia SHALL NOT impedir el inicio de sesión.

#### Scenario: El proveedor y el identificador de la persona siempre están

- **WHEN** un proveedor entrega una identidad
- **THEN** incluye de qué proveedor proviene
- **AND** incluye el identificador que ese proveedor asigna a la persona

#### Scenario: Un dato descriptivo ausente no impide entrar

- **WHEN** el proveedor no entrega imagen de la persona
- **THEN** el inicio de sesión se completa igual

### Requirement: La persona se identifica por el proveedor y su identificador, nunca por el correo

La correspondencia entre una identidad externa y un usuario del sistema SHALL establecerse por el par formado por el proveedor y el identificador que ese proveedor asigna. El correo SHALL tratarse como un dato descriptivo y SHALL NOT usarse para reconocer a una persona ni imponerse como único entre usuarios.

#### Scenario: La misma persona que vuelve es el mismo usuario

- **WHEN** una persona que ya entró antes vuelve a iniciar sesión con el mismo proveedor
- **THEN** el sistema la reconoce como el mismo usuario
- **AND** no se crea un usuario nuevo

#### Scenario: Un correo que cambió no crea un usuario nuevo

- **WHEN** una persona vuelve a entrar y su correo en el proveedor cambió
- **THEN** sigue siendo el mismo usuario
- **AND** el correo registrado queda actualizado

#### Scenario: El mismo correo en dos proveedores son dos usuarios

- **WHEN** dos identidades de proveedores distintos declaran el mismo correo
- **THEN** el sistema las trata como dos usuarios distintos
- **AND** ninguna impide la creación de la otra

### Requirement: Los datos descriptivos se refrescan en cada inicio de sesión

El nombre, el correo y la imagen que el proveedor entrega SHALL actualizarse cada vez que la persona inicia sesión, porque son datos que cambian en el proveedor y este sistema no es su fuente de verdad.

#### Scenario: Un nombre cambiado se refleja al volver a entrar

- **WHEN** una persona cambia su nombre en el proveedor y vuelve a iniciar sesión
- **THEN** el sistema muestra el nombre nuevo

### Requirement: El retorno del proveedor se rechaza si no corresponde a un inicio que el sistema emitió

Cada inicio de sesión SHALL emitir un valor impredecible que acompañe al ciclo de autorización, y el retorno SHALL rechazarse si no presenta ese mismo valor. Un valor ya usado SHALL NOT volver a aceptarse.

#### Scenario: Un retorno sin correspondencia se rechaza

- **WHEN** llega un retorno cuyo valor de correspondencia no coincide con ninguno que el sistema emitió
- **THEN** el retorno se rechaza
- **AND** no se establece ninguna sesión

#### Scenario: Un valor de correspondencia no se reutiliza

- **WHEN** se presenta por segunda vez un retorno con un valor que ya se consumió
- **THEN** el segundo se rechaza

### Requirement: El destino de retorno se conserva y se valida como ruta del propio sitio

Cuando alguien llegue sin sesión a una ubicación que la requiere, esa ubicación SHALL conservarse y SHALL ser el destino al que se lo envíe después de autenticarse. El destino SHALL validarse como una ruta del propio sitio: SHALL NOT aceptarse una dirección hacia otro sitio ni un esquema distinto, y en ese caso SHALL usarse el destino por omisión.

#### Scenario: Volver a donde se quería llegar

- **WHEN** alguien sin sesión abre una ubicación que requiere sesión y luego se autentica
- **THEN** termina en esa misma ubicación

#### Scenario: Un destino hacia otro sitio se descarta

- **WHEN** el destino conservado apunta a un sitio distinto de este
- **THEN** se descarta
- **AND** la persona termina en el destino por omisión

#### Scenario: Sin destino conservado se usa el de omisión

- **WHEN** alguien se autentica sin que hubiera un destino conservado
- **THEN** termina en el destino por omisión

### Requirement: Un fallo del proveedor no deja rastro

Si el canje del código falla o el proveedor devuelve un error, SHALL NOT crearse ninguna sesión ni ningún usuario. La persona SHALL recibir un error que le permita volver a intentar.

#### Scenario: Un canje fallido no crea nada

- **WHEN** el canje del código falla
- **THEN** no se establece sesión
- **AND** no se crea ningún usuario
- **AND** la persona puede volver a intentar iniciar sesión

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
