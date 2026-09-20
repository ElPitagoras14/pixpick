## 1. Bloque de identidad

- [x] 1.1 Crear `features/albums/AlbumHeader.tsx` con el bloque de identidad en una sola columna -- título, descripción cuando existe, vencimiento y resumen de participación -- recibiendo el álbum y el resumen ya resueltos por props, sin montar ninguna query propia; verificar con `npx tsc --noEmit` que el resumen entra como opcional y que el componente no necesita saber si quien mira es el dueño.
- [x] 1.2 Hacer que el componente no renderice nada en lugar del resumen cuando no lo recibe, sin contenedor, sin separador y sin alto reservado; verificar con el inspector en un álbum ajeno que entre el vencimiento y lo que sigue no queda ningún nodo vacío.

## 2. Header del layout

- [x] 2.1 Montar `albumStatsQueryOptions` en `albums/$albumId/route.tsx` con `enabled` atado a que quien mira sea el dueño y a que la pantalla sea la vista del álbum; verificar en las herramientas de red que abrir el álbum dispara una sola petición de estadísticas y que entrar a upload o a swipe no dispara ninguna.
- [x] 2.2 Reemplazar el bloque de título inline por `AlbumHeader`, pasándole el resumen solo cuando la pantalla es la vista del álbum y no cuando simplemente hay dato en cache; verificar entrando al álbum y navegando desde ahí a upload y a swipe que el resumen desaparece en las dos subvistas aunque ya se haya cargado antes.
- [x] 2.3 Dejar el link de vuelta de desktop fuera de `AlbumHeader`, como hermano anterior dentro del header; verificar a 1024px que sigue apareciendo arriba del título y que en el DOM no queda dentro del bloque de identidad.
- [x] 2.4 Cambiar el contenedor del header a columna por defecto y a fila desde `md`, con las acciones alineadas al inicio del bloque; verificar a 360px que las acciones quedan debajo de la identidad y a 1024px que vuelven al costado alineadas con el título.

## 3. Galería

- [x] 3.1 Quitar de `albums/$albumId/index.tsx` la línea de participantes y calificaciones, conservando la query de estadísticas que alimenta las cantidades por foto; verificar que las tarjetas del grid siguen mostrando sus cantidades y que la línea ya no aparece bajo los tabs.
- [x] 3.2 Revisar que el contenedor del que se retiró esa línea no quede con un envoltorio de un solo hijo ni con separación sobrante; verificar visualmente que los tabs de filtro y `Delete album` conservan la misma posición que antes del cambio.

## 4. Área táctil de las acciones

- [x] 4.1 Llevar `Upload photos` y `Rate N photos` a 44px de alto por debajo de `md`, conservando su alto actual desde ese ancho; verificar midiendo el área activable en el inspector, no la caja del texto.
- [x] 4.2 Aplicar el mismo tratamiento al trigger de `Share` dentro de `features/shares/ShareDialog.tsx`; verificar que los tres controles miden lo mismo entre sí a 360px y lo mismo entre sí a 1024px.

## 5. Verificación de los escenarios del spec

- [x] 5.1 Abrir como dueño un álbum con calificaciones a 360px y verificar que nombre, vencimiento y resumen aparecen contiguos, sin ningún control ni sección intercalada entre ellos.
- [x] 5.2 Abrir el mismo álbum con una cuenta que sea miembro y no dueña, y verificar que se ven nombre y vencimiento, que no aparece el resumen y que no queda hueco en su lugar.
- [x] 5.3 Entrar a upload y a swipe como dueño y verificar en cada una que la identidad del álbum sigue visible y que el resumen no.
- [x] 5.4 Verificar a 360px que el título dispone del ancho completo del contenido y que ninguna acción comparte línea con él, comparando contra el comportamiento previo con un título de varias palabras.
- [x] 5.5 Verificar a 360px que la pantalla no produce desplazamiento horizontal, con un álbum que tenga los tres botones visibles.
- [x] 5.6 Correr `npm run check` y `npx tsc --noEmit` en `frontend/` y verificar que ambos pasan sin hallazgos.
