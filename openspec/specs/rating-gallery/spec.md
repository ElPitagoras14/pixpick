# rating-gallery Specification

## Purpose

Gobierna cómo se mira un álbum calificado: qué muestra cada foto sobre la decisión de quien mira, qué filtros existen y cómo se expresan, cómo se corrige una calificación ya emitida y cómo se retoma lo que falta. No se solapa con `album-stats`, que gobierna la información agregada que solo ve el dueño, ni con `photo-rating`, que gobierna qué es una calificación y cómo se registra.

## Requirements

### Requirement: La galería muestra las fotos del álbum junto con la decisión de quien mira

Cada foto disponible del álbum SHALL presentarse acompañada de la calificación que emitió quien pide, o de la indicación de que todavía no la calificó. No haber calificado SHALL ser un estado distinguible de haber rechazado, y SHALL NOT representarse de una forma que los confunda.

#### Scenario: Cada foto viene con la decisión de quien mira

- **WHEN** un miembro pide la galería del álbum
- **THEN** cada foto trae la calificación que esa persona emitió

#### Scenario: Sin calificar se distingue de rechazada

- **WHEN** se comparan una foto que quien mira rechazó con una que todavía no calificó
- **THEN** los dos estados se distinguen entre sí
- **AND** ninguno se presenta como ausencia del otro

### Requirement: Existen cuatro filtros y los tres parciales particionan el total

La galería SHALL ofrecer cuatro filtros: todas, las aprobadas, las desaprobadas y las que quedan sin calificar. Los tres filtros parciales SHALL ser mutuamente excluyentes y su unión SHALL ser exactamente el filtro de todas: ninguna foto SHALL quedar fuera de los tres ni aparecer en dos.

#### Scenario: Cada filtro devuelve lo que nombra

- **WHEN** se pide la galería con el filtro de aprobadas
- **THEN** aparecen todas las que quien mira aprobó
- **AND** ninguna otra

#### Scenario: Los tres filtros parciales suman el total

- **WHEN** se suman las cantidades de los filtros de aprobadas, desaprobadas y sin calificar
- **THEN** el resultado es la cantidad del filtro de todas
- **AND** ninguna foto aparece en más de uno

### Requirement: El filtro de las sin calificar es el mismo conjunto que lo pendiente

El filtro de las que quedan sin calificar SHALL coincidir exactamente con lo pendiente de esa persona en ese álbum. La cantidad que muestra el contador del álbum, la cantidad de fotos de ese filtro y la cantidad de fotos que entrega la secuencia de calificación SHALL coincidir siempre, porque las tres expresan lo mismo.

#### Scenario: Las tres vistas de lo pendiente coinciden

- **WHEN** se comparan el contador del álbum, la cantidad del filtro de sin calificar y la cantidad de fotos que entrega la secuencia
- **THEN** los tres números son iguales

#### Scenario: Calificar una foto baja los tres a la vez

- **WHEN** quien mira califica una de sus fotos pendientes
- **THEN** los tres números bajan en uno

#### Scenario: Agregar fotos sube los tres a la vez

- **WHEN** el dueño agrega fotos disponibles al álbum
- **THEN** los tres números suben en la misma cantidad

### Requirement: El filtro forma parte de la dirección

El filtro seleccionado SHALL formar parte de la dirección de la galería, de modo que recargar la página lo conserve y compartir la dirección muestre la misma vista. Un filtro no reconocido SHALL resolverse como el filtro por omisión y SHALL NOT producir un error.

#### Scenario: Recargar conserva el filtro

- **WHEN** se selecciona un filtro y se recarga la página
- **THEN** la galería sigue mostrando ese filtro

#### Scenario: La dirección compartida muestra la misma vista

- **WHEN** se abre la dirección de una galería filtrada
- **THEN** se ve el mismo filtro que veía quien la compartió

#### Scenario: Un filtro desconocido cae al de omisión

- **WHEN** se abre la galería con un filtro que no existe
- **THEN** se muestra el filtro por omisión
- **AND** no se produce un error

### Requirement: La galería es de cada miembro y refleja sus propias decisiones

Todo miembro del álbum SHALL poder ver la galería, y lo que cada uno vea SHALL reflejar sus propias calificaciones. Quien no sea miembro ni dueño SHALL recibir la misma respuesta que si el álbum no existiera.

#### Scenario: Dos miembros ven filtros distintos

- **WHEN** dos miembros que calificaron distinto piden el filtro de aprobadas
- **THEN** cada uno recibe las fotos que aprobó él
- **AND** las dos respuestas difieren

#### Scenario: Quien no es miembro no ve la galería

- **WHEN** una persona autenticada que no es miembro ni dueña pide la galería
- **THEN** la respuesta es la misma que si el álbum no existiera

### Requirement: La calificación se puede cambiar desde la galería

Desde la galería SHALL poder emitirse o cambiarse la calificación de una foto, usando la misma operación que emplea la secuencia de calificación. SHALL NOT introducirse una operación distinta para el mismo efecto. El cambio SHALL reflejarse de inmediato, incluido el filtro al que la foto pertenece.

#### Scenario: Cambiar la calificación mueve la foto de filtro

- **WHEN** quien mira cambia una foto de aprobada a desaprobada
- **THEN** deja de aparecer en el filtro de aprobadas
- **AND** aparece en el de desaprobadas

#### Scenario: Calificar una pendiente la saca de las sin calificar

- **WHEN** quien mira califica desde la galería una foto que no había calificado
- **THEN** deja de aparecer entre las sin calificar
- **AND** los tres números de lo pendiente bajan en uno

#### Scenario: Es la misma operación que usa la secuencia

- **WHEN** se inspecciona cómo la galería registra una calificación
- **THEN** usa la misma operación que la secuencia de calificación

### Requirement: Desde la galería se retoma lo que falta

Cuando queden fotos sin calificar, la galería SHALL ofrecer un camino directo a la secuencia de calificación con lo pendiente. Cuando no quede ninguna, ese camino SHALL NOT ofrecerse, para no conducir a una secuencia vacía.

#### Scenario: Con pendientes se ofrece retomar

- **WHEN** quien mira tiene fotos sin calificar
- **THEN** la galería le ofrece retomar la calificación

#### Scenario: Sin pendientes no se ofrece

- **WHEN** quien mira no tiene ninguna foto sin calificar
- **THEN** la galería no ofrece retomar

### Requirement: Las fotos se presentan en el orden del álbum

En cualquier filtro, las fotos SHALL aparecer en el orden que tienen dentro del álbum. SHALL NOT reordenarse según la calificación ni según cuándo se emitió.

#### Scenario: Cada filtro conserva el orden del álbum

- **WHEN** se pide la galería con cualquiera de los cuatro filtros
- **THEN** las fotos aparecen en el orden del álbum
