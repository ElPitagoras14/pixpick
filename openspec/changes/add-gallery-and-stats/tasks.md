## 1. La consulta compartida de fotos con calificación

- [x] 1.1 Implementar la consulta única de fotos disponibles con la calificación de quien pide, parametrizada por filtro, y hacer que la secuencia de calificación, el contador de pendientes y la galería la consuman (D1); verificar leyendo el código que las tres comparten implementación y no solo resultado.
- [x] 1.2 Verificar que el filtro de las sin calificar produce exactamente el mismo conjunto de fotos que entrega la secuencia de calificación, comparando los dos resultados y no solo sus cantidades.
- [x] 1.3 Calcular los cuatro conteos en una sola pasada sobre las mismas filas (D2); verificar que la respuesta los incluye siempre, cualquiera sea el filtro pedido.
- [x] 1.4 Verificar la partición: la suma de aprobadas, desaprobadas y sin calificar es igual al total, y ninguna foto aparece en más de un filtro.
- [x] 1.5 Implementar el endpoint de la galería con autorización de miembro; verificar que quien no es miembro ni dueño recibe la misma respuesta que si el álbum no existiera, y que dos miembros que calificaron distinto obtienen filtros distintos.
- [x] 1.6 Verificar que "sin calificar" y "rechazada" llegan como estados distinguibles y que ninguno se representa como la ausencia del otro, dado que colapsarlos rompería la partición y haría mentir al indicador.

## 2. Las estadísticas

- [x] 2.1 Implementar la agregación partiendo de las fotos y no de las calificaciones (D3); verificar que una foto que nadie calificó aparece con dos ceros y que no falta ninguna foto disponible.
- [x] 2.2 Incluir el resumen del álbum con cuántas personas participaron y cuántas calificaciones hay; verificar que el total coincide con la suma de las cantidades por foto.
- [x] 2.3 Implementar la autorización de las estadísticas; verificar los tres casos: el dueño accede, un miembro recibe que la acción está prohibida, y quien no es miembro ni dueño recibe la misma respuesta que si el álbum no existiera.
- [x] 2.4 Verificar que una foto cuya subida no se confirmó no figura en las estadísticas.
- [x] 2.5 Verificar que la respuesta no contiene nombres, correos ni identificadores, y que no permite atribuir una calificación a una persona determinada.
- [x] 2.6 Verificar que la respuesta de la galería **no** incluye las cantidades agregadas ni siquiera cuando quien pide es el dueño, porque la separación entre los dos recursos es lo que resuelve quién puede verlas.
- [x] 2.7 Verificar que una calificación nueva y un cambio de opinión se reflejan en las estadísticas al volver a pedirlas, sin valores calculados de antemano.

## 3. La galería

- [x] 3.1 Declarar el filtro como parte de la dirección con sus cuatro valores y el de omisión (D9); verificar que recargar conserva el filtro, que abrir una dirección filtrada muestra lo mismo, y que un filtro desconocido cae al de omisión sin producir un error.
- [x] 3.2 Implementar las solapas con la cantidad de cada filtro tomada de la propia respuesta (D2); verificar que cambiar de solapa no emite una petición adicional solo para conocer las cantidades.
- [x] 3.3 Implementar el indicador por foto con sus tres estados; verificar en pantalla que no calificada se distingue a simple vista de rechazada.
- [x] 3.4 Implementar el cambio de calificación tocando el indicador, con una mutación optimista común y **no** con la cola del swipe (D6); verificar que emplea la misma operación de API que la secuencia.
- [x] 3.5 Hacer que al cambiar una calificación cambie el indicador pero la foto **no se arranque** de la lista (D7); verificar que la lista no salta bajo el dedo y que al volver a pedir el filtro la foto ya no aparece.
- [x] 3.6 Ofrecer el camino a retomar la secuencia cuando queden pendientes y ocultarlo cuando no; verificar los dos casos.
- [x] 3.7 Verificar que las fotos aparecen en el orden del álbum en los cuatro filtros, sin reordenarse por calificación ni por cuándo se emitió.

## 4. Conteos y resumen para el dueño

- [x] 4.1 Pedir la galería y las estadísticas en paralelo y dibujar el grid sin esperar los conteos (D5); verificar que el grid aparece antes de que lleguen las estadísticas.
- [x] 4.2 Superponer los conteos sobre el grid, ubicándolos como una franja compacta debajo de cada miniatura en anchos chicos (Risks); verificar en un viewport de 360px que no tapan la foto y que no compiten con el indicador de la propia calificación.
- [x] 4.3 Mostrar el resumen del álbum en el encabezado para el dueño (D8); verificar que para un miembro que no es dueño esa zona no existe, en lugar de mostrarse vacía.
- [x] 4.4 Verificar que no existe ninguna ruta ni pantalla de estadísticas separada.

## 5. La lista de álbumes en dos grupos

- [x] 5.1 Separar la lista en el grupo de los propios y el de los compartidos, con la selección en la dirección igual que el filtro de la galería (D10); verificar que recargar conserva el grupo seleccionado.
- [x] 5.2 Calcular la cantidad de cada grupo en el cliente a partir de la respuesta que ya se recibe; verificar que mostrar los dos números no emite ninguna petición adicional y que el backend no cambió.
- [x] 5.3 Implementar el estado vacío de cada grupo diciendo qué aparecería ahí; verificar que un grupo sin álbumes no se confunde con una lista que no terminó de cargar.
- [x] 5.4 Verificar que los dos grupos no se mezclan: el de propios muestra solo los propios y el de compartidos solo aquellos de los que se es miembro sin ser dueño.
- [x] 5.5 Verificar que la comprobación de estilo y la construcción del frontend pasan sin errores.

## 6. Documentación

- [x] 6.1 Actualizar el README con el flujo completo de punta a punta —crear, subir, compartir, calificar, mirar resultados— ahora que el recorrido está entero; verificar siguiendo las instrucciones tal como están escritas.

## 7. Verificación integral

- [x] 7.1 Recorrer el flujo completo del producto con dos cuentas, desde crear un álbum hasta que el dueño ve los conteos de cada foto.
- [x] 7.2 Verificar que las tres vistas de lo pendiente coinciden, que bajan juntas al calificar una foto y que suben juntas cuando el dueño agrega fotos nuevas.
- [x] 7.3 Verificar la partición desde la interfaz: las cantidades de las tres solapas parciales suman la de todas.
- [x] 7.4 Corregir desde la galería una calificación emitida con el gesto, cerrando el hueco que el change anterior dejó abierto a propósito.
- [x] 7.5 Verificar la galería, las estadísticas y la lista en dos grupos en el **modo nativo** de trabajo.
