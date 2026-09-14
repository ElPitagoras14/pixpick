## Why

Hoy nada se borra nunca. Un álbum se crea, recibe fotos, se comparte, se califica — y después se queda ahí para siempre, aunque nadie vuelva a abrirlo. El producto es de ciclo corto: se suben las fotos de un evento, unas personas eligen cuáles les gustan, se toma la decisión y se acabó. Pasada esa semana el álbum no vuelve a mirarse, pero sus fotos siguen ocupando espacio del dueño y facturando en el proveedor.

Hay además una razón que no es de costo. Un álbum compartido contiene fotos que otras personas vieron y calificaron, a veces fotos de ellas. Que eso quede indefinidamente disponible porque nadie se acordó de borrarlo es una decisión por omisión, y la omisión siempre cae del lado de guardar más.

Un plazo convierte esa omisión en una regla que se puede ver y anticipar.

## What Changes

- **Un álbum vive 30 días desde su última foto.** El plazo arranca al crearlo y se reinicia cada vez que una foto queda disponible en él. El valor se declara en la configuración del entorno, como el máximo de fotos por álbum y el límite de la cuenta.
- **Solo subir renueva.** Calificar, compartir, renombrar o eliminar fotos no mueven el plazo. La caducidad mide si el álbum sigue creciendo, no si lo están mirando: un álbum al que ya nadie le agrega nada terminó su ciclo, aunque todavía se lo esté recorriendo.
- **Renueva la foto que queda disponible, no la que se pide.** Un permiso de subida pedido y nunca completado no mantiene vivo un álbum; el proyecto ya trata esas subidas como inexistentes en todos lados.
- **Al vencer, el álbum y sus fotos dejan de existir para todos**: para el dueño, para quien recibió el enlace compartido, y para cualquier lectura. Los objetos correspondientes se eliminan del almacenamiento, igual que cuando alguien elimina un álbum a mano.
- **El espacio vuelve a la cuenta en el momento del vencimiento**, no cuando se borren los bytes. Que el límite de la persona la siga penalizando por algo que ya no puede ver sería castigarla por un detalle de implementación.
- **Mientras esté vivo, el dueño ve cuánto le queda.** En la lista de álbumes y en el álbum mismo, junto a lo que ya se muestra de él.

### Fuera de alcance

- **Renovar a mano, con un botón de extender.** Sería la vía directa para que todo álbum viva para siempre con un clic cada mes, que es exactamente lo que el plazo evita. Si un álbum tiene que seguir vivo, la forma de decirlo es seguir usándolo para lo que existe: subirle fotos.
- **Una papelera o cualquier forma de recuperación después del vencimiento.** El plazo es visible desde el primer día y avisa todo el tiempo que le queda; una recuperación posterior convertiría el vencimiento en un trámite en vez de un límite.
- **Descargar o exportar el álbum antes de que venza.** Es una funcionalidad razonable y probablemente deseable, pero es un change propio: tiene su propio formato, su propio flujo y sus propias preguntas.
- **Avisar por correo.** El proyecto no envía correos y nada de su infraestructura lo contempla. El aviso es el plazo visible en la interfaz.
- **Que calificar renueve el plazo.** Se consideró y se descartó por decisión explícita. Tiene una consecuencia que conviene tener presente: un álbum compartido que varias personas están calificando activamente se borra igual a los 30 días de su última foto. Es el caso en que alguien pierde algo que creía vivo, y está aceptado a cambio de que la regla sea una sola, medible en un único momento que ya existe —confirmar una foto— y no en una noción difusa de "actividad" repartida por media docena de flujos.

## Capabilities

### New Capabilities

- `album-retention`: gobierna cuánto vive un álbum y qué ocurre cuando se le acaba el plazo. Define de dónde sale el plazo, qué lo reinicia y qué no, desde qué momento un álbum vencido deja de existir para toda lectura —incluida la de quien tiene su enlace compartido—, qué pasa con sus objetos y con el espacio que ocupaba, y que el plazo restante sea visible mientras corre. Es una capability propia porque atraviesa varias: toca lo que la lista de álbumes devuelve, lo que un enlace compartido resuelve y lo que la cuenta computa, sin pertenecer a ninguna de las tres.

### Modified Capabilities

Ninguna. Las capabilities que este change atraviesa siguen diciendo lo mismo: `album-management` gobierna quién ve y modifica un álbum, y eso no cambia por que el álbum pueda dejar de existir; `album-sharing` gobierna qué habilita un enlace, y un enlace hacia algo que ya no existe no resuelve nada, igual que hoy con un álbum eliminado a mano; `account-quota` cuenta las fotos que están en los álbumes de una persona, y las de un álbum vencido dejaron de estarlo. La regla nueva es del plazo, y por eso vive entera en su capability.

## Impact

**Base de datos**

Una migración. El plazo necesita un momento de referencia que hoy no existe: `albums` tiene `created_at`, pero nada registra cuándo entró su última foto. Reutilizar la fecha de modificación de las filas de fotos sería atarse a una columna que la mantiene un trigger y que cambia por cualquier escritura, así que una regla de producto quedaría dependiendo de un efecto secundario. Si lo que se guarda es el momento de la última foto o directamente el del vencimiento lo decide el diseño.

**El mecanismo de borrado es la decisión central**

El proyecto no tiene ningún trabajo periódico. Su única limpieza es un comando que se corre a mano, y está justificado así en su propio código: lo que descarta es invisible para todos hasta entonces, de modo que no hay urgencia. Ese argumento no se traslada aquí — un álbum vencido que sigue a la vista es exactamente lo que este change existe para evitar. El diseño tiene que separar **dejar de existir**, que puede ser exacto sin ningún proceso nuevo si lo decide una condición en las consultas, como ya ocurre con los permisos de subida vencidos, de **borrar los bytes**, que puede ocurrir después sin que nadie lo note.

**Backend**

- La configuración del plazo, junto a los otros dos topes.
- Toda lectura de álbumes y de sus fotos deja de ver los vencidos, incluida la que resuelve un enlace compartido.
- Confirmar una foto pasa a reiniciar el plazo de su álbum.
- La eliminación física de lo vencido, con el mecanismo que decida el diseño, reutilizando el borrado de objetos que ya existe para eliminar un álbum.

**Interfaz**

- La lista de álbumes y la vista del álbum muestran cuánto le queda.
- Un álbum que venció mientras alguien lo tenía abierto se comporta como uno eliminado, que es un camino que la interfaz ya recorre.

**Precedencia**

Después de `add-account-quota`: la regla de que el vencimiento libera espacio se apoya en que ese espacio se mida, y las dos tocan la misma consulta de consumo.
