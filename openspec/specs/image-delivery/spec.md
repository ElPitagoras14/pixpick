# image-delivery Specification

## Purpose

Gobierna cómo se entregan al navegador las variantes de una imagen guardada: qué variantes existen, cómo se autoriza pedirlas, cuándo se producen, cómo se cachean, cómo se invalida ese cache y qué pasa cuando el transformador no responde. No se solapa con `object-storage`, que gobierna cómo la imagen original llegó a estar guardada.

## Requirements

### Requirement: Existe un conjunto cerrado de variantes con nombre

Las variantes disponibles SHALL formar un conjunto fijo y con nombre. Quien pide una imagen SHALL nombrar la variante y SHALL NOT declarar sus medidas ni ningún otro parámetro de transformación. No SHALL ser posible obtener una variante fuera del conjunto.

#### Scenario: El consumidor nombra la variante, no sus medidas

- **WHEN** el código necesita la dirección de una imagen
- **THEN** nombra la variante que quiere
- **AND** no declara medidas ni calidad

#### Scenario: Una variante fuera del conjunto no se puede obtener

- **WHEN** se intenta pedir una transformación que no corresponde a ninguna variante del conjunto
- **THEN** no se obtiene imagen

### Requirement: Las direcciones de variante van firmadas

Toda dirección de variante SHALL llevar una firma que el transformador verifique. Una dirección sin firma o con firma que no corresponda SHALL rechazarse, para que nadie pueda pedir transformaciones arbitrarias y convertir el transformador en cómputo a disposición de terceros.

#### Scenario: Una dirección sin firma se rechaza

- **WHEN** se pide una variante con una dirección que no lleva firma
- **THEN** no se obtiene imagen

#### Scenario: Alterar la dirección invalida la firma

- **WHEN** se modifica cualquier parte de una dirección firmada
- **THEN** la firma deja de corresponder
- **AND** no se obtiene imagen

### Requirement: Construir la dirección de una variante es una operación local

Construir y firmar la dirección de una variante SHALL resolverse sin comunicarse con ningún servicio. SHALL NOT requerir que el transformador ni el almacenamiento estén disponibles, para que armar una respuesta con muchas imágenes no cueste una petición por imagen.

#### Scenario: Construir muchas direcciones no genera peticiones

- **WHEN** se construyen las direcciones de todas las imágenes de un álbum
- **THEN** no se emite ninguna petición a ningún servicio

#### Scenario: Se puede construir con el transformador caído

- **WHEN** el transformador no está disponible y se construye la dirección de una variante
- **THEN** la dirección se construye igual

### Requirement: La variante se produce al pedirla y queda cacheada

Una variante SHALL producirse la primera vez que se la pide, y las peticiones siguientes por la misma variante SHALL servirse de lo ya producido sin volver a transformar.

SHALL NOT existir un mecanismo que produzca derivados por su cuenta y los almacene como objetos propios: el único camino por el que una variante se produce es una petición por la vía normal de entrega. Pedir una variante anticipadamente, para que quede cacheada antes de que la mire una persona, SHALL considerarse una petición como cualquier otra y no una excepción a esta regla — quien la pide obtiene exactamente lo mismo que obtendría cualquier visitante, y lo único que cambia es el momento.

La distinción importa porque las dos cosas se parecen y tienen consecuencias opuestas: pre-generar y almacenar derivados agrega una copia que hay que mantener sincronizada con la original y regenerar cuando cambia una variante, mientras que anticipar una petición no agrega estado alguno y lo ya cacheado se invalida por el mismo mecanismo que todo lo demás.

#### Scenario: La primera petición la produce

- **WHEN** se pide una variante que nunca se pidió
- **THEN** se produce y se entrega

#### Scenario: La segunda petición no vuelve a producirla

- **WHEN** se pide otra vez la misma variante
- **THEN** se entrega sin volver a transformar

#### Scenario: Anticipar la petición deja la variante lista

- **WHEN** el sistema pide una variante antes de que ninguna persona la haya mirado
- **THEN** la variante queda producida y cacheada
- **AND** la primera persona que la mira la recibe sin esperar a que se produzca

#### Scenario: No hay derivados almacenados como objetos propios

- **WHEN** se inspecciona qué objetos existen en el almacenamiento
- **THEN** solo están las imágenes originales
- **AND** ninguna variante figura como un objeto almacenado

### Requirement: Peticiones simultáneas por la misma variante la producen una sola vez

