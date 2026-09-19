# upload-feedback Specification

## Purpose

Gobierna qué ve quien está esperando a que una subida termine: cómo se informa cada archivo por separado, cuánto lugar tienen su avance y su desenlace, y cómo se presenta la pantalla donde eso ocurre. No se solapa con `photo-upload`, que gobierna el contrato de subir —qué se concede, qué se verifica y qué se rechaza—; aquí se gobierna lo que la interfaz muestra mientras eso pasa.

## Requirements

### Requirement: Cada archivo se informa por separado y sin perder su identidad

Cada archivo del lote SHALL aparecer con su propia identidad visible —su nombre y su tamaño— y con su propio estado, informado de forma independiente del de los demás. SHALL NOT recortarse la identidad al punto de que dos archivos distintos se vean iguales, que es el caso corriente cuando los nombres comparten prefijo, como los que produce una cámara.

#### Scenario: Un lote grande informa archivo por archivo

- **WHEN** se suben cincuenta archivos a la vez
- **THEN** cada uno aparece con su nombre, su tamaño y su propio estado

#### Scenario: Dos archivos de nombre parecido se distinguen

- **WHEN** el lote incluye dos archivos cuyos nombres solo difieren en los últimos caracteres
- **THEN** se puede saber cuál es cuál mirando la pantalla

### Requirement: El avance de un archivo tiene lugar suficiente para leerse

Mientras un archivo se está subiendo, su avance SHALL mostrarse de forma continua y SHALL disponer del ancho del bloque que le corresponde, en lugar de una porción fija de una fila. SHALL NOT compartir renglón con la identidad del archivo, que es lo que obliga a recortarlo.

En la pantalla de teléfono, que es el caso base del proyecto, el avance SHALL seguir siendo legible sin desplazamiento horizontal.

#### Scenario: El avance se lee de un vistazo

- **WHEN** un archivo se está subiendo
- **THEN** su avance se distingue sin esfuerzo y se actualiza mientras progresa

#### Scenario: También se lee en un teléfono

- **WHEN** se mira la pantalla de subida a 360 píxeles de ancho
- **THEN** el avance de cada archivo sigue siendo legible
- **AND** no hay desplazamiento horizontal

### Requirement: Cuando un archivo no termina bien, el motivo se lee completo

Cuando un archivo no llegue a subirse, SHALL mostrarse el motivo, con el espacio que necesite aunque ocupe más de un renglón, y SHALL NOT reemplazarse por un estado genérico ni recortarse hasta volverlo inútil. Si el motivo incluye un dato que permite corregir la situación —cuánto espacio queda, cuánto lugar tiene el álbum—, ese dato SHALL formar parte de lo que se muestra.

Cuando el motivo sea uno que quien lo recibe no puede resolver, porque lo que falta no está bajo su control, SHALL decirse como tal. SHALL NOT indicársele una acción que no va a cambiar el resultado —eliminar fotos propias cuando el espacio que falta es el de la instancia y el suyo le sobra—. Un motivo que manda a hacer algo inútil es peor que uno escueto: cuesta tiempo y deja creyendo que el problema es propio cuando no lo es.

Cuando el motivo admita reintentar, SHALL ofrecerse reintentar ese archivo y solo ese.

#### Scenario: Un archivo que no entra explica por qué y cuánto falta

- **WHEN** un archivo no recibe permiso porque no hay espacio disponible
- **THEN** su bloque dice que no hay espacio
- **AND** dice cuánto espacio queda

#### Scenario: Un motivo que no depende de quien sube no le pide que actúe

- **WHEN** un archivo no recibe permiso porque no hay espacio en la instancia y la cuenta de quien sube tiene lugar de sobra
- **THEN** su bloque dice que el espacio que falta no es el suyo
- **AND** no le indica eliminar fotos propias

#### Scenario: Un fallo de transferencia se puede reintentar solo

- **WHEN** un archivo falla al transferirse y otros del mismo lote van bien
- **THEN** se ofrece reintentar ese archivo
- **AND** reintentarlo no vuelve a subir los que ya terminaron

### Requirement: El desenlace de un archivo no confunde el de los demás

El resultado de un archivo SHALL NOT alterar ni interrumpir lo que se informa de los otros. Terminado un lote con resultados mixtos, SHALL poder distinguirse a simple vista cuáles terminaron bien y cuáles no.

#### Scenario: Un lote con resultados mixtos se entiende

- **WHEN** de un lote de diez archivos tres no se suben
- **THEN** los siete que terminaron se muestran como terminados
- **AND** los tres que no se muestran con su motivo
- **AND** no hace falta contar para saber cuáles fueron cuáles

### Requirement: La vista de subida es un flujo propio y se sale de ella por donde se sale de todo

La pantalla de subida SHALL presentarse como un flujo propio: SHALL NOT ofrecer las acciones del álbum —compartir, volver a subir, calificar— mientras se está en ella.

SHALL ofrecer volver al álbum, y ese acceso SHALL estar por encima del título, en la misma posición en que aparece el acceso de vuelta en las demás pantallas de la aplicación. SHALL NOT haber dos accesos de vuelta simultáneos, ni quedar el acceso por debajo del título.

#### Scenario: La salida está donde está siempre

- **WHEN** se abre la vista de subida de un álbum
- **THEN** el acceso de vuelta aparece por encima del título del álbum
- **AND** lleva a ese álbum y no a la lista de álbumes

#### Scenario: La vista no ofrece las acciones del álbum

- **WHEN** se está en la vista de subida
- **THEN** no se ofrecen las acciones propias del álbum

#### Scenario: Hay una sola salida

- **WHEN** se recorre la vista de subida completa
- **THEN** hay exactamente un acceso de vuelta
