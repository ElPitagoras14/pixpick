# local-environment Specification

## Purpose

Gobierna cómo se levanta el proyecto completo en una máquina de desarrollo: qué lo compone, por dónde entra el tráfico, qué queda expuesto al host y cómo se declara su configuración. No se solapa con `frontend-delivery`, que gobierna cómo se construye y se entrega la interfaz, ni con `frontend-runtime-config`, que gobierna cómo la interfaz recibe sus valores de entorno.

## Requirements

### Requirement: Un solo comando levanta el entorno completo

Partiendo de un clon del repositorio, un único comando SHALL dejar el proyecto operativo y accesible desde el navegador. SHALL NOT requerir instalar ni configurar servicios en el host más allá del runtime de contenedores, ni ejecutar pasos manuales en un orden determinado.

#### Scenario: Un clon limpio queda operativo

- **WHEN** se parte de un clon del repositorio sin estado previo y se ejecuta el comando de arranque
- **THEN** la aplicación responde en el navegador
- **AND** no fue necesario ningún paso manual adicional

#### Scenario: El host no acumula dependencias

- **WHEN** se revisa lo que hace falta instalar en la máquina de desarrollo
- **THEN** solo aparece el runtime de contenedores
- **AND** ni la base de datos ni ningún otro servicio se instalan en el host

### Requirement: Todo el tráfico de la aplicación entra por un único punto

La interfaz y la API SHALL servirse desde el mismo origen a través de un único punto de entrada. SHALL NOT existir un origen distinto por servicio propio del proyecto, para que el navegador no distinga entre pedir la interfaz y pedir cualquier otra cosa de la aplicación.

El punto de entrada SHALL repartir según un conjunto de espacios reservados, cada uno asociado al servicio que lo atiende, y SHALL entregar la interfaz para toda ruta que no pertenezca a ninguno de ellos. Agregar un servicio propio alcanzable por el navegador SHALL consistir en agregar un espacio reservado.

Se admite una excepción acotada: un servicio contra el que el navegador escriba directamente MAY vivir en su propio origen **únicamente cuando lo sirva un proveedor externo bajo su propio dominio**, porque ahí no hay forma de interponer el punto de entrada. Un servicio que el proyecto levanta dentro de su propio entorno SHALL alcanzarse por el punto de entrada aunque el navegador escriba directamente contra él. El modo local y el cloud siguen comportándose igual donde importa, que es el cliente: la concesión de escritura viaja describiendo qué petición hacer, así que el cliente aplica la que recibe sin saber a qué dirección apunta.

Hacer pasar la escritura por el punto de entrada además habilita acotar ahí el tamaño de lo que se escribe, que es la única cota posible sobre lo efectivamente subido cuando ningún esquema de firma por URL puede expresar un rango de tamaño.

Ese servicio MAY conservar un origen propio; lo que SHALL cumplirse es que ese origen lo atienda el punto de entrada y que el servicio no quede publicado por sí mismo. El punto de entrada SHALL reenviar esas peticiones sin alterar la ruta ni el destino, porque la firma de la escritura los cubre y reescribirlos invalidaría la concesión.

#### Scenario: La interfaz y la API comparten origen

- **WHEN** la interfaz hace una petición a la API
- **THEN** la petición viaja al mismo origen desde el que se cargó la interfaz
- **AND** el navegador no necesita una negociación de origen cruzado

#### Scenario: El punto de entrada reparte según la ruta

- **WHEN** se pide una ruta del espacio reservado a la API
- **THEN** responde el backend
- **WHEN** se pide cualquier otra ruta
- **THEN** responde la interfaz

#### Scenario: El punto de entrada reparte según el espacio reservado

- **WHEN** se pide una ruta que pertenece a un espacio reservado
- **THEN** responde el servicio asociado a ese espacio
- **WHEN** se pide una ruta que no pertenece a ningún espacio reservado
- **THEN** responde la interfaz

#### Scenario: Ningún servicio propio se alcanza por un origen aparte

