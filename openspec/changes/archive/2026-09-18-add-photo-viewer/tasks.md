## 1. El backend expone la variante grande

- [x] 1.1 Agregar a la respuesta de la galería la dirección de la variante de mayor calidad, armada con el mismo puerto de imágenes que ya arma la de la miniatura. Verificar que no se agrega ninguna consulta ni cambia el esquema.
- [x] 1.2 Verificar contra el entorno real que esa dirección devuelve una imagen: pedirla a través de nginx y comprobar que llega con el lado mayor esperado, sin recorte y sin haber ampliado un original más chico.
- [x] 1.3 Verificar que la respuesta sigue llevando la miniatura tal como estaba: el campo nuevo se suma, no reemplaza.

## 2. La foto deja de recortarse donde se la mira

- [x] 2.1 Quitar de la tarjeta de la grilla la proporción de la foto y dejar el contenedor cuadrado (D7). Verificar que la miniatura ya no se recorta dos veces y que la cuadrícula queda pareja.
- [x] 2.2 Cambiar la tarjeta del mazo de llenado a ajuste, conservando su proporción fija (D7). Verificar que una foto apaisada se ve entera dentro de la tarjeta y que todas las tarjetas siguen midiendo lo mismo.
- [x] 2.3 Verificar los dos cambios con fotos reales de las tres formas —apaisada, vertical y cuadrada— y comprobar que ninguna se deforma.

## 3. El visor

- [x] 3.1 Crear el componente del visor, que muestra la foto completa sirviendo la variante de mayor calidad y nunca el original.
- [x] 3.2 Expresar la foto abierta como un parámetro de la dirección sobre la pantalla que ya está montada, sin navegar a una ruta hija (D1, D2). Definir el nombre del parámetro en un solo lugar, ya que lo usan dos pantallas.
- [x] 3.3 Abrir el visor al tocar una foto de la grilla. Verificar que la grilla queda montada debajo y no se reconstruye.
- [x] 3.4 Abrir el visor al tocar la foto del mazo, usando el dato de toque que el gesto de arrastre ya expone, sin agregar un manejador aparte (D4). Verificar que arrastrar sigue calificando, que tocar abre, y que un movimiento corto e intermedio no hace las dos cosas.
- [x] 3.5 Implementar el paso a la foto siguiente y anterior sobre la lista que la pantalla le pasa al visor (D3). Verificar con un filtro aplicado en la galería que el recorrido solo muestra las fotos de ese filtro.
- [x] 3.6 Reiniciar el acercamiento al cambiar de foto, y dejar claro cuándo no hay más en una dirección. Verificar los dos extremos del conjunto.
- [x] 3.7 Verificar que cerrar devuelve a la pantalla de origen con su filtro y su posición de desplazamiento intactos, tanto con el botón de cerrar como con el botón de atrás del navegador.

## 4. El acercamiento

- [x] 4.1 Implementar acercar y alejar con pellizco, rueda y doble toque, usando la biblioteca de gestos que ya está instalada (D5). Verificar que no se agregó ninguna dependencia.
- [x] 4.2 Implementar el desplazamiento sobre la foto ampliada, acotado a sus bordes. Verificar que se puede llegar a cualquier zona y que no se puede arrastrar la foto fuera de la vista.
- [x] 4.3 Volver al tamaño completo en un solo paso. Verificar que no hay que alejarse gradualmente.
- [x] 4.4 Calcular el tope de acercamiento a partir del tamaño real de la imagen cargada frente al tamaño mostrado (D6). Verificar que no se puede ampliar más allá de ese punto y que el límite se ajusta solo al cambiar el tamaño de la ventana.
- [x] 4.5 Verificar en una pantalla táctil que acercarse sobre la foto no mueve ni amplía la página de atrás.

## 5. Verificación final

- [ ] 5.1 Probar con dedos en un teléfono real —no simulado— el pellizco, el desplazamiento, el doble toque y el paso entre fotos, y comprobar que el arrastre del mazo sigue calificando igual que antes. Es la parte de este change que no se verifica leyendo código; si no hay un dispositivo disponible, dejarlo dicho en vez de darlo por hecho.
  - No se hizo: no hubo un teléfono disponible en esta sesión. Lo que sí se verificó, en Chromium con emulación táctil y eventos de dos dedos despachados por el protocolo de devtools: el pellizco acerca y aleja, el doble toque acerca y vuelve al tamaño completo, el desplazamiento llega a los bordes y se detiene en ellos, el paso entre fotos funciona, y el arrastre del mazo sigue calificando igual. Queda sin verificar con dedos reales, que es distinto de emulado.
- [x] 5.2 Recorrer el ciclo completo con un álbum de fotos de formas mezcladas: abrir desde la grilla con un filtro aplicado, recorrer todo el conjunto filtrado, acercarse en una, cerrar, y comprobar que se vuelve al mismo punto.
- [x] 5.3 Verificar el mismo recorrido desde el mazo: abrir la foto que se está calificando, acercarse, cerrar, y comprobar que sigue sin calificar y que el mazo quedó donde estaba.
- [x] 5.4 Correr la suite del backend con `ruff format` y `ruff check`, y `tsc --noEmit`, el linter y el build del frontend, y verificar que todo termina limpio.
- [x] 5.5 Correr `openspec validate --changes add-photo-viewer --strict` y verificar que pasa.
