## Context

El estado de partida son tres changes: un entorno con un edge que reparte espacios reservados y que ya tiene declarado cómo crecen esos espacios, una capa de datos con SQL crudo y errores traducidos a dominio, y una suite que corre contra servicios reales con aislamiento por rollback. Este change es el único de la fase local **sin interfaz**: se verifica enteramente con pruebas y con peticiones al edge.

Dos cosas del contexto lo condicionan más que ninguna otra. La primera es que el consumidor de estos puertos todavía no existe —llega en el change siguiente—, así que la superficie se define por lo que ese consumidor va a necesitar y nada más, o el puerto nace sobre-diseñado. La segunda es que no hay pruebas end-to-end, así que la suite de contrato es la única red que atrapa un adapter roto, y de ella depende que el change de los adapters cloud sea seguro.

Un tercer condicionante apareció al probar el diseño contra el caso cloud: en modo cloud el navegador escribe contra un dominio del proveedor de almacenamiento, no contra el nuestro. Todo lo que asuma un único origen para la subida hace que el modo local y el cloud se comporten distinto, que es exactamente lo que este proyecto intenta evitar.

## Goals / Non-Goals

**Goals:**

- Que el contrato de cada puerto sea ejecutable, y que pasar la suite sea la definición operativa de "este proveedor sirve".
- Que la superficie de los puertos sea la mínima que el consumidor del change siguiente necesita.
- Que el modo local y el modo cloud tengan la misma forma: mismas operaciones, misma relación entre el navegador y los servicios, mismos supuestos de cacheo.
- Que ningún byte de imagen atraviese la aplicación, ni al subir ni al entregar.

**Non-Goals:**

- Cualquier endpoint o pantalla. Este change no agrega superficie HTTP propia ni toca la interfaz.
- Los adapters cloud, aunque el diseño se justifique en parte por ellos.
- Pre-generar derivados, procesar el contenido en la aplicación, y toda capacidad de la edición paga del transformador.
- Cuotas, límites por usuario y medición de consumo.

## Decisions

### D1 - Dos puertos independientes, cada uno con su propia variable

El almacenamiento y la transformación se configuran por separado. Nada impide combinar un almacenamiento cloud con un transformador autoalojado, y cada puerto se verifica sin depender del otro.

**Alternativa descartada:** una sola variable que seleccione el par completo, del tipo "modo local" o "modo cloud". Es menos configuración y hace imposible una combinación inválida, pero ata dos decisiones que no tienen por qué ir juntas —cambiar de almacenamiento no obliga a cambiar de transformador— y, sobre todo, haría que el contrato de un puerto no se pudiera ejercitar sin el otro, que es justo lo que este change busca.

### D2 - El puerto de almacenamiento tiene tres operaciones y ninguna devuelve bytes

Conceder una subida, consultar un objeto y eliminar objetos. No hay una cuarta que lea el contenido, y no por minimalismo sino porque nadie la necesita: el transformador lee del almacenamiento por su cuenta, y ningún otro consumidor tiene motivo para tener una imagen en memoria. Esa ausencia es una garantía verificable —que los bytes nunca atraviesan la aplicación— y la convierte en una propiedad del diseño en vez de una costumbre.

### D3 - La subida es de origen cruzado y el almacenamiento declara quién puede escribir

El navegador escribe directo contra el almacenamiento, que vive en otro origen: en local un servicio con su propia dirección, en cloud un dominio del proveedor. El almacenamiento declara qué orígenes admite, y esa declaración se aplica al preparar el entorno.

**Alternativa descartada:** proxear el almacenamiento por el edge para que la subida comparta origen con la aplicación. Suena mejor y es lo que el principio de puerta única sugiere, pero no funciona por dos razones. La firma del protocolo cubre la ruta y el host, así que el prefijo público tendría que coincidir exactamente con lo que el almacenamiento valida y cualquier reescritura invalidaría la firma. Y en modo cloud el proveedor sirve bajo su propio dominio de todas formas, así que forzar el proxy en local haría que los dos modos se comportaran distinto justo en el flujo de subida.

