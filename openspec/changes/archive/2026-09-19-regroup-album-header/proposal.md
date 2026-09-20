## Why

En un viewport de teléfono, la pantalla de un álbum amontona su identidad y sus acciones en una sola fila. El header del layout (`albums/$albumId/route.tsx:40`) es un `flex items-center justify-between` sin `flex-wrap` y sin variación por ancho: los tres botones del dueño —Share, Upload photos y Rate N photos— se quedan con la mayor parte de los ~312px útiles de un viewport de 360px, y al título le sobran unos 60, que se parten en varias líneas junto con el vencimiento. Lo que se lee como "text-wrap agresivo" no es el título: es la fila que nunca se rompe.

A eso se suma que el dato que describe al álbum está lejos del álbum. La cantidad agregada de participantes y calificaciones no vive en ese header sino en la vista de galería (`albums/$albumId/index.tsx:119`), dos filas más abajo, apilada bajo los tabs de filtro y compartiendo fila con `Delete album`. Nombre, vencimiento y participación son tres caras de la misma cosa y hoy están repartidas entre dos componentes.

## What Changes

- La identidad del álbum pasa a ser un bloque único: título, descripción cuando la hay, vencimiento y —para el dueño— la cantidad de participantes y de calificaciones, en ese orden y como una sola columna.
- La cantidad agregada deja de renderizarse en la vista de galería y se renderiza en el header del layout. El dato es el mismo y el recurso que lo provee no cambia; cambia dónde se lee.
- Esa cantidad aparece únicamente en la vista del álbum. Las subvistas de upload y de swipe siguen mostrando la identidad del álbum, pero no su resumen de participación: ahí el conteo no acompaña ninguna decisión.
- Por debajo de `md`, las acciones dejan de compartir fila con la identidad y pasan a ocupar una fila propia debajo del bloque. Desde `md` siguen a la derecha, como hoy.
- Los tres botones del header ganan un área tocable de al menos 44 píxeles de alto por debajo de `md`, y conservan su tamaño actual a partir de ese ancho. Hoy son `size="sm"`, que en este design system son 28px de alto, muy por debajo de lo que exige `frontend-delivery` para el pulgar.
- No cambia qué muestra ninguna pantalla que no sea la del álbum, ni qué puede ver quién: el resumen agregado sigue siendo exclusivo del dueño y se sigue pidiendo por separado de la galería.

## Capabilities

### New Capabilities

Ninguna. La circulación entre pantallas ya la gobierna `app-navigation` y este change no la toca; lo que se agrega es cómo se compone una pantalla que ya existe.

### Modified Capabilities

- `album-management`: gana un requirement sobre la pantalla de un álbum. Hoy la capability declara qué es un álbum y qué información hace falta para reconocerlo, pero nada dice que esa información se presente junta: el vencimiento lo exige `album-retention` y el resumen de participación lo exige `album-stats`, cada uno por su lado, y ninguno de los dos puede afirmar que los dos datos y el nombre forman una unidad. Ese es el requirement que falta, junto con el de que las acciones del álbum no compitan con esa unidad por el mismo ancho en un viewport de teléfono.

No se modifican `album-retention` ni `album-stats`: qué se cuenta, quién lo ve y desde cuándo se informa el vencimiento siguen diciendo exactamente lo mismo. Tampoco `frontend-delivery`, cuyo requirement sobre área táctil suficiente para el pulgar ya cubre los botones del header sin necesidad de repetirlo.

## Impact

- `frontend/src/routes/_app/albums/$albumId/route.tsx`: el header se reordena, monta la query del resumen agregado y forkea por ancho.
- `frontend/src/routes/_app/albums/$albumId/index.tsx`: deja de renderizar la línea de participantes y calificaciones. Sigue consumiendo el mismo recurso para las cantidades por foto.
- Probable componente nuevo bajo `frontend/src/features/albums/`, que hoy solo tiene `api.ts`.
- Sin cambios de backend, de API, de esquema de datos ni de dependencias: el recurso de estadísticas ya existe y ya se consume.
- Queda fuera de alcance la fila de tabs de filtro y `Delete album` de la vista de galería, que en mobile también queda ajustada. Este change la deja como está.
