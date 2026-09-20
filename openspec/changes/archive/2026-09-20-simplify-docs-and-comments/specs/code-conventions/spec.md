## ADDED Requirements

### Requirement: Un comentario existe solo cuando dice algo que el código no dice

Un comentario del código SHALL aportar lo que no se lee del código que acompaña. Califican tres cosas: lo contraintuitivo —por qué no se hizo lo que el lector esperaría—, el acoplamiento que no se ve desde el archivo —que este valor tiene que coincidir con otro archivo, otro servicio u otra variable— y la consecuencia de cambiarlo.

Un comentario SHALL NOT parafrasear lo que la línea siguiente ya expresa, ni argumentar la alternativa descartada: lo primero se desactualiza sin que nada avise, y lo segundo es material de decisión, que vive en las specs y en los artefactos de cada change. Cuando lo que hay que explicar es qué hace el código, SHALL ser el código el que lo diga —un nombre, una función extraída— antes que un comentario que lo repita.

Esta regla cae bajo la exigencia de esta capability de que toda convención suya tenga comprobación automática. Lo comprobable de ella es la ausencia de referencias a artefactos de decisión; el juicio sobre si un comentario aporta queda en la revisión, y la comprobación SHALL NOT pretender sustituirlo.

#### Scenario: Un comentario que repite el código no está

- **WHEN** se toma cualquier comentario del código
- **THEN** afirma algo que no se deduce leyendo el código que acompaña

#### Scenario: Un acoplamiento invisible sí está explicado

- **WHEN** un valor del código tiene que coincidir con uno declarado en otro archivo o en otro servicio
- **THEN** un comentario lo dice
- **AND** nombra dónde vive el otro valor

#### Scenario: Una referencia a un artefacto de decisión hace fallar la validación

- **WHEN** se escribe un comentario que nombra una spec, un change o una decisión numerada y se valida el proyecto
- **THEN** la validación falla
- **AND** el mensaje identifica el archivo y la línea
