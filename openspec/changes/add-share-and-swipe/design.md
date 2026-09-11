## Context

El estado de partida son cinco changes: entorno con edge y dos modos de trabajo, capa de datos en SQL crudo, identidad y sesión por puerto, los dos puertos de medios con contrato verificado, y álbumes con fotos subidas y disponibles. Este change agrega la interacción por la que existe el producto.

Lo que más condiciona el diseño es que este es el primer change donde **varias decisiones tomadas antes se ejercitan juntas por primera vez**, y si alguna quedó mal implementada se ve acá: el link se abre desde otra aplicación, así que depende del modo laxo de las cookies que fijó `add-auth-port-and-local-provider`; el destino de retorno tiene que sobrevivir al inicio de sesión; la dirección del link se construye desde la configuración y no desde la petición; y el token que no sirve responde como inexistente según las convenciones de la API.

El segundo condicionante es una propiedad que el change anterior dejó instalada sin que se notara: el máximo de fotos por álbum. Como un álbum tiene un techo, **lo pendiente de una persona también lo tiene**, y eso simplifica el deck más de lo que parece.

## Goals / Non-Goals

**Goals:**

- Que lo pendiente no sea un dato que alguien tenga que mantener, sino el resultado de una comparación.
- Que calificar se sienta inmediato aunque la red no lo sea.
- Que revocar un link nunca destruya trabajo ya hecho.
- Que el gesto sea un atajo y no una barrera para quien no puede usarlo.

**Non-Goals:**

- La galería con filtros y las estadísticas.
- Deshacer desde el swipe, notificaciones, comentarios, invitaciones nominales y caducidad del token.
- Sincronizar el avance entre dispositivos más allá de lo que ya da derivar lo pendiente.

## Decisions

### D1 - Tres tablas, y la membresía es una entidad separada del token

El token de compartir, la membresía y la calificación son tres tablas. La membresía no es un campo del token ni se deriva de él: es una relación entre una persona y un álbum, con su propia vida.

Esa separación es lo que permite revocar un link sin expulsar a nadie. Si la membresía fuera una consecuencia de que el token siga vigente, revocarlo dejaría a los miembros afuera y sus calificaciones inaccesibles — el dueño perdería exactamente lo que estaba esperando recibir. Con dos entidades, el token gobierna quién *entra* y la membresía gobierna quién *tiene acceso*, y cada una se administra por su cuenta.

Los links revocados se conservan en lugar de eliminarse, para que un token nunca se reutilice y para poder distinguir "revocado" de "nunca existió" en los registros del servidor, aunque hacia afuera las dos respuestas sean idénticas.

### D2 - Lo pendiente es una sola consulta, usada de dos maneras

La secuencia de calificación y el contador de pendientes son la misma comparación: las fotos disponibles del álbum que quien pregunta no calificó. Una devuelve las filas, el otro las cuenta.

Se implementa una sola vez y se usa en las dos formas. Tener dos consultas que expresan lo mismo es la manera más común de que el contador diga una cosa y la secuencia muestre otra, y esa discrepancia es invisible hasta que alguien la nota usándolo.

La comparación se hace contra la vista de fotos disponibles de `add-albums-and-upload`, así que una foto que todavía no se subió no aparece como pendiente sin que este change tenga que acordarse de excluirla.

### D3 - La calificación se registra en una sola sentencia que resuelve el conflicto

Calificar es una inserción que, ante la clave única de persona y foto, actualiza en lugar de fallar. Una sola sentencia, sin leer antes para decidir si insertar o actualizar.

No es una preferencia de estilo: leer y después escribir abre una ventana en la que dos peticiones de la misma persona —dos pestañas, un reintento que se cruzó con el original— pueden decidir ambas que corresponde insertar. La resolución del conflicto en la propia sentencia hace que la idempotencia que el spec exige sea una propiedad de la base y no una carrera que la aplicación gana casi siempre.

### D4 - Abrir el link es una lectura, incorporarse es una escritura

La dirección compartida es una ruta de la interfaz: abrirla carga la aplicación. La incorporación como miembro la hace la aplicación con una operación de escritura, ya en el mismo origen.

Separarlas importa por el modo laxo de las cookies que fijó `add-auth-port-and-local-provider`: una navegación de nivel superior que llega desde otra aplicación —el mensajero donde alguien pegó el link— sí lleva la cookie de sesión. Si incorporarse fuera una lectura, bastaría un enlace en cualquier lado para sumar gente a un álbum sin que se entere. Como es una escritura emitida por la aplicación desde su propio origen, eso no ocurre.

