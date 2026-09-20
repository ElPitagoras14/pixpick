## Context

El álbum se carga una sola vez, en el loader del layout `albums/$albumId/route.tsx`, y las vistas que cuelgan de él lo leen del cache de react-query en lugar de volver a pedirlo. Ese layout dibuja hoy una única fila con dos hijos: un bloque con el link de vuelta de desktop, el título, la descripción y el vencimiento, y un bloque con las acciones del dueño. La fila es `flex items-center justify-between gap-4`, sin `flex-wrap` y sin ninguna variante por ancho, así que su reparto es el mismo a 360px que a 1440px.

El resumen agregado del álbum es otro recurso y se pide aparte: `albumStatsQueryOptions` se monta en la vista de galería (`albums/$albumId/index.tsx`) con `enabled: album.isOwner`, sin bloquear al grid, y de esa misma respuesta salen las cantidades por foto que el grid usa en cada tarjeta. La línea de participantes y calificaciones se renderiza ahí, bajo los tabs de filtro.

Las acciones del header son tres y no viven todas en el mismo archivo: `Upload photos` y `Rate N photos` son `Button size="sm"` en el layout, y `Share` es el trigger que `features/shares/ShareDialog.tsx` renderiza por su cuenta. En este design system `size="sm"` son 28px de alto.

## Goals / Non-Goals

**Goals:**

- Que el resumen agregado se lea junto al nombre y al vencimiento sin que eso signifique pedirlo dos veces ni moverlo de recurso.
- Que el fork por ancho sea un cambio de eje y no un cambio de contenido: el mismo árbol en los dos anchos.
- Que los tres controles del header alcancen el umbral táctil sin alterar su tamaño en desktop.

**Non-Goals:**

- Cambiar qué devuelve el backend, cuándo se pide o quién puede pedirlo.
- Rediseñar la tipografía o la jerarquía visual del título más allá del reordenamiento.
- Tocar la fila de tabs de filtro y `Delete album` de la vista de galería.

## Decisions

### D1. El resumen se monta en el layout, no se sube por contexto ni se baja el título

La query del resumen pasa a montarse también en el layout, con la misma `queryKey` que ya usa la galería. No es una segunda petición: react-query resuelve los dos consumidores contra la misma entrada de cache, que es el mismo mecanismo por el que la galería lee el álbum sin volver a pedirlo. La galería conserva su propio uso del recurso, porque de ahí salen las cantidades por foto de cada tarjeta.

Alternativas descartadas: pasar el resumen desde la galería hacia arriba por el contexto del router invierte el sentido natural del árbol y obliga al layout a renderizar dos veces, una sin dato y otra con él, para algo que el cache ya resuelve; y mover el título hacia abajo, a la vista de galería, deja a las subvistas de upload y swipe sin identidad de álbum, que es justo lo que el spec exige conservar.

### D2. La condición de render es la ruta, no la presencia del dato

El resumen se renderiza si la pantalla es la vista del álbum y quien mira es el dueño, no si hay dato en mano. La distinción importa: `enabled: false` impide disparar la petición, pero no vacía el cache, así que alguien que entra al álbum y después pasa a cargar fotos seguiría teniendo el resumen disponible en el cache y lo vería aparecer en una pantalla donde el spec dice que no va. El `enabled` queda entonces como optimización de red -- no pedir lo que no se va a mostrar -- y el render lo decide `isAlbumView`, que el layout ya calcula para elegir a dónde apunta el link de vuelta.

### D3. Un solo árbol y una clase responsive, no dos bloques alternados

El fork se hace con `flex-col md:flex-row md:items-start md:justify-between` sobre el contenedor que ya existe. El change anterior de navegación resolvió su propio fork duplicando controles y ocultando uno con `md:hidden` y el otro con `hidden md:block`, pero ahí el contenido y el destino eran distintos en cada ancho. Acá no cambia nada más que la dirección del eje, y duplicar el árbol dejaría dos `h1` con el mismo texto en el DOM, que es un problema para quien navega con lector de pantalla y no gana nada a cambio.

El `items-center` actual pasa a `md:items-start`: con el bloque de identidad ahora de tres o cuatro líneas, centrar las acciones contra él las deja flotando a media altura en lugar de alineadas con el título al que pertenecen.

### D4. El bloque de identidad se extrae a un componente propio

El bloque pasa a `features/albums/AlbumHeader.tsx`, que recibe el álbum y el resumen ya resueltos y no pide nada por su cuenta. Es la misma división que el repo ya usa entre `AppLayout` y `BackButton`, donde el layout resuelve y el componente solo dibuja, y evita que `route.tsx` acumule el reordenamiento, el fork y las dos queries en un solo cuerpo de función.

