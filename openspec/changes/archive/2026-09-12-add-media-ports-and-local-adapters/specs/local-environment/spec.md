## MODIFIED Requirements

### Requirement: Todo el tráfico de la aplicación entra por un único punto

La interfaz y la API SHALL servirse desde el mismo origen a través de un único punto de entrada. SHALL NOT existir un origen distinto por servicio propio del proyecto, para que el navegador no distinga entre pedir la interfaz y pedir cualquier otra cosa de la aplicación.

El punto de entrada SHALL repartir según un conjunto de espacios reservados, cada uno asociado al servicio que lo atiende, y SHALL entregar la interfaz para toda ruta que no pertenezca a ninguno de ellos. Agregar un servicio propio alcanzable por el navegador SHALL consistir en agregar un espacio reservado.

Se admite una excepción acotada: un servicio de terceros contra el que el navegador escriba directamente MAY vivir en su propio origen, porque en modo cloud ese servicio lo sirve el proveedor bajo su propio dominio y forzarlo a pasar por el punto de entrada haría que el modo local y el cloud dejaran de comportarse igual. Esa excepción SHALL limitarse a la escritura directa y SHALL NOT extenderse a los servicios propios del proyecto.

#### Scenario: La interfaz y la API comparten origen

- **WHEN** la interfaz hace una petición a la API
- **THEN** la petición viaja al mismo origen desde el que se cargó la interfaz
- **AND** el navegador no necesita una negociación de origen cruzado

#### Scenario: El punto de entrada reparte según la ruta

- **WHEN** se pide una ruta del espacio reservado a la API
- **THEN** responde el backend
- **WHEN** se pide cualquier otra ruta
- **THEN** responde la interfaz

#### Scenario: El punto de entrada reparte según el espacio reservado

- **WHEN** se pide una ruta que pertenece a un espacio reservado
- **THEN** responde el servicio asociado a ese espacio
- **WHEN** se pide una ruta que no pertenece a ningún espacio reservado
- **THEN** responde la interfaz

#### Scenario: Ningún servicio propio se alcanza por un origen aparte

- **WHEN** se enumeran los servicios propios del proyecto a los que el navegador hace peticiones
- **THEN** todos se alcanzan por el punto de entrada
- **AND** ninguno expone un origen propio

#### Scenario: La excepción vale solo para escritura directa a un tercero

- **WHEN** el navegador escribe directamente contra el servicio de almacenamiento
- **THEN** puede hacerlo contra el origen que ese servicio determine
- **AND** ninguna otra interacción del navegador con el sistema usa un origen distinto del punto de entrada
