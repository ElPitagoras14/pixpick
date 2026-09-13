## Why

Cierra el flujo completo del producto. El recorrido que motivó todo esto —crear un álbum, subir fotos, compartirlo, esperar las aprobaciones y **ver el resultado de cada foto**— llega hasta la anteúltima estación con los seis changes anteriores. Faltan las dos piezas finales: mirar un álbum ya calificado y ver qué opinó la gente.

Cierra además un hueco que el change anterior dejó abierto a propósito. Al calificar con un gesto, un movimiento equivocado quedaba sin forma de corregirse: no hay deshacer en el swipe porque la corrección vive acá, en la galería, donde se ve lo que uno decidió y se puede cambiar sin prisa.

Vale señalar una propiedad de este change: **no toca el esquema**. Todo lo que muestra sale de datos que ya existen, combinados de otra manera. Es la primera vez en el proyecto que un change no agrega una tabla ni una columna, y es la señal de que el modelo de datos aguantó lo que se le pidió.

## What Changes

- **La galería del álbum con cuatro filtros**: todas, las aprobadas, las desaprobadas y las que quedan sin calificar. El filtro vive en la dirección, de modo que una vista filtrada se puede compartir por link y sobrevive a recargar la página.
- **Cada foto muestra en una esquina qué decidió quien mira**, con un indicador distinto para la aprobación y para el rechazo, y sin indicador cuando todavía no la calificó.
- **La calificación se puede cambiar desde la galería**, tocando el indicador. Reutiliza la misma operación idempotente que usa el swipe, así que no hay una manera nueva de calificar sino otra entrada a la misma.
- **Las fotos sin calificar aparecen en la vista de todas** y tienen además su propio filtro, desde el cual hay un camino directo a retomar la secuencia de calificación con lo que falta. Ese filtro es, exactamente, el conjunto de pendientes que ya alimentan la secuencia de swipe y el contador del álbum: **la misma comparación con un tercer consumidor**, no una consulta nueva.
- **Estadísticas por foto para el dueño**: cuántas aprobaciones y cuántos rechazos acumuló cada una, más el total del álbum.
- **El dueño ve las estadísticas sobre el mismo grid** que la galería, con el resumen del álbum en el encabezado. No hay una pantalla de estadísticas aparte: sin ordenamiento por popularidad, que está fuera de alcance, esa pantalla sería la galería con números y sin filtros.
- **La lista de álbumes se separa en dos grupos**: los propios y los compartidos. Responden a intenciones distintas —en los propios se entra a administrar y ver resultados, en los compartidos a calificar o revisar lo que uno opinó— y mezclarlos obliga a leer cada entrada para saber cuál es cuál. La selección vive en la dirección, igual que el filtro de la galería.
- **Dos endpoints separados y no uno con campos condicionales**: la galería la consumen todos los miembros y devuelve la calificación de quien pide; las estadísticas las consume solo el dueño y devuelven los conteos. La frontera de autorización queda en el ruteo y no dentro del armado de la respuesta.

### Fuera de alcance

- **Quién calificó qué.** Las estadísticas son agregadas: dicen cuántos aprobaron, no quiénes. Es una decisión tomada al principio del proyecto y este change la respeta.
- Ordenar el álbum por cantidad de aprobaciones, o filtrar por las más votadas.
- Exportar o descargar el resultado.
- Comparar dos álbumes, o cualquier estadística que cruce álbumes.
- Notificar al dueño cuando alguien termina de calificar.
- Comentarios sobre las fotos.
- Cualquier cambio en el esquema: si algo pareciera necesitarlo, es señal de que se está saliendo del alcance.
- Los adapters cloud.

## Capabilities

### New Capabilities

- `rating-gallery`: cómo se mira un álbum calificado, qué filtros existen y cómo se expresan, qué muestra cada foto sobre la decisión de quien mira, cómo se corrige una calificación ya emitida, y cómo se retoma lo que falta.
- `album-stats`: qué información agregada existe sobre las calificaciones de un álbum, quién puede verla, cómo se relaciona con lo que ve un miembro común, y qué no revela.

### Modified Capabilities

- `album-management`: su requirement de listado ya distingue los álbumes propios de los compartidos desde el change anterior, pero no dice nada sobre cómo se presentan. El delta agrega que se muestren en grupos separados y que la selección forme parte de la dirección. Es un requirement de presentación y no de datos: la respuesta de la API no cambia, porque ya trae todo lo necesario para separarlos.

La capability de calificación, en cambio, **no** se modifica, y conviene decir por qué porque es un resultado y no una casualidad: ya establece que calificar es idempotente y que emitir una calificación distinta reemplaza la anterior, así que corregir desde la galería no requiere ningún comportamiento nuevo — es la misma operación con otra puerta de entrada.

## Impact

**Archivos nuevos**

- `backend/src/packages/photos/` gana la lectura del álbum con la calificación de quien pide y su filtro
- `backend/src/packages/ratings/` gana la consulta agregada por foto
- Pruebas de la galería con sus cuatro filtros y su partición, de la edición desde la galería, y de la autorización de las estadísticas
- `frontend/src/features/gallery/`, con el grid filtrable, el indicador por foto y la presentación de los conteos para el dueño

**Archivos modificados**

- `frontend/src/routes/_app/albums/index.tsx` y `frontend/src/features/albums/`: la lista se separa en los dos grupos, con la selección en la dirección.
- `frontend/src/routes/_app/albums/$albumId/index.tsx`: la vista del álbum deja de ser un grid simple y pasa a ser la galería con filtros, que para el dueño incorpora además los conteos y el resumen. No se agrega ninguna ruta nueva.
- `backend/src/routes.py`: montaje de los endpoints nuevos.
- `README.md`: el flujo completo de punta a punta.

**Dependencias**

Ninguna nueva de ningún tipo, y **ninguna migración**: este change combina datos que ya existen. Tampoco agrega variables de entorno.

**Precedencia**

Depende de `add-share-and-swipe`, que aporta las calificaciones y la membresía sobre las que todo esto se construye.
