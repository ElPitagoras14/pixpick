## MODIFIED Requirements

### Requirement: El entorno declara su configuración en un archivo de ejemplo

Toda variable que el entorno requiera SHALL aparecer en un archivo de ejemplo versionado, con un valor por defecto apto para desarrollo cuando no sea un secreto. SHALL NOT figurar variables sin consumidor en el alcance vigente, ni existir variables requeridas ausentes del ejemplo.

Cada variable SHALL venir acompañada de lo suficiente para elegir su valor —qué controla, qué valores admite y qué cambia al cambiarla— y de nada más: SHALL NOT incluirse alternativas descartadas, referencias a changes ni el porqué de la decisión que la introdujo.

Cada variable SHALL indicar además si necesita un valor, distinguiendo tres casos: la que siempre lo requiere, la que puede quedar vacía, y la que pertenece a un grupo de alternativas del que solo aplica el grupo que nombra el valor activo de otra variable. SHALL NOT quedar en manos del lector deducir de la prosa a cuál de los tres pertenece.

Ese texto SHALL vivir únicamente en el archivo de ejemplo, y SHALL NOT repetirse en los archivos que consumen las variables.

#### Scenario: Copiar el ejemplo alcanza para arrancar

- **WHEN** se copia el archivo de ejemplo tal cual y se levanta el entorno
- **THEN** el entorno arranca
- **AND** lo único que hace falta ajustar son secretos

#### Scenario: No hay variables huérfanas

- **WHEN** se toma cualquier variable del archivo de ejemplo
- **THEN** existe un servicio del entorno que la consume

#### Scenario: Cada variable dice si hay que darle un valor

- **WHEN** se toma cualquier variable del archivo de ejemplo
- **THEN** queda dicho si necesita valor siempre, si puede quedar vacía, o si pertenece a un grupo de alternativas
- **AND** en el último caso queda dicho qué variable decide cuál de los grupos aplica

#### Scenario: Llenar el grupo que no corresponde se puede evitar leyendo

- **WHEN** alguien tiene que elegir entre dos grupos de credenciales de proveedores distintos
- **THEN** el archivo de ejemplo dice cuál de los dos hay que llenar según el proveedor activo
- **AND** no hace falta abrir el código ni los archivos del entorno para saberlo

#### Scenario: La explicación de una variable está en un solo lugar

- **WHEN** se busca en el repositorio qué controla una variable y qué valores admite
- **THEN** la explicación aparece solo en el archivo de ejemplo

## ADDED Requirements

### Requirement: Cada servicio declara qué variables recibe

La definición del entorno SHALL declarar, servicio por servicio, qué variables recibe cada uno, de modo que saber qué necesita una pieza no requiera leer la explicación de cada variable ni inspeccionar el código que las consume.

Esa declaración SHALL nombrar variables en lugar de repetir sus valores, para que cada valor siga escrito una sola vez. Un valor que el entorno compone, o que depende de cómo se alcanzan los servicios entre sí cuando corren juntos, SHALL declararse en un único lugar: es el que difiere del valor con el que se trabaja fuera del entorno, y tenerlo escrito dos veces permite que las dos copias digan cosas distintas sin que nada falle de forma visible.

#### Scenario: Abrir el entorno dice qué necesita cada servicio

- **WHEN** se abre la definición del entorno y se elige un servicio
- **THEN** se ve qué variables recibe
- **AND** no hace falta abrir el código del servicio para saberlo

#### Scenario: Cambiar un valor es un solo cambio

- **WHEN** se cambia el valor de una variable del entorno
- **THEN** hay un único lugar donde cambiarlo
- **AND** ningún otro archivo del entorno conserva el valor anterior

#### Scenario: Los servicios se siguen alcanzando entre sí al levantar el entorno

- **WHEN** se levanta el entorno completo y un servicio necesita alcanzar a otro
- **THEN** recibe la dirección con la que se alcanzan entre sí
- **AND** no la que se usa para alcanzarlos desde fuera del entorno
