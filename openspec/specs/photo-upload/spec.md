# photo-upload Specification

## Purpose

Gobierna cómo una foto llega a formar parte de un álbum: quién puede subirla, qué se valida y en qué momento, cómo se concede la escritura, cómo se confirma que efectivamente llegó, qué estados atraviesa, qué se hace con lo que queda a medio camino, y qué pasa al eliminarla. No se solapa con `object-storage`, que gobierna el mecanismo de la escritura, ni con `album-management`, que gobierna el álbum que las contiene.

## Requirements

### Requirement: Solo el dueño del álbum puede subirle fotos

Pedir permiso de subida para un álbum SHALL requerir ser su dueño. Pedirlo para un álbum ajeno o inexistente SHALL responderse de la misma manera, para no revelar la existencia de álbumes de otras personas.

#### Scenario: El dueño obtiene permiso de subida

- **WHEN** el dueño pide subir fotos a su álbum
- **THEN** obtiene los permisos

#### Scenario: Un álbum ajeno responde como inexistente

- **WHEN** una persona autenticada pide subir fotos a un álbum del que no es dueña
- **THEN** la respuesta es la misma que para un álbum que no existe

### Requirement: El tipo y el tamaño se validan antes de conceder, y un archivo inadmisible rechaza el lote

El tipo de contenido y el tamaño declarado SHALL validarse antes de emitir cualquier permiso, para que un archivo inadmisible no consuma ancho de banda. Si algún archivo del lote no es admisible, SHALL rechazarse el lote completo y la respuesta SHALL identificar cuál archivo lo provocó y por qué.

El rechazo del lote completo es aceptable porque el cliente conoce el tipo y el tamaño antes de pedir y puede filtrar por su cuenta: un rechazo del servidor indica una inconsistencia, no un caso normal de uso.

#### Scenario: Un tipo no admitido se rechaza al pedir

- **WHEN** se pide subir un archivo cuyo tipo no está admitido
- **THEN** se rechaza antes de emitir ningún permiso
- **AND** la respuesta nombra el archivo y el motivo

#### Scenario: Un tamaño por encima del límite se rechaza al pedir

- **WHEN** se pide subir un archivo cuyo tamaño declarado excede el límite
- **THEN** se rechaza antes de emitir ningún permiso

#### Scenario: Un archivo inadmisible rechaza el lote entero

- **WHEN** se pide subir un lote en el que un archivo no es admisible
- **THEN** no se emite permiso para ninguno del lote
- **AND** la respuesta identifica el archivo que lo provocó

### Requirement: Conceder evalúa el límite del álbum, el de la cuenta y el de la instancia, y distingue cuál se alcanzó

Al conceder permisos de subida SHALL evaluarse tres límites independientes: el máximo de fotos del álbum, el espacio disponible de la cuenta de su dueño y el espacio disponible de la instancia. Un archivo SHALL recibir permiso solo si entra en los tres.

Cuando un archivo no reciba permiso, la respuesta SHALL indicar cuál de los tres límites lo impidió. No son intercambiables y se resuelven distinto: quedarse sin lugar en el álbum se resuelve creando otro álbum, quedarse sin espacio en la cuenta se resuelve eliminando algo propio, y quedarse sin espacio en la instancia no lo resuelve quien pide, porque el espacio que falta puede no ser suyo.

Cuando el de la cuenta y el de la instancia se hayan alcanzado los dos, el motivo informado SHALL ser el de la cuenta. Es el único de los dos sobre el que quien pide puede actuar, y eliminar fotos propias libera espacio en los dos a la vez; informar el de la instancia mientras la cuenta también está llena escondería la acción que sí sirve.

La evaluación del espacio de la cuenta SHALL considerar todos los álbumes de esa persona, y no solo aquel al que se está subiendo. Dos lotes pedidos al mismo tiempo en álbumes distintos de la misma persona SHALL NOT poder superar el límite entre ambos por no haberse visto entre sí.

