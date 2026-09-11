## Why

El producto entero existe para esto: que alguien mire las fotos de otro y diga sí o no, una por una, sin pensarlo demasiado. Los cinco changes anteriores construyeron las condiciones; este entrega la interacción que les da sentido.

Hay dos decisiones estructurales que este change materializa y conviene nombrarlas antes que nada, porque de ellas depende la forma de todo lo demás.

La primera es que **no existe un estado que diga "esta persona ya terminó de calificar"**. Lo que le falta calificar a alguien se deriva de comparar las fotos disponibles del álbum contra las calificaciones que esa persona emitió. La consecuencia es que cuando el autor sube fotos nuevas, lo pendiente de cada miembro crece solo, sin que ningún proceso actualice nada y sin que exista siquiera la posibilidad de que un contador quede desviado de la realidad.

La segunda es que **el token que se comparte y el acceso que concede son cosas distintas**. El token controla quién *entra*; la membresía controla quién *tiene acceso*. Si fueran lo mismo, revocar un link destruiría las calificaciones ya emitidas y el autor perdería justo aquello que estaba esperando.

## What Changes

- **Tablas nuevas**: el token de compartir con su revocación, la membresía del álbum, y las calificaciones con unicidad por foto y persona.
- **Generar, regenerar y revocar el link de un álbum.** Regenerar revoca el anterior y emite uno nuevo, conservando el registro de lo que hubo antes.
- **Ingresar por el link**: se valida el token, se incorpora como miembro a quien entra, y se lo lleva a calificar o a mirar el álbum según lo que le falte.
- **Un token inválido o revocado responde como inexistente**, para no confirmarle a nadie que el álbum existe.
- **Quien ya es miembro conserva su acceso aunque el token se revoque.** Revocar corta a los nuevos, no a los que ya entraron.
- **El deck de calificación**: las fotos disponibles del álbum que quien pregunta todavía no calificó, en el orden del álbum.
- **Calificar es una operación idempotente por persona y foto**, así que reintentarla es seguro y el cliente no necesita llevar la cuenta de qué llegó a registrarse.
- **El autor califica su propio álbum** como cualquier otro miembro: crear un álbum lo hace miembro de él.
- **La interacción de swipe**: la tarjeta sigue al dedo sin interpolación, al soltar vuela o rebota con física, el umbral combina distancia con velocidad, las próximas fotos se precargan, el avance es optimista con una cola que reintenta, y **los botones y el teclado no son un agregado sino parte del mecanismo**.
- **La ruta del link funciona sin sesión**: manda a iniciar sesión conservando el destino, y después de autenticarse la persona termina en el álbum y no en la portada.
- **Lo pendiente se muestra** en la lista de álbumes y en el álbum.

### Fuera de alcance

- La galería con filtros y las estadísticas: son el change siguiente, y el deck de este alcanza para verificar todo lo de acá.
- **Deshacer la última calificación desde el swipe.** Se corrige editándola en la galería, que llega en el change siguiente; entre uno y otro, un swipe equivocado queda como está.
- Notificar al autor cuando alguien termina de calificar.
- Comentarios sobre las fotos.
- Invitar por correo o restringir quién puede entrar a una lista de personas: el link es el mecanismo.
- Que el token caduque por tiempo. Se revoca o se regenera a mano.
- Los adapters cloud.

## Capabilities

### New Capabilities

- `album-sharing`: cómo se comparte un álbum, qué concede el link, cómo se revoca y se regenera, cómo se ingresa con él, y qué relación hay entre el token y el acceso de quien ya entró.
- `photo-rating`: qué es una calificación, quién puede emitirla, cómo se determina qué le falta calificar a alguien, y qué pasa cuando el álbum cambia después de que alguien ya calificó.

### Modified Capabilities

- `album-management`: dos de sus requirements dejan de ser ciertos con este change. El que dice que solo el dueño puede ver el álbum queda desactualizado, porque ahora los miembros también acceden —con permisos distintos de los del dueño, que sigue siendo el único que puede modificarlo o eliminarlo—. Y el que dice que listar devuelve solo los álbumes propios también, porque un álbum al que alguien entró por un link tiene que aparecerle en su lista: de lo contrario, quien calificó pierde el camino de vuelta y depende de conservar el link para volver a verlo.

Esa capability se materializa al archivar `add-albums-and-upload`, así que estos deltas asumen que los changes se archivan en el orden en que fueron planificados.

## Impact

**Archivos nuevos**

- `dbmate/migrations/0004_create_shares_members_and_ratings.sql`
- `backend/src/packages/shares/router.py`, `service.py`, `repository.py`, `schemas.py`, `responses.py`
- `backend/src/packages/ratings/router.py`, `service.py`, `repository.py`, `schemas.py`, `responses.py`
- Pruebas de compartir, de revocación, de membresía, del deck y de la idempotencia de la calificación
- `frontend/src/features/swipe/` con sus componentes, sus hooks y su precarga
- `frontend/src/routes/a.$token.tsx` y `frontend/src/routes/_app/albums/$albumId/swipe.tsx`

**Archivos modificados**

- `dbmate/schema.sql`: regenerado con las tres tablas nuevas.
- `backend/src/routes.py`: montaje de los dos routers nuevos.
- `backend/src/packages/albums/`: el listado incorpora los álbumes de los que se es miembro y lo pendiente de cada uno.
- `backend/tests/factories.py`: constructores de token, membresía y calificación.
- `frontend/src/features/albums/`: la lista distingue los propios de los compartidos y muestra lo pendiente.
- `frontend/package.json`: las dos dependencias nuevas.
- `README.md`: el flujo de compartir y calificar.

**Dependencias**

Las dos primeras dependencias de npm que agrega el proyecto: una para detectar el gesto de arrastre y otra, en su variante reducida, para las animaciones de soltar. El reparto entre ellas es deliberado — una detecta, la otra anima, y el arrastre en sí no pasa por ninguna. Sin dependencias nuevas de Python ni variables de entorno nuevas: la dirección pública del sitio, que el link necesita, ya existe desde `add-auth-port-and-local-provider`.

**Precedencia**

Depende de `add-albums-and-upload`, que aporta los álbumes y las fotos que se comparten y se califican.