- **WHEN** se enumeran los servicios propios del proyecto a los que el navegador hace peticiones
- **THEN** todos se alcanzan por el punto de entrada
- **AND** ninguno expone un origen propio

#### Scenario: El almacenamiento del entorno se alcanza por el punto de entrada

- **WHEN** el navegador escribe contra el almacenamiento que el proyecto levanta en su propio entorno
- **THEN** la escritura viaja por el punto de entrada
- **AND** el servicio de almacenamiento no está publicado por sí mismo

#### Scenario: Lo publicado se limita al punto de entrada

- **WHEN** se enumera qué está alcanzable desde fuera del entorno
- **THEN** solo aparece el punto de entrada
- **AND** de cada servicio que atiende queda alcanzable únicamente lo que su dirección reservada cubre

#### Scenario: La excepción vale solo para escritura directa a un tercero

- **WHEN** el almacenamiento activo es un proveedor externo bajo su propio dominio y el navegador escribe directamente contra él
- **THEN** puede hacerlo contra el origen que ese proveedor determine
- **AND** ninguna otra interacción del navegador con el sistema usa un origen distinto del punto de entrada

#### Scenario: La concesión sigue siendo válida al pasar por el punto de entrada

- **WHEN** el navegador usa una concesión emitida para la dirección del punto de entrada
- **THEN** la escritura se acepta
- **AND** el punto de entrada no alteró la ruta ni el destino de la petición

#### Scenario: Cambiar de proveedor no cambia el cliente

- **WHEN** se pasa del almacenamiento del entorno a un proveedor externo
- **THEN** el código del cliente que sube archivos no se modifica

### Requirement: Al host se expone el punto de entrada y solo los servicios de terceros que el trabajo nativo necesita

El punto de entrada SHALL exponerse al host porque es la puerta de la aplicación. Los servicios de terceros que el modo de trabajo nativo necesite alcanzar SHALL exponerse al host, y ninguno que no lo requiera SHALL exponerse. Los servicios propios del proyecto —los que se construyen en este repositorio— SHALL ser alcanzables únicamente dentro de la red del entorno.

#### Scenario: Un servicio propio no es alcanzable directamente

- **WHEN** se intenta llegar al backend desde el host sin pasar por el punto de entrada
- **THEN** la conexión no se establece

#### Scenario: La base de datos sí es alcanzable

- **WHEN** se conecta un cliente de base de datos desde el host
- **THEN** la conexión se establece

#### Scenario: Un servicio de terceros que el trabajo nativo no necesita no se expone

- **WHEN** se revisa qué puertos publica el entorno
- **THEN** cada servicio de terceros expuesto lo está porque el modo nativo lo alcanza
- **AND** ninguno está expuesto sin esa necesidad

### Requirement: El proyecto admite trabajar con el backend y la interfaz de forma nativa

Además del modo en que todo corre en contenedores, el proyecto SHALL admitir un modo en que los servicios de terceros corren en contenedores mientras el backend y la interfaz corren directamente en la máquina de desarrollo. Pasar de un modo al otro SHALL consistir en usar otro perfil de configuración, y SHALL NOT requerir editar código, la declaración del entorno ni los nombres de las variables.

#### Scenario: Cambiar de modo es cambiar de perfil

- **WHEN** se pasa del modo con todo en contenedores al modo nativo
- **THEN** lo único que cambia son los valores de configuración
- **AND** los nombres de las variables son los mismos en los dos modos

#### Scenario: El código no sabe en qué modo corre

- **WHEN** se inspecciona el código del backend o de la interfaz
- **THEN** no existe ninguna condición que distinga un modo de trabajo del otro

#### Scenario: La interfaz nativa conserva un solo origen

- **WHEN** la interfaz corre en su servidor de desarrollo y pide algo de un espacio reservado
- **THEN** la petición sale al mismo origen desde el que se cargó la interfaz
- **AND** el servidor de desarrollo la reenvía al servicio que corresponde