La evaluación del espacio de la instancia SHALL considerar las fotos de todas las cuentas. Dos lotes pedidos al mismo tiempo por personas distintas SHALL NOT poder superar el límite de la instancia entre ambos por no haberse visto entre sí. Es la misma exigencia que el párrafo anterior hace para una persona, un alcance más arriba: excluir por persona alcanza para un límite de la persona y no para uno que abarca a todas.

#### Scenario: Un archivo necesita entrar en los tres límites

- **WHEN** un archivo entra en el espacio disponible de la cuenta y en el de la instancia pero el álbum ya está lleno
- **THEN** no recibe permiso

#### Scenario: El motivo del rechazo identifica el límite

- **WHEN** un archivo no recibe permiso porque no hay espacio en la cuenta
- **THEN** la respuesta lo distingue de un rechazo por álbum lleno y de uno por instancia llena
- **AND** indica cuánto espacio queda

#### Scenario: El espacio se mide sobre toda la cuenta

- **WHEN** una persona sube a un álbum vacío teniendo su cuenta llena por fotos de otros álbumes
- **THEN** no recibe permiso
- **AND** el motivo es el espacio de la cuenta, no el álbum

#### Scenario: La instancia llena rechaza aunque la cuenta tenga lugar

- **WHEN** una persona con espacio de sobra en su cuenta pide subir a un álbum con lugar, estando la instancia llena
- **THEN** no recibe permiso
- **AND** el motivo es el espacio de la instancia, y no el de su cuenta ni el del álbum

#### Scenario: La cuenta llena gana sobre la instancia llena

- **WHEN** una persona con la cuenta llena pide subir estando también llena la instancia
- **THEN** el motivo informado es el espacio de la cuenta

#### Scenario: Dos lotes simultáneos en álbumes distintos no superan el límite

- **WHEN** se piden a la vez dos lotes en dos álbumes de la misma persona y entre los dos excederían su espacio
- **THEN** lo concedido entre ambos no supera el límite

#### Scenario: Dos lotes simultáneos de personas distintas no superan el límite de la instancia

- **WHEN** dos personas distintas piden a la vez sendos lotes que entre los dos excederían el espacio de la instancia
- **THEN** lo concedido entre ambos no supera el límite de la instancia

### Requirement: Un álbum admite una cantidad máxima de fotos, configurable, y un lote que no entra se concede en parte

La cantidad de fotos que un álbum admite SHALL tener un máximo declarado en la configuración del entorno. El máximo SHALL evaluarse al conceder.

Un lote que no entre completo SHALL concederse en parte: SHALL recorrerse los archivos en el orden en que se pidieron y SHALL emitirse permiso para cada uno que entre, y los que no entren SHALL devolverse sin permiso, con su motivo y con cuánto lugar queda. SHALL NOT rechazarse el lote completo por esta causa. Quedarse sin lugar no es un error de quien pide sino un hecho del estado del álbum, y obligarlo a rehacer la selección entera no le da nada que no pueda decidir viendo qué entró y qué no.

El cómputo SHALL contar las fotos disponibles más las que están a la espera de confirmarse con su permiso vigente, y SHALL NOT contar las que quedaron a la espera con el permiso vencido, porque esas ya no pueden completarse. Sin contar las que están a la espera, pedir concesiones repetidamente permitiría superar el máximo.

El máximo SHALL condicionar únicamente la incorporación de fotos nuevas. Un álbum que ya supera el máximo —porque el máximo se redujo después— SHALL conservar todas sus fotos y SHALL seguir siendo legible y utilizable en todo sentido; lo único que SHALL rechazarse es agregarle más. Eliminar fotos de un álbum que supera el máximo SHALL volver a habilitar la incorporación en cuanto quede espacio.

#### Scenario: Un lote que excede el máximo se concede en parte

- **WHEN** se pide un lote más grande que el lugar que queda en el álbum
- **THEN** reciben permiso los archivos que entran, en el orden en que se pidieron
- **AND** los demás se devuelven sin permiso, indicando el motivo y cuánto lugar quedaba

#### Scenario: Un álbum sin lugar no concede ninguno

- **WHEN** se pide un lote en un álbum que ya alcanzó el máximo
- **THEN** ningún archivo del lote recibe permiso
- **AND** cada uno indica que el álbum está lleno

