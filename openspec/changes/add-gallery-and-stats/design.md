## Context

El estado de partida son seis changes, y por primera vez el que sigue no necesita nada nuevo de la base: las fotos, las membresías y las calificaciones ya existen, y lo que falta es combinarlas de otra manera y mostrarlas.

Dos cosas del contexto condicionan el diseño. La primera es que **lo pendiente ya tiene dos consumidores** —la secuencia de calificación y el contador del álbum— y este change suma un tercero con el filtro de las sin calificar. Tres consultas equivalentes escritas por separado divergen antes que dos, y la divergencia sería visible de la peor manera posible: el contador diciendo que faltan tres, el filtro mostrando cuatro fotos y la secuencia arrancando con dos.

La segunda es que el máximo de fotos por álbum, que se fijó por una razón de producto, vuelve a pagar algo que no era su objetivo: **la galería no necesita paginarse**. Un álbum acotado entra entero en una respuesta, con sus cuatro conteos, y eso simplifica tanto la consulta como la interfaz.

## Goals / Non-Goals

**Goals:**

- Que las tres vistas de lo pendiente no puedan divergir, porque comparten implementación y no solo resultado.
- Que quién puede ver los conteos quede resuelto por el recurso al que se accede, no por una condición dentro de la respuesta.
- Que corregir una calificación se sienta inmediato sin que la lista salte bajo el dedo.
- Que el dueño pueda comparar fotos entre sí sin cambiar de pantalla.

**Non-Goals:**

- Todo lo que el proposal ya dejó fuera: identidad de quien calificó, ordenamientos por popularidad, exportación, comparación entre álbumes.
- Cualquier cambio de esquema. Si algo pareciera necesitarlo, es señal de haberse salido del alcance.
- Paginación, agregación incremental y cualquier optimización que el tamaño acotado de un álbum vuelve innecesaria.

## Decisions

### D1 - Hay una sola consulta de fotos con calificación, y lo pendiente es esa consulta con un filtro

Las cuatro vistas de la galería son la misma consulta —fotos disponibles del álbum con la calificación de quien pide— con una condición final distinta. Y lo pendiente que ya usaban la secuencia y el contador es exactamente esa consulta con la condición de "sin calificación".

Se implementa una vez y los tres consumidores la usan. Lo que cambia entre ellos no es el conjunto de filas sino qué se hace con ellas: la secuencia necesita la variante grande de cada foto, la galería la miniatura, y el contador solo la cantidad. Esa diferencia vive en el servicio que arma la respuesta, no en la consulta.

**Alternativa descartada:** una consulta por vista, cada una escrita para lo que necesita. Es lo que sale naturalmente si se escribe cada endpoint por separado, y produce tres definiciones de "pendiente" que coinciden mientras nadie las toque. El spec exige que los tres números coincidan siempre; compartir la consulta es lo que convierte esa exigencia en algo estructural en lugar de una coincidencia que hay que mantener.

### D2 - La galería devuelve los cuatro conteos, siempre, calculados en una sola pasada

Cualquiera sea el filtro pedido, la respuesta trae cuántas fotos hay en cada uno de los cuatro. Se calculan en una sola pasada sobre las mismas filas, no con cuatro consultas.

Tiene dos consecuencias buenas. La interfaz puede mostrar las cuatro solapas con su cantidad sin pedir nada más, que es lo que hace que cambiar de filtro se sienta instantáneo. Y el invariante de partición que el spec exige —que los tres parciales sumen el total— queda expuesto en la propia respuesta, así que verificarlo es sumar tres números de un mismo cuerpo en lugar de comparar cuatro peticiones.

### D3 - Las estadísticas son una agregación con filtro en una sola consulta

Los conteos por foto salen de contar con condición dentro de la misma agregación, en una pasada sobre las calificaciones del álbum, junto con el resumen. Es exactamente la consulta que se usó como argumento al decidir que este proyecto no lleva un mapeador objeto-relacional, así que acá se cobra aquel argumento.

Las fotos sin ninguna calificación tienen que aparecer en cero, lo que obliga a partir de las fotos y no de las calificaciones: agregar sobre las calificaciones dejaría afuera justamente las fotos que nadie miró, que son las que el dueño más quiere ver.

### D4 - Los conteos se calculan al pedirlos y no se guardan

No hay columnas con totales ni nada que mantener al calificar. Es la misma decisión que se tomó para la cantidad de fotos de un álbum, con un argumento más fuerte todavía: un contador de calificaciones tendría que actualizarse en cada emisión y en cada cambio de opinión, incluido el caso de reemplazar una aprobación por un rechazo, que mueve dos contadores a la vez. Cada uno de esos caminos es una oportunidad de quedar desviado.

