## MODIFIED Requirements

### Requirement: El tipo y el tamaño se validan antes de conceder, y un archivo inadmisible rechaza el lote

El tipo de contenido y el tamaño declarado SHALL validarse antes de emitir cualquier permiso, para que un archivo inadmisible no consuma ancho de banda. El tamaño SHALL admitirse solo si es positivo y no supera el máximo: un valor que no sea positivo SHALL rechazarse igual que uno excesivo, porque al descontarse de lo disponible aumentaría el espacio libre de la cuenta y el de la instancia en lugar de consumirlo. Las dimensiones declaradas SHALL acotarse del mismo modo. Si algún archivo del lote no es admisible, SHALL rechazarse el lote completo y la respuesta SHALL identificar cuál archivo lo provocó y por qué.

El rechazo del lote completo es aceptable porque el cliente conoce el tipo y el tamaño antes de pedir y puede filtrar por su cuenta: un rechazo del servidor indica una inconsistencia, no un caso normal de uso.

La cota inferior SHALL sostenerla también el almacén de datos y no únicamente la validación de entrada, porque es la última defensa de tres límites que dependen de esa suma.

#### Scenario: Un tipo no admitido se rechaza al pedir

- **WHEN** se pide subir un archivo cuyo tipo no está admitido
- **THEN** se rechaza antes de emitir ningún permiso
- **AND** la respuesta nombra el archivo y el motivo

#### Scenario: Un tamaño por encima del límite se rechaza al pedir

- **WHEN** se pide subir un archivo cuyo tamaño declarado excede el límite
- **THEN** se rechaza antes de emitir ningún permiso

#### Scenario: Un tamaño negativo o cero se rechaza al pedir

- **WHEN** se pide subir un archivo declarando un tamaño negativo o cero
- **THEN** se rechaza antes de emitir ningún permiso
- **AND** la respuesta nombra el archivo y el campo que lo provocó

#### Scenario: Un tamaño no positivo tampoco puede llegar al almacén de datos

- **WHEN** se intenta registrar una foto con un tamaño declarado que no es positivo
- **THEN** el almacén de datos lo rechaza

#### Scenario: Un tamaño no positivo no altera el espacio disponible

- **WHEN** se intenta conceder un lote con algún tamaño negativo
- **THEN** el consumo de la cuenta y el de la instancia quedan como estaban
- **AND** ninguna otra cuenta ve crecer su espacio disponible

#### Scenario: Un archivo inadmisible rechaza el lote entero

- **WHEN** se pide subir un lote en el que un archivo no es admisible
- **THEN** no se emite permiso para ninguno del lote
- **AND** la respuesta identifica el archivo que lo provocó

### Requirement: Una subida abandonada no ensucia el álbum y puede descartarse

Una foto que quedó no disponible porque nadie subió su objeto SHALL ser inocua: SHALL NOT aparecer en ninguna lectura y SHALL NOT poder pasar a disponible una vez que su permiso venció.

SHALL existir una forma de descartar esos registros y los objetos huérfanos, y esa limpieza SHALL ejecutarse periódicamente sin intervención, con la frecuencia declarada en la configuración del entorno. No alcanza con que sea posible ejecutarla: un objeto huérfano ocupa espacio que ninguna de las tres cuotas contabiliza, porque una vez vencido su permiso deja de contar, de modo que dejar la limpieza librada a que alguien se acuerde convierte el techo de la instancia en un número que no describe lo que hay. SHALL seguir siendo invocable a mano además de periódicamente.

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

#### Scenario: La limpieza ocurre sola

- **WHEN** transcurre el intervalo declarado desde la última limpieza
- **THEN** la limpieza vuelve a ejecutarse
- **AND** nadie tuvo que invocarla

#### Scenario: Muchos restos acumulados se limpian igual

- **WHEN** la limpieza encuentra más objetos huérfanos de los que el almacenamiento admite eliminar en una petición
- **THEN** todos quedan eliminados

## ADDED Requirements

### Requirement: Confirmar un lote tiene el mismo techo de cantidad que concederlo

La cantidad de fotos que una confirmación puede nombrar SHALL tener el mismo techo que la concesión, y SHALL declararse en el mismo lugar. Un lote por encima del techo SHALL rechazarse como error de validación antes de consultar nada.

Sin ese techo una sola petición nombra cuantas fotos quiera, y como cada una que no esté disponible obliga a consultar el almacenamiento, el trabajo que una petición provoca deja de estar acotado por lo que esa petición cuesta enviar.

#### Scenario: Un lote dentro del techo se confirma

- **WHEN** se confirma un lote con una cantidad de fotos que no supera el techo
- **THEN** la confirmación se procesa normalmente

#### Scenario: Un lote por encima del techo se rechaza

- **WHEN** se confirma un lote que nombra más fotos que el techo declarado
- **THEN** se rechaza como error de validación
- **AND** no se consulta el almacenamiento por ninguna de ellas

#### Scenario: El techo es el mismo que el de conceder

- **WHEN** se comparan el techo de la concesión y el de la confirmación
- **THEN** son el mismo valor