#### Scenario: Las fotos a la espera ocupan lugar

- **WHEN** se piden concesiones que llenan el álbum y, antes de confirmarlas, se piden más
- **THEN** el segundo pedido no recibe ningún permiso
- **AND** el álbum no supera el máximo

#### Scenario: Las esperas vencidas dejan de ocupar lugar

- **WHEN** un permiso vence sin que se haya subido el archivo
- **THEN** esa foto deja de contar para el máximo
- **AND** se puede volver a pedir una concesión en su lugar

#### Scenario: Reducir el máximo no toca los álbumes existentes

- **WHEN** se reduce el máximo por debajo de la cantidad de fotos de un álbum existente
- **THEN** el álbum conserva todas sus fotos
- **AND** sigue siendo legible y utilizable como cualquier otro
- **AND** solo se rechaza agregarle fotos nuevas

#### Scenario: Liberar espacio vuelve a habilitar la incorporación

- **WHEN** se eliminan fotos de un álbum que superaba el máximo hasta quedar por debajo
- **THEN** se puede volver a agregar fotos hasta el máximo

### Requirement: La foto se registra al conceder y no está disponible hasta confirmarse

Al conceder el permiso SHALL registrarse la foto en un estado que la declara no disponible, porque sus bytes todavía no existen. Una foto no disponible SHALL ser invisible para todo el sistema: SHALL NOT aparecer en ninguna lectura del álbum, SHALL NOT contar para la cantidad de fotos, y SHALL NOT considerarse para la portada.

#### Scenario: Tras conceder, la foto existe pero no está disponible

- **WHEN** se concede el permiso de subida de una foto
- **THEN** la foto queda registrada
- **AND** su estado la declara no disponible

#### Scenario: Una foto no disponible no aparece en el álbum

- **WHEN** se mira un álbum que tiene fotos no disponibles
- **THEN** esas fotos no aparecen
- **AND** no se cuentan entre las fotos del álbum

#### Scenario: Una foto no disponible no puede ser portada

- **WHEN** la única foto de un álbum está no disponible
- **THEN** el álbum no tiene portada

### Requirement: La confirmación verifica contra el objeto y no contra lo declarado

Al confirmar, el sistema SHALL consultar el objeto almacenado y comparar su tamaño y su tipo reales con lo que se había declarado. SHALL NOT darse por buena la declaración del cliente. Si el objeto no está, la foto SHALL permanecer no disponible. Si está pero no coincide con lo declarado, SHALL rechazarse y el objeto SHALL eliminarse.

#### Scenario: Un objeto ausente deja la foto no disponible

- **WHEN** se confirma una foto cuyo objeto nunca se subió
- **THEN** la foto sigue no disponible
- **AND** la respuesta lo indica sin tratarlo como un error del sistema

#### Scenario: Un objeto que no coincide se rechaza y se elimina

- **WHEN** se confirma una foto cuyo objeto tiene un tamaño o un tipo distinto del declarado
- **THEN** la foto no queda disponible
- **AND** el objeto se elimina del almacenamiento

#### Scenario: Un objeto que coincide deja la foto disponible

- **WHEN** se confirma una foto cuyo objeto coincide con lo declarado
- **THEN** la foto queda disponible
- **AND** su tamaño registrado es el real del objeto

### Requirement: Confirmar una foto ya disponible no cambia nada

Confirmar una foto que ya está disponible SHALL terminar satisfactoriamente sin modificarla, para que reintentar una confirmación interrumpida sea seguro.

#### Scenario: Reconfirmar es inofensivo

- **WHEN** se confirma una foto que ya estaba disponible
- **THEN** la operación termina satisfactoriamente
- **AND** la foto no se modifica

### Requirement: Las dimensiones de la imagen son una pista de presentación

Las dimensiones SHALL poder declararlas el cliente y SHALL usarse únicamente para reservar el espacio de la foto antes de que cargue. Ninguna decisión de autorización, validación, almacenamiento ni entrega SHALL depender de ellas, y su ausencia SHALL NOT impedir nada.

#### Scenario: Sin dimensiones la subida funciona

