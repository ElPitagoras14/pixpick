# session-management Specification

## Purpose

Gobierna la sesión: cómo se establece una vez que la identidad quedó establecida, cómo se transporta entre el navegador y la API, cómo se valida en cada petición, cómo se termina, y cómo el usuario autenticado llega al código que lo necesita. No se solapa con `identity-provider`, que gobierna cómo se averigua quién es la persona.

## Requirements

### Requirement: La sesión se transporta en una cookie inaccesible al script de la página

El identificador de sesión SHALL viajar en una cookie que el navegador no exponga al código de la página, y SHALL acompañar automáticamente a las peticiones al mismo origen. SHALL NOT guardarse en ningún almacenamiento que el script pueda leer, ni exigirle al cliente que la administre.

#### Scenario: El script de la página no puede leer la sesión

- **WHEN** el código que corre en la página intenta leer el valor de sesión
- **THEN** no lo obtiene

#### Scenario: Las peticiones la incluyen sin administrarla

- **WHEN** la interfaz hace una petición a la API
- **THEN** la sesión viaja con la petición
- **AND** el código de la interfaz no tuvo que adjuntarla

### Requirement: Lo que se almacena es el hash del identificador de sesión

El sistema SHALL almacenar únicamente un resumen criptográfico del identificador de sesión. SHALL NOT almacenarse el valor que viaja en la cookie, de modo que el acceso al almacenamiento no permita suplantar a nadie.

#### Scenario: El almacenamiento no contiene sesiones utilizables

- **WHEN** se inspecciona lo que el sistema guardó sobre las sesiones activas
- **THEN** ningún valor almacenado sirve como cookie de sesión

### Requirement: El identificador de sesión es impredecible

El identificador SHALL generarse con una fuente aleatoria apta para uso criptográfico y con longitud suficiente para que no pueda adivinarse. SHALL NOT derivarse del identificador del usuario, de un contador, del momento de creación ni de ningún dato conocible.

#### Scenario: Dos sesiones no guardan relación aparente

- **WHEN** se comparan los identificadores de dos sesiones creadas una tras otra
- **THEN** no se observa relación entre ellos

#### Scenario: El identificador no se deriva de datos conocidos

- **WHEN** se inspecciona cómo se genera el identificador
- **THEN** no participa ningún dato del usuario ni del momento de creación

### Requirement: Una sesión vence y una sesión vencida no autentica

Toda sesión SHALL tener un momento de vencimiento. Presentar una sesión vencida SHALL tratarse igual que no presentar ninguna, aunque su registro siga existiendo. La cookie SHALL dejar de estar vigente a más tardar cuando la sesión venza, para que no quede una cookie viva apuntando a una sesión muerta.

#### Scenario: Una sesión vencida no autentica

- **WHEN** se presenta una sesión cuyo vencimiento ya pasó
- **THEN** la petición se trata como no autenticada

#### Scenario: La cookie no sobrevive a la sesión

- **WHEN** se compara la vigencia de la cookie con el vencimiento de la sesión
- **THEN** la cookie no sigue vigente después de que la sesión venció

### Requirement: Cerrar sesión termina la sesión del lado del servidor

Cerrar sesión SHALL eliminar el registro de esa sesión, y SHALL NOT limitarse a borrar la cookie del navegador. Las demás sesiones del mismo usuario SHALL permanecer activas.

#### Scenario: La cookie anterior deja de servir

- **WHEN** alguien cierra sesión y luego presenta la misma cookie
- **THEN** la petición se trata como no autenticada

#### Scenario: Cerrar una sesión no afecta a las otras

- **WHEN** un usuario con sesión en dos navegadores cierra sesión en uno
- **THEN** la sesión del otro sigue activa

### Requirement: El usuario autenticado llega al código como una dependencia declarada

Un endpoint que requiera sesión SHALL declararlo de forma explícita y recibir el usuario autenticado como parámetro. SHALL NOT obtenerse de un estado global ni de un contexto implícito, y sin una sesión válida el endpoint SHALL NOT ejecutarse.

#### Scenario: La necesidad de sesión se ve en la firma

- **WHEN** se lee un endpoint que requiere sesión
- **THEN** la necesidad está declarada en su firma
- **AND** el usuario autenticado llega como parámetro

#### Scenario: Sin sesión válida el endpoint no corre

- **WHEN** se pide un endpoint que requiere sesión sin presentar una válida
- **THEN** el código del endpoint no se ejecuta

### Requirement: La identidad actual se puede consultar

El sistema SHALL ofrecer una forma de obtener la identidad asociada a la sesión vigente. La respuesta SHALL incluir los datos descriptivos de la persona y SHALL NOT incluir el identificador de sesión ni su hash.

#### Scenario: Con sesión se obtiene la identidad

- **WHEN** se consulta la identidad actual presentando una sesión válida
- **THEN** la respuesta describe a la persona autenticada
- **AND** no contiene el identificador de sesión ni su hash

#### Scenario: Sin sesión no hay identidad

- **WHEN** se consulta la identidad actual sin presentar una sesión válida
- **THEN** la respuesta indica que no hay autenticación