**Alternativa descartada:** materializar los conteos con un trigger que los mantenga. Resolvería el olvido, y sigue siendo trabajo permanente para acelerar una consulta que sobre un álbum acotado es instantánea.

### D5 - La galería y las estadísticas se piden en paralelo, y el grid no espera a los conteos

El dueño necesita las dos cosas, y la ruta las pide a la vez. El grid se dibuja en cuanto llega la galería; los conteos aparecen sobre las fotos cuando llegan las estadísticas.

No encadenar las dos peticiones importa porque la galería es lo que hace que la pantalla sea usable: bloquearla hasta tener los conteos haría que el dueño espere por información secundaria para ver sus propias fotos.

### D6 - Cambiar la calificación desde la galería usa la misma operación, pero no la cola del swipe

La operación de la API es la misma que usa la secuencia —eso lo exige el spec y es lo correcto—, pero del lado del cliente la galería usa una mutación optimista común y no la cola con reintentos del swipe.

La cola existe porque calificando con gestos se emiten muchas decisiones seguidas y conviene que ninguna bloquee a la siguiente. En la galería se toca un indicador de vez en cuando. Reutilizar la cola sería arrastrar maquinaria diseñada para otra situación, que es justo lo que la regla sobre abstracciones débiles desaconseja: compartir código porque se parece, no porque resuelva el mismo problema.

### D7 - Al cambiar una calificación cambia el indicador, pero la foto no se arranca de la lista

Tocar el indicador cambia el indicador de inmediato. Si esa foto deja de pertenecer al filtro que se está mirando, **no desaparece en ese momento**: se va cuando la lista se vuelve a pedir.

Arrancarla al instante sería lo literal y es peor de usar: la lista salta bajo el dedo justo después de tocar, y quien quiso corregir dos fotos seguidas pierde la posición. Cambiar el indicador ya es la confirmación de que el toque hizo algo.

Esto es compatible con lo que el spec exige, porque sus escenarios hablan de qué devuelve cada filtro cuando se lo pide: pedir el filtro de aprobadas después del cambio ya no la trae.

### D8 - Hay una sola pantalla de álbum: la galería, con los conteos encima y el resumen en su encabezado

El grid del álbum que introdujo el change anterior no convive con una galería nueva: se convierte en ella. Gana las solapas de filtro y el indicador por foto, y sigue siendo la misma ruta. **Y no hay una pantalla de estadísticas aparte**: para el dueño, los conteos se superponen sobre las mismas fotos y el resumen del álbum va en el encabezado de esa misma vista.

La pantalla dedicada parecía natural y no se gana su lugar. Lo que podría justificarla es ordenar las fotos por cantidad de aprobaciones, que es una forma de mirar que la galería no ofrece — y eso está explícitamente fuera de alcance. Sin ordenamiento, esa pantalla sería la galería con números y sin filtros, más una línea con cuántas personas participaron y cuántas calificaciones hay. Una línea no necesita una pantalla: necesita un encabezado.

Esto no toca el requirement de que las estadísticas sean un recurso distinto de la galería, que sigue valiendo y sigue siendo importante: lo que se elimina es una ruta de la interfaz, no la separación entre los dos recursos. La vista del álbum pide los dos cuando quien mira es el dueño.

**Disparador para revisarlo:** si alguna vez entra el ordenamiento por popularidad, una pantalla dedicada vuelve a tener sentido, porque ahí sí ofrecería una forma de mirar que la galería no tiene.

### D9 - El filtro se valida en la ruta, y es el único lugar donde la ruta tiene lógica propia

La ruta declara los cuatro valores admitidos y el de omisión, y usa el filtro como parte de lo que identifica los datos que carga. Un valor desconocido cae al de omisión en lugar de fallar.

Es la excepción prevista en la regla de que las rutas solo orquestan: el filtro es estado de la dirección, y la dirección le pertenece al enrutador. Todo lo demás —cómo se dibuja el grid, cómo se cambia una calificación— vive en las features.

### D10 - La lista de álbumes se separa en dos grupos, y es un cambio solo de presentación

Los álbumes propios y los compartidos se muestran en grupos separados, con la selección en la dirección igual que el filtro de la galería. Reutilizar ese patrón no es simetría por simetría: hace que las dos listas del producto —la de álbumes y la de fotos de un álbum— se comporten igual al recargar y al compartir una dirección, que es lo que evita tener que recordar cuál de las dos conserva su estado.

**No cambia nada del backend.** La respuesta del listado ya distingue unos de otros desde `add-share-and-swipe`, y como un álbum acotado en cantidad se lista completo, la separación en grupos y el conteo de cada uno se resuelven en el cliente sin una petición adicional ni un parámetro nuevo.

Esta separación llega en este change y no en el anterior por una razón de producto: hasta que existió la galería, un álbum compartido era solo un lugar donde deslizar una vez, y no había mucho a lo que volver. Con la galería pasa a ser un lugar que se revisita, y ahí es cuando mezclar las dos clases de álbum empieza a estorbar.

