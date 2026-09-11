## Context

El estado de partida son cuatro changes: un entorno con edge y dos modos de trabajo, una capa de datos en SQL crudo con la conexión explícita y modelos validados en la frontera, identidad y sesión resueltas por un puerto, y los dos puertos de medios con su contrato verificado. Este change es el primero que junta todo y el primero que produce algo que una persona puede usar.

Lo que más condiciona el diseño es una consecuencia del change anterior: como la subida es directa al almacenamiento y la API solo concede el permiso, **la fila de una foto nace antes que sus bytes**. Ese intervalo no es un detalle de implementación que se pueda esconder: dura lo que dure la subida, puede no cerrarse nunca si alguien abandona, y cualquier lectura que lo ignore muestra fotos que no están.

El segundo condicionante es que este change estrena las tareas diferidas del proceso de la API, con las tres salvaguardas que el proyecto ya decidió al descartar un worker. Y el tercero es que D11 del change anterior eligió WebP precisamente porque el costo de codificar cae acá, en el calentamiento.

## Goals / Non-Goals

**Goals:**

- Que una foto no disponible sea invisible por construcción y no por disciplina de cada consulta.
- Que el cliente pueda reintentar cualquier paso de la subida sin razonar sobre el estado, porque cada paso es seguro de repetir.
- Que la lista de álbumes se resuelva en una consulta, con portada y conteo incluidos.
- Que la desincronización entre la base y el almacenamiento, cuando ocurra, deje huérfanos invisibles y nunca referencias rotas.

**Non-Goals:**

- Reordenar, elegir portada, editar la imagen y todo lo que el proposal ya dejó fuera.
- Compartir, calificar y las estadísticas.
- Cualquier forma de procesamiento del contenido en la aplicación.
- Un proceso permanente que limpie restos: la reconciliación es un comando.

## Decisions

### D1 - La disponibilidad de una foto se filtra en una vista, no en cada consulta

El spec exige que una foto no disponible sea invisible para todo el sistema. Implementarlo agregando una condición a cada consulta funcionaría hasta que alguien escriba la siguiente y se olvide, y el síntoma sería una foto fantasma en un grid o un conteo inflado — el tipo de error que nada señala.

Así que la migración crea una vista que expone solo las fotos disponibles, y **todas las lecturas van contra la vista mientras las escrituras van contra la tabla**. El deck del change siguiente y las estadísticas del posterior heredan la garantía sin saber que existe: al consultar la vista, no hay condición que olvidar.

Es el mismo razonamiento que llevó al trigger de última modificación en `add-backend-data-layer`: convertir una regla que hay que recordar en una propiedad de la estructura.

**Alternativa descartada:** una condición en cada consulta, con una prueba por consulta que verifique que la incluye. Es lo directo, y el problema es que la prueba hay que acordarse de escribirla también, así que solo mueve el olvido de lugar.

### D2 - El lote es la unidad de la subida en las dos operaciones

Conceder y confirmar operan sobre un conjunto de fotos, no sobre una. Quien sube elige varias de una vez en el selector del teléfono, y hacer una vuelta de red por foto multiplica la latencia y la cantidad de estados intermedios que el cliente tiene que representar.

Del lote como unidad se sigue el rechazo completo que el spec establece: si un archivo del conjunto es inadmisible, no se concede ninguno.

### D3 - El cliente valida antes de pedir y el servidor valida igual, y la duplicación es deliberada

El cliente conoce el tipo y el tamaño de cada archivo antes de pedir nada, así que filtra y avisa de inmediato sin gastar una petición. El servidor vuelve a validar porque es la frontera y no puede confiar en el cliente.

Ninguna de las dos validaciones reemplaza a la otra: la del cliente existe para que la experiencia sea inmediata, la del servidor para que la regla se cumpla. Y es lo que hace defendible el rechazo del lote completo — un rechazo del servidor significa que el cliente mandó algo que su propia validación debería haber atajado, o sea una inconsistencia, no un caso de uso normal.

