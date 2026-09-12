# database-access Specification

## Purpose

Gobierna cómo la aplicación llega a la base de datos: cómo se expresan las consultas, cómo viaja la conexión, cómo se delimita una unidad de trabajo, qué forma tienen los resultados que cruzan hacia el resto de la aplicación y cómo se manifiestan los fallos. No se solapa con `database-migrations`, que gobierna cómo evoluciona el esquema, ni con `backend-testing`, que gobierna cómo se verifica este comportamiento.

## Requirements

### Requirement: Las consultas se expresan en SQL con parámetros por nombre

Las consultas SHALL escribirse como SQL. SHALL NOT construirse mediante un lenguaje de expresiones ni derivarse de modelos declarativos. Los valores SHALL pasarse como parámetros con nombre y SHALL NOT interpolarse en el texto de la consulta.

#### Scenario: Los valores viajan como parámetros, no dentro del texto

- **WHEN** una consulta necesita un valor provisto por quien la invoca
- **THEN** el valor se pasa como parámetro con nombre
- **AND** el texto de la consulta no contiene ese valor

#### Scenario: No se derivan consultas de modelos

- **WHEN** se inspecciona el código de acceso a datos
- **THEN** no existen modelos declarativos, sesiones de mapeo objeto-relacional ni relaciones declaradas

#### Scenario: Una consulta se lee tal como se ejecuta

- **WHEN** se lee una función de acceso a datos
- **THEN** el SQL que ejecuta está a la vista en el mismo lugar
- **AND** no hay que reconstruirlo mentalmente a partir de llamadas encadenadas

### Requirement: La configuración de conexión se expresa en una sola variable

La conexión a la base SHALL configurarse mediante un único valor que contenga todo lo necesario para establecerla. SHALL NOT existir variables separadas por componente que haya que mantener coherentes entre sí.

#### Scenario: Un solo valor configura la conexión

- **WHEN** se configura el acceso a la base
- **THEN** un único valor lo determina por completo
- **AND** no hay componentes declarados por separado

### Requirement: Las funciones de acceso reciben la conexión y no la administran

Toda función que ejecute consultas SHALL recibir la conexión como parámetro. SHALL NOT abrirla, cerrarla ni obtenerla de un estado compartido implícito. El nivel que abre la conexión SHALL ser el que define el alcance de la unidad de trabajo.

#### Scenario: Una función de acceso no crea su propia conexión

- **WHEN** se invoca una función que ejecuta una consulta
- **THEN** utiliza la conexión que recibió
- **AND** no abre ni cierra ninguna por su cuenta

#### Scenario: La pertenencia a una transacción se ve en el punto de llamada

- **WHEN** se lee el código que invoca a una función de acceso
- **THEN** puede determinarse si esa llamada participa de una transacción observando únicamente la conexión que se le pasa
- **AND** no hace falta inspeccionar la pila de llamadas para averiguarlo

#### Scenario: Omitir la conexión es un error detectable antes de ejecutar

- **WHEN** una llamada a una función de acceso no provee la conexión
- **THEN** el error se manifiesta como una firma incompleta
- **AND** no se produce una ejecución que parezca correcta

### Requirement: Una operación de varias escrituras es atómica

Cuando una operación abarque varias escrituras, todas SHALL ejecutarse sobre la misma conexión y dentro de la misma transacción. Un fallo intermedio SHALL NOT dejar ninguna de ellas confirmada.

#### Scenario: Un fallo intermedio no deja escrituras parciales

- **WHEN** una operación de varias escrituras falla después de la primera
- **THEN** ninguna de sus escrituras queda confirmada

#### Scenario: Sin fallo, todas las escrituras quedan confirmadas

- **WHEN** la misma operación se completa sin fallos
- **THEN** todas sus escrituras quedan confirmadas

#### Scenario: Las escrituras de una operación comparten conexión

- **WHEN** una operación abarca varias escrituras
- **THEN** todas se ejecutan sobre la misma conexión
- **AND** ninguna se ejecuta sobre una conexión distinta de la que abrió la transacción

### Requirement: La conexión no permanece abierta durante espera ajena a la base

