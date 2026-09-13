## ADDED Requirements

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
