## ADDED Requirements

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