### D5 - La precarga reutiliza exactamente las direcciones que la secuencia ya entregó

La secuencia entrega, junto a cada foto, la dirección de su variante. La precarga de las siguientes usa esas mismas direcciones sin pedir nada al servidor ni construir nada por su cuenta.

Tiene que ser la misma dirección, carácter por carácter: una dirección equivalente pero distinta sería una entrada de cache distinta, y la precarga calentaría algo que después nadie pide. Es el mismo error de D7 de `add-albums-and-upload` con otra forma — trabajo que parece hecho y no sirve.

### D6 - El avance es optimista y la cola envía de a una, no en lote

Al calificar, la secuencia avanza de inmediato y la calificación se encola. La cola envía cada calificación por separado y en cuanto puede, con reintentos espaciados ante fallos temporales.

Enviar de a una y no acumular es deliberado: si la persona cierra la pestaña, lo que se pierde es a lo sumo la petición en vuelo. Acumular para mandar en lote ahorraría peticiones y ampliaría esa ventana a todo el lote, que es justamente lo que no conviene perder.

### D7 - Cada librería hace una cosa y el arrastre no pasa por ninguna

La detección del gesto la hace la librería de gestos, que además resuelve la parte tediosa: impedir que arrastrar la tarjeta desplace la página, lo que requiere un escucha no pasivo que los manejadores habituales no dan. De ahí salen el desplazamiento, la dirección y la velocidad.

Mientras el dedo se mueve, **el transform se escribe directamente sobre el elemento**, sin animación ni estado de React: la tarjeta tiene que seguir al dedo sin interpolación, y cualquier cosa en el medio se siente como retraso.

Al soltar es donde aparece la física: la variante reducida de la librería de animación anima la salida o el regreso con un resorte. Es el único momento con animación real, y el rebote con leve sobrepaso es lo que hace que la tarjeta se sienta como un objeto.

Las dos librerías quieren el mismo elemento —una su referencia, la otra su ámbito—, así que hay que combinar las dos referencias. Es trivial y es exactamente el tipo de detalle que consume media hora si no está anotado.

### D8 - El umbral tiene dos vías, las dos con piso de distancia, y solo cuenta el gesto horizontal

Se acepta la calificación por cualquiera de dos vías. La **vía por distancia** acepta cuando el desplazamiento horizontal supera el treinta por ciento del ancho de la tarjeta. La **vía rápida** acepta cuando la velocidad al soltar supera medio píxel por milisegundo **y además** el desplazamiento superó el diez por ciento del ancho. En los dos casos el gesto solo cuenta si el movimiento horizontal domina al vertical, y el arrastre recién empieza a considerarse gesto a partir de unos pocos píxeles, para que un toque no se convierta en uno.

El piso de distancia de la vía rápida no es un detalle: sin él, un roce de treinta píxeles en cuarenta milisegundos alcanza medio píxel por milisegundo y calificaría la foto. La velocidad sola no puede decidir, porque un movimiento diminuto y veloz es indistinguible de un impulso deliberado si solo se mira la velocidad. Y la condición de dominancia horizontal evita que desplazar la página verticalmente emita una calificación.

La distancia es relativa al ancho y no absoluta para que el gesto se comporte igual en cualquier pantalla. El treinta por ciento sale de dos consideraciones: un arco de pulgar cómodo en un teléfono sostenido con una mano barre entre cien y ciento cincuenta píxeles horizontales sin recolocar la mano, que sobre una tarjeta de ancho típico es aproximadamente esa fracción; y **hasta que exista la edición de calificaciones en la galería, un gesto equivocado no se puede deshacer**, así que dentro del rango cómodo conviene el extremo que hace más difícil equivocarse.

Los tres números son puntos de partida calibrados, no verdades: lo que se siente bien se termina de ajustar arrastrando con el dedo. Cambiarlos es editar constantes y no afecta a ningún requirement, porque el spec exige que el umbral combine distancia con velocidad y no cuánto de cada una.

### D9 - La lista de álbumes es una sola consulta sobre membresía

Como crear un álbum incorpora a su dueño como miembro, "mis álbumes" y "los álbumes que me compartieron" son el mismo conjunto: aquellos de los que soy miembro. La lista no es la unión de dos consultas sino una sola, y distinguir los propios es comparar el dueño con quien pregunta.