### D4 - El almacenamiento se alcanza por dos direcciones: la del navegador y la del servidor

Lo que se firma para el navegador se firma contra la dirección que el navegador puede alcanzar. Las operaciones del servidor —consultar y eliminar— usan la dirección por la que el servidor lo alcanza, que en el entorno de contenedores es el nombre del servicio en la red interna.

Son dos valores de configuración distintos, no uno derivado del otro. En modo cloud coinciden, porque el proveedor es público desde los dos lados. Unificarlos habría obligado a que el servidor salga a la red para hablar con un servicio que tiene al lado, o a que el navegador reciba firmas hechas para un host que no puede resolver.

### D5 - El transformador entra por el edge en local, y el adapter devuelve la dirección completa

En local la entrega de variantes pasa por el edge, que es donde vive el cache. En cloud el adapter devuelve el dominio del proveedor, que ya es un CDN. El puerto no expone esa diferencia: devuelve una dirección completa, y quien la consume no sabe si apunta al edge o a un tercero.

Esto no rompe la simetría que D3 sí obligaba a respetar, porque una imagen entregada no necesita negociación de origen cruzado: una etiqueta de imagen carga desde cualquier origen.

### D6 - El catálogo de variantes se declara en el proyecto y el adapter construye la transformación completa

Las variantes —su nombre, sus medidas, su calidad, su formato y la regla de no ampliar— se declaran una sola vez en el proyecto. El adapter lee esa declaración y construye con ella las opciones de procesamiento completas que pone en la dirección, más su firma. El transformador no necesita ninguna configuración de presets: recibe la transformación ya especificada.

**Alternativa descartada:** declarar las variantes en la configuración del transformador y que el adapter solo las nombre. Es tentador porque parece sacar las medidas del código, y tiene dos problemas. El primero es que convierte el nombre de la variante en un contrato entre dos lugares —el código lo nombra, la configuración del transformador lo define—, y un nombre que exista de un lado y no del otro produce imágenes que no cargan, con el error apareciendo en el navegador y no en las pruebas. El segundo es que no sobrevive a un segundo proveedor: un transformador cloud no tiene un archivo de configuración equivalente, así que el catálogo tendría que unificarse igual más adelante, y mientras tanto habría que mantener el mecanismo de invalidación que D7 describe.

Conviene desactivar un argumento que suele esgrimirse contra construir la transformación en el código: que multiplicaría el espacio de claves del cache. No lo hace. El catálogo es cerrado, así que el conjunto de direcciones que el sistema puede emitir también lo es, y en cualquier momento hay tantas como variantes. Lo que sí ocurre —y es deseable— es que cambiar el catálogo produzca direcciones nuevas, que es exactamente la invalidación que D7 necesitaba resolver con un mecanismo aparte.

### D7 - Cambiar una variante invalida sola, porque su definición viaja en la dirección

Como la dirección lleva las medidas, la calidad y el formato, cambiar cualquiera de ellos produce una dirección distinta y por lo tanto una entrada de cache distinta. Lo anterior deja de pedirse y envejece por su cuenta. No hace falta un valor invalidador, ni acceso al cache, ni un procedimiento que alguien deba recordar.

Esta propiedad vale también con una red de distribución delante, que es justamente el caso donde vaciar el cache a mano no alcanza porque no se administra ese cache.

**Alternativa descartada:** un valor de configuración que participe en la identidad de la respuesta para invalidar todo lo anterior al cambiarlo. Es la solución correcta **si la definición de la variante no viaja en la dirección** — o sea, si las variantes viven en la configuración del transformador. Con el catálogo en el proyecto es un mecanismo sin trabajo que hacer, y mantenerlo sería conservar una pieza cuyo motivo ya no existe.

### D8 - Firmar no habla con nadie, así que el cliente puede ser sincrónico

Conceder una subida es cómputo puro: se arma una cadena y se la firma, sin una sola petición. Consultar y eliminar sí hablan con el almacenamiento. Así que se usa el cliente sincrónico del protocolo, se firma directamente, y solo las dos operaciones que hacen red se apartan del bucle de eventos.

