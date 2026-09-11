## Purpose

Gobierna la forma de lo que la API devuelve y la correspondencia entre cada situación y su código de estado, para que un cliente pueda tratar respuestas y errores de manera uniforme sin conocer el endpoint, y para que ninguna respuesta revele más de lo que corresponde. Rige para todos los endpoints del proyecto, no solo los que este change introduce.

## ADDED Requirements

### Requirement: Todas las respuestas comparten una misma forma

Los cuerpos que la API devuelve SHALL compartir una estructura común que permita distinguir un resultado satisfactorio de un error sin conocer de antemano el endpoint. SHALL NOT haber endpoints que devuelvan una forma propia.

#### Scenario: Dos endpoints devuelven la misma estructura

- **WHEN** se comparan las respuestas de dos endpoints distintos
- **THEN** comparten la misma estructura externa

#### Scenario: Un cliente distingue éxito de error sin conocer el endpoint

- **WHEN** un cliente recibe una respuesta de un endpoint que no conoce
- **THEN** puede determinar si fue satisfactoria o un error a partir de la estructura

### Requirement: Los campos que llegan al cliente usan una sola convención de nombres

Los nombres de campo de los cuerpos SHALL seguir una única convención en toda la API, y SHALL ser la propia del cliente y no la del esquema de la base. La nomenclatura interna SHALL NOT filtrarse hacia afuera.

#### Scenario: La convención es la misma en todas las respuestas

- **WHEN** se comparan los nombres de campo de dos respuestas distintas
- **THEN** ambas siguen la misma convención

#### Scenario: La nomenclatura del esquema no se filtra

- **WHEN** se comparan los nombres de campo de una respuesta con los de la tabla que los originó
- **THEN** la respuesta usa su propia convención

### Requirement: Falta de sesión y falta de permiso se distinguen entre sí

Pedir algo sin una sesión válida SHALL responderse como no autenticado, y pedir algo con una sesión válida pero sin autorización sobre ese recurso SHALL responderse como prohibido. Son situaciones distintas porque exigen acciones distintas de quien pide: en un caso iniciar sesión, en el otro no insistir.

#### Scenario: Sin sesión, no autenticado

- **WHEN** se pide un recurso que requiere sesión sin presentar una válida
- **THEN** la respuesta indica que falta autenticación

#### Scenario: Con sesión pero sin autorización, prohibido

- **WHEN** alguien con sesión válida pide un recurso al que no está autorizado, y su existencia ya le consta
- **THEN** la respuesta indica que la acción está prohibida

### Requirement: Cuando conocer la existencia es en sí una filtración, no existir y no tener acceso se responden igual

Para los recursos a los que se llega por un identificador opaco que funciona como credencial, un recurso que existe pero al que quien pide no tiene acceso SHALL responderse exactamente igual que uno inexistente. La respuesta SHALL NOT permitir inferir cuál de las dos situaciones ocurrió.

#### Scenario: Existente sin acceso y inexistente son indistinguibles

- **WHEN** se pide, con un identificador opaco, un recurso que existe pero al que quien pide no tiene acceso
- **AND** se pide otro con un identificador que no corresponde a nada
- **THEN** las dos respuestas son iguales

#### Scenario: La respuesta no delata la existencia

- **WHEN** alguien prueba identificadores opacos al azar
- **THEN** ninguna respuesta le permite distinguir un identificador válido de uno inválido

### Requirement: Un error de validación indica qué campo lo causó

Cuando el cuerpo o los parámetros de una petición no cumplan lo que el endpoint espera, la respuesta SHALL indicar qué campo lo provocó y por qué, de forma que el cliente pueda corregir sin adivinar.

#### Scenario: La respuesta nombra el campo inválido

- **WHEN** se envía una petición con un campo que no cumple lo esperado
- **THEN** la respuesta nombra ese campo
- **AND** describe qué se esperaba

### Requirement: Ninguna respuesta de error revela el interior del sistema

Las respuestas de error SHALL NOT contener trazas de ejecución, texto de consultas, nombres de tablas o columnas, rutas de archivos ni mensajes originados en dependencias. Un fallo inesperado SHALL responderse con un mensaje genérico acompañado de un identificador que permita encontrar el detalle en los registros del servidor.

#### Scenario: Un fallo inesperado no expone detalle

- **WHEN** ocurre un fallo que el sistema no previó
- **THEN** la respuesta es genérica
- **AND** incluye un identificador que permite localizar el detalle en los registros

#### Scenario: La respuesta no contiene rastros internos

- **WHEN** se inspecciona el cuerpo de cualquier respuesta de error
- **THEN** no contiene trazas, consultas, nombres de tablas ni rutas de archivos