- **WHEN** se sube una foto sin declarar sus dimensiones
- **THEN** la subida y la confirmación se completan igual

#### Scenario: Dimensiones incorrectas no alteran nada relevante

- **WHEN** el cliente declara dimensiones que no corresponden a la imagen
- **THEN** el único efecto es que el espacio reservado no coincide
- **AND** ni la validación ni la entrega cambian su comportamiento

### Requirement: La posición dentro del álbum se asigna al conceder y no cambia

Cada foto SHALL recibir una posición dentro del álbum al momento de concederse su subida, siguiendo el orden en que se pidieron. Las fotos de un lote posterior SHALL ubicarse después de las existentes. SHALL NOT existir ninguna operación que reordene.

#### Scenario: Un lote conserva el orden en que se pidió

- **WHEN** se concede un lote de varias fotos
- **THEN** quedan en el álbum en el orden en que se pidieron

#### Scenario: Un lote nuevo continúa después de las existentes

- **WHEN** se sube un lote a un álbum que ya tenía fotos
- **THEN** las nuevas quedan después de las anteriores

#### Scenario: No hay forma de reordenar

- **WHEN** se inspeccionan las operaciones disponibles sobre las fotos
- **THEN** ninguna cambia su posición

### Requirement: Eliminar una foto elimina su objeto

Eliminar una foto SHALL eliminar su registro y el objeto almacenado. Como en la eliminación de un álbum, el registro SHALL eliminarse primero, de modo que un fallo al eliminar el objeto deje un huérfano y nunca un registro que apunte a nada.

#### Scenario: Se eliminan el registro y el objeto

- **WHEN** el dueño elimina una foto
- **THEN** la foto deja de existir
- **AND** su objeto almacenado deja de existir

#### Scenario: Un fallo al eliminar el objeto no deja el registro

- **WHEN** la eliminación del objeto falla
- **THEN** el registro de la foto ya no existe
- **AND** el objeto queda como huérfano identificable

### Requirement: Una subida abandonada no ensucia el álbum y puede descartarse

Una foto que quedó no disponible porque nadie subió su objeto SHALL ser inocua: SHALL NOT aparecer en ninguna lectura y SHALL NOT poder pasar a disponible una vez que su permiso venció. SHALL existir una forma de descartar esos registros y los objetos huérfanos sin que eso requiera un proceso permanente corriendo.

#### Scenario: Una subida abandonada nunca se vuelve visible

- **WHEN** se concede una subida y nadie sube el archivo
- **THEN** la foto nunca aparece en el álbum

#### Scenario: Un permiso vencido ya no permite completar la subida

- **WHEN** se intenta subir el archivo después de que el permiso venció
- **THEN** la escritura se rechaza
- **AND** la foto sigue no disponible

#### Scenario: Los restos se pueden descartar

- **WHEN** se ejecuta la operación de limpieza
- **THEN** los registros no disponibles con permiso vencido y los objetos huérfanos quedan eliminados

### Requirement: El calentamiento de variantes no afecta el resultado de la confirmación

Tras confirmar un lote, el sistema SHALL pedir la variante de calificación de las fotos que quedaron disponibles, para que quede cacheada antes de que alguien la mire. Esa tarea SHALL ocurrir después de responder, SHALL acotar cuántas peticiones mantiene en curso, y su fallo SHALL NOT alterar la respuesta, el estado de las fotos ni producir un error visible para quien subió.

#### Scenario: La respuesta no espera al calentamiento

- **WHEN** se confirma un lote de fotos
- **THEN** la respuesta llega sin esperar a que las variantes estén producidas

#### Scenario: Un calentamiento fallido no rompe nada

- **WHEN** el calentamiento de una variante falla
- **THEN** la confirmación sigue siendo satisfactoria
- **AND** las fotos quedan disponibles igual
- **AND** quien subió no ve ningún error

#### Scenario: El calentamiento no se dispara una vez por foto

- **WHEN** se confirma un lote de muchas fotos
- **THEN** el calentamiento se organiza como una sola tarea para el lote
- **AND** la cantidad de peticiones simultáneas que mantiene está acotada