Es una consecuencia agradable de una decisión que se tomó por otro motivo —evitar un caso especial para que el autor califique—, y de esas conviene dejar registro: si alguna vez se revierte aquella, esta consulta se parte en dos.

### D10 - El contador de pendientes se resuelve en la misma consulta de la lista

La lista ya resolvía portada y conteo por álbum en una consulta; ahora suma cuántas le faltan calificar a quien pregunta. Sigue siendo una consulta, y sigue sin haber una petición por álbum.

### D11 - La secuencia no se pagina

Lo pendiente está acotado por el máximo de fotos del álbum, así que la secuencia entrega todas las pendientes de una vez con sus direcciones. Paginar agregaría estado de paginación a una interacción que ya deriva su posición de lo que falta, para ahorrar unas decenas de filas.

Esto es una consecuencia directa del máximo por álbum de `add-albums-and-upload`: sin ese techo habría que paginar, y con él no.

## Risks / Trade-offs

**Abrir el link incorpora como miembro sin pedir confirmación** → Es deliberado: una pantalla de confirmación antes de calificar agrega fricción al flujo central por una decisión que quien abrió el link ya tomó al abrirlo. El costo es que la membresía se concede por el solo hecho de abrir, y como la membresía solo da acceso de lectura y la capacidad de calificar, el daño posible es nulo.

**Un miembro conserva acceso a un álbum cuyo link fue revocado** → Es lo que el spec exige y la razón está en D1, pero conviene tenerlo presente: revocar no es una forma de quitarle el acceso a alguien en particular. Hoy no existe una operación para eso, y si alguna vez hace falta, es eliminar la membresía y no revocar el token.

**La cola en memoria pierde la calificación en vuelo si se cierra la pestaña** → Acotado por D6 a una sola calificación. Persistirla en el navegador resolvería ese caso y agregaría estado que hay que sincronizar y limpiar; no se paga por una foto.

**La precarga compite por ancho de banda con la foto que se está mirando** → Se acota a unas pocas por delante y se dispara una vez que la actual terminó de cargar, para que nunca retrase lo que la persona está viendo.

**Dos pestañas abiertas sobre el mismo álbum muestran la misma foto** → Ocurre porque la secuencia se deriva y cada pestaña la derivó en su momento. Es inofensivo: calificar la misma foto dos veces deja una sola calificación por D3, y la segunda pestaña simplemente muestra algo ya decidido.

**Las dos librerías del gesto sobre el mismo elemento** → Anotado en D7 y convertido en tarea, porque es un detalle que no se deduce de la documentación de ninguna de las dos.

## Migration Plan

La migración es aditiva: tres tablas sobre un esquema que ya tiene usuarios, sesiones, álbumes y fotos. La única sutileza es que los álbumes que ya existan al aplicarla no tienen a su dueño como miembro, porque esa regla nace con este change. La migración incorpora como miembro al dueño de cada álbum existente, de modo que la propiedad de la que depende D9 valga también hacia atrás y no solo para los álbumes nuevos.

El rollback elimina las tres tablas y con ellas todas las calificaciones, que es la única pérdida real de información que un rollback produce en este proyecto: a diferencia de los usuarios, que se recrean al volver a entrar, y de las fotos, cuyos objetos sobreviven en el almacenamiento, una calificación no se puede reconstruir de ninguna parte.

## Open Questions

Ninguna. La que quedó abierta se resolvió con una derivación que además destapó un error en el propio diseño.

**Resueltas durante la redacción**

- **Los valores del umbral del gesto.** Se cerraron dentro de D8: treinta por ciento del ancho por la vía de distancia, medio píxel por milisegundo por la vía rápida, y diez por ciento como piso de esa segunda vía. La derivación fue más valiosa que los números, porque mostró que la regla original —distancia **o** velocidad— califica fotos sola: un roce de treinta píxeles en cuarenta milisegundos alcanza el umbral de velocidad. De ahí salieron el piso de distancia de la vía rápida y la condición de dominancia horizontal, que tampoco estaba y sin la cual desplazar la página verticalmente emitiría una calificación. El treinta por ciento se eligió en el extremo alto del rango cómodo por una razón del proyecto: hasta que exista la edición en la galería, un gesto equivocado no se puede deshacer.
