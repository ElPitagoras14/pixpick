## Purpose

Gobierna la calificación de fotos: qué es una calificación, quién puede emitirla, cómo se determina qué le falta calificar a cada persona, qué pasa cuando el álbum cambia después de que alguien ya calificó, y cómo se interactúa para emitirla. No se solapa con `album-sharing`, que gobierna cómo se obtiene acceso al álbum.

## ADDED Requirements

### Requirement: Una calificación es una aprobación o un rechazo de una persona sobre una foto

Una calificación SHALL expresar únicamente una de dos posiciones sobre una foto, y SHALL pertenecer a una persona identificada. Una persona SHALL tener a lo sumo una calificación por foto, y esa unicidad SHALL garantizarla el esquema y no la aplicación.

#### Scenario: Una persona tiene una sola calificación por foto

- **WHEN** una persona califica dos veces la misma foto
- **THEN** queda una única calificación, con el valor más reciente

#### Scenario: Dos personas califican la misma foto de forma independiente

- **WHEN** dos personas califican la misma foto
- **THEN** quedan dos calificaciones, una de cada una

### Requirement: Solo los miembros del álbum pueden calificar sus fotos

Calificar una foto SHALL requerir ser miembro del álbum al que pertenece. Intentarlo sin serlo SHALL responderse igual que si la foto no existiera, y SHALL NOT registrarse ninguna calificación.

#### Scenario: Un miembro califica

- **WHEN** un miembro del álbum califica una de sus fotos
- **THEN** la calificación queda registrada

#### Scenario: Quien no es miembro no califica

- **WHEN** una persona autenticada que no es miembro intenta calificar una foto del álbum
- **THEN** la respuesta es la misma que si la foto no existiera
- **AND** no se registra ninguna calificación

### Requirement: Calificar es idempotente y reintentar es seguro

Emitir la misma calificación dos veces SHALL dejar el mismo resultado que emitirla una vez. Emitir una calificación distinta sobre una foto ya calificada SHALL reemplazar la anterior. El cliente SHALL poder reintentar sin llevar registro de qué llegó a completarse.

#### Scenario: Repetir la misma calificación no cambia nada

- **WHEN** se emite dos veces la misma calificación sobre la misma foto
- **THEN** el resultado es el mismo que si se hubiera emitido una vez

#### Scenario: Cambiar de opinión reemplaza la calificación

- **WHEN** se califica una foto de una manera y después de la otra
- **THEN** queda registrada la última

### Requirement: Lo que falta calificar se deriva y no se almacena

Lo pendiente de una persona en un álbum SHALL calcularse comparando las fotos disponibles del álbum contra las calificaciones que esa persona emitió. SHALL NOT existir ningún estado almacenado que declare que alguien terminó de calificar, ni contador que haya que mantener.

#### Scenario: Lo pendiente son las fotos disponibles sin calificar

- **WHEN** se consulta lo que le falta calificar a una persona en un álbum
- **THEN** son exactamente las fotos disponibles que esa persona no calificó

#### Scenario: No hay estado de finalización

- **WHEN** se inspecciona lo que el sistema almacena sobre la relación entre una persona y un álbum
- **THEN** no existe ningún dato que declare que terminó de calificar

#### Scenario: Una foto no disponible no cuenta como pendiente

- **WHEN** un álbum tiene fotos que todavía no están disponibles
- **THEN** no aparecen entre las pendientes de nadie

### Requirement: Las fotos que el autor agrega después se vuelven pendientes solas

Cuando se agreguen fotos a un álbum que ya tiene miembros con calificaciones, esas fotos SHALL pasar a estar pendientes para cada miembro sin que ninguna operación adicional lo provoque. Eliminar una foto SHALL reducir lo pendiente de la misma manera.

#### Scenario: Subir fotos aumenta lo pendiente de quien ya calificó

