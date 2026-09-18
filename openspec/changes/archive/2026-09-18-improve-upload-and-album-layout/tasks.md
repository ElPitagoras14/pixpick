## 1. La salida de la vista de subida

- [x] 1.1 Hacer que el encabezado del álbum dibuje siempre el enlace de vuelta por encima del título, y que la subvista activa decida su destino: al álbum desde la subida, a la lista desde la grilla (D1). Verificar que la rama que hoy lo esconde desaparece en lugar de sumarse una nueva.
- [x] 1.2 Quitar el enlace de vuelta propio de la vista de subida. Verificar recorriendo la pantalla completa que queda exactamente uno.
- [x] 1.3 Verificar en la vista de subida que el acceso está por encima del título y lleva a ese álbum, no a la lista de álbumes.
- [x] 1.4 Verificar que no se movió nada más: la vista de subida sigue sin ofrecer las acciones del álbum, la grilla conserva su enlace a la lista y sus botones, y la subvista de calificación queda exactamente como estaba (D1).

## 2. La card de cada archivo

- [x] 2.1 Crear el componente que recibe un elemento de la cola y traduce su estado a lo que se muestra (D2), y dejar en la ruta solo la elección de archivos y la lista. Verificar que la ruta no conserva ninguna rama de presentación por estado.
- [x] 2.2 Mostrar el nombre recortando por el medio, de modo que los últimos caracteres queden siempre visibles (D3). Verificar con dos archivos cuyos nombres solo difieran en el último carácter y sean más largos que el ancho disponible: los dos tienen que poder distinguirse mirando la pantalla.
- [x] 2.3 Mostrar el tamaño de cada archivo, tomado del archivo local que la cola ya tiene (D4). Verificar que no se agrega ninguna petición de red.
- [x] 2.4 Dibujar la barra de avance a todo el ancho del bloque, sin compartir renglón con la identidad del archivo. Verificar a 360 píxeles de ancho que se lee y que no aparece desplazamiento horizontal.
- [x] 2.5 Mostrar el motivo cuando un archivo no termina bien, con el espacio que necesite aunque ocupe más de un renglón, incluyendo el dato que permite corregirlo cuando exista —cuánto espacio queda, cuánto lugar tiene el álbum—, y ofrecer reintentar solo ese archivo cuando el motivo lo admita. Verificar que reintentar uno no vuelve a subir los que ya terminaron.
- [x] 2.6 Agrupar los ocho estados en tres desenlaces visibles —en curso, terminado bien, no terminó— conservando la etiqueta propia de cada uno (D5). Verificar que el grupo se distingue sin leer el texto y que el texto sigue disponible para el detalle.

## 3. El resumen del lote

- [x] 3.1 Mostrar sobre la lista cuántos archivos terminaron y cuántos no (D6). Verificar que el orden de la lista sigue siendo el de la selección y que nada se reordena mientras las subidas avanzan.

## 4. Verificación final

- [x] 4.1 Recorrer un lote mixto real: elegir diez archivos y provocar que tres no terminen —uno que exceda el espacio disponible, uno que falle al transferirse y uno que el álbum no admita por estar lleno—. Verificar que los siete buenos se muestran terminados, que cada uno de los tres muestra su propio motivo, y que el resumen coincide sin tener que contar.
- [x] 4.2 Verificar que el módulo de la cola de subida no tiene ni un cambio (D7): el diff de este change no debe tocarlo.
- [x] 4.3 Verificar la pantalla con un lote de cincuenta archivos: que la lista siga siendo utilizable y que el resumen evite tener que recorrerla entera para saber cómo terminó todo.
- [x] 4.4 Correr `tsc --noEmit`, el linter y el build del frontend, y verificar que terminan limpios.
- [x] 4.5 Correr `openspec validate --changes improve-upload-and-album-layout --strict` y verificar que pasa.
