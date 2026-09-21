## Purpose

Gobierna cómo el código ya integrado se convierte en artefactos desplegables: cuándo hay una versión nueva, qué se publica bajo su nombre, qué se reconstruye y qué se reutiliza, en qué orden queda visible para quien consume las imágenes, y quién dispara el despliegue. No se solapa con `local-environment`, que gobierna cómo se levanta el proyecto a partir de lo que esta capability publica.

## ADDED Requirements

### Requirement: Hay release cuando la versión declarada supera a la última publicada

La versión SHALL declararse en el código, y el pipeline SHALL decidir si hay algo que publicar comparándola contra la versión más alta ya publicada. SHALL publicar únicamente cuando la declarada sea mayor. Integrar cambios sin tocar la versión SHALL NOT publicar imágenes ni registrar un release.

La comparación SHALL hacerse por precedencia numérica de cada tramo y SHALL NOT hacerse alfabéticamente, porque en orden alfabético una versión con un tramo de dos dígitos queda por debajo de una con un solo dígito.

#### Scenario: Subir la versión publica

- **WHEN** se integra un cambio que deja la versión declarada por encima de la última publicada
- **THEN** el pipeline publica las imágenes de esa versión
- **AND** queda registrado un release con ese nombre

#### Scenario: Integrar sin tocar la versión no publica nada

- **WHEN** se integra un cambio que deja la versión declarada igual a la última publicada
- **THEN** no se publica ninguna imagen
- **AND** no se registra ningún release

#### Scenario: Una versión anterior no publica

- **WHEN** la versión declarada es menor que la última publicada
- **THEN** no se publica ninguna imagen

#### Scenario: El orden de versiones es numérico

- **WHEN** la última publicada tiene un tramo final de un dígito y la declarada lo tiene de dos, con el mismo valor en los tramos anteriores
- **THEN** la declarada se considera posterior
- **AND** el release ocurre

### Requirement: Cada release publica todos los servicios bajo el nombre de la versión

Al terminar un release, cada servicio propio del proyecto SHALL tener una imagen publicada bajo el nombre de esa versión, se haya reconstruido o no. SHALL NOT quedar un servicio sin imagen para una versión publicada.

Un hueco rompería dos cosas a la vez: el conjunto de imágenes de esa versión dejaría de poder levantarse completo, y el release siguiente no encontraría de dónde reutilizar ese servicio.

#### Scenario: Los servicios que no cambiaron también quedan publicados

- **WHEN** se publica una versión en la que cambió el contexto de un solo servicio
- **THEN** todos los servicios tienen imagen publicada bajo el nombre de esa versión

#### Scenario: Una versión se puede levantar completa

- **WHEN** se toma cualquier versión publicada y se piden las imágenes de todos los servicios con ese nombre
- **THEN** todas existen

### Requirement: Un servicio cuyo contexto no cambió se reutiliza en lugar de reconstruirse

Cuando el contexto de construcción de un servicio no cambió desde el release anterior, el pipeline SHALL publicarlo reutilizando la imagen de ese release anterior, y SHALL NOT reconstruirlo. La imagen publicada SHALL ser exactamente la misma que ya existía, no una reconstrucción equivalente.

La diferencia es observable: reutilizar no sube contenido nuevo al registro, y quien ya tenga la versión anterior descargada no descarga nada al pedir la nueva.

#### Scenario: Reutilizar no produce contenido nuevo

- **WHEN** se publica una versión en la que el contexto de un servicio no cambió
- **THEN** la imagen de ese servicio para la versión nueva tiene el mismo contenido que la de la versión anterior

#### Scenario: Quien ya la tiene no descarga de nuevo

- **WHEN** alguien que tiene descargada la imagen anterior de un servicio reutilizado pide la de la versión nueva
- **THEN** no necesita descargar contenido adicional

#### Scenario: Un cambio en el contexto sí reconstruye

- **WHEN** se publica una versión en la que el contexto de un servicio cambió
- **THEN** ese servicio se reconstruye
- **AND** su imagen refleja el código de esa versión

### Requirement: Qué cuenta como cambio de un servicio se define excluyendo, no enumerando

El conjunto de archivos que determina si un servicio cambió SHALL definirse partiendo de su contexto completo y quitando lo que ese servicio versiona pero no incorpora a su imagen. SHALL NOT definirse enumerando los archivos que sí la afectan.

Las dos formas fallan distinto ante un archivo nuevo que nadie contempló. Enumerando, ese archivo queda fuera del conjunto y el servicio se reutiliza aunque su imagen debiera haber cambiado: el registro pasa a ofrecer, bajo el nombre de una versión, una imagen que no corresponde a ese código. Excluyendo, el archivo queda dentro y provoca una reconstrucción de más, que solo cuesta tiempo.

#### Scenario: Un archivo nuevo no contemplado reconstruye

- **WHEN** se agrega al contexto de un servicio un archivo que ninguna regla menciona y se publica una versión
- **THEN** ese servicio se reconstruye

#### Scenario: Cambiar lo que no se hornea no reconstruye

- **WHEN** lo único que cambió en el contexto de un servicio es material que ese servicio versiona pero no incorpora a su imagen
- **THEN** ese servicio no se reconstruye

