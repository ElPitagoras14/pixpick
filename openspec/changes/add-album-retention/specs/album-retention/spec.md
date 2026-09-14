## Purpose

Gobierna cuánto vive un álbum y qué ocurre cuando se le acaba el plazo: de dónde sale ese plazo, qué lo renueva y qué no, desde qué momento un álbum vencido deja de existir para toda lectura, y qué pasa con sus objetos y con el espacio que ocupaba. No se solapa con `album-management`, que gobierna quién ve y modifica un álbum mientras existe; aquí se define hasta cuándo existe.

## ADDED Requirements

### Requirement: Un álbum vence a un plazo declarado, contado desde su última foto

El tiempo que un álbum permanece SHALL tener un plazo declarado en la configuración del entorno. El vencimiento de un álbum SHALL calcularse desde el momento en que su última foto quedó disponible; un álbum que todavía no tiene ninguna SHALL contarlo desde su creación.

#### Scenario: Un álbum sin fotos vence a partir de su creación

- **WHEN** se crea un álbum y no se le sube ninguna foto
- **THEN** vence al cumplirse el plazo desde que fue creado

#### Scenario: La última foto corre el vencimiento

- **WHEN** una foto queda disponible en un álbum
- **THEN** el vencimiento pasa a contarse desde ese momento
- **AND** el plazo que le quedaba antes deja de aplicarse

#### Scenario: El plazo sale de la configuración

- **WHEN** se cambia el plazo declarado en el entorno
- **THEN** los vencimientos pasan a calcularse con el valor nuevo

### Requirement: Solo una foto nueva renueva el plazo

Renovar el plazo SHALL ser consecuencia únicamente de que una foto quede disponible en el álbum. SHALL NOT renovarlo calificar, compartir, revocar un enlace, renombrar el álbum, eliminar fotos ni abrirlo para verlo.

Un permiso de subida pedido y no completado SHALL NOT renovar el plazo: renueva la foto que queda disponible, no la que se pide. De lo contrario bastaría con pedir permisos que nunca se usan para mantener vivo un álbum indefinidamente.

La regla mide si el álbum sigue creciendo y no si lo están mirando: un álbum al que ya nadie le agrega fotos terminó su ciclo, aunque todavía se lo esté recorriendo. La consecuencia aceptada es que un álbum compartido que varias personas están calificando vence igual si nadie sube nada nuevo.

#### Scenario: Calificar no renueva el plazo

- **WHEN** varias personas califican las fotos de un álbum durante días
- **THEN** su vencimiento sigue siendo el mismo que antes de esas calificaciones

#### Scenario: Compartir o renombrar no renueva el plazo

- **WHEN** se genera un enlace, se revoca, o se cambia el título o la descripción del álbum
- **THEN** su vencimiento no cambia

#### Scenario: Un permiso no completado no renueva el plazo

- **WHEN** se pide permiso para subir una foto y el permiso vence sin que el archivo se haya subido
- **THEN** el vencimiento del álbum es el mismo que antes de pedirlo

#### Scenario: Eliminar fotos no adelanta ni corre el plazo

- **WHEN** se eliminan fotos de un álbum, incluida la última que se subió
- **THEN** su vencimiento sigue siendo el que ya tenía

### Requirement: Un álbum vencido deja de existir para toda lectura

Desde el momento en que un álbum vence, SHALL dejar de estar disponible en toda lectura: para su dueño, para quien es miembro, y para quien resuelve su enlace compartido. La respuesta SHALL ser indistinguible de la de un álbum que nunca existió, igual que hoy ocurre con uno eliminado a mano.

Dejar de existir SHALL NOT depender de que ningún proceso de limpieza haya corrido. Un álbum cuyo plazo se cumplió hace un minuto ya no está disponible, aunque sus filas y sus objetos todavía existan.

#### Scenario: El dueño deja de ver un álbum vencido

- **WHEN** el dueño lista sus álbumes después de que uno venció
- **THEN** ese álbum no aparece
- **AND** pedirlo directamente responde como si no existiera

#### Scenario: Un enlace compartido hacia un álbum vencido no resuelve

- **WHEN** alguien abre el enlace de un álbum que ya venció
- **THEN** no obtiene acceso
- **AND** la respuesta no revela que ese álbum existió

#### Scenario: No hace falta que corra ninguna limpieza

- **WHEN** un álbum vence y nadie ejecuta ningún proceso de mantenimiento
- **THEN** deja de estar disponible igual, desde el momento del vencimiento

#### Scenario: Subir a un álbum vencido no es posible

- **WHEN** se piden permisos de subida para un álbum que venció
- **THEN** la respuesta es la de un álbum que no existe

### Requirement: El vencimiento libera el espacio de la cuenta en el acto

Desde el momento del vencimiento, las fotos de un álbum vencido SHALL dejar de contar para el espacio ocupado de la cuenta de su dueño, aunque sus objetos todavía no se hayan eliminado del almacenamiento. Seguir midiendo contra el límite algo que su dueño ya no puede ver sería penalizarlo por un detalle de implementación.

#### Scenario: Un álbum que vence devuelve su espacio

- **WHEN** vence un álbum de una cuenta que estaba en su límite
- **THEN** el consumo de esa cuenta ya no incluye las fotos de ese álbum
- **AND** se puede volver a subir por el espacio liberado

### Requirement: Los objetos de un álbum vencido se eliminan del almacenamiento

Las fotos de un álbum vencido SHALL eliminarse del almacenamiento, igual que cuando alguien elimina un álbum a mano. SHALL NOT quedar indefinidamente objetos de álbumes vencidos.

Esa eliminación SHALL poder ocurrir después del momento del vencimiento, y la demora SHALL NOT tener ningún efecto observable: lo único que un objeto todavía no eliminado consume es espacio en el proveedor, nunca visibilidad ni espacio de la cuenta.

#### Scenario: Los objetos terminan eliminados

- **WHEN** se completa la eliminación de lo vencido
- **THEN** no queda en el almacenamiento ningún objeto de álbumes vencidos

#### Scenario: La demora en eliminar no cambia lo que se ve

- **WHEN** un álbum venció y sus objetos todavía no se eliminaron
- **THEN** nadie puede ver el álbum ni sus fotos
- **AND** su espacio ya no cuenta para la cuenta de su dueño

### Requirement: Mientras el álbum esté vigente, se puede saber cuánto le queda

Un álbum vigente SHALL informar cuándo vence, y esa información SHALL estar disponible tanto para su dueño como para quien accede a él por un enlace compartido. No es información sensible y le sirve a las dos partes: a quien decide si subir más fotos, y a quien tiene que terminar de calificar antes de que el álbum desaparezca.

#### Scenario: El dueño ve el plazo restante de cada álbum

- **WHEN** el dueño lista sus álbumes
- **THEN** cada uno indica cuándo vence

#### Scenario: Quien califica también ve el plazo

- **WHEN** alguien accede a un álbum compartido
- **THEN** también puede saber cuándo vence ese álbum

#### Scenario: Subir una foto corre el plazo a la vista

- **WHEN** se sube una foto a un álbum y queda disponible
- **THEN** el plazo que se muestra pasa a reflejar el vencimiento nuevo
