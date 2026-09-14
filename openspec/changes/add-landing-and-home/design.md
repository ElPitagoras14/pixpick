## Context

La raíz (`routes/index.tsx`) es un título y una frase centrados, sin acceso a ningún lado. Está fuera del layout protegido, así que no tiene guard, pero la ruta raíz de la aplicación resuelve la sesión en su `beforeLoad` y la reparte por contexto a todo lo que cuelga debajo — incluida ella.

`routes/_app/home.tsx` es una sola frase y es a donde el backend manda después de iniciar sesión (`DEFAULT_RETURN_TO`). El encabezado del layout tiene un único enlace, a `/albums`, y ninguno de vuelta a la home.

La lista de álbumes se obtiene con una sola consulta, de clave `["albums"]`, que devuelve **todos** los álbumes de la persona —propios y compartidos— cada uno con `isOwner`, `photoCount`, `coverUrl` y `pendingCount`. Los dos grupos que muestra `/albums` son un corte del lado del cliente sobre ese mismo resultado, no dos pedidos. La factory de esa consulta está definida en un solo lugar con la regla explícita de que ningún consumidor guarde una segunda copia.

Crear un álbum ya tiene su ruta (`/albums/new`).

## Goals / Non-Goals

**Goals:**

- Que la home no agregue una sola petición de red a lo que la aplicación ya pide.
- Que la coincidencia entre lo que dice la home de un álbum y lo que dice ese álbum no haya que mantenerla.
- Que los tres estados vacíos se distingan entre sí, en lugar de colapsar en una sección sin filas.

**Non-Goals:**

- Rediseñar el encabezado. Gana un enlace y nada más.
- Decidir el contenido de presentación de la landing más allá de qué pregunta responde.

## Decisions

### D1 - La home consume exactamente la misma consulta que la lista, no una propia

Lo pendiente por álbum se arma leyendo la consulta de álbumes que ya existe, con su misma clave, y filtrando en memoria los que tienen algo pendiente.

Es la decisión de la que cuelga todo lo demás. Como la consulta devuelve todos los álbumes con su `pendingCount` en una sola respuesta, la home no agrega ninguna petición: si alguien ya pasó por la lista, la home se dibuja del cache, y si entra directo a la home, la lista después no vuelve a pedir nada.

Y el requirement de que el número coincida entre la home y el álbum deja de ser algo que mantener: **es el mismo dato leído dos veces**, no dos cálculos que hay que mantener sincronizados. Un endpoint propio de "pendientes" habría sido la otra opción, y habría creado exactamente el problema que el spec quiere evitar — dos fuentes para el mismo número, capaces de discrepar.

La alternativa se vuelve atractiva solo cuando alguien tenga tantos álbumes que traerlos todos sea caro. Con un límite de 150 MiB por cuenta eso no ocurre, y si ocurriera, el cambio es interno: el spec no dice de dónde sale el número.

### D2 - El espacio se pide aparte y no bloquea el resto de la pantalla

El medidor de espacio viene del recurso de cuenta, en su propia consulta, pedida junto con la de álbumes y nunca esperada antes de dibujar.

Es el mismo patrón que la vista del álbum ya usa con las estadísticas del dueño: la pantalla aparece con lo que tiene, y el medidor se completa cuando llega. Si ese pedido falla, la home muestra el resto igual — quedarse sin ver el espacio no puede impedir ver qué falta calificar.

### D3 - La landing lee la sesión del contexto, sin consulta propia

El acceso de la landing decide su texto y su destino con la sesión que la ruta raíz ya resolvió y reparte por contexto. No agrega consulta ni deja de ser pública: quien no tiene sesión recibe el mismo contexto, con la sesión vacía.

### D4 - Los tres estados vacíos se escriben por separado

La home distingue explícitamente: sin álbumes, con álbumes y nada por calificar, y con álbumes y cosas por calificar.

Se escriben como tres casos y no como una condición sobre la longitud de una lista, porque los dos primeros se ven igual —una sección sin filas— y significan lo contrario: uno es "empezá por acá" y el otro es "ya terminaste". Colapsarlos es el error natural de implementación, y por eso el spec los separó en escenarios distintos.

### D5 - El encabezado gana un enlace, no una barra de navegación

Se agrega el enlace a la home junto al de álbumes, con el mismo tratamiento de estado activo que ya tiene ese. Dos enlaces no justifican un componente de navegación, un menú ni una estructura nueva.

## Risks / Trade-offs

**La landing espera la resolución de la sesión antes de dibujarse (D3)** → Es el comportamiento actual de todas las rutas, no algo que este change introduzca: la raíz de la aplicación resuelve la sesión para cualquier dirección. Tiene un costo real —la pantalla que ve alguien que nunca entró paga una ida y vuelta que va a responder que no hay sesión— y no se toca acá, porque ese mismo mecanismo es el que permite que ninguna ruta consulte la sesión por su cuenta. Si alguna vez importa, es un change propio sobre cómo se resuelve la sesión, no sobre estas dos pantallas.

**Traer todos los álbumes para mostrar solo los pendientes (D1)** → Es traer lo que la aplicación ya trae, no un pedido extra. El límite de la cuenta acota cuántos álbumes puede haber, y el día que deje de acotar, cambiar de dónde sale el número no toca el spec.

**La home depende de un recurso que introduce otro change (D2)** → La precedencia está declarada. Si se aplicara antes, el medidor quedaría sin datos y habría que volver sobre la misma pantalla.

## Migration Plan

No aplica. No hay datos, esquema ni configuración: son dos pantallas de la interfaz y un enlace. El rollback es revertir el commit, y lo que queda es lo que hay hoy.

## Open Questions

Ninguna. Las dos preguntas que este change podía dejar abiertas —qué es la home frente a la lista de álbumes, y qué hace la raíz con una sesión iniciada— las respondió el usuario antes de escribir el primer artefacto, y el resto se resolvió leyendo qué datos ya devuelve la aplicación.

### Resueltas durante la redacción

- **¿Hace falta un endpoint de "pendientes"? (D1)** No: la consulta de álbumes ya devuelve todos los álbumes con su cantidad pendiente en una sola respuesta, propios y compartidos. Usarla es además lo que vuelve automático el requirement de que los números coincidan. *Fuente: la factory de consulta de álbumes y la forma de su respuesta.*
- **¿La home agrega peticiones? (D1, D2)** Ninguna sobre álbumes, por compartir clave de consulta con la lista; una sola sobre el espacio, que no bloquea el dibujado. *Fuente: la clave de la consulta existente y el patrón que ya usan las estadísticas del álbum.*
- **¿Cómo sabe la landing si hay sesión, estando fuera del layout protegido? (D3)** Por el contexto: la ruta raíz resuelve la sesión para todas las direcciones, protegidas o no. *Fuente: el `beforeLoad` de la ruta raíz.*
- **¿Crear álbum necesita algo nuevo?** No, la ruta ya existe; la home solo la enlaza. *Fuente: el árbol de rutas del frontend.*
- **¿Por qué separar los estados vacíos en el diseño y no dejarlo a la implementación? (D4)** Porque los dos casos se ven igual —una sección sin filas— y significan lo contrario, así que colapsarlos es el resultado natural de no decidirlo antes. *Fuente: los escenarios del spec, que los distinguen explícitamente.*