### D4 - Cada paso de la subida es seguro de repetir

Conceder de nuevo produce concesiones nuevas para fotos nuevas; subir de nuevo sobrescribe el mismo objeto; confirmar de nuevo no cambia nada. Eso le permite al cliente reintentar sin llevar la cuenta de qué llegó a completarse, que es la única forma de que una cola de subida en un teléfono con señal intermitente sea manejable.

La consecuencia inversa también importa: **el cliente puede confirmar fotos que nunca subió, y es inofensivo**, porque la confirmación verifica contra el objeto y no contra lo que el cliente afirma. No hace falta protegerse de eso.

### D5 - La cola de subida del cliente mantiene estado por archivo y reintenta de a uno

Cada archivo del lote tiene su propio estado —esperando, subiendo con su progreso, subido, fallido—, la cantidad de subidas en curso está acotada, y un reintento reintenta únicamente el archivo que falló. Al confirmar se confirman solo los que llegaron a subirse.

Esto es estado real coordinándose, con varios valores que cambian de forma independiente, así que se gana su propio módulo en la feature en lugar de vivir dentro del componente. Es el caso que la regla de D8 de `add-local-environment` describe como digno de extraerse.

### D6 - Los objetos se eliminan después de confirmar la transacción, nunca dentro

Eliminar una foto o un álbum es una transacción que borra registros, y recién después de confirmarla se eliminan los objetos del almacenamiento.

El orden no es solo para que un fallo deje huérfanos en vez de referencias rotas: es que eliminar objetos es una llamada de red a un sistema externo, y `database-access` prohíbe explícitamente mantener una transacción abierta mientras se espera una respuesta externa. Hacerlo dentro violaría ese requirement además de retener una conexión del pool durante una llamada remota.

### D7 - El calentamiento pide la variante por el mismo camino que un visitante

Después de responder la confirmación, una única tarea diferida pide la variante de calificación de las fotos que quedaron disponibles, con la cantidad de peticiones en curso acotada, un tiempo de espera corto por petición, y cualquier fallo registrado y nada más.

El detalle que hay que no equivocar: **esas peticiones van al edge, no al transformador**. El objetivo es llenar el cache del edge, que es lo que vería una persona; pedírselo directamente al transformador produciría la variante, la descartaría y dejaría el cache igual de vacío. Es un error que no da ningún síntoma —el calentamiento parece funcionar— hasta que se mide la primera vista y sigue siendo lenta.

### D8 - La reconciliación es un comando que se ejecuta cuando hace falta

Un comando descarta los registros no disponibles cuya concesión venció y los objetos que no tienen registro. No hay proceso permanente ni tarea programada, en coherencia con la decisión de no tener worker: lo que la reconciliación limpia no afecta a nada observable, así que no hay urgencia que justifique automatizarla.

**Alternativa descartada:** limpiar de forma oportunista, por ejemplo al listar un álbum. Evita el comando, pero pone una escritura en un camino de lectura y hace que el costo de una operación dependa de cuánta basura haya acumulada.

### D9 - La lista de álbumes resuelve portada y conteo en la misma consulta

Una sola consulta devuelve cada álbum con su cantidad de fotos disponibles y la primera de ellas como portada, usando una subconsulta lateral por álbum en lugar de una vuelta por álbum. Es exactamente el tipo de consulta que motivó elegir SQL crudo: expresarla es natural en SQL y trabajosa a través de cualquier capa que la derive de modelos.

### D10 - La cantidad de fotos se cuenta, no se guarda

No hay columna con el total. Mantener un contador obliga a actualizarlo al conceder, al confirmar y al eliminar, y basta un camino que se olvide para que quede desviado de la realidad sin que nada lo señale. Contar sobre un índice es barato en las magnitudes de este proyecto.

