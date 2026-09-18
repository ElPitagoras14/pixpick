## Context

El proyecto no borra nada por sí solo. Su única limpieza es un comando que se corre a mano —descarta las subidas cuyo permiso venció, junto con los objetos que hayan quedado— y su propio código justifica que sea manual: lo que descarta es invisible para todos hasta entonces, así que no hay urgencia. Ese comando borra primero las filas y confirma, y recién después elimina los objetos, que es la regla de todo borrado del proyecto.

Para ocultar filas que existen pero no deben verse, el proyecto ya tiene un patrón: la vista `available_photos`, que es literalmente `select * from photos where available = true`, y la regla de que toda lectura pase por ella en lugar de tocar la columna. Hoy la consumen siete lugares distintos entre álbumes, fotos y calificaciones. La elección de una vista fue deliberada: que cada consulta nueva tenga que acordarse de una condición es exactamente el olvido que se quiso eliminar.

`albums` tiene `created_at` y `updated_at`; este último lo mantiene un trigger y cambia con cualquier escritura sobre la fila. Nada registra cuándo entró la última foto. En `photos`, en cambio, sí hay un precedente de plazo: `upload_expires_at` guarda el instante de vencimiento ya calculado, y las consultas comparan contra él.

El consumo de la cuenta —definido en `add-account-quota`— se calcula sumando el tamaño de las fotos de los álbumes de una persona.

## Goals / Non-Goals

**Goals:**

- Que un álbum vencido deje de verse en el instante exacto, sin depender de que nadie ejecute nada.
- Que el plazo siga siendo un valor de configuración de verdad, y no una constante escondida en una migración.
- Que olvidar la condición de vigencia en una consulta nueva sea un fallo visible y no un álbum fantasma.

**Non-Goals:**

- Introducir un proceso permanente, un planificador o un servicio nuevo. Este change tiene que resolverse con lo que el proyecto ya tiene.
- Borrar los objetos en el instante del vencimiento. La spec admite explícitamente que esa parte ocurra después.

## Decisions

### D1 - Se guarda el momento desde el que se cuenta, no la fecha de vencimiento

`albums` gana una columna con el instante desde el cual corre el plazo: se inicializa al crear el álbum y se actualiza cada vez que una foto queda disponible. La vigencia se evalúa comparando ese instante más el plazo configurado contra el momento actual.

La alternativa era guardar directamente la fecha de vencimiento, que es lo que ya hace `photos.upload_expires_at` y que haría la consulta más simple. Se descarta por un escenario del spec: cambiar el plazo en la configuración tiene que cambiar los vencimientos. Con la fecha guardada, un álbum creado bajo un plazo de 30 días conservaría esos 30 días para siempre, y bajar el valor no tendría efecto hasta que existieran álbumes nuevos — el valor de configuración sería decorativo durante un mes.

La diferencia con `upload_expires_at` no es incoherencia sino distinta naturaleza: el plazo de un permiso de subida es una constante corta del contrato, no una perilla de producto, y sus filas viven quince minutos.

### D2 - La condición de vigencia vive en un solo lugar, y una prueba impide saltearla

Toda lectura de álbumes pasa a componer una única condición compartida, definida en un solo lugar del repositorio, en vez de escribirla cada consulta por su cuenta. Una prueba recorre el código del backend y falla si alguna consulta lee la tabla de álbumes sin pasar por ese lugar.

Lo natural habría sido una vista, que es lo que el proyecto ya hace con las fotos y lo que vuelve estructural la garantía. **No se puede acá**, y la razón es concreta: la condición necesita el plazo configurado, y una vista no recibe parámetros. Escribirlo dentro de la vista movería una perilla de producto del entorno a una migración, y cambiarla pasaría a ser un cambio de esquema.

Se consideró también fijar el plazo como valor de sesión de la base en cada conexión, de modo que la vista pudiera leerlo. Se descarta con el mismo argumento que otro change ya usó para descartar esa misma técnica: agrega un mecanismo con su propio modo de falla —una conexión que no lo fijó— y el fallo no es ruidoso, es una consulta que devuelve lo que no debía.

La prueba es más débil que una vista, y conviene decirlo: protege el código del proyecto, no la base. Alguien consultando la base a mano ve álbumes vencidos. Es aceptable porque lo que el spec exige es qué devuelve la aplicación, no qué filas existen.

### D3 - La eliminación física se suma al comando que ya existe, que pasa a ser uno solo

El comando de limpieza actual gana la eliminación de álbumes vencidos, junto con sus fotos y sus objetos, y se muda a un módulo de mantenimiento propio en vez de quedar colgando del paquete de fotos, que ya no lo contiene entero.

La alternativa era un comando nuevo, separado. Se descarta porque el costo real de este mecanismo no es escribirlo sino acordarse de correrlo, y dos comandos es el doble de cosas que recordar para una misma tarea: borrar lo que ya nadie puede ver. Los dos hacen además exactamente lo mismo en la misma secuencia —encontrar lo que sobra, borrar filas, confirmar, borrar objetos—, que es la regla de todo borrado del proyecto.

Lo que vuelve tolerable que siga siendo manual es D2: si el comando no se corre en un mes, nadie ve un álbum que no debería, nadie paga espacio de su cuenta por él, y lo único que se acumula son objetos en el proveedor.

### D4 - Confirmar una foto corre el plazo, en la misma transacción que la deja disponible

La actualización del instante de referencia ocurre dentro de la misma transacción que marca la foto como disponible. No es un efecto posterior ni una tarea diferida: si la confirmación se deshace, el plazo tampoco se movió.

Es además el único punto del código que lo toca, lo que hace verificable la regla de que solo subir renueva: no hay ningún otro lugar donde buscar.

