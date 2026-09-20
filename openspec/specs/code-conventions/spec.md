# code-conventions Specification

## Purpose

Gobierna las convenciones de código que ninguna herramienta trae resueltas de fábrica y que, sin quedar escritas, se deciden imitando el archivo de al lado: qué forma tiene una importación interna, y dónde vive el marcado que el backend sirve. Su exigencia central es que ninguna de esas reglas dependa de que alguien la note al revisar. No se solapa con `api-conventions`, que gobierna la forma de la API HTTP, ni con `backend-testing`, que gobierna la forma de las pruebas.

## Requirements

### Requirement: La forma de una importación interna la decide dónde está el módulo que se importa

En el código del backend, importar un módulo que vive dentro del subárbol del paquete del archivo SHALL hacerse de forma relativa. Importar cualquier otro módulo propio del proyecto SHALL hacerse de forma absoluta desde la raíz del código. Una importación relativa SHALL NOT subir de nivel: si el destino no está por debajo del paquete que importa, la forma es absoluta.

Un archivo SHALL poder contener las dos formas, y solo porque sus destinos caen de lados distintos de esa línea. SHALL NOT existir dos importaciones con destinos del mismo lado escritas de forma distinta.

#### Scenario: Un módulo del mismo directorio se importa relativo

- **WHEN** un archivo importa otro que está en su mismo directorio
- **THEN** la importación es relativa

#### Scenario: Un subpaquete propio se importa relativo

- **WHEN** un archivo importa un módulo que está en un directorio por debajo del suyo
- **THEN** la importación es relativa
- **AND** no se escribe la ruta completa desde la raíz

#### Scenario: Un paquete ajeno se importa absoluto

- **WHEN** un archivo importa un módulo que no está por debajo de su propio paquete
- **THEN** la importación es absoluta desde la raíz del código

#### Scenario: Ninguna importación sube de nivel

- **WHEN** se recorre todo el código del backend buscando importaciones relativas que apunten a un paquete superior
- **THEN** no hay ninguna

### Requirement: En la interfaz, un módulo propio se importa por el alias del proyecto

En el código de la interfaz, importar otro módulo del proyecto SHALL hacerse por el alias que la raíz del código expone, sin importar qué tan cerca esté el destino. SHALL NOT usarse una ruta relativa para alcanzar un módulo propio. Los archivos generados por una herramienta quedan fuera, porque su contenido no se edita a mano; las importaciones escritas hacia ellos, no.

#### Scenario: Un módulo vecino también se importa por el alias

- **WHEN** un archivo importa otro módulo propio que está en su mismo directorio
- **THEN** la importación usa el alias del proyecto

#### Scenario: Una importación hacia un archivo generado sigue la misma regla

- **WHEN** un archivo escrito a mano importa uno generado por una herramienta
- **THEN** esa importación usa el alias del proyecto

### Requirement: El marcado que el backend sirve no vive dentro del código

Cuando el backend responda con una página, su marcado SHALL vivir en un archivo de plantilla propio y SHALL NOT estar incrustado en un literal del código. Los valores que cambian entre una respuesta y otra SHALL llegar a la plantilla como datos, y la plantilla SHALL neutralizarlos al insertarlos, de modo que un valor que venga de la petición no pueda alterar la estructura de la página.

#### Scenario: El marcado no aparece en el código

- **WHEN** se busca marcado en el código del backend
- **THEN** no hay ninguno incrustado en un literal
- **AND** la página que el backend sirve es la misma que antes

#### Scenario: Un valor recibido en la petición no altera la página

- **WHEN** se pide la página con un valor que contiene caracteres con significado en el marcado
- **THEN** el valor aparece en la página como texto
- **AND** no agrega ni cierra ningún elemento

### Requirement: Cada convención se comprueba sin intervención humana

Cada regla de esta capability SHALL tener una comprobación automática, y esa comprobación SHALL formar parte de lo que se ejecuta para validar el proyecto. Introducir una violación SHALL hacerla fallar. SHALL NOT quedar una regla cuyo cumplimiento dependa solo de que alguien la advierta al revisar: una convención que solo vive en un documento se incumple sin que nada lo señale, que es exactamente lo que este change corrige.

#### Scenario: Una violación introducida hace fallar la validación

- **WHEN** se escribe una importación que incumple la forma exigida y se valida el proyecto
- **THEN** la validación falla
- **AND** el mensaje identifica el archivo y la línea

#### Scenario: Ninguna regla queda sin comprobación

- **WHEN** se toma cualquier regla de esta capability
- **THEN** existe una comprobación automática que la verifica

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
