## Context

El encabezado del álbum lo dibuja el layout que comparten sus tres subvistas —la grilla, la subida y la calificación—. Ese layout ya sabe cuál está activa: usa el emparejador de rutas para detectarlo, y hoy usa ese dato para **esconder** su enlace de vuelta cuando la subvista es la de subir. La subvista dibuja entonces uno propio, que cae dentro del área de contenido y por lo tanto debajo del título.

La lista de archivos es una fila por archivo: el nombre ocupa el espacio flexible con recorte al final, y a su derecha una franja fija de 160 píxeles muestra o la barra de avance o el texto del estado. Los estados son siete, y con el límite de la cuenta pasan a ser ocho.

La cola de subida vive aparte de la vista y ya expone, por archivo, su estado, su avance, su error y el objeto del archivo original. Nada de lo que este change necesita mostrar hay que ir a buscarlo: el tamaño está en el propio archivo elegido, sin ninguna petición.

El proyecto ya separó en componentes propios la tarjeta de la galería y la del mazo de calificación, ambas por la misma razón: una pieza con varios estados se lee mejor sola que embebida en la ruta.

## Goals / Non-Goals

**Goals:**

- Que el avance y el motivo de fallo dejen de competir por el lugar de la identidad del archivo.
- Que la salida de la vista de subida esté donde está en todas las demás pantallas, sin casos especiales.
- Que un lote con resultados mixtos se entienda sin contar.

**Non-Goals:**

- Tocar la cola de subida. Ni su concurrencia, ni su reintento, ni sus estados.
- Uniformar las otras subvistas del álbum. Este change corrige la de subida, que es la que se observó.

## Decisions

### D1 - El encabezado elige el destino del enlace en vez de esconderlo

El enlace de vuelta pasa a dibujarse siempre en el encabezado, por encima del título, y lo que depende de la subvista activa es a dónde apunta: al álbum desde la subida, a la lista desde la grilla.

Es el mismo dato que el layout ya calcula, usado para decidir en lugar de para ocultar. El resultado tiene un caso especial menos: hoy hay una rama que esconde el enlace y una subvista que dibuja el suyo; después hay una sola expresión que resuelve el destino.

De paso, es lo que garantiza el escenario de que haya exactamente una salida: si el enlace vive en un único lugar, no puede haber dos.

**La subvista de calificación se deja como está, a propósito.** Hoy muestra el enlace a la lista de álbumes y las acciones del álbum, y podría argumentarse que también es un flujo propio que debería volver al álbum. Puede que lo sea, pero no es lo que se observó ni lo que el spec exige, y cambiarlo sin haberlo mirado en uso es adivinar. Queda anotado acá para que se note que es una decisión y no un olvido.

### D2 - La card es un componente propio y traduce un estado a una presentación

El bloque de un archivo se implementa como un componente propio que recibe el elemento de la cola y decide qué mostrar. La ruta queda con la elección de archivos y la lista; la traducción de ocho estados a lo que se ve queda en un solo lugar.

Es el mismo criterio con el que ya existen la tarjeta de la galería y la del mazo, y es lo que evita que la ruta acumule ocho ramas de presentación mezcladas con el manejo del selector de archivos.

### D3 - El nombre se recorta conservando el final, no el principio

Cuando el nombre no entre, lo que se recorta es el medio: el comienzo y **los últimos caracteres** quedan visibles.

Es la respuesta concreta al escenario de los nombres parecidos. El recorte natural —el que da el navegador con una sola propiedad de estilo— corta por el final, que es exactamente donde están los caracteres que distinguen `IMG_4821` de `IMG_4822`. Recortar al final es gratis y equivocado para este caso; conservar la cola cuesta un poco más y es lo que hace verdadero el escenario.

### D4 - El tamaño sale del archivo elegido, sin pedir nada

El tamaño que se muestra es el del archivo local que la persona seleccionó, que la cola ya tiene y que la validación previa ya usa. No hay petición ni dato del servidor involucrado.

### D5 - Los ocho estados se agrupan en tres desenlaces, sin perder su etiqueta

