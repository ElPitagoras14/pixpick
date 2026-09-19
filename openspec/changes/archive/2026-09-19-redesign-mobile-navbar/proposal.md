## Why

El header de `_app/route.tsx` es el mismo en mobile y en desktop: mezcla navegación (Home/Albums), identidad (avatar+nombre) y logout en una sola fila angosta. En mobile eso le come espacio a lo que más se usa y deja la acción de crear un álbum como un link suelto dentro de cada pantalla (`home.tsx`, `albums/index.tsx`) en lugar de vivir en la navegación misma.

## What Changes

- En viewports por debajo de `md` (768px), reemplaza la navegación superior por un footer nav fijo con dos accesos (Home, Albums) más un botón central destacado (ícono Plus) que lleva a `/albums/new`.
- Home y Albums en el footer nav llevan ícono + label, con estado activo visible.
- El botón central Plus queda elevado/flotante sobre la barra (más grande, color primary, sobresaliendo), distinto de Home/Albums.
- El header superior en mobile se reduce a lo que no se usa frecuente: avatar, nombre y logout. Los links Home/Albums se sacan de ahí.
- En `md` y viewports mayores, el header superior actual (Home/Albums + avatar/nombre + logout, todo en una fila) no cambia.
- El footer nav se oculta en `/albums/$albumId/swipe` para no competir con los gestos de calificación de esa pantalla.
- Los links "New album" / "Create your first album" existentes en `home.tsx` y `albums/index.tsx` no se eliminan: siguen siendo un acceso adicional a la misma ruta `/albums/new`, no el único.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

(ninguna — el requirement de `app-entry` sobre volver a la pantalla de entrada "desde cualquier lugar" ya no prescribe estructura visual, y sigue cumplido tanto por el header superior en desktop como por el footer nav en mobile; el requirement de `frontend-delivery` sobre viewport de teléfono como caso base tampoco cambia, este change lo refuerza. Es un cambio de "cómo se ve", no de "qué debe cumplir".)

## Impact

- `frontend/src/routes/_app/route.tsx`: separa el header actual en una barra superior reducida (avatar/nombre/logout) y un footer nav nuevo, condicionados por breakpoint.
- Componente nuevo para el footer nav (Home, Albums, Create Album) bajo `frontend/src/features/` o `frontend/src/components/`.
- El footer nav necesita saber si la ruta activa es `/albums/$albumId/swipe` para ocultarse ahí.
- Sin cambios de API, backend, ni de esquema de datos.
