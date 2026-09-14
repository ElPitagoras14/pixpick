## Context

La tarjeta de la grilla fija el contenedor con la proporción de la foto (`aspectRatio` calculado de sus dimensiones declaradas) y dentro pone la miniatura con recorte de llenado. La miniatura que sirve el backend es un recorte cuadrado de 400 px; el resultado es un cuadrado recortado otra vez para entrar en un contenedor de otra proporción.

La tarjeta del mazo de calificación vive en un contenedor de proporción fija 3:4 y muestra la imagen con recorte de llenado. La variante que consume —la de calificación— es de 1080 px sin recorte, así que el recorte lo hace enteramente la presentación.

El catálogo define tres variantes y la más grande, de 2048 px sin recorte y calidad 85, no la consume nadie. Su comentario dice que existe para tolerar el acercamiento sin que los bytes dejen de ser razonables en un teléfono. Ninguna respuesta de la API lleva su dirección: las dos respuestas de foto llevan solo la miniatura.

El gesto de arrastre del mazo está construido con `@use-gesture/react`, configurado con `filterTaps` y un umbral de 5 px. Esa biblioteca —ya instalada— exporta además `usePinch` y `useWheel`, y su núcleo expone `tap` en el estado del gesto cuando `filterTaps` está activo.

La galería ya lleva su filtro en la dirección, por decisión explícita de otro change, validado con un esquema que convierte un valor desconocido en el filtro por omisión en vez de fallar.

## Goals / Non-Goals

**Goals:**

- Que cerrar el visor devuelva al mismo lugar sin que haya que guardar y restaurar nada a mano.
- Que el recorrido entre fotos respete el filtro sin que el visor tenga que enterarse de que existe un filtro.
- Que abrir en el mazo no pueda confundirse con calificar.

**Non-Goals:**

- Construir un visor genérico reutilizable. Es para este producto y estos dos puntos de entrada.
- Optimizar la carga de la variante grande antes de tener evidencia de que pesa.

## Decisions

### D1 - El visor abierto es parte de la dirección, no un estado interno

Qué foto está abierta se expresa en la dirección, como un parámetro de búsqueda junto al filtro que ya vive ahí.

El proyecto ya tomó esta decisión una vez, para el filtro de la galería, y las razones se repiten: el botón de atrás cierra el visor sin que haya que interceptarlo, una foto abierta se puede compartir por enlace, y recargar la página deja las cosas como estaban.

Y hay una razón propia de este change: el requirement de que cerrar devuelva exactamente a donde se estaba —mismo filtro, misma posición— se cumple solo, porque cerrar es volver a una dirección que ya existía en el historial. Con un estado interno habría que guardar la posición de desplazamiento y restaurarla, que es código que existe para recrear algo que el navegador ya hace.

### D2 - Un parámetro en la misma ruta, no una ruta hija

El visor se abre sobre la pantalla que ya está montada, agregando un parámetro a su dirección, y no navegando a una ruta hija.

La diferencia importa: la galería es la ruta índice del álbum, así que abrir una ruta hija la desmontaría. Al volver habría que reconstruirla y recuperar su posición, que es justo lo que D1 busca evitar. Con un parámetro, la grilla queda debajo, intacta, y el visor se dibuja encima.

Como efecto secundario, el conjunto que el visor recorre queda definido por la misma dirección que define el filtro: no hay forma de que uno diga una cosa y el otro otra.

### D3 - El conjunto que se recorre es el que la pantalla ya tiene cargado

El visor recibe la lista que la pantalla que lo abrió ya tiene —la galería filtrada, en su orden, o la secuencia de calificación— y se mueve dentro de ella. No pide nada propio.

Es lo que hace verdadero el requirement del filtro sin que el visor sepa qué es un filtro: recorre lo que le dieron. Y evita el error opuesto, que es el natural al implementar: pasarle todas las fotos del álbum porque es la lista más a mano.

### D4 - El toque se detecta con el mismo gesto que ya existe, no con un manejador aparte

En el mazo, abrir el visor se dispara desde el mismo gesto que ya maneja el arrastre, usando el dato de toque que ese gesto expone cuando el filtrado de toques está activo —que ya lo está—.

La alternativa era agregar un manejador de clic sobre la tarjeta. Se descarta porque serían dos mecanismos escuchando el mismo dedo, con dos criterios distintos sobre qué es un toque y qué es un arrastre; el caso intermedio —un movimiento de ocho píxeles— quedaría decidido por cuál de los dos reacciona primero. Con un solo gesto hay un solo criterio y el umbral ya está fijado.

### D5 - El acercamiento se construye con la biblioteca de gestos que ya está

El acercamiento por pellizco, por rueda y por doble toque, y el desplazamiento sobre la foto ampliada, se implementan con la misma biblioteca que ya resuelve el arrastre del mazo. Exporta lo necesario para pellizco y rueda, así que no entra ninguna dependencia nueva.