Cuando varias peticiones por la misma variante lleguen antes de que esté producida, SHALL producirse una sola vez y todas SHALL recibir ese resultado. Es lo que evita que precargar varias imágenes de golpe multiplique el trabajo del transformador.

#### Scenario: Varias peticiones concurrentes producen una transformación

- **WHEN** llegan al mismo tiempo varias peticiones por una variante que no está producida
- **THEN** la transformación ocurre una sola vez
- **AND** todas las peticiones reciben el resultado

### Requirement: Cambiar la definición de una variante invalida lo ya producido

Cuando cambien las características de una variante, las peticiones siguientes SHALL recibir la definición nueva. SHALL NOT quedar sirviéndose indefinidamente lo producido con la definición anterior, y lograrlo SHALL NOT requerir vaciar el cache a mano.

#### Scenario: La nueva definición se sirve

- **WHEN** se cambian las características de una variante y se la vuelve a pedir
- **THEN** se recibe la variante con la definición nueva

#### Scenario: No hay que vaciar el cache a mano

- **WHEN** se cambia la definición de una variante
- **THEN** el mecanismo de invalidación hace el trabajo
- **AND** nadie tiene que intervenir sobre el cache

### Requirement: Con el transformador caído se sigue sirviendo lo cacheado, y lo no cacheado falla como imagen

Si el transformador no responde, las variantes ya producidas SHALL seguir entregándose. Una variante no producida SHALL responder un error, y SHALL NOT entregarse en su lugar el documento de la interfaz.

#### Scenario: Lo cacheado sobrevive al transformador

- **WHEN** el transformador no está disponible y se pide una variante ya producida
- **THEN** se entrega

#### Scenario: Lo no cacheado falla como error y no como documento

- **WHEN** el transformador no está disponible y se pide una variante que no está producida
- **THEN** la respuesta es un error
- **AND** no se entrega el documento de la interfaz

### Requirement: Una variante produce un resultado equivalente con cualquier proveedor

El conjunto de variantes y las características de cada una SHALL definirse una sola vez para todo el sistema, y cada proveedor SHALL traducir esa definición a su propio vocabulario. Una variante nombrada SHALL producir una imagen con las mismas medidas y el mismo formato cualquiera sea el proveedor activo, de modo que cambiar de proveedor no altere lo que la gente ve ni obligue a ajustar la interfaz.

Ningún proveedor SHALL ofrecer variantes que otro no pueda producir. Si un proveedor no puede producir alguna del conjunto, la salida SHALL ser reducir el conjunto o descartar ese proveedor, y SHALL NOT ser tener variantes disponibles solo con algunos: eso convertiría la elección de proveedor en una decisión de producto en lugar de una de infraestructura.

#### Scenario: La misma variante da la misma imagen

- **WHEN** se pide una variante con un proveedor activo y luego la misma variante con otro
- **THEN** las dos imágenes tienen las mismas medidas y el mismo formato

#### Scenario: Cambiar de proveedor no cambia la presentación

- **WHEN** se cambia el proveedor de transformación activo
- **THEN** la interfaz no requiere ningún ajuste
- **AND** lo que se ve es equivalente a lo anterior

#### Scenario: Las características se declaran una sola vez

- **WHEN** se cambia la medida de una variante
- **THEN** el cambio vale para todos los proveedores
- **AND** no hay que repetirlo por cada uno

#### Scenario: Un proveedor que no cubre el conjunto no se acepta

- **WHEN** un proveedor de transformación no puede producir alguna variante del conjunto
- **THEN** no se lo considera utilizable
- **AND** no se resuelve dejando esa variante disponible solo con los demás

### Requirement: La firma y la imposibilidad de adivinar la dirección son el control de acceso a las imágenes

La entrega de una variante SHALL apoyarse en que quien tiene la dirección la obtuvo de un endpoint que lo autorizó, y SHALL NOT requerir sesión. Para que eso sea suficiente, los identificadores que componen el nombre del objeto SHALL ser impredecibles: SHALL NOT ser secuenciales ni derivables de otros identificadores.

#### Scenario: Una dirección firmada se entrega sin sesión

- **WHEN** se pide una variante con una dirección firmada válida y sin presentar sesión
- **THEN** la imagen se entrega

#### Scenario: Las direcciones no se pueden enumerar

- **WHEN** se conoce la dirección de una imagen
- **THEN** no permite derivar la dirección de otra
- **AND** los identificadores que la componen no son secuenciales
