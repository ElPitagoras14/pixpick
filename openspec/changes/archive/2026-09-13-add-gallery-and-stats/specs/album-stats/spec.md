## Purpose

Gobierna la información agregada sobre las calificaciones de un álbum: qué se cuenta, quién puede verla, cómo se relaciona con lo que ve un miembro común, y qué no revela. No se solapa con `rating-gallery`, que gobierna lo que cada persona ve sobre sus propias decisiones.

## ADDED Requirements

### Requirement: Las estadísticas son agregadas y no identifican a quién calificó

Las estadísticas SHALL limitarse a cantidades. SHALL NOT incluir la identidad de quienes calificaron, ni ningún dato que permita atribuir una calificación concreta a una persona concreta.

#### Scenario: La respuesta no contiene identidades

- **WHEN** el dueño pide las estadísticas de su álbum
- **THEN** la respuesta contiene cantidades
- **AND** no contiene el nombre, el correo ni el identificador de ninguna persona

#### Scenario: No se puede atribuir una calificación

- **WHEN** se inspecciona la respuesta de estadísticas
- **THEN** no permite saber qué calificó una persona determinada

### Requirement: Solo el dueño accede a las estadísticas

Las estadísticas SHALL ser accesibles únicamente para el dueño del álbum. Un miembro que no sea dueño SHALL recibir una respuesta que indique que la acción está prohibida, porque la existencia del álbum ya le consta. Quien no sea miembro ni dueño SHALL recibir la misma respuesta que si el álbum no existiera.

#### Scenario: El dueño accede

- **WHEN** el dueño pide las estadísticas de su álbum
- **THEN** las obtiene

#### Scenario: Un miembro recibe prohibido

- **WHEN** un miembro que no es dueño pide las estadísticas
- **THEN** la respuesta indica que la acción está prohibida
- **AND** no incluye ninguna cantidad

#### Scenario: Un extraño recibe inexistente

- **WHEN** una persona que no es miembro ni dueña pide las estadísticas
- **THEN** la respuesta es la misma que si el álbum no existiera

### Requirement: Cada foto disponible aparece con sus dos cantidades, aunque sean cero

Las estadísticas SHALL incluir todas las fotos disponibles del álbum, cada una con cuántas aprobaciones y cuántos rechazos acumuló. Una foto que nadie calificó SHALL aparecer con ambas cantidades en cero y SHALL NOT omitirse, porque su ausencia sería indistinguible de que no exista.

#### Scenario: Una foto sin calificaciones aparece en cero

- **WHEN** el álbum tiene una foto que nadie calificó
- **THEN** aparece en las estadísticas con cero aprobaciones y cero rechazos

#### Scenario: No falta ninguna foto disponible

- **WHEN** se comparan las fotos de las estadísticas con las fotos disponibles del álbum
- **THEN** están todas

### Requirement: Las fotos que no están disponibles no figuran en las estadísticas

Una foto cuya subida no se completó SHALL NOT aparecer en las estadísticas, del mismo modo que no aparece en ninguna otra lectura del álbum.

#### Scenario: Una subida incompleta no aparece

- **WHEN** el álbum tiene una foto cuya subida no se confirmó
- **THEN** no figura en las estadísticas

### Requirement: Las calificaciones del dueño cuentan como las de cualquier otro

El dueño es un miembro más a efectos de calificar, así que sus propias calificaciones SHALL sumarse a las cantidades de sus fotos. SHALL NOT excluirse ni contarse aparte.

#### Scenario: Calificar una foto propia mueve su cantidad

- **WHEN** el dueño aprueba una foto de su álbum y después pide las estadísticas
- **THEN** esa aprobación está incluida en la cantidad de esa foto

### Requirement: El resumen del álbum es consistente con las cantidades por foto

Las estadísticas SHALL incluir un resumen del álbum con cuántas personas emitieron al menos una calificación y cuántas calificaciones hay en total. El total SHALL coincidir con la suma de las cantidades por foto.

#### Scenario: El total coincide con la suma

- **WHEN** se suman todas las aprobaciones y rechazos de todas las fotos
- **THEN** el resultado es el total que declara el resumen

#### Scenario: El resumen dice cuántas personas participaron

- **WHEN** tres personas calificaron al menos una foto del álbum
- **THEN** el resumen indica que participaron tres

### Requirement: Las estadísticas son un recurso distinto de la galería

Las cantidades agregadas SHALL obtenerse por separado de la galería. La respuesta de la galería SHALL NOT incluirlas para nadie, ni siquiera para el dueño, de modo que la decisión de quién puede verlas quede resuelta por el recurso al que se accede y no por una condición dentro del armado de la respuesta.

#### Scenario: La galería no trae cantidades agregadas

- **WHEN** el dueño pide la galería de su álbum
- **THEN** la respuesta trae sus propias calificaciones
- **AND** no trae las cantidades agregadas

#### Scenario: El dueño obtiene las dos cosas por separado

- **WHEN** el dueño quiere ver su álbum con las cantidades
- **THEN** obtiene la galería y las estadísticas como dos respuestas distintas

### Requirement: Las estadísticas reflejan el estado al momento de pedirlas

Las cantidades SHALL corresponder al estado de las calificaciones en el momento de la consulta. SHALL NOT servirse valores calculados previamente que puedan haber quedado desactualizados.

#### Scenario: Una calificación nueva se refleja enseguida

- **WHEN** alguien califica una foto y el dueño vuelve a pedir las estadísticas
- **THEN** la cantidad de esa foto ya incluye la calificación nueva

#### Scenario: Un cambio de opinión se refleja enseguida

- **WHEN** alguien cambia una aprobación por un rechazo y el dueño vuelve a pedir las estadísticas
- **THEN** la aprobación ya no se cuenta
- **AND** el rechazo sí
