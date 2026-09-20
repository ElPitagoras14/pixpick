## 1. Resolución del destino en AppLayout

- [x] 1.1 Extender `_app/route.tsx` con los matches que le faltan (`/albums/new`, `/albums/$albumId`, `/albums/$albumId/upload`) y derivar de ellos un único valor de destino, o ninguno cuando la pantalla es un destino de la navegación principal, tomando el `albumId` del valor que devuelve el match en lugar de descartarlo con `!!`; verificar con `npx tsc --noEmit` que el destino queda tipado sin type assertions ni acceso opcional defensivo.
- [x] 1.2 Ordenar las comprobaciones de la más específica a la más general y con las rutas estáticas antes que las dinámicas; verificar abriendo `/albums/new` y un álbum real que cada una resuelve su propio destino y que `new` nunca se trata como el id de un álbum.

## 2. Control de salida en el header

- [x] 2.1 Crear el componente de salida en `features/navigation/`, que recibe el destino ya resuelto como prop y no renderiza nada cuando no hay destino; verificar que `/home` y `/albums` no muestran ningún control y que las cuatro subvistas sí.
- [x] 2.2 Montarlo en el header de `AppLayout` visible solo por debajo de `md`, con área activable de al menos 44 por 44 píxeles CSS; verificar con el inspector midiendo el área activable del botón y no la caja del ícono.
- [x] 2.3 Ocultar el nombre del usuario por debajo de `md` dejando el avatar; verificar a 360px de ancho que la fila del header entra sin desbordar ni envolverse, incluso con un nombre largo.
- [x] 2.4 Verificar que el control recibe el foco recorriendo la pantalla con el teclado, que el foco se ve, y que se acciona desde ahí sin usar el puntero.

## 3. Salida en el contenido y destinos corregidos

- [x] 3.1 En `albums/$albumId/route.tsx`, reemplazar la condición que hoy distingue la vista de upload por una que distinga subvista del álbum, de modo que upload y swipe vuelvan al álbum y el álbum vuelva a la lista; verificar los tres destinos en desktop, prestando atención a que el swipe deck ya no salte a la lista.
- [x] 3.2 Pasar ese link a visible solo desde `md` en adelante; verificar a 360px que el único control es el del header y a 1024px que el único control es el del contenido.
- [x] 3.3 Agregar la salida hacia la lista de álbumes en `albums/new.tsx`, con el mismo tratamiento visual que la del álbum; verificar en desktop que la pantalla deja de quedarse sin salida.

## 4. Verificación de los escenarios del spec

- [x] 4.1 Abrir cada una de las cuatro subvistas por enlace directo en una pestaña nueva, sin historial previo, y verificar en cada una que la salida está visible y lleva al destino esperado sin recurrir al atrás del navegador.
- [x] 4.2 Verificar en el swipe deck a 360px que la salida sigue visible con el footer nav oculto, y que permite abandonar la pantalla.
- [x] 4.3 Recorrer las cuatro subvistas a 360px y a 1024px contando los controles de salida en pantalla, y verificar que en ningún caso hay más de uno ni menos de uno.
- [x] 4.4 Correr `npm run check` y `npx tsc --noEmit` en `frontend/` y verificar que ambos pasan sin hallazgos.