## Risks / Trade-offs

**Un cuarto consumidor de lo pendiente podría escribirse por separado** → El riesgo no desaparece con D1, solo se reduce. Lo que lo contiene es que el spec exige que las tres vistas coincidan y que esa coincidencia está verificada; un cuarto que diverja rompería esas pruebas en cuanto se lo conecte.

**Con un único calificador, los conteos revelan qué votó esa persona** → Es inevitable y conviene decirlo en lugar de dejarlo implícito: si el álbum tiene un solo miembro además del dueño, un conteo de una aprobación identifica su decisión. Ocultar los conteos por debajo de un mínimo de participantes protegería ese caso y volvería la función inútil justo en los álbumes chicos, que son la mayoría. Se acepta que las estadísticas son agregadas en su forma, no anónimas en sentido fuerte.

**Los conteos superpuestos pueden tapar la foto en una pantalla de teléfono** → Se resuelve ubicándolos como una franja compacta debajo de cada miniatura en anchos chicos, en lugar de encima de la imagen. Es una decisión de disposición, pero conviene anotarla porque la versión obvia —una insignia sobre la esquina— compite con el indicador de la propia calificación, que ya ocupa una esquina.

**Representar la ausencia de calificación como un valor falso rompería la partición** → Es el error más probable de este change: si "sin calificar" y "rechazada" se colapsan, los filtros dejan de particionar y el indicador miente. El spec lo cubre con escenarios propios, y la partición sumada es la verificación que lo detecta de inmediato.

**El grupo de compartidos está vacío hasta que alguien comparte un álbum con vos** → Para quien solo usa sus propios álbumes, uno de los dos grupos está siempre vacío y puede parecer que la aplicación está incompleta. Se mitiga con que el grupo vacío diga qué aparecería ahí, en lugar de mostrar una lista en blanco, y es la razón por la que el spec lo exige con un escenario propio.

**El encabezado del álbum muestra información distinta según quién mira** → Para el dueño incluye el resumen de participación y para un miembro no. Es una diferencia legítima, pero conviene que la ausencia del resumen no se lea como un error de carga: para quien no es dueño el encabezado simplemente no tiene esa zona, en lugar de mostrarla vacía.

## Migration Plan

No hay migración: este change no toca el esquema. Es la primera vez que ocurre en el proyecto y hace que el despliegue sea trivial.

El rollback es revertir el commit. No se pierde nada, porque nada de lo que este change introduce se almacena: la galería y las estadísticas son formas de mirar datos que ya existían y que siguen existiendo después de revertir.

## Open Questions

Ninguna. La única que había quedado abierta se cerró razonando qué aportaría realmente la pantalla en discusión, y la respuesta resultó ser lo bastante concreta como para no necesitar uso real.

**Resueltas durante la redacción**

- **Si la vista de estadísticas separada se gana su lugar.** No se la gana, y se eliminó en D8. Lo que cerró la pregunta fue preguntarse qué forma de mirar ofrecería esa pantalla que la galería no ofrece: ordenar por cantidad de aprobaciones, que está fuera de alcance. Sin eso, la pantalla sería la galería con números y sin filtros más una línea de resumen, y una línea va en un encabezado. Quedó anotado el disparador para revisarlo: si alguna vez entra el ordenamiento por popularidad, la pantalla dedicada vuelve a tener sentido.
- **Si la galería necesita paginarse.** La cerró una decisión de otro change: el máximo de fotos por álbum que fijó `add-albums-and-upload` acota el álbum entero, así que entra completo en una respuesta junto con sus cuatro conteos. Es la segunda vez que ese límite paga algo que no era su objetivo.
- **Dónde ubicar los conteos sobre el grid.** La versión obvia —una insignia en la esquina de cada miniatura— compite con el indicador de la propia calificación, que ya ocupa una esquina. Se resolvió ubicándolos como una franja compacta debajo de cada miniatura en anchos chicos, y quedó anotado en Risks.
- **Si la galería debe reutilizar la cola de calificaciones del swipe.** Se cerró en D6 distinguiendo dos cosas que el spec no distingue: la operación de la API tiene que ser la misma, pero el mecanismo del cliente no. La cola existe porque calificando con gestos se emiten muchas decisiones seguidas; en la galería se toca un indicador de vez en cuando, así que una mutación optimista común alcanza.
- **Si ocultar los conteos por debajo de un mínimo de participantes.** Surgió al notar que con un único calificador los conteos revelan qué votó esa persona. Se resolvió aceptando la limitación y dejándola escrita en Risks: el umbral protegería ese caso y volvería la función inútil justo en los álbumes chicos, que son la mayoría.
