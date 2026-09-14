## Why

Las dos pantallas por las que se entra al producto están vacías.

La raíz muestra el nombre y una frase, y nada más: no hay forma de iniciar sesión desde ahí. Quien llega por primera vez tiene que adivinar que existe `/login` o encontrarlo rebotando contra una ruta protegida. Es la única pantalla que ve alguien que todavía no decidió usar el producto, y no dice qué hace ni ofrece entrar.

La otra es peor, porque no es una pantalla secundaria: `/home` es el destino al que el backend manda después de iniciar sesión. Dice «You're signed in. Nothing here yet.» y no tiene un solo enlace. Lo primero que ve alguien recién autenticado es una página vacía sin salida, y el único acceso a sus álbumes está en el encabezado, que es donde uno mira último.

Al mismo tiempo hay información que no tiene dónde vivir. Cuánto espacio queda es una pregunta de cuenta, no de álbum, así que no pertenece a la lista. Y qué álbumes tienen fotos esperando una calificación hoy solo se descubre recorriendo la lista y leyendo el contador de cada uno.

## What Changes

- **La raíz se convierte en una landing de verdad**: qué es pixpick, para qué sirve en una frase que alguien entienda sin conocerlo, y un acceso visible para entrar.
- **La landing se muestra siempre, con o sin sesión.** Lo que cambia es el acceso: dice iniciar sesión para quien no entró, y entrar para quien ya tiene sesión, llevándolo adentro. La raíz sigue siendo pública: nadie queda fuera de ella por no estar autenticado.
- **La home pasa a ser un panel que responde "¿qué hago ahora?"**, con tres cosas: cuánto espacio se está usando contra el límite, qué álbumes tienen fotos esperando la calificación de quien mira, y un acceso para crear un álbum.
- **El encabezado gana el acceso a la home**, que hoy no tiene: una vez que se sale de ella no hay forma de volver salvo escribiendo la dirección.
- **La lista de álbumes no cambia.** Sigue siendo la pantalla de "¿qué tengo?", y la home es la de "¿qué hago?". Son dos preguntas distintas y por eso son dos pantallas.

### Fuera de alcance

- **Cambiar a dónde lleva iniciar sesión.** Sigue llevando a la home, que es justamente lo que este change convierte en un destino que vale la pena.
- **Rediseñar la lista de álbumes.** No se toca ni su contenido ni su forma.
- **Contenido de presentación elaborado** — capturas, ejemplos, secciones de características, testimonios. La landing tiene que decir qué es esto y dejar entrar; todo lo demás es material de marketing y es otro trabajo, con otras decisiones.
- **Cualquier página pública además de la raíz.** Nada de perfiles públicos, álbumes visibles sin enlace, ni páginas de ayuda.
- **Traducir la interfaz.** Sigue en inglés, como el resto.

## Capabilities

### New Capabilities

- `app-entry`: gobierna las dos pantallas por las que se entra al producto y qué tiene que resolver cada una. Define que la raíz sea pública y ofrezca entrar en cualquier estado de sesión, y que la primera pantalla después de iniciar sesión responda qué hacer a continuación en lugar de quedarse vacía: el espacio disponible, lo que espera una calificación, y por dónde empezar algo nuevo. No define cómo se ve, sino qué preguntas contesta cada una — que es lo que hoy no está escrito en ninguna parte y lo que permitió que las dos quedaran en blanco sin que ninguna spec lo señalara.

### Modified Capabilities

Ninguna. `frontend-delivery` gobierna cómo se construye y entrega la interfaz, no qué muestra cada pantalla; `album-management` y `rating-gallery` siguen gobernando la lista y la galería, que este change no toca; y el destino posterior a iniciar sesión, que `identity-provider` gobierna, se conserva tal cual.

## Impact

**Interfaz**

- `routes/index.tsx`: la landing, con su acceso condicionado al estado de sesión.
- `routes/_app/home.tsx`: el panel, hoy una sola frase.
- `routes/_app/route.tsx`: el acceso a la home en el encabezado.

**Sin backend nuevo**

El panel se arma con datos que ya existen. Lo pendiente por álbum ya viaja en la lista de álbumes —es lo que alimenta el botón de calificar en la vista del álbum—, y el espacio consumido contra el límite es el recurso de cuenta que introduce `add-account-quota`. Este change compone, no agrega endpoints.

**La landing necesita saber si hay sesión, y ya puede**

La raíz está fuera del layout protegido, así que no tiene el guard. Pero la ruta raíz ya carga la sesión con la misma factory de consulta que usa el guard, de modo que la landing la lee del contexto. No hace falta ningún mecanismo nuevo, y la pantalla sigue siendo pública: quien no tiene sesión la ve igual, solo con otro botón.

**Precedencia**

Después de `add-account-quota`, que es de donde sale el medidor de espacio. Al revés habría que construir la home dos veces: una vacía de ese dato y otra con él.
