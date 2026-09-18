# photo-viewer Specification

## Purpose

Gobierna mirar una foto con detalle: desde dónde se abre, qué se sirve para mostrarla, que se vea completa sea cual sea su forma, cómo se la acerca y se la recorre, cómo se pasa a la siguiente y cómo se vuelve a donde se estaba. No se solapa con `rating-gallery`, que gobierna cómo se recorre un álbum y qué filtros existen, ni con `image-delivery`, que gobierna cómo se producen y se entregan las variantes.

## Requirements

### Requirement: Una foto se abre en detalle desde donde se la esté viendo

Tocar una foto SHALL abrirla en el visor, tanto desde la grilla del álbum como desde la tarjeta donde se la está calificando.

Abrir desde la tarjeta de calificación SHALL NOT emitir ninguna calificación ni interferir con el gesto de arrastre que ya existe ahí: un toque abre, un arrastre califica, y SHALL NOT ocurrir que uno se interprete como el otro.

#### Scenario: Se abre desde la grilla

- **WHEN** se toca una foto de la grilla del álbum
- **THEN** esa foto se abre en el visor

#### Scenario: Se abre desde la tarjeta de calificación

- **WHEN** se toca la foto que se está calificando
- **THEN** esa foto se abre en el visor
- **AND** no se emite ninguna calificación

#### Scenario: Arrastrar sigue calificando y no abre

- **WHEN** se arrastra la tarjeta de calificación hasta emitir una calificación
- **THEN** la calificación se emite
- **AND** el visor no se abre

### Requirement: La foto se ve completa, sea cual sea su forma

En el visor, la foto SHALL verse completa y sin recortar, tanto si es vertical como apaisada o cuadrada. SHALL ocupar todo el espacio que su forma permita sin deformarse: SHALL NOT estirarse ni comprimirse para llenar la pantalla.

#### Scenario: Una foto apaisada se ve entera

- **WHEN** se abre en el visor una foto más ancha que alta
- **THEN** se ve completa, de borde a borde de su contenido
- **AND** no le falta ninguna parte

#### Scenario: Una foto vertical se ve entera

- **WHEN** se abre en el visor una foto más alta que ancha
- **THEN** se ve completa
- **AND** conserva su proporción

### Requirement: El visor sirve una variante, nunca el archivo original

Lo que el visor muestra SHALL ser la variante de mayor calidad del catálogo: la más grande, sin recorte. SHALL NOT entregarse el archivo tal como se subió, ni mostrarlo ni ofrecerlo para descargar.

El acercamiento máximo SHALL corresponderse con la resolución real de esa variante. SHALL NOT poder ampliarse más allá del punto en que la imagen deja de tener información propia: el límite es una consecuencia declarada de servir una variante y no el original, y dejarlo abierto haría que alguien concluya que la foto salió mal cuando lo que hizo fue pasarse de acercamiento.

#### Scenario: Lo que se pide es la variante

- **WHEN** el visor muestra una foto
- **THEN** lo que solicita es la variante de mayor calidad del catálogo
- **AND** en ningún momento solicita el archivo original

#### Scenario: El acercamiento tiene un tope

- **WHEN** se intenta acercarse más allá del límite
- **THEN** el acercamiento se detiene en ese límite
- **AND** la imagen no se amplía hasta perder definición por completo

### Requirement: La foto ampliada se puede recorrer y volver al tamaño completo

El visor SHALL permitir acercarse y alejarse sobre la foto, y con la foto ampliada SHALL permitir desplazarse por ella para llegar a cualquier parte. SHALL poder volverse al tamaño completo en un solo paso, sin tener que alejarse gradualmente.

En una pantalla táctil, acercarse sobre la foto SHALL NOT desplazar ni ampliar la página que está detrás.

#### Scenario: Acercarse y recorrer

- **WHEN** se acerca sobre una foto y se la desplaza
- **THEN** se puede llegar a cualquier zona de la foto

#### Scenario: Volver al tamaño completo de una vez

- **WHEN** la foto está ampliada y se pide volver al tamaño completo
- **THEN** vuelve a verse entera en un solo paso

#### Scenario: El acercamiento no arrastra la página

- **WHEN** se acerca sobre la foto en una pantalla táctil
- **THEN** la página que está detrás no se mueve ni se amplía

### Requirement: Desde el visor se pasa a la foto siguiente y a la anterior

Estando en el visor SHALL poder pasarse a la foto siguiente y a la anterior sin cerrarlo. El conjunto por el que se avanza SHALL ser el mismo que se estaba mirando al abrirlo, en el mismo orden: si había un filtro aplicado en la galería, el recorrido SHALL respetar ese filtro y no el álbum completo.

Al cambiar de foto, el acercamiento SHALL volver al tamaño completo, para que la foto siguiente no aparezca ampliada en una zona que nadie eligió.

Al llegar al primero o al último del conjunto SHALL quedar claro que no hay más en esa dirección.

#### Scenario: Se avanza sin cerrar

- **WHEN** se abre una foto y se pide la siguiente
- **THEN** el visor muestra la siguiente sin cerrarse

#### Scenario: El recorrido respeta el filtro aplicado

- **WHEN** se abre una foto desde la galería con un filtro aplicado y se avanza
- **THEN** las fotos que aparecen son las de ese filtro
- **AND** no aparecen fotos que el filtro excluye

#### Scenario: Cambiar de foto reinicia el acercamiento

- **WHEN** se acerca sobre una foto y se pasa a la siguiente
- **THEN** la siguiente se muestra completa y no ampliada

#### Scenario: El final del conjunto se nota

- **WHEN** se está en la última foto del conjunto y se pide avanzar
- **THEN** queda claro que no hay más en esa dirección

### Requirement: Cerrar el visor devuelve exactamente a donde se estaba

Cerrar el visor SHALL devolver a la pantalla desde la que se abrió, conservando su estado: el filtro que estaba aplicado y la posición en que se estaba mirando. SHALL NOT volverse al principio de la lista ni perderse el filtro.

#### Scenario: Se vuelve al mismo punto de la galería

- **WHEN** se abre una foto desde la mitad de una galería larga y se cierra el visor
- **THEN** se vuelve a la galería en el mismo punto en que se estaba
- **AND** con el mismo filtro aplicado

#### Scenario: Se vuelve a la calificación en curso

- **WHEN** se abre la foto que se está calificando y se cierra el visor
- **THEN** se vuelve a la calificación de esa misma foto, sin haberla calificado
