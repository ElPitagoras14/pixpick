## MODIFIED Requirements

### Requirement: Cada servicio declara qué variables recibe

La definición del entorno SHALL declarar, servicio por servicio, qué variables recibe cada uno, de modo que saber qué necesita una pieza no requiera leer la explicación de cada variable ni inspeccionar el código que las consume.

Esa declaración SHALL nombrar variables en lugar de repetir sus valores, para que cada valor siga escrito una sola vez, en el archivo de ejemplo. Un valor que depende de cómo se alcanzan los servicios entre sí cuando corren juntos SHALL componerse dentro de la declaración que lo usa, y SHALL NOT tomarse del archivo de ejemplo: ahí el mismo nombre guarda el valor con el que se alcanza ese servicio desde afuera, y tomarlo de ahí dejaría a un servicio buscando a otro en el lugar equivocado. Cuando dos declaraciones componen el mismo valor, las dos SHALL decir lo mismo, y esa coincidencia SHALL comprobarse sin depender de que alguien la revise.

#### Scenario: Abrir el entorno dice qué necesita cada servicio

- **WHEN** se abre la definición del entorno y se elige un servicio
- **THEN** se ve qué variables recibe
- **AND** no hace falta abrir el código del servicio para saberlo

#### Scenario: Cambiar un valor es un solo cambio

- **WHEN** se cambia el valor de una variable del entorno
- **THEN** hay un único lugar donde cambiarlo
- **AND** ninguna declaración del entorno conserva el valor anterior

#### Scenario: Los servicios se siguen alcanzando entre sí al levantar el entorno

- **WHEN** se levanta el entorno completo y un servicio necesita alcanzar a otro
- **THEN** recibe la dirección con la que se alcanzan entre sí
- **AND** no la que se usa para alcanzarlos desde fuera del entorno

#### Scenario: Las dos declaraciones no se separan

- **WHEN** una declaración cambia el valor que compone para alcanzar a otro servicio, y la otra no
- **THEN** la diferencia se detecta sin que nadie tenga que compararlas a mano

## ADDED Requirements

### Requirement: Cada forma de levantar el proyecto se declara completa y por separado

El proyecto SHALL admitir más de una forma de levantarse —al menos la que construye desde el código fuente y la que consume imágenes ya publicadas—, y cada una SHALL estar declarada de forma completa: elegir una SHALL bastar para levantar el entorno entero. SHALL NOT existir una declaración que solo funcione aplicada encima de otra, ni hacer falta combinar dos para obtener un entorno utilizable.

Elegir una forma SHALL ser explícito en el comando que la levanta, y SHALL NOT depender de una variable de configuración que cambie en silencio qué declaración se usa por omisión.

Un servicio SHALL declararse en cada forma que pueda usarlo, aunque una configuración concreta no lo consulte. Un servicio declarado y levantado que nadie consulta SHALL NOT afectar el funcionamiento del entorno: a qué proveedor apunta la aplicación lo deciden sus variables, no qué servicios están declarados o corriendo.

#### Scenario: Elegir una declaración alcanza para levantar el entorno

- **WHEN** se elige cualquiera de las formas y se ejecuta su comando de arranque
- **THEN** el entorno queda operativo
- **AND** no hizo falta nombrar ninguna otra declaración

#### Scenario: Una declaración se entiende sin abrir la otra

- **WHEN** se abre cualquiera de las declaraciones
- **THEN** están todos los servicios del entorno con lo que cada uno necesita para arrancar
- **AND** ninguno queda definido a medias

#### Scenario: Qué forma se usa está escrito en el comando

- **WHEN** se lee el comando que levanta el entorno
- **THEN** queda dicho cuál de las formas se está usando
- **AND** ninguna variable de configuración puede cambiarla sin tocar el comando

#### Scenario: Un servicio declarado y no consultado no molesta

- **WHEN** se levanta el entorno con una configuración que apunta a un proveedor externo, y el servicio local equivalente está declarado
- **THEN** el entorno funciona contra el proveedor externo
- **AND** el servicio local queda levantado sin que nada lo consulte, y nada falla por eso

#### Scenario: Alternar entre las dos formas conserva los datos

- **WHEN** se levanta el entorno con una forma y después con la otra
- **THEN** los datos que había siguen estando