**Alternativa descartada:** una columna con el total, mantenida por trigger. El trigger resolvería el olvido, pero agrega una pieza para optimizar una consulta que todavía no es lenta, y un contador desviado es más difícil de diagnosticar que una consulta lenta.

### D11 - Las rutas del álbum comparten la carga del álbum en su layout

El layout del álbum lo carga una vez y las cuatro vistas hijas —grid, subida, y las dos que llegan en changes posteriores— lo leen de ahí. Ninguna vuelve a pedirlo. Es la razón por la que el directorio del álbum tiene un layout propio y no cuatro rutas planas.

### D12 - Las posiciones del lote se asignan dentro de la misma transacción que los registros

La posición de cada foto se calcula a partir de la última existente y se asigna en la misma transacción en la que se insertan los registros del lote. Si dos lotes del mismo álbum se conceden a la vez, la transacción es lo que evita que ambos reclamen las mismas posiciones.

### D13 - El lote admite hasta cincuenta fotos, y el cliente parte una selección más grande

El techo del lote es cincuenta. El número no sale del producto sino de qué es lo que el límite acota: cincuenta concesiones son una respuesta de pocas decenas de kilobytes, y cincuenta archivos del tamaño máximo son ya varios minutos de subida con la concurrencia acotada del cliente, así que un lote más grande no se aprovecharía mejor.

Lo que hace seguro ese número es que **el límite acota la petición y no el álbum**. Una selección de más de cincuenta fotos la parte el cliente en lotes sucesivos, y quien sube ve una sola operación con su progreso. El techo no expresa ninguna regla de producto: solo tiene que ser lo bastante grande para que subir sea eficiente y lo bastante chico para que una petición esté acotada.

De eso se siguen dos precisiones. La primera es que **el lote es una unidad de transporte y no una unidad visible**: refina D2 sin contradecirlo, porque el lote sigue siendo la unidad de la operación mientras una selección puede abarcar varios. La segunda es que **los lotes de una misma selección se envían en orden y no en paralelo**, porque D12 asigna las posiciones dentro de la transacción y lotes concurrentes obtendrían rangos que no se solapan pero podrían intercalarse, alterando el orden en que la persona eligió las fotos.

### D14 - El álbum tiene un máximo configurable que condiciona la escritura y no lo ya guardado

Un álbum admite hasta una cantidad máxima de fotos, declarada en la configuración del entorno con cincuenta por omisión. No es una cuota de consumo —el no-goal de cuotas que fijó `add-media-ports-and-local-adapters` sigue en pie— sino una restricción de producto: la interacción central de pixpick es calificar un álbum foto por foto con un gesto, y un álbum de quinientas fotos es incalificable. El máximo protege esa interacción, no el costo de almacenamiento, y por eso vive en el álbum y no en el usuario.

Dos precisiones hacen que sea implementable sin sobresaltos.

La primera es **qué se cuenta**: las fotos disponibles más las que están a la espera de confirmarse con su permiso vigente. Contar solo las disponibles permitiría superar el máximo pidiendo concesiones repetidamente antes de confirmar ninguna. Y excluir las esperas vencidas es correcto porque una concesión vencida ya no puede completarse, así que esa foto no va a existir nunca: el vencimiento que D13 y el spec ya establecen hace de liberación automática del lugar reservado, sin necesidad de ningún proceso que lo devuelva.

La segunda es **que el máximo es una precondición de la escritura y no un invariante de lo almacenado**. Un álbum que ya lo supera —porque el máximo se bajó después de que se llenó— conserva todas sus fotos y sigue funcionando igual; lo único que se rechaza es agregarle más. Eliminar fotos hasta quedar por debajo vuelve a habilitar la incorporación. Esto evita el escenario destructivo que tendría la interpretación contraria: bajar un valor de configuración no puede hacer desaparecer fotos de nadie.