### Requirement: Un servicio sin imagen previa se construye

Cuando no exista imagen del release anterior para un servicio, el pipeline SHALL construirlo, aunque su contexto no haya cambiado. SHALL NOT intentar reutilizar una imagen ausente.

Cubre el servicio recién incorporado al proyecto, el registro purgado y el primer release de todos, que no tiene release anterior contra el cual comparar.

#### Scenario: El primer release construye todo

- **WHEN** se publica la primera versión y no existe ningún release anterior
- **THEN** todos los servicios se construyen

#### Scenario: Un servicio nuevo se construye

- **WHEN** se incorpora un servicio al proyecto y se publica una versión
- **THEN** ese servicio se construye aunque su contexto no tenga cambios respecto del release anterior

#### Scenario: Una imagen ausente se reconstruye

- **WHEN** el contexto de un servicio no cambió pero su imagen del release anterior ya no está en el registro
- **THEN** ese servicio se construye

### Requirement: La etiqueta móvil se mueve recién cuando la versión completa está publicada

El proyecto SHALL ofrecer, para cada servicio, una etiqueta que siempre apunte a la última versión publicada. Esa etiqueta SHALL moverse únicamente después de que todas las imágenes de la versión estén publicadas, y SHALL NOT moverse servicio por servicio a medida que cada uno termina.

Quien levanta el proyecto por esa etiqueta toma todos los servicios a la vez; si se movieran de a uno, podría tomar una combinación de versiones distintas que nunca se probó junta.

#### Scenario: Nadie ve una combinación intermedia

- **WHEN** se levanta el proyecto por la etiqueta móvil mientras un release está en curso
- **THEN** todos los servicios resuelven a la misma versión

#### Scenario: La etiqueta sigue a la última versión

- **WHEN** termina un release
- **THEN** la etiqueta móvil de cada servicio apunta a esa versión

### Requirement: Un release interrumpido se recupera en el intento siguiente

El punto de comparación de un release SHALL ser la última versión publicada por completo, y SHALL NOT ser el estado del intento anterior. El registro del release SHALL quedar asentado al final, después de publicar las imágenes.

Así, un intento que falla a mitad de camino no deja constancia de haber ocurrido: el intento siguiente vuelve a ver los mismos cambios pendientes desde la misma referencia y rehace el trabajo completo, sin que nadie tenga que reparar el estado a mano.

#### Scenario: Un fallo a mitad de camino no avanza la referencia

- **WHEN** un release publica parte de sus imágenes y falla antes de terminar
- **THEN** no queda registrado como release

#### Scenario: El intento siguiente rehace el trabajo

- **WHEN** se vuelve a intentar un release después de uno interrumpido
- **THEN** se evalúan los mismos cambios que el intento fallido había detectado
- **AND** el resultado es el mismo que si el primero no hubiera ocurrido

### Requirement: Las imágenes publicadas sirven a más de una arquitectura

Cada imagen publicada SHALL poder ejecutarse tanto en procesadores x86 de 64 bits como en procesadores ARM de 64 bits, de modo que quien levante el proyecto obtenga la variante que corresponde a su máquina sin tener que elegirla.

Reutilizar una imagen SHALL conservar todas las arquitecturas que esa imagen ya servía.

#### Scenario: Cada máquina obtiene su variante

- **WHEN** se levanta el proyecto en una máquina de cualquiera de las dos arquitecturas
- **THEN** las imágenes se ejecutan sin emulación
- **AND** no hubo que indicar la arquitectura

#### Scenario: Reutilizar no pierde arquitecturas

- **WHEN** un servicio se reutiliza en lugar de reconstruirse
- **THEN** su imagen sigue sirviendo a las mismas arquitecturas que antes

### Requirement: Cada release queda registrado en el historial del repositorio

Cada versión publicada SHALL quedar asentada en el repositorio bajo el mismo nombre con que se publicaron sus imágenes, de modo que localizar el código de una imagen no requiera correlacionar fechas. El registro SHALL acompañarse de lo que entró desde el release anterior.

#### Scenario: El nombre coincide con el de las imágenes

- **WHEN** se toma una versión publicada
- **THEN** existe en el repositorio una referencia con exactamente ese nombre
- **AND** apunta al código desde el que se publicaron esas imágenes

#### Scenario: Un release dice qué trae

- **WHEN** se consulta un release
- **THEN** figura qué se integró desde el release anterior

### Requirement: El despliegue lo dispara el propio pipeline

Al terminar de publicar y registrar una versión, el pipeline SHALL notificar al entorno desplegado para que tome esa versión. Desplegar SHALL NOT requerir una acción manual posterior.

Un fallo al notificar SHALL NOT invalidar el release ya publicado: las imágenes y el registro son válidos por sí mismos, y el despliegue puede reintentarse sin rehacerlos.

#### Scenario: Publicar dispara el despliegue

- **WHEN** termina de registrarse un release
- **THEN** el entorno desplegado recibe la indicación de tomar esa versión
- **AND** nadie tuvo que iniciarlo a mano

#### Scenario: Un despliegue fallido no invalida el release

- **WHEN** la notificación de despliegue falla
- **THEN** las imágenes de esa versión y su registro siguen siendo válidos
- **AND** el release no queda marcado como fallido
