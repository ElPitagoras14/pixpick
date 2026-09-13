## ADDED Requirements

### Requirement: Una variante produce un resultado equivalente con cualquier proveedor

El conjunto de variantes y las características de cada una SHALL definirse una sola vez para todo el sistema, y cada proveedor SHALL traducir esa definición a su propio vocabulario. Una variante nombrada SHALL producir una imagen con las mismas medidas y el mismo formato cualquiera sea el proveedor activo, de modo que cambiar de proveedor no altere lo que la gente ve ni obligue a ajustar la interfaz.

Ningún proveedor SHALL ofrecer variantes que otro no pueda producir. Si un proveedor no puede producir alguna del conjunto, la salida SHALL ser reducir el conjunto o descartar ese proveedor, y SHALL NOT ser tener variantes disponibles solo con algunos: eso convertiría la elección de proveedor en una decisión de producto en lugar de una de infraestructura.

#### Scenario: La misma variante da la misma imagen

- **WHEN** se pide una variante con un proveedor activo y luego la misma variante con otro
- **THEN** las dos imágenes tienen las mismas medidas y el mismo formato

#### Scenario: Cambiar de proveedor no cambia la presentación

- **WHEN** se cambia el proveedor de transformación activo
- **THEN** la interfaz no requiere ningún ajuste
- **AND** lo que se ve es equivalente a lo anterior

#### Scenario: Las características se declaran una sola vez

- **WHEN** se cambia la medida de una variante
- **THEN** el cambio vale para todos los proveedores
- **AND** no hay que repetirlo por cada uno

#### Scenario: Un proveedor que no cubre el conjunto no se acepta

- **WHEN** un proveedor de transformación no puede producir alguna variante del conjunto
- **THEN** no se lo considera utilizable
- **AND** no se resuelve dejando esa variante disponible solo con los demás
