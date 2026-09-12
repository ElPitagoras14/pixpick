## ADDED Requirements

### Requirement: Los datos de prueba se construyen con constructores compartidos

La creación de datos de prueba SHALL concentrarse en constructores reutilizables que provean valores por defecto válidos. Una prueba SHALL declarar únicamente los campos relevantes para lo que verifica, de modo que agregar un campo obligatorio al esquema no obligue a modificar cada prueba.

#### Scenario: Una prueba declara solo lo que le importa

- **WHEN** una prueba necesita una entidad para ejercitar su comportamiento
- **THEN** declara únicamente los campos que su verificación involucra
- **AND** el resto toma valores por defecto válidos

#### Scenario: Un campo obligatorio nuevo se absorbe en un solo lugar

- **WHEN** el esquema gana un campo obligatorio
- **THEN** alcanza con ajustar el constructor compartido
- **AND** las pruebas que no involucran ese campo siguen pasando sin cambios