**Alternativa descartada:** una envoltura asincrónica del cliente. Evita apartar trabajo del bucle, pero agrega una dependencia menos difundida, con su propio ciclo de versiones, para dos operaciones que en este proyecto se llaman poco y nunca en el camino caliente. Firmar, que sí es frecuente, no gana nada porque no hace red.

### D9 - La suite de contrato es una sola, parametrizada por implementación

Existe un único conjunto de pruebas del contrato del almacenamiento, y se ejecuta dos veces: contra el doble y contra el servicio real. No hay dos suites que haya que mantener en correspondencia, porque dos suites divergen y la divergencia es invisible hasta que un proveedor falla en producción.

La consecuencia práctica es que el doble tiene que ser lo bastante fiel para pasar las mismas pruebas, y que agregar un proveedor es agregar un parámetro, no escribir pruebas nuevas.

### D10 - El doble de pruebas es un almacenamiento en memoria, no un simulacro de llamadas

El doble guarda objetos en memoria y responde como respondería el almacenamiento: rechaza una concesión vencida, rechaza escribir un objeto distinto del concedido, distingue ausente de vacío. No intercepta llamadas ni verifica que se haya invocado tal método.

**Alternativa descartada:** un doble que registre invocaciones. Es más rápido de escribir y no verifica nada útil: pasaría igual con un adapter que hace las llamadas correctas en el orden correcto y aun así no funciona. Un doble con comportamiento puede compartir suite con el proveedor real; uno que solo registra llamadas, no.

### D11 - Las medidas de las variantes se derivan del uso, el formato es WebP, y nunca se amplía

La variante de miniatura recorta a cuadrado de 400 píxeles de lado, porque el grid de la galería en un teléfono son dos columnas de entre 170 y 210 píxeles de ancho lógico, y a densidad de pantalla alta eso pide más de los 320 que parecían suficientes. La variante de calificación ajusta a 1080 píxeles en el lado largo **sin recortar**, porque la tarjeta ocupa casi todo el ancho de la pantalla y lo que se está juzgando es la foto completa: recortarla invalidaría la decisión que la persona está tomando. La variante de visor ajusta a 2048 en el lado largo, que tolera acercarse sin que los bytes dejen de pagarse en un teléfono.

A eso se agrega una regla que faltaba: **una imagen nunca se amplía**. Un original más chico que la variante se entrega con su tamaño original, porque ampliarlo gasta bytes para mostrar exactamente la misma información.

El formato de salida es WebP para las tres. La decisión merece explicarse porque la inclinación inicial fue la contraria: un formato más moderno comprime bastante mejor, y con un cache delante el cómputo extra se paga una sola vez por variante, lo que parecía zanjarlo. No lo zanja, porque ese cómputo no cae en un momento neutro: cae exactamente en el calentamiento de variantes al confirmar una subida y en la primera vista de una foto durante el swipe, que son las dos latencias que este diseño ya identificó como el riesgo real. Codificar en el formato más moderno es varias veces más lento, y el calentamiento hace una de esas codificaciones por foto del álbum, sobre una máquina de desarrollo o un servidor modesto. Sumado a que la negociación automática de formato es una capacidad de la edición paga —de modo que hay que elegir un formato para todos, sin poder degradar según el navegador—, WebP gana: soporte universal, codificación rápida y compresión suficientemente buena.

**Alternativa descartada:** el formato más moderno para las tres variantes, o mezclarlo solo en la miniatura, que es la más barata de codificar. Lo primero empeora las dos latencias que importan; lo segundo agrega una dimensión de variabilidad al conjunto de variantes a cambio de unos kilobytes en el payload más chico de los tres.

### D12 - El cache en disco se acota en dos gigabytes y treinta días de inactividad

El número sale de la aritmética y no de una intuición. Con las medidas de D11, las tres variantes de una foto pesan entre seiscientos kilobytes y un megabyte, así que un álbum de cuarenta fotos ocupa unos cuarenta megabytes. Dos gigabytes sostienen del orden de dos mil fotos con sus tres variantes, que está muy por encima de lo que puede estar en uso simultáneo en este proyecto. El plazo de inactividad es largo a propósito: lo que se quiere es que una variante sobreviva entre sesiones de uso, y la expulsión por espacio ya cubre el caso de que el cache se llene.