### D5 - El consumo de la cuenta hereda la condición, y con eso el espacio se libera solo

La consulta que suma el consumo de una persona pasa a componer la misma condición de vigencia de D2, por ser una lectura de álbumes más.

Con eso, el requirement de que el vencimiento libere espacio en el acto no necesita código propio: las fotos de un álbum vencido dejan de sumarse en el mismo instante en que el álbum deja de estar vigente, y no cuando alguien borra sus objetos. Es la ventaja de que la condición esté en un solo lugar y no repartida por consulta.

### D6 - La API devuelve el instante de vencimiento y la interfaz decide cómo lo dice

La respuesta lleva el momento exacto en que el álbum vence, no un texto ni una cantidad de días. La interfaz es la que lo convierte en "vence en 3 días" o en la forma que corresponda.

Es la misma regla que el proyecto ya aplica a toda fecha que cruza la API, y evita que el backend tenga que decidir cómo se redondea un plazo o en qué idioma se lo dice.

## Risks / Trade-offs

**La prueba de D2 es más débil que la vista que protege a las fotos (D2)** → Protege el código, no la base. Es la única opción que conserva el plazo como valor de configuración, y lo que el spec exige es el comportamiento de la aplicación.

**El comando puede no correrse nunca (D3)** → Se acumulan objetos en el proveedor y nada más: ni visibilidad, ni espacio de cuenta, ni datos accesibles. Es el mismo compromiso que el proyecto ya aceptó para las subidas abandonadas, ahora con la diferencia de que la parte que sí importa no depende de él.

**Bajar el plazo en la configuración mata álbumes de golpe (D1)** → Es exactamente lo que el spec pide, y la contracara de que el valor sea configurable de verdad. Conviene que quien lo baje sepa que el efecto es inmediato sobre todo lo existente, así que la documentación del valor tiene que decirlo.

**Un álbum puede vencer con alguien mirándolo** → Se comporta como uno eliminado mientras alguien lo tenía abierto, que es un camino que la interfaz ya recorre hoy. No hace falta nada nuevo.

**Una foto subida un segundo antes del vencimiento lo corre entero** → Es la regla funcionando, no un borde: subir renueva.

## Migration Plan

Una migración agrega la columna y la inicializa con el momento de aplicarla, no con la fecha de creación de cada álbum.

La diferencia importa. Inicializar con la creación haría que todo álbum de más de 30 días quedara vencido en el mismo instante en que la migración corre, y sus objetos se borraran en la primera limpieza — datos perdidos como efecto secundario de un despliegue. Inicializando con el momento de aplicar, la regla empieza a correr cuando la regla empieza a existir, que es lo que alguien esperaría de una política nueva: todos los álbumes existentes arrancan con el plazo completo.

El rollback es revertir el commit y la migración. Como la columna es lo único que se agrega, quitarla devuelve el comportamiento anterior sin residuo: los álbumes vuelven a no vencer nunca. Lo que la limpieza ya haya borrado antes del rollback no vuelve, así que conviene revertir antes de correr el comando por primera vez si hay dudas.

## Open Questions

Ninguna. La única decisión que podía quedar en el aire —cómo garantizar la visibilidad sin un proceso periódico— quedó cerrada por lo que el propio proyecto ya tiene: el patrón de la vista, el motivo por el que acá no aplica, y una técnica alternativa que otro change ya había evaluado y descartado con su razón escrita.

### Resueltas durante la redacción

- **¿Se puede usar una vista, como con las fotos? (D2)** No: la condición necesita el plazo configurado y una vista no recibe parámetros. Meterlo dentro convertiría una perilla del entorno en un cambio de esquema. *Fuente: la definición de `available_photos` y la naturaleza del valor.*
- **¿Y fijando el plazo como valor de sesión de la base para que la vista lo lea? (D2)** Descartado con el argumento que `add-cloud-media-adapters` ya usó contra esa misma técnica: agrega un modo de falla silencioso, una conexión que no lo fijó. *Fuente: el proposal de ese change, sección de alternativas descartadas.*
- **¿Guardar la fecha de vencimiento o el momento desde el que se cuenta? (D1)** El momento desde el que se cuenta, porque un escenario del spec exige que cambiar el plazo cambie los vencimientos existentes. *Fuente: el requirement del plazo en `album-retention`.*
- **¿Por qué `photos` sí guarda la fecha ya calculada? (D1)** Porque el plazo de un permiso de subida es una constante corta del contrato y no una perilla de producto, y sus filas viven quince minutos. *Fuente: la columna `upload_expires_at` y el requirement que la gobierna.*
- **¿Se puede reutilizar la fecha de modificación de la fila? (D1)** No: la mantiene un trigger y cambia con cualquier escritura, así que una regla de producto quedaría dependiendo de un efecto secundario. *Fuente: el trigger de `updated_at` establecido en `add-backend-data-layer`.*
- **¿Comando nuevo o el que ya existe? (D3)** El que existe, unificado, porque el costo de este mecanismo es acordarse de correrlo y dos comandos duplican ese costo para una misma tarea. *Fuente: decisión tomada al redactar, con la alternativa registrada.*
- **¿Hay que escribir algo para que el vencimiento libere espacio? (D5)** No: la consulta de consumo es una lectura de álbumes más, así que hereda la condición y el espacio se libera en el mismo instante. *Fuente: la forma de la consulta de consumo definida en `add-account-quota`.*
- **¿Con qué valor se inicializa la columna en la migración?** Con el momento de aplicarla. Inicializar con la fecha de creación borraría, en la primera limpieza, todo álbum de más de 30 días — pérdida de datos como efecto de un despliegue. *Fuente: derivación del propio plazo aplicado a los datos existentes.*
