# api-conventions Specification

## Purpose

Gobierna la forma de lo que la API devuelve y la correspondencia entre cada situación y su código de estado, para que un cliente pueda tratar respuestas y errores de manera uniforme sin conocer el endpoint, y para que ninguna respuesta revele más de lo que corresponde. Rige para todos los endpoints del proyecto, no solo los que este change introduce.

## Requirements

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

### Requirement: Una operación rechazada por el estado del recurso se distingue de un error de validación

Cuando una petición esté bien formada pero no pueda completarse por el estado en que se encuentra el recurso, la respuesta SHALL indicar que el conflicto es de estado y SHALL NOT presentarse como un error de validación de un campo. La respuesta SHALL incluir la información que permita a quien pide corregir la situación, cuando esa información exista.

La distinción importa porque exige acciones distintas: un error de validación se corrige cambiando lo que se envió, mientras que un conflicto de estado se resuelve cambiando el recurso —liberando espacio, eliminando algo, esperando— y reintentando la misma petición sin modificarla.

#### Scenario: Un conflicto de estado no se confunde con validación

- **WHEN** una petición bien formada no puede completarse por el estado del recurso
- **THEN** la respuesta indica que se trata de un conflicto de estado
- **AND** no señala ningún campo de la petición como inválido

#### Scenario: La respuesta dice qué haría falta para que la operación proceda

- **WHEN** el conflicto de estado tiene una condición cuantificable
- **THEN** la respuesta incluye esa información
- **AND** quien pide puede ajustar sin adivinar

#### Scenario: Reintentar sin cambiar la petición tiene sentido

- **WHEN** se resuelve el estado que provocó el conflicto
- **THEN** la misma petición, sin modificar, se completa

### Requirement: Una petición rechazada por falta de capacidad se distingue y dice cuándo reintentar

Una petición que el sistema no puede atender por falta de capacidad SHALL responderse de una forma que la distinga tanto de un error de validación como de un fallo interno, y esa respuesta SHALL incluir cuánto conviene esperar antes de reintentar.

Las tres condiciones piden reacciones distintas de quien llama: un error de validación exige cambiar lo que se envía, un fallo interno exige reportarlo, y una falta de capacidad exige únicamente volver más tarde con lo mismo. Presentar la tercera como cualquiera de las otras dos lleva a quien llama a la reacción equivocada, y a quien opera el sistema a leer una saturación como un defecto.

La forma común de las respuestas SHALL admitir esa indicación de reintento, de modo que expresarla no requiera salirse de la estructura que comparten todas.

#### Scenario: La falta de capacidad no se confunde con un error de validación

- **WHEN** una petición bien formada se rechaza porque el sistema no tiene capacidad
- **THEN** la respuesta indica que la condición es transitoria
- **AND** no señala ningún campo como causante

#### Scenario: La falta de capacidad no se confunde con un fallo interno

- **WHEN** una petición se rechaza porque un recurso compartido está saturado
- **THEN** la respuesta la identifica como falta de capacidad
- **AND** no se presenta como un error inesperado del sistema

#### Scenario: La respuesta indica cuándo reintentar

- **WHEN** se recibe un rechazo por falta de capacidad
- **THEN** la respuesta incluye cuánto esperar antes de volver a pedir

#### Scenario: La indicación cabe en la forma común

- **WHEN** se inspecciona la estructura que comparten las respuestas de error
- **THEN** admite expresar la indicación de reintento
- **AND** no hizo falta una estructura aparte para este caso