Cada estado conserva su texto propio, y además se presenta dentro de uno de tres grupos: en curso, terminado bien, y no terminó. El grupo es lo que se lee de un vistazo; la etiqueta es lo que se lee cuando hace falta el detalle.

Sin esa agrupación, distinguir "confirmando" de "pendiente" o "rechazada" exige leer ocho textos parecidos, que es justo lo que el escenario del lote mixto quiere evitar.

### D6 - Un resumen arriba, en lugar de reordenar la lista

Sobre la lista se muestra un resumen del lote: cuántos terminaron y cuántos no. El orden de la lista sigue siendo el de la selección.

La alternativa era mover los fallos al principio para que se vean. Se descarta porque el orden de la selección es lo que le permite a alguien encontrar un archivo concreto entre cincuenta, y reordenar bajo los pies de quien está mirando es peor que pedirle que se desplace. El resumen resuelve el mismo problema —saber cuántos fueron cuáles sin contar— sin mover nada.

### D7 - La cola no se toca

Ningún cambio entra en el módulo de la cola de subida. Todo lo de este change ocurre en la presentación, que es lo que mantiene su riesgo acotado: si algo sale mal, lo que se rompe es cómo se ve una lista, nunca una subida en curso.

## Risks / Trade-offs

**Una card ocupa más alto que una fila, y un lote puede tener cincuenta (D2, D6)** → Se compensa manteniendo la card en dos renglones de contenido y con el resumen de arriba, que es lo que evita tener que recorrer la lista entera para saber cómo terminó todo. Reordenar habría ahorrado desplazamiento al precio de mover cosas bajo la vista de quien mira.

**Conservar el final del nombre no sale de una propiedad de estilo (D3)** → Cuesta un poco más que el recorte por omisión. Es el precio de que el escenario de los nombres parecidos sea cierto y no una aspiración.

**El encabezado pasa a tener una expresión que depende de la subvista (D1)** → Ya la tiene; lo que cambia es que decide un destino en vez de ocultar algo. Hay un caso especial menos, no uno más.

**Este change y el de la cuota tocan el mismo archivo** → La precedencia está declarada: primero el estado nuevo funcionando, después su presentación. Al revés, la lista se rediseña dos veces.

## Migration Plan

No aplica. No hay datos, esquema, configuración ni contrato de API: son dos archivos de interfaz y un componente nuevo. El rollback es revertir el commit.

## Open Questions

Ninguna. La única elección de fondo —tabla o cards— la respondió el usuario antes de escribir el primer artefacto, y el resto se resolvió mirando qué datos ya tiene la cola y cómo el proyecto ya resuelve piezas equivalentes.

### Resueltas durante la redacción

- **¿Mostrar el tamaño obliga a pedir algo? (D4)** No: es el tamaño del archivo local, que la cola ya tiene y la validación previa ya usa. *Fuente: la cola de subida y su validación por archivo.*
- **¿Cómo se cumple el escenario de los nombres parecidos? (D3)** Conservando los últimos caracteres al recortar. El recorte por omisión del navegador corta justo donde están los caracteres que distinguen. *Fuente: el escenario del spec confrontado con el comportamiento del recorte estándar.*
- **¿Se reordena la lista para que los fallos se vean? (D6)** No: el orden de la selección es lo que permite encontrar un archivo entre cincuenta. Un resumen arriba cubre el mismo escenario sin mover nada. *Fuente: decisión tomada al redactar, con la alternativa registrada.*
- **¿Qué pasa con la subvista de calificación? (D1)** Se deja como está, deliberadamente: no fue observada y no está en el spec, así que cambiarla sería adivinar. *Fuente: el alcance de las observaciones y de los requirements escritos.*
- **¿Hace falta tocar la cola de subida? (D7)** No: todos los estados que hay que mostrar ya los expone. *Fuente: la interfaz que la cola ya ofrece por archivo.*
- **¿Componente propio o todo en la ruta? (D2)** Componente propio, por el mismo criterio con el que ya existen la tarjeta de la galería y la del mazo de calificación. *Fuente: la organización actual del código del frontend.*
