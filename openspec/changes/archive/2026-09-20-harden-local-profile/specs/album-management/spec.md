## MODIFIED Requirements

### Requirement: Un álbum tiene un título obligatorio y una descripción opcional

El título SHALL ser obligatorio y SHALL tener contenido: un valor compuesto solo de espacios SHALL rechazarse. La descripción SHALL ser opcional y su ausencia SHALL ser un estado válido, no un valor vacío que haya que interpretar.

Los dos SHALL tener una longitud máxima declarada, y un valor que la supere SHALL rechazarse como error de validación nombrando el campo. Sin un máximo, el único tope es cuánto cuerpo acepta el punto de entrada, que es un número que nadie eligió para esto y que además viaja de vuelta en cada listado de álbumes.

#### Scenario: Sin título no se crea

- **WHEN** se intenta crear un álbum sin título
- **THEN** la respuesta indica que el título es obligatorio y nombra el campo

#### Scenario: Un título en blanco se rechaza

- **WHEN** se intenta crear un álbum con un título compuesto únicamente de espacios
- **THEN** se rechaza igual que si faltara

#### Scenario: Sin descripción se crea igual

- **WHEN** se crea un álbum sin descripción
- **THEN** el álbum queda creado

#### Scenario: Un título más largo que el máximo se rechaza

- **WHEN** se intenta crear o renombrar un álbum con un título que supera la longitud máxima
- **THEN** se rechaza como error de validación
- **AND** la respuesta nombra el campo

#### Scenario: Una descripción más larga que el máximo se rechaza

- **WHEN** se intenta guardar una descripción que supera la longitud máxima
- **THEN** se rechaza como error de validación
- **AND** la respuesta nombra el campo
