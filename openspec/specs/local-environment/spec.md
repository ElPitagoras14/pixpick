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

Se admite una excepción acotada: un servicio de terceros contra el que el navegador escriba directamente MAY vivir en su propio origen, porque en modo cloud ese servicio lo sirve el proveedor bajo su propio dominio y forzarlo a pasar por el punto de entrada haría que el modo local y el cloud dejaran de comportarse igual. Esa excepción SHALL limitarse a la escritura directa y SHALL NOT extenderse a los servicios propios del proyecto.

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

#### Scenario: La excepción vale solo para escritura directa a un tercero

- **WHEN** el navegador escribe directamente contra el servicio de almacenamiento
- **THEN** puede hacerlo contra el origen que ese servicio determine
- **AND** ninguna otra interacción del navegador con el sistema usa un origen distinto del punto de entrada

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

#### Scenario: Copiar el ejemplo alcanza para arrancar

- **WHEN** se copia el archivo de ejemplo tal cual y se levanta el entorno
- **THEN** el entorno arranca
- **AND** lo único que hace falta ajustar son secretos

#### Scenario: No hay variables huérfanas

- **WHEN** se toma cualquier variable del archivo de ejemplo
- **THEN** existe un servicio del entorno que la consume

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
