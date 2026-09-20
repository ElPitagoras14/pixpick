## MODIFIED Requirements

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

## ADDED Requirements

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