#### Scenario: El backend nativo alcanza lo que necesita

- **WHEN** el backend corre de forma nativa
- **THEN** alcanza cada servicio de terceros del que depende
- **AND** no hizo falta modificar la declaración del entorno para lograrlo

#### Scenario: El flujo completo funciona en modo nativo

- **WHEN** se recorre el flujo de la aplicación con el backend y la interfaz nativos
- **THEN** funciona igual que con todo en contenedores

### Requirement: Los puertos publicados al host son configurables

Cada puerto que el entorno publica al host SHALL declararse en una variable de configuración, para que el proyecto pueda convivir con otros que usen puertos parecidos. SHALL NOT haber puertos fijos escritos de forma que requieran editar la declaración del entorno para cambiarlos.

#### Scenario: Cambiar la variable mueve el puerto

- **WHEN** se cambia el valor de la variable que declara un puerto y se vuelve a levantar el entorno
- **THEN** el servicio queda accesible en el puerto nuevo
- **AND** no hubo que editar la declaración del entorno

### Requirement: Las versiones de las imágenes de terceros están fijadas

Toda imagen de terceros que use el entorno SHALL declararse con una versión explícita. SHALL NOT usarse etiquetas móviles, para que reconstruir el entorno en otro momento no traiga silenciosamente una versión distinta.

#### Scenario: Cada imagen declara su versión

- **WHEN** se inspecciona la declaración del entorno
- **THEN** cada imagen de terceros indica una versión explícita
- **AND** ninguna usa una etiqueta que se mueva con el tiempo

#### Scenario: Reconstruir más tarde da lo mismo

- **WHEN** se reconstruye el entorno tiempo después sin cambiar la declaración
- **THEN** se obtienen las mismas versiones de los servicios de terceros

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

### Requirement: El estado de la base de datos sobrevive al reinicio

Los datos de la base SHALL persistir cuando los servicios se detienen y se vuelven a levantar. SHALL NOT perderse por un reinicio ordinario del entorno.

#### Scenario: Un reinicio conserva los datos

- **WHEN** se escribe un dato, se detiene el entorno y se lo vuelve a levantar
- **THEN** el dato sigue estando

### Requirement: Existe un healthcheck accesible por el punto de entrada

El entorno SHALL exponer, a través del punto de entrada, un recurso que confirme que la cadena punto de entrada → backend está operativa. SHALL NOT requerir credenciales, y su respuesta SHALL distinguir el caso en que el backend no responde del caso en que responde correctamente.

#### Scenario: La cadena completa se verifica sin credenciales

- **WHEN** se pide el recurso de salud a través del punto de entrada sin autenticarse
- **THEN** la respuesta indica que el backend está operativo

#### Scenario: Un backend caído se distingue de una respuesta normal

- **WHEN** el backend no está disponible y se pide el recurso de salud
- **THEN** la respuesta indica el fallo
- **AND** no se devuelve el documento de la interfaz en su lugar

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

### Requirement: Cada servicio declara cuánta memoria puede tomar y qué hacer si cae

Cada servicio del entorno SHALL declarar un techo de memoria y SHALL declarar qué hacer si termina de forma inesperada. SHALL NOT quedar librado a que el servicio tome toda la que haya disponible.

Los servicios comparten una sola máquina, y el que transforma imágenes consume tanto como le pidan: sin un techo, una carga sobre él alcanza para que el resto —incluida la base de datos— se quede sin memoria.

#### Scenario: Cada servicio tiene su techo declarado

- **WHEN** se inspecciona la declaración del entorno
- **THEN** cada servicio indica cuánta memoria puede tomar

#### Scenario: Un servicio saturado no arrastra a los demás

- **WHEN** un servicio recibe más carga de la que puede atender
- **THEN** consume hasta su techo y no más
- **AND** los demás servicios siguen operando

#### Scenario: Un servicio que termina inesperadamente vuelve

- **WHEN** un servicio termina de forma inesperada
- **THEN** el entorno lo vuelve a levantar
