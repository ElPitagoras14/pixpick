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