## Risks / Trade-offs

**Una declaración de orígenes mal hecha rompe la subida con un error opaco en el navegador** → Es la falla más probable de este change y la más difícil de leer, porque el navegador informa poco. Se mitiga con una tarea que verifica la subida desde el navegador en los dos modos de trabajo, no solo con pruebas del backend, que nunca ejercitan la negociación de origen.

**La firma incluye la dirección, así que usar el perfil de configuración equivocado produce firmas inválidas** → El síntoma es una subida rechazada sin explicación clara. Lo que lo previene es que cada modo sea un perfil completo, según D10 de `add-local-environment`; lo que lo detecta es verificar la subida en cada modo.

**Una variante del catálogo podría no tener traducción en algún transformador** → Con un solo transformador no puede pasar, pero el catálogo existe para sostener varios, y un proveedor que no pueda producir alguna variante tiene que detectarse al agregarlo y no al mirarlo en el navegador. La prueba que lo cubre es que cada variante del catálogo produzca una dirección válida con el adapter activo.

**El cache en disco crece sin techo** → Se declaran el tamaño máximo y el tiempo de inactividad, para que el cache tenga una cota y no llene el disco de la máquina de desarrollo.

**El doble puede ser más permisivo que el proveedor real** → La suite compartida acota el riesgo pero no lo elimina: un comportamiento que ninguna prueba cubre puede diferir. La mitigación es que la suite corra contra el proveedor real en cada ejecución y no solo en una corrida especial, para que la divergencia se note enseguida.

**Sin pruebas end-to-end, este contrato es la única red** → Asumido y ya considerado al decidir el alcance del testing. Es la razón por la que el contrato se escribe con este nivel de detalle y no como un puñado de pruebas de humo.

## Migration Plan

No hay nada que migrar: el change no toca el esquema ni tiene datos previos. Lo que agrega son dos servicios al entorno y dos módulos de infraestructura sin consumidores todavía, así que su despliegue no puede romper nada que exista.

El rollback es revertir el commit y bajar los dos servicios. El volumen del cache y el del almacenamiento quedan huérfanos y se eliminan con el comando de limpieza del entorno; ninguno contiene información que no se pueda reconstruir, porque en este punto del proyecto nadie subió nada.

## Open Questions

Ninguna. Las tres que quedaron abiertas al redactar se cerraron con aritmética y con una consecuencia del propio diseño.

**Resueltas durante la redacción**

- **Las medidas de las tres variantes.** Se derivaron del uso y quedaron en D11: el grid de dos columnas en un teléfono pide cuatrocientos píxeles para la miniatura, la tarjeta a ancho completo pide mil ochenta sin recortar, y el visor dos mil cuarenta y ocho. La derivación agregó una regla que no estaba: nunca ampliar un original más chico que la variante.
- **El formato de salida.** Se cerró en WebP, contra la inclinación inicial. El argumento de que con cache el cómputo se paga una sola vez resultó irrelevante al ubicar dónde cae ese cómputo: en el calentamiento y en la primera vista del swipe, las dos latencias que el diseño ya había identificado como el riesgo real. Sumado a que la negociación automática de formato es de la edición paga, obliga a elegir uno para todos.
- **La cota del cache en disco.** Se cerró en dos gigabytes con la aritmética a la vista, para que el número fuera auditable: las tres variantes de una foto pesan entre seiscientos kilobytes y un megabyte, así que dos gigabytes sostienen unas dos mil fotos calientes.

Una cuarta cuestión se resolvió durante la redacción sin haber llegado a ser pregunta abierta: **cómo alcanza el navegador al almacenamiento**. Probar el diseño contra el caso cloud mostró que proxearlo por el edge no funciona —la firma cubre la ruta y el host, y en cloud el proveedor sirve bajo su propio dominio—, lo que produjo D3 y obligó a corregir el delta de `local-environment`.