La alternativa era una biblioteca de visor ya hecha. Se descarta por lo de siempre con este tipo de piezas: traen su propia idea de cómo se abre, cómo se cierra, cómo se navega y cómo se ve, y adaptarla a los requirements de arriba —el recorrido que respeta el filtro, el reinicio del acercamiento al cambiar de foto, el tope atado a la variante— termina costando más que las pocas cosas que hay que escribir.

### D6 - El tope de acercamiento se calcula, no se escribe como constante

El máximo se deriva en tiempo de ejecución del tamaño real de la imagen cargada frente al tamaño con el que se la está mostrando, de modo que no se pueda ampliar más allá de donde la variante deja de tener información propia.

Escribirlo como un número fijo lo ataría a suposiciones sobre el tamaño de pantalla y sobre la definición de la variante: el día que alguien cambie los 2048 px del catálogo, un número fijo quedaría mintiendo en silencio. Calculado, se ajusta solo.

### D7 - La grilla y el mazo cambian poco y en direcciones opuestas

En la grilla se quita la proporción de la foto del contenedor y queda cuadrado: la miniatura ya es cuadrada, así que el recorte de llenado deja de recortar nada.

En el mazo se conserva la proporción fija de la tarjeta y se cambia el llenado por ajuste: la variante de calificación ya viene sin recortar, así que la foto entra entera y sobra espacio en los lados que no coinciden.

Las dos son de una línea, y ninguna toca la definición de las variantes.

## Risks / Trade-offs

**El acercamiento táctil es la parte que no se verifica leyendo código (D5)** → Hay que probarlo con dedos en un teléfono real: pellizcar sobre la foto sin que la página de atrás se mueva, y que el arrastre del mazo siga calificando igual. Es el mismo tipo de límite que ya quedó documentado cuando se implementó el gesto de arrastre, donde el propio gesto no se pudo simular con las herramientas disponibles.

**Dos pantallas abren el visor, así que el parámetro vive en dos direcciones (D1)** → Es duplicación de una convención, no de lógica: el componente del visor es uno solo y cada pantalla le pasa su lista. Lo que se repite es el nombre del parámetro, que conviene definir en un solo lugar.

**La variante grande pesa más que la de calificación** → Se pide solo al abrir el visor, no al dibujar la grilla ni el mazo. Mientras nadie abre una foto, el tráfico es el de hoy.

**El tope calculado depende de que la imagen ya esté cargada (D6)** → Hasta que carga, el acercamiento se limita con el valor conservador; una vez conocido el tamaño real, se ajusta. Es preferible a permitir ampliar de más durante el primer segundo.

## Migration Plan

No aplica. El cambio de backend agrega un campo a una respuesta —nada que migrar, nada que romper: un cliente viejo lo ignora—. El resto es interfaz. El rollback es revertir el commit.

## Open Questions

Ninguna. Las dos decisiones que estaban abiertas al terminar la proposal —si el visor es una dirección propia y cómo convive el toque con el arrastre— se cerraron con un precedente del propio proyecto y con la capacidad verificada de la biblioteca que ya está instalada.

### Resueltas durante la redacción

- **¿Dirección propia o estado interno? (D1)** Dirección, con el precedente del filtro de la galería y con una razón nueva: el requirement de volver al mismo punto se cumple solo si cerrar es volver atrás en el historial. *Fuente: la decisión ya tomada para el filtro en `rating-gallery`.*
- **¿Ruta hija o parámetro en la misma ruta? (D2)** Parámetro: la galería es la ruta índice del álbum y una ruta hija la desmontaría, obligando a reconstruirla y a recuperar la posición a mano. *Fuente: la estructura de rutas del álbum.*
- **¿Hace falta una dependencia para el pellizco? (D5)** No: la biblioteca de gestos ya instalada exporta lo necesario para pellizco y rueda, además del arrastre que ya se usa. *Fuente: los exports del paquete instalado.*
- **¿Se puede distinguir un toque de un arrastre sin agregar un manejador aparte? (D4)** Sí: el núcleo de esa biblioteca expone el toque en el estado del gesto cuando el filtrado de toques está activo, que es la configuración que el mazo ya tiene. *Fuente: el código del núcleo instalado, versión 10.3.1.*
- **¿De dónde sale el tope de acercamiento? (D6)** Del tamaño real de la imagen cargada frente al tamaño mostrado, calculado en ejecución. Un número fijo quedaría mintiendo el día que cambie la definición de la variante. *Fuente: derivación a partir de la variante del catálogo y su propósito declarado.*
- **¿La grilla necesita una variante distinta? (D7)** No: la miniatura ya es cuadrada, y con el contenedor cuadrado el recorte de llenado deja de recortar. El catálogo no se toca. *Fuente: la definición de la variante de miniatura.*