Una transacción abierta SHALL NOT permanecer así mientras se espera la respuesta de un sistema externo ni mientras transcurre una espera deliberada. Todo dato que dependa de un sistema externo SHALL obtenerse antes de abrir la transacción que lo persiste.

#### Scenario: El resultado de una llamada externa se obtiene antes de abrir la transacción

- **WHEN** una operación necesita datos de un sistema externo para completar sus escrituras
- **THEN** esos datos se obtienen antes de abrir la transacción de escritura
- **AND** la transacción, una vez abierta, no espera ninguna respuesta externa

#### Scenario: La transacción abierta solo contiene operaciones de base de datos

- **WHEN** se inspecciona el código dentro de un bloque de transacción
- **THEN** todas las llamadas dentro de ese bloque son lecturas o escrituras sobre la base
- **AND** ninguna es una llamada de red externa ni una espera artificial

### Requirement: Los límites del pool de conexiones están declarados

La cantidad de conexiones permanentes y el máximo alcanzable SHALL declararse de forma explícita. SHALL NOT quedar librados a los valores por defecto de la capa de acceso, para que un cambio de esa capa no altere la capacidad del servicio de forma inadvertida.

#### Scenario: Los límites son explícitos

- **WHEN** se inspecciona la construcción del acceso a la base
- **THEN** la cantidad de conexiones permanentes y el techo total están declarados

#### Scenario: Cambiar de capa de acceso no cambia la capacidad

- **WHEN** se reemplaza la capa que ejecuta las consultas
- **THEN** el techo de conexiones simultáneas se mantiene igual al anterior

### Requirement: El servicio no arranca si la base no responde

La aplicación SHALL verificar la conectividad con la base durante su arranque y SHALL fallar si no la obtiene. Al cerrar de forma ordenada, SHALL liberar las conexiones que mantenga.

#### Scenario: Una base inalcanzable impide el arranque

- **WHEN** la aplicación arranca y la base no responde
- **THEN** el arranque falla con un error explícito
- **AND** el servicio no queda aceptando peticiones que fallarían al consultar

#### Scenario: Al cerrar se liberan las conexiones

- **WHEN** la aplicación se detiene de forma ordenada
- **THEN** las conexiones que mantenía quedan liberadas

#### Scenario: El healthcheck refleja el estado de la base

- **WHEN** se consulta el healthcheck y la base no responde
- **THEN** la respuesta indica que el servicio no está operativo
- **AND** no informa un estado satisfactorio

### Requirement: Los resultados cruzan la frontera como modelos tipados

Las funciones de acceso SHALL devolver modelos con campos declarados y validados. SHALL NOT devolver filas ni estructuras de claves arbitrarias, para que el resto de la aplicación no dependa de nombres de columna y para que una discrepancia entre el esquema y lo que el código espera se manifieste en la frontera de la capa de datos.

#### Scenario: El consumidor accede a campos declarados

- **WHEN** una función de acceso devuelve un resultado
- **THEN** su consumidor accede a campos declarados con su tipo
- **AND** no consulta claves por nombre sobre una estructura genérica

#### Scenario: Una discrepancia con el esquema se detecta en la frontera

- **WHEN** una consulta deja de devolver un campo que el modelo declara
- **THEN** el fallo ocurre al construir el modelo
- **AND** no se propaga como un valor ausente hacia el resto de la aplicación

### Requirement: Los fallos de la capa de datos se traducen a errores de dominio

Un fallo al ejecutar una consulta o al obtener una conexión SHALL presentarse al resto de la aplicación como un error propio del dominio. SHALL NOT propagarse la excepción original de la capa de acceso ni del controlador de la base, y el texto de la consulta SHALL NOT aparecer en lo que el sistema devuelve a un cliente.

#### Scenario: Un fallo de la base llega como error de dominio

- **WHEN** una consulta falla porque la base no está disponible
- **THEN** el consumidor recibe un error de dominio
- **AND** no recibe la excepción original de la capa de acceso

#### Scenario: La respuesta al cliente no revela la consulta

- **WHEN** un fallo de base de datos se traduce en una respuesta al cliente
- **THEN** la respuesta no contiene el texto de la consulta
- **AND** no contiene nombres de tablas ni de columnas
