## Why

Una foto apaisada nunca se ve entera en este producto.

En la tarjeta de calificación, que es donde se decide si una foto sirve o no, la tarjeta tiene forma vertical fija y la imagen se recorta para llenarla. De una foto apaisada se ve la franja del medio. El catálogo de variantes del backend dice, en su propio comentario, que la variante de calificación nunca recorta porque «recortarla invalidaría la decisión que se está tomando» — y la interfaz la recorta igual al mostrarla. La intención estaba escrita en un comentario y ninguna spec la exigía, así que nada podía detectar la contradicción.

En la grilla del álbum pasa algo parecido y duplicado. La miniatura que produce el backend es un recorte cuadrado deliberado, pero la tarjeta fija el contenedor con la proporción original de la foto: a una foto apaisada se le recorta un cuadrado y después ese cuadrado se recorta de nuevo para entrar en un contenedor apaisado. Dos decisiones que se contradicen entre sí, y ninguna de las dos sobrevive sola.

Y no hay ningún lugar donde ver una foto con detalle. Ni un acercamiento, ni la foto completa, ni nada más grande que una miniatura recortada — aunque el backend ya sabe producir una variante grande sin recortar, que hoy no usa nadie.

## What Changes

- **La tarjeta de calificación muestra la foto entera.** Conserva su forma vertical, y una foto apaisada entra completa dentro de ella con bandas arriba y abajo. Todas las tarjetas siguen midiendo lo mismo, así que el gesto de arrastre se siente igual sea cual sea la foto.
- **La grilla pasa a ser una cuadrícula pareja.** Se quita la proporción original del contenedor, que es lo que hoy pelea con la miniatura cuadrada. La miniatura no cambia: el recorte cuadrado se conserva, y ver la foto sin recortar es para lo que está el visor.
- **Tocar una foto la abre en un visor**, desde la grilla y desde la tarjeta de calificación. El visor muestra la foto completa.
- **Lo que el visor sirve es la variante de mayor calidad del catálogo, nunca el original.** Es la que el backend ya define y hoy no consume nadie: la más grande de las tres, sin recorte, pensada justamente para tolerar un acercamiento sin que los bytes dejen de ser razonables en un teléfono. El original no se entrega: es el archivo tal como se subió, puede pesar hasta veinte veces más, y el producto nunca lo expone.
- **El visor permite acercarse y desplazarse** sobre la foto ampliada, y volver al tamaño completo.
- **Desde el visor se pasa a la foto siguiente y a la anterior** del mismo álbum, sin cerrarlo. Un visor sin eso obliga a cerrar y volver a tocar por cada foto, que es la mitad del trabajo de revisar un álbum.
- **La respuesta de la galería pasa a incluir la dirección de la variante grande.** Es el único cambio de backend, y es pequeño: la variante ya está definida y el transformador ya sabe producirla; lo que falta es que alguna respuesta la lleve.

### Fuera de alcance

- **Entregar el original, para verlo o para descargarlo.** El visor sirve la variante de mayor calidad y nada más. Exponer el archivo tal como se subió es otra decisión, con su propia pregunta sobre quién puede hacerlo y a qué costo de tráfico.
- **Rotar, recortar o editar.** El producto no edita fotos.
- **Modo presentación automática.** Pasar de foto en foto solo con la acción de quien mira.
- **Calificar desde el visor.** La calificación tiene sus dos caminos —el mazo y la grilla— y agregar un tercero es una decisión de producto propia, no una consecuencia de poder ver mejor.
- **Cambiar la definición de las variantes.** Las tres quedan como están; lo que cambia es cuáles se usan y cómo se muestran.

## Capabilities

### New Capabilities

- `photo-viewer`: gobierna mirar una foto con detalle. Define desde dónde se abre, que la foto se vea completa sin importar su forma, que se pueda acercar y recorrer la foto ampliada, cómo se pasa a la siguiente y a la anterior dentro del álbum, y cómo se cierra volviendo a donde se estaba. No existía nada equivalente: el producto tenía tres formas de ver una foto —miniatura, tarjeta de calificación y nada más— y ninguna mostraba la foto entera.

### Modified Capabilities

- `photo-rating`: gana un requirement que hoy solo existe como comentario en el código. La foto que se está calificando SHALL verse completa, sin recortes, porque la decisión se toma sobre lo que se ve: recortarla hace que alguien apruebe o rechace algo distinto de lo que hay. Esa capability ya gobierna cómo se emite una calificación —los controles visibles, el teclado, el arrastre como atajo—, así que es el lugar donde corresponde exigir que lo que se califica sea la foto y no un recorte suyo.

## Impact

**Backend**

- `packages/photos/responses.py`: la respuesta de la galería suma la dirección de la variante grande, armada con el mismo puerto de imágenes que ya arma la de la miniatura. Sin consultas nuevas, sin cambios de esquema y sin tocar el catálogo de variantes.

**Interfaz**

- La tarjeta de la galería deja de imponer la proporción de la foto al contenedor.
- La tarjeta del mazo de calificación deja de recortar.
- Un componente nuevo para el visor, con su acercamiento y su recorrido entre fotos.
- Queda por decidir en el diseño si el visor abierto es un estado interno o una dirección propia. Hay precedente para lo segundo: el filtro de la galería forma parte de la dirección por decisión explícita de otro change, y una dirección propia haría que el botón de atrás cierre el visor.

**Riesgo concentrado en un lugar**

El acercamiento sobre una foto en un teléfono convive con los gestos del navegador y, en el mazo, con el gesto de arrastre que ya existe para calificar. Es la parte del change que hay que probar con dedos y no leyendo código.

**Hasta dónde se puede acercar**

Servir la variante y no el original tiene una consecuencia directa: el acercamiento tiene un techo real, el de los píxeles que esa variante trae. Pasado ese punto la imagen se ve blanda, y eso no es un defecto sino la elección hecha a propósito. El diseño tiene que fijar el límite en función de ese tamaño en vez de dejarlo abierto, para que nadie pueda acercarse hasta ver una mancha y creer que la foto salió mal.

**Precedencia**

Ninguna respecto de los otros seis. No comparte archivos con `improve-upload-and-album-layout` —ese toca la vista de subida y el encabezado, este la grilla y el mazo— así que pueden aplicarse en cualquier orden.