- **WHEN** el dueño agrega fotos a un álbum en el que un miembro ya había calificado todo
- **THEN** ese miembro pasa a tener pendientes las fotos nuevas
- **AND** ningún proceso tuvo que actualizar nada para lograrlo

#### Scenario: Eliminar una foto la quita de lo pendiente

- **WHEN** se elimina una foto que estaba pendiente para alguien
- **THEN** deja de estar pendiente
- **AND** deja de contarse

### Requirement: La secuencia de calificación entrega las pendientes en el orden del álbum

Al calificar, las fotos SHALL presentarse en el orden que tienen dentro del álbum y SHALL incluir únicamente las pendientes de quien califica. Una foto ya calificada SHALL NOT volver a presentarse, y volver a entrar después de una interrupción SHALL continuar donde se había quedado, porque lo que se presenta se deriva de lo que falta.

#### Scenario: Se presentan solo las pendientes, en orden

- **WHEN** una persona empieza a calificar un álbum
- **THEN** recibe sus fotos pendientes en el orden del álbum

#### Scenario: Interrumpir y volver continúa donde se dejó

- **WHEN** alguien califica algunas fotos, se va, y vuelve más tarde
- **THEN** retoma con las que le faltaban
- **AND** no vuelve a ver las que ya calificó

#### Scenario: Terminar deja la secuencia vacía

- **WHEN** una persona califica la última foto que le faltaba
- **THEN** no quedan fotos por presentar

### Requirement: Calificar es operable sin el gesto de arrastre

El arrastre SHALL ser un atajo y SHALL NOT ser el único camino para emitir una calificación. SHALL existir controles visibles que emitan cada una de las dos calificaciones, y la interacción SHALL poder completarse con teclado, porque un gesto de arrastre no es operable con teclado ni con un lector de pantalla.

#### Scenario: Se puede calificar sin arrastrar

- **WHEN** alguien usa los controles visibles en lugar del arrastre
- **THEN** puede emitir cualquiera de las dos calificaciones
- **AND** avanza a la foto siguiente igual que con el arrastre

#### Scenario: Se puede calificar con teclado

- **WHEN** alguien recorre la secuencia usando únicamente el teclado
- **THEN** puede emitir ambas calificaciones y avanzar

#### Scenario: Los controles están siempre disponibles

- **WHEN** se muestra una foto para calificar
- **THEN** los controles de aprobar y rechazar están visibles sin necesidad de descubrirlos

### Requirement: La interacción avanza sin esperar a que la calificación se registre

Al calificar, la secuencia SHALL avanzar de inmediato sin esperar la confirmación del servidor. Si el registro falla, SHALL reintentarse, y solo tras agotar los reintentos SHALL informarse a la persona, sin perder lo que ya había decidido.

#### Scenario: El avance no espera al servidor

- **WHEN** alguien califica una foto
- **THEN** la siguiente aparece de inmediato

#### Scenario: Un fallo temporal se reintenta solo

- **WHEN** el registro de una calificación falla por una interrupción momentánea
- **THEN** se reintenta sin intervención
- **AND** la persona puede seguir calificando mientras tanto

#### Scenario: Un fallo persistente se informa sin perder lo decidido

- **WHEN** el registro de una calificación no se logra tras los reintentos
- **THEN** se le informa a la persona
- **AND** lo que ya había decidido no se pierde

### Requirement: Las fotos siguientes se precargan mientras se mira la actual

Mientras alguien mira una foto, las siguientes de la secuencia SHALL precargarse, para que avanzar no implique esperar a que la imagen llegue. La precarga SHALL limitarse a unas pocas fotos por delante y SHALL NOT descargar el álbum completo.

#### Scenario: Avanzar no espera a la imagen

- **WHEN** alguien califica y avanza a la foto siguiente
- **THEN** la imagen ya está disponible

#### Scenario: La precarga está acotada

- **WHEN** se observa qué imágenes se solicitan mientras alguien mira una foto
- **THEN** son unas pocas por delante de la actual
- **AND** no es el álbum entero
