## ADDED Requirements

### Requirement: La foto que se califica se ve completa

La foto sobre la que se está emitiendo una calificación SHALL mostrarse completa, sin recortar, cualquiera sea su forma. SHALL NOT recortarse para llenar la tarjeta: la decisión se toma sobre lo que se ve, así que mostrar una parte hace que alguien apruebe o rechace algo distinto de lo que hay.

La tarjeta SHALL conservar la misma forma para todas las fotos, y una foto cuya proporción no coincida con la de la tarjeta SHALL entrar completa dentro de ella, dejando espacio libre en los lados que sobren. Que todas las tarjetas midan igual es lo que hace que el gesto de arrastre se sienta igual sea cual sea la foto, y que la pila no cambie de forma a cada decisión.

#### Scenario: Una foto apaisada se califica entera

- **WHEN** se está calificando una foto más ancha que alta
- **THEN** se la ve completa dentro de la tarjeta
- **AND** no se le recortan los costados

#### Scenario: Todas las tarjetas miden lo mismo

- **WHEN** se recorren fotos de proporciones distintas en la secuencia de calificación
- **THEN** la tarjeta mantiene la misma forma y el mismo tamaño en todas

#### Scenario: Lo que se aprueba es lo que se vio

- **WHEN** se aprueba o se rechaza una foto desde la secuencia de calificación
- **THEN** lo que se estaba viendo era la foto completa
