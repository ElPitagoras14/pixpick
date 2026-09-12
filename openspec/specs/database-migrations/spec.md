# database-migrations Specification

## Purpose

Gobierna cómo evoluciona el esquema de la base de datos: cómo se declara una migración, cómo se aplica, cómo se conoce el esquema vigente sin ejecutar nada, y cómo se garantiza que el esquema esté al día antes de que la aplicación atienda peticiones. No se solapa con `database-access`, que gobierna cómo se consulta la base una vez que el esquema existe.

## Requirements

### Requirement: El esquema se declara en migraciones SQL versionadas e inmutables

El esquema SHALL evolucionar mediante migraciones escritas en SQL, con un orden de aplicación determinado por su identificador. Una migración ya aplicada SHALL NOT editarse: un cambio sobre lo que ella creó se expresa como una migración nueva.

#### Scenario: Corregir algo ya aplicado crea una migración nueva

- **WHEN** hace falta cambiar una estructura que una migración anterior creó
- **THEN** se agrega una migración nueva que expresa el cambio
- **AND** la migración anterior queda intacta

#### Scenario: El mismo conjunto de migraciones produce el mismo esquema

- **WHEN** dos entornos aplican el mismo conjunto de migraciones sobre una base vacía
- **THEN** ambos quedan con un esquema idéntico

### Requirement: Cada migración declara cómo se hace rollback

Toda migración SHALL declarar, junto a su aplicación, la operación que la deshace. Cuando una migración no sea reversible, SHALL declararlo de forma explícita en lugar de omitir el rollback en silencio.

#### Scenario: Hacer rollback de la última migración devuelve el esquema anterior

- **WHEN** se hace rollback de la migración aplicada más recientemente
- **THEN** el esquema queda como estaba antes de aplicarla

#### Scenario: Una migración irreversible lo dice

- **WHEN** una migración no puede deshacerse
- **THEN** su declaración de rollback indica explícitamente esa condición

### Requirement: El esquema vigente está versionado como archivo

El esquema resultante de aplicar todas las migraciones SHALL mantenerse como un archivo versionado, regenerado cada vez que se agrega una migración. Su propósito es que el esquema pueda leerse y revisarse sin ejecutar nada, y que una migración cuyo efecto sobre el esquema no coincide con lo que su autor creía se vuelva visible en la revisión del cambio.

#### Scenario: El esquema se puede leer sin base de datos

- **WHEN** alguien necesita saber qué tablas y columnas existen
- **THEN** puede leerlo del archivo versionado
- **AND** no necesita levantar la base ni aplicar migraciones

#### Scenario: El efecto de una migración es visible en la revisión

- **WHEN** se agrega una migración y se regenera el archivo del esquema
- **THEN** el cambio en el esquema aparece en la diferencia del código
- **AND** puede compararse con lo que la migración declaraba hacer

### Requirement: Las migraciones se aplican antes de que la aplicación atienda peticiones

El esquema SHALL estar al día antes de que la aplicación empiece a aceptar peticiones. Si la aplicación de migraciones falla, la aplicación SHALL NOT quedar atendiendo contra un esquema desactualizado.

#### Scenario: Un entorno recién levantado atiende con el esquema al día

- **WHEN** se levanta el entorno desde cero
- **THEN** las migraciones se aplican antes de que la aplicación acepte peticiones

#### Scenario: Una migración fallida impide atender

- **WHEN** la aplicación de migraciones falla
- **THEN** la aplicación no queda aceptando peticiones
- **AND** el fallo es visible en lugar de silencioso

### Requirement: Aplicar migraciones ya aplicadas no tiene efecto

Ejecutar la aplicación de migraciones sobre una base que ya está al día SHALL terminar satisfactoriamente sin modificar nada, para que el arranque del entorno sea repetible sin condiciones previas.

#### Scenario: Aplicar dos veces es inofensivo

- **WHEN** se aplican las migraciones sobre una base que ya está al día
- **THEN** no se modifica el esquema
- **AND** la operación termina satisfactoriamente

### Requirement: La herramienta de migraciones está fijada en una versión exacta

La versión de la herramienta que aplica las migraciones SHALL declararse de forma exacta en cada lugar que la referencie, y todas las referencias SHALL nombrar la misma versión. SHALL NOT usarse una etiqueta que se mueva con el tiempo, para que el comportamiento de la aplicación de migraciones no cambie sin que nadie lo haya decidido.

#### Scenario: Todas las referencias declaran la misma versión exacta

- **WHEN** se buscan todas las referencias a la herramienta de migraciones en el repositorio
- **THEN** cada una declara una versión exacta
- **AND** todas nombran la misma

### Requirement: Las migraciones viajan con lo que las aplica

Las migraciones SHALL estar disponibles para el proceso que las aplica sin requerir que el repositorio esté presente en la máquina donde corren. Un despliegue con artefactos preconstruidos SHALL poder migrar la base sin acceso al código fuente.

#### Scenario: Migrar sin el repositorio presente

- **WHEN** se aplican las migraciones en una máquina que no tiene el repositorio
- **THEN** la operación se completa

### Requirement: La integridad referencial la declara el esquema

Las relaciones entre entidades y el comportamiento al eliminar una fila de la que otras dependen SHALL declararse en el esquema. La aplicación SHALL NOT ser responsable de eliminar filas dependientes ni de verificar que una referencia exista.

#### Scenario: Eliminar una fila referenciada limpia sus dependientes

- **WHEN** se elimina una fila de la que otras dependen
- **THEN** las filas dependientes desaparecen
- **AND** la aplicación no ejecutó ninguna eliminación adicional

#### Scenario: Una referencia inexistente es rechazada por la base

- **WHEN** se intenta insertar una fila que referencia algo que no existe
- **THEN** la base rechaza la operación
- **AND** el rechazo no depende de una verificación previa de la aplicación

### Requirement: El campo de última modificación lo mantiene la base

Cuando una tabla registre el momento de su última modificación, ese campo SHALL actualizarse en la base al modificar la fila. SHALL NOT depender de que cada sentencia de actualización lo incluya, para que olvidarlo en una sentencia no produzca un dato desactualizado en silencio.

#### Scenario: Una actualización que no menciona el campo igual lo actualiza

- **WHEN** se modifica una fila con una sentencia que no menciona el campo de última modificación
- **THEN** el campo queda con el momento de esa modificación

#### Scenario: Todas las actualizaciones se comportan igual

- **WHEN** se comparan dos sentencias distintas que modifican la misma tabla
- **THEN** ambas dejan el campo de última modificación al día
- **AND** ninguna necesitó declararlo