Del máximo se sigue una situación de error que las convenciones de la API todavía no cubrían: una petición bien formada que no procede por el estado del recurso. Se distingue de un error de validación porque exige una acción distinta —liberar espacio y reintentar la misma petición, en lugar de corregir lo enviado— y por eso este change la agrega como requirement de esa capability en vez de resolverla como un caso particular acá.

## Risks / Trade-offs

**Alguien puede consultar la tabla de fotos en vez de la vista y perder la garantía de D1** → La vista lo hace fácil de hacer bien pero no imposible de hacer mal. La mitigación es que la regla quede escrita acá y que cada change posterior que lea fotos verifique en sus pruebas que una foto no disponible no aparece; el spec ya obliga a esos escenarios, así que el costo es nulo.

**El calentamiento apuntado al transformador en vez del edge no da ningún síntoma** → Es el riesgo más engañoso del change, porque todo parece funcionar. Se mitiga con una tarea que verifica que después del calentamiento el cache del edge efectivamente tiene la variante, no solo que el calentamiento no falló.

**Las tareas diferidas corren en el proceso de la API después de responder** → Un lote grande deja al proceso emitiendo peticiones cuando ya contestó. Lo acotan el límite de peticiones en curso y el tiempo de espera corto; y el lote está acotado por cuántas fotos tenga un álbum, que en este producto es decenas.

**Los objetos huérfanos se acumulan hasta que alguien ejecute la reconciliación** → Aceptado: son invisibles y solo cuestan almacenamiento. El riesgo real es que nadie recuerde que el comando existe, así que queda documentado en el README junto al resto de las operaciones.

**Una subida abandonada deja un registro que nunca se limpia solo** → Mismo caso que el anterior y con la misma mitigación. Lo que sí está garantizado por el spec es que ese registro no afecta nada observable.

**El grid del álbum pide una miniatura por foto y todas a la vez** → Con el cache del edge la segunda visita es barata, pero la primera de un álbum recién subido dispara tantas transformaciones como fotos. El calentamiento cubre la variante de calificación, no la miniatura, así que la primera apertura del grid sigue siendo el momento más caro. Se acepta porque el colapso de peticiones simultáneas del change anterior evita que se multiplique, y porque es una sola vez por álbum.

Vale anotar que ese último punto es un candidato natural a ampliar el calentamiento para que cubra también la miniatura, si al usarlo resulta molesto.

## Migration Plan

La migración es aditiva: dos tablas y una vista sobre un esquema que ya tiene usuarios y sesiones. No hay datos que transformar.

El rollback elimina la vista y las dos tablas, y con ellas toda referencia a los objetos subidos. Esos objetos quedan huérfanos en el almacenamiento y se eliminan con el comando de limpieza del entorno o con la reconciliación antes de revertir. Es la primera vez en el proyecto que un rollback deja estado externo: hasta acá revertir solo afectaba a la base.

## Open Questions

Ninguna. La que quedó abierta se resolvió al preguntarse qué acota realmente el límite, y una segunda llegó como pedido explícito del usuario.

**Resueltas durante la redacción**

- **El máximo de fotos por lote.** Se cerró en cincuenta dentro de D13. Lo que la resolvió fue notar que el límite acota la petición y no el álbum: una selección mayor la parte el cliente en lotes sucesivos y quien sube ve una sola operación. De ahí salieron dos precisiones que no estaban: el lote es una unidad de transporte y no una unidad visible, y los lotes de una misma selección se envían en orden y no en paralelo, porque D12 asigna las posiciones dentro de la transacción.
- **El máximo de fotos por álbum.** Llegó como pedido del usuario y se cerró en D14 con dos definiciones que hacían falta para que fuera implementable: qué se cuenta —disponibles más esperas con permiso vigente, porque contar solo las disponibles permitiría superar el máximo pidiendo concesiones repetidamente— y que el máximo es una precondición de la escritura y no un invariante de lo almacenado, de modo que bajar el valor nunca haga desaparecer fotos de nadie.