El link de vuelta de desktop queda **fuera** de ese componente, como hermano anterior dentro del header: es navegación, no identidad, y meterlo adentro del bloque contradiría el requirement de que entre los datos de identidad no se intercale ningún control.

### D5. El umbral táctil se aplica con una clase por breakpoint sobre cada botón

Los tres controles llevan `h-11 md:h-7`: 44px donde se toca, y los 28px actuales desde `md`, donde se apunta con puntero. No se agrega un `size` nuevo al design system por tres botones de una pantalla, ni se sube `size="sm"` a `default`, que son 32px y tampoco alcanzan.

El trigger de `Share` vive dentro de `ShareDialog`, que tiene un único consumidor -- este header --, así que la clase se aplica ahí directamente en lugar de abrirle una prop de tamaño que ningún segundo consumidor justifica.

### D6. Orden de lectura del bloque

Título, descripción cuando existe, vencimiento y resumen, en ese orden y en una sola columna. La descripción se queda donde ya está, entre el título y el vencimiento: ninguna decisión de este change la mueve, y bajarla por debajo de los datos de estado la convertiría en un pie de bloque cuando es parte de lo que el álbum es.

## Risks / Trade-offs

- El resumen llega después que el álbum, así que el bloque crece de alto cuando aparece. Mitigación: el salto ya ocurre hoy, solo que más abajo en la pantalla; no se reserva espacio para evitarlo porque un hueco reservado es exactamente lo que el spec prohíbe mostrarle a quien no es dueño, y distinguir "todavía no llegó" de "no corresponde" a nivel de layout duplica la condición en dos lugares.
- `h-11 md:h-7` convive con la altura que `size="sm"` ya declara en la misma clase de variante. Mitigación: tailwind-merge resuelve el conflicto quedándose con la última, pero es el tipo de override que se rompe en silencio si el orden cambia, así que se verifica midiendo el área activable en el inspector y no leyendo el código.
- Montar la query en dos componentes acopla el header a un recurso que hoy solo consume la galería. Mitigación: cada consumidor declara su propia query y ninguno depende de que el otro esté montado, así que el header sigue funcionando por su cuenta si mañana el layout deja de renderizar la galería como hija.
- En `md` el bloque de identidad y las acciones vuelven a compartir fila, así que un título muy largo vuelve a competir por el ancho. Mitigación: a ese ancho hay espacio de sobra para los tres botones y el `max-w-3xl` del contenedor acota el resto; el spec fija el orden de lectura solo en viewport de teléfono y permite explícitamente la disposición ancha.

## Open Questions

Ninguna. El alcance quedó cerrado en la conversación previa: qué pantallas muestran el resumen, cómo se ordenan los datos del bloque, si había fork por ancho y si los touch targets entraban son todas respuestas del usuario, y la única decisión que quedó delegada -- en qué capability vive el requirement -- se resolvió leyendo los Purpose de las capabilities candidatas.

### Resueltas durante la redacción

- ¿El resumen acompaña también a upload y swipe? Respuesta del usuario: solo la vista del álbum.
- ¿Nombre y vencimiento en la misma línea, como pedía el planteo inicial? Respuesta del usuario tras ver el trade-off: vencimiento debajo del nombre y resumen debajo del vencimiento. Esto además disuelve un conflicto que el análisis había detectado: con el vencimiento a la derecha del título, en `md` habría competido por el mismo eje con las acciones que vuelven a esa posición.
- ¿Una sola disposición para todo ancho o fork por viewport? Respuesta del usuario: con fork.
- ¿Entran los touch targets de los botones del header? Respuesta del usuario: sí.
- ¿Entra la fila de tabs y `Delete album`, que en mobile también queda ajustada? Respuesta del usuario: dejarla fuera.
- ¿En qué capability vive el requirement? Delegado por el usuario y resuelto leyendo los Purpose: `album-retention` y `album-stats` gobiernan cada dato por separado y ninguna puede afirmar que forman una unidad; `app-navigation` gobierna circulación, no composición; `frontend-delivery` gobierna construcción y entrega, y su requirement táctil ya cubre estos botones. Queda `album-management`, cuyo Purpose ya declara qué información hace falta para reconocer un álbum.
- ¿`size="sm"` son 32px, como se asumió al principio? No: verificado en `components/ui/button.tsx`, son `h-7`, 28px. El dato cambia cuánto falta para el umbral, no la decisión.
- ¿El trigger de `Share` se puede tocar sin afectar a otras pantallas? Verificado con una búsqueda de usos: `ShareDialog` se monta en un único lugar, este header.
