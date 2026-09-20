## Why

El atrás de las subvistas de un álbum es un link de texto de 12px sin área tocable propia (`text-muted-foreground text-xs` en `albums/$albumId/route.tsx`): unos 60x16 px reales, por debajo del mínimo de 24x24 de WCAG 2.2 SC 2.5.8 en el eje vertical y lejos de los 44x44 de las guías de plataforma. En desktop, con puntero, pasa; en mobile es un objetivo que se falla.

El swipe deck agrava el problema hasta volverlo estructural: el footer nav se oculta ahí a propósito, así que ese link minúsculo es la única salida de la pantalla — y encima salta dos niveles hasta la lista de álbumes en vez de volver al álbum del que se entró. `/albums/new`, a la que se llega por el botón central del footer nav, no tiene ninguna salida propia.

## What Changes

- Por debajo de `md`, el header superior gana un botón de atrás en el borde izquierdo, con área tocable de al menos 44x44, que lleva a la pantalla padre de la ruta activa. Aparece solo en subvistas: las pantallas que ya son destino del footer nav no lo llevan.
- El link de texto que hoy vive en el contenido sobrevive únicamente en `md` y mayores. Desktop queda exactamente como está, y por debajo del breakpoint se oculta para que nunca haya dos atrás en pantalla.
- El atrás del swipe deck pasa a volver al álbum del que se entró en lugar de a la lista de álbumes. Es un cambio de comportamiento observable, no solo de presentación.
- `/albums/new` entra en el esquema y gana un atrás hacia la lista de álbumes, que hoy no tiene.
- `/home` y `/albums` siguen sin atrás: son destinos del footer nav, no subvistas.
- El footer nav no se toca. Mantiene sus tres accesos y sigue oculto en el swipe deck: el atrás no es una pestaña, y mezclar una operación de pila con un conmutador entre destinos pares rompe la memoria muscular de la barra.
- El bloque de identidad del header (avatar y nombre) comparte fila con el botón nuevo en anchos de 360px; qué se cede ahí lo resuelve el diseño.

## Capabilities

### New Capabilities

- `app-navigation`: cómo se circula dentro de la aplicación una vez autenticado. Cubre qué pantallas son destinos y cuáles subvistas, que toda subvista tenga una salida visible hacia su pantalla padre sin recurrir a la navegación hacia atrás del navegador, y que esos controles sean operables con el dedo y no solo con un puntero. No cubre cuáles son las pantallas de entrada ni qué tiene que resolver cada una, que es asunto de `app-entry`, ni cómo se construye y se entrega la interfaz, que es asunto de `frontend-delivery`.

### Modified Capabilities

Ninguna. El requirement de `app-entry` sobre volver a la pantalla de entrada desde cualquier lugar sigue diciendo lo mismo y este change no altera cómo se llega ahí: lo que se agrega es subir un nivel en la jerarquía, que es una pregunta distinta de volver al inicio.

Queda registrado un hallazgo adyacente que este change no toma: ese requirement hoy no se cumple en mobile dentro del swipe deck, porque ahí el footer nav está oculto y los accesos a Home y Albums del header superior solo existen a partir de `md`. El atrás que introduce este change lo deja a un toque de distancia en vez de inalcanzable, pero no lo resuelve de frente. Corresponde a su propio change.

## Impact

- `frontend/src/routes/_app/route.tsx`: resuelve cuál es la pantalla padre de la ruta activa y renderiza el control en el header por debajo de `md`.
- `frontend/src/routes/_app/albums/$albumId/route.tsx`: el link de texto actual queda restringido a desktop y su variante de swipe cambia de destino.
- `frontend/src/routes/_app/albums/new.tsx`: pasa a tener pantalla padre declarada.
- Probable componente nuevo bajo `frontend/src/features/navigation/`, junto a `BottomNav`.
- Sin cambios de backend, de API, de esquema de datos ni de dependencias: el ícono sale de `lucide-react`, que ya es dependencia del proyecto.
