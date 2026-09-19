## Context

Conceder permisos de subida hoy hace, dentro de una transacción: bloquear la fila de la persona dueña con `select ... for update` —que a la vez comprueba que exista—, comprobar la pertenencia del álbum como consulta aparte, contar las fotos ocupadas del álbum, sumar el consumo de la cuenta, calcular la posición siguiente, y recorrer los archivos concediendo los que entran en los dos límites y devolviendo con su motivo los que no. La firma de cada permiso es un cálculo local sobre las credenciales y no sale a la red en ninguno de los dos proveedores, así que esa transacción dura milisegundos aunque el lote tenga cincuenta archivos.

El consumo de una cuenta se calcula al momento, con una consulta que suma sobre las fotos de sus álbumes el tamaño real de las disponibles y el declarado de las que esperan con permiso vigente, excluyendo las de permiso vencido y los álbumes que la retención ya dio de baja. Esas tres condiciones —qué bytes cuenta cada foto, qué fotos cuentan y qué álbumes están activos— viven como constantes compartidas en el repositorio de `quota`, y la consulta de la cuenta y la del desglose por álbum ya las reusan.

Los tamaños están en la base desde antes: `declared_size` se escribe al conceder y `size` al confirmar, y la confirmación compara el objeto real contra lo declarado y rechaza el que no coincide. Para toda foto disponible el tamaño registrado es el real.

Lo que hay en el almacenamiento, en cambio, no coincide exactamente con lo que la base cuenta. Una foto cuyo permiso venció deja de contar, pero su objeto puede haber llegado igual y sigue ocupando lugar hasta que se lo descarte; y eliminar una foto borra primero el registro, de modo que un fallo posterior deja un huérfano identificable. El comando `src.maintenance.reconcile` es lo que descarta ambas cosas, y hoy se corre a mano: su docstring dice explícitamente que lo que descarta es invisible para todos hasta entonces y que por eso no hay urgencia que justifique agendarlo.

La primera pantalla después de iniciar sesión ya pide el consumo de la cuenta sin esperarlo para dibujar y lo muestra con un medidor que calcula el porcentaje, pinta la barra y cambia de color cuando no queda lugar.

## Goals / Non-Goals

**Goals:**

- Que el límite de la instancia no se pueda superar por dos pedidos simultáneos, ni de la misma persona ni de personas distintas.
- Que las dos sumas —la de la cuenta y la de la instancia— no puedan contar cosas distintas, por construcción y no por disciplina.
- Que un rechazo por instancia llena se distinga de uno por cuenta llena en todo el recorrido, del motivo que devuelve el backend al texto que se lee en pantalla.

**Non-Goals:**

- Hacer que el número contado coincida exactamente con lo que el proveedor factura. No puede: hay objetos que existen y no cuentan. Lo que se busca es que la diferencia esté acotada y absorbida por el margen, no que sea cero.
- Optimizar la suma de la instancia antes de tener un caso que lo pida, por la misma razón que D2 de `add-account-quota` no optimizó la de la cuenta.
- Sostener concesiones concurrentes a gran escala. La instancia tiene un techo de decenas de cuentas; el diseño se permite serializar donde eso alcance.

## Decisions

### D1 - El punto de exclusión pasa a ser la instancia entera, y reemplaza al bloqueo por persona

La transacción de concesión toma un advisory lock de transacción con una clave fija, siempre la misma, en lugar de bloquear la fila de la persona dueña.

No es un bloqueo más sino uno en vez del otro, por el mismo argumento con el que D1 de `add-account-quota` reemplazó el bloqueo del álbum por el de la persona: como serializar por persona ya serializaba por álbum, serializar globalmente ya serializa por persona. Todo lo que el bloqueo por persona protegía —que dos lotes no cuenten la misma ocupación ni calculen la misma posición siguiente— queda protegido igual, y con una sola exclusión para los tres límites en lugar de una por alcance.

Y sobre todo, evita el problema que aquel D1 ya había identificado al descartar su propia alternativa: dos mecanismos para una misma exclusión admiten dos órdenes de adquisición y por lo tanto un abrazo mortal entre transacciones que los tomen en orden distinto. Con un único mutex no hay orden que equivocar.

Un advisory lock y no una fila de una tabla marcadora porque no hay ninguna fila que represente a la instancia, y crear una tabla con un solo registro para usarla de mutex es una migración y un concepto nuevo en el esquema para algo que Postgres ya ofrece. El lock de transacción se libera solo al terminar, con commit o con rollback, sin nada que recordar liberar.

La comprobación de que la persona existe, que hoy viaja pegada al bloqueo, se conserva como consulta sin bloqueo para no cambiar de paso qué error devuelve una sesión viva de una cuenta eliminada.

Serializar solo la concesión alcanza porque es el único flujo que **agrega**. Confirmar reemplaza el tamaño declarado por el real, que ya estaba contado, y eliminar solo libera; ninguno de los dos puede hacer que un límite se supere.

### D2 - El total de la instancia se suma al momento, con las mismas condiciones que el de la cuenta

El consumo de la instancia se calcula con la misma consulta que el de la cuenta, sin la condición sobre el dueño, reusando las tres constantes que ya definen qué bytes aporta cada foto, qué fotos cuentan y qué álbumes están activos.

Reusar las constantes es la decisión, no un detalle de escritura. El spec exige que las dos sumas cuenten lo mismo y difieran solo en el alcance; si cada consulta llevara sus propias condiciones, cumplir eso dependería de que alguien acordara cambiar las dos a la vez cada vez que cambie una. Compartiendo las condiciones, la exigencia se cumple porque no hay dos lugares donde divergir.

La alternativa —un total acumulado en una fila— se descarta por las mismas razones que D2 de `add-account-quota` descartó el acumulado por cuenta, agravadas: habría que mantenerlo en los mismos cinco flujos, y un desfase acá no afecta a una cuenta sino a todas.

El límite acota el tamaño del problema, aunque menos que el de la cuenta. Con 6 GiB y fotos de tamaño corriente son unos pocos miles de filas; en el peor caso realista, con fotos de unos 10 KB, unas seiscientas mil. Es una agregación sin filtro que se paga una vez por lote, dentro del lock de D1, así que su costo es también el ancho de la ventana de serialización. A la escala de este proyecto eso es aceptable; si dejara de serlo, el acumulado se puede introducir sin tocar ninguna spec, porque ninguna dice cómo se calcula el número.

### D3 - El consumo de la instancia viaja por un recurso propio, y solo como porcentaje

Se agrega un recurso que devuelve únicamente el porcentaje ocupado de la instancia, redondeado. No se agregan el total ni el límite en bytes al recurso del consumo de la cuenta, ni se los devuelve tampoco este recurso propio.

El propósito escrito de `account-quota` es el espacio de una persona, y define tres niveles —cuenta, álbum y foto— que son todos suyos y todos reservados a ella. El de la instancia no es de nadie: colgarlo de ahí obligaría a que un recurso cuyo contrato entero es "esto es tuyo y de nadie más" devolviera además un número que es de todos, y el mismo para cualquiera que lo pida.

La contrapartida es un pedido más en la primera pantalla. No se espera para dibujar, igual que el del consumo de la cuenta, así que no retrasa nada de lo que se ve.

El recurso devuelve el porcentaje y nada más: ni el total, ni el límite, ni un desglose por cuenta. El desglose por cuenta se descarta por la misma razón que en la primera versión de esta decisión: `account-quota` reserva el consumo de una persona a esa persona, y exponerlo aquí lo filtraría por la puerta de al lado. El total y el límite en bytes se descartan después, a pedido explícito: son la capacidad real de la instalación, y publicarlos a cualquier sesión iniciada describe la infraestructura de quien la hospeda sin que quien pide subir necesite ese dato — el porcentaje ya es lo único que le permite decidir algo (esperar, o intentarlo más tarde). El cálculo (`used_bytes / limit_bytes`, redondeado y con techo en 100) sigue viviendo en el backend, sobre los mismos dos números que ya calcula D2; lo único que cambia es que esos dos números nunca cruzan la respuesta.

### D4 - El tercer límite se evalúa después del de la cuenta, en el mismo recorrido

El recorrido que hoy comprueba el álbum y después la cuenta comprueba la instancia en tercer lugar, y descuenta del remanente de la instancia a medida que concede, igual que ya hace con los otros dos.

El orden es lo que implementa la precedencia que el spec exige: comprobar la cuenta antes que la instancia hace que, cuando las dos estén llenas, el motivo que salga sea el de la cuenta, que es el accionable. No hace falta una comparación explícita entre los dos motivos; alcanza con el orden de las comprobaciones.

Como el de la cuenta y a diferencia del álbum, no corta el lote: un archivo más chico más adelante puede entrar igual, y descartar el resto por el orden en que se eligieron no libera nada.

### D5 - El medidor se generaliza en lugar de duplicarse

El componente que ya muestra el consumo de la cuenta pasa a recibir qué nombra y qué decir cuando no queda lugar, y se usa para los dos medidores.

La barra, el cálculo del porcentaje, el tope en cien y el cambio de color al llenarse son idénticos para los dos casos; lo único distinto es el rótulo y el texto de lleno, que es justamente lo que el spec de `upload-feedback` pide que no se confunda. Un componente aparte para la instancia sería el mismo archivo con dos cadenas cambiadas, y el día que la barra cambie habría que acordarse de los dos.

### D6 - De dónde salen 6 GiB y 120 MiB

Los dos valores son binarios, siguiendo la convención que el código ya usa para el límite por cuenta y el tamaño máximo de archivo.

6 GiB contra los 10 GB del free tier de R2 deja un margen deliberado de más de tres gigabytes. Ese margen no es redondeo: es lo que absorbe la diferencia entre lo que la base cuenta y lo que el proveedor factura, que existe por los objetos huérfanos descritos en el Context y que solo desaparece cuando se corre la limpieza.

120 MiB por cuenta entran 51 veces en 6 GiB. Que el techo de la instancia se alcance con unas cincuenta cuentas llenas es la consecuencia buscada: ninguna cuenta sola puede acercarse al límite común, y hace falta que la instancia se use de verdad para que el límite empiece a morder.

## Risks / Trade-offs

**Toda concesión de la instancia se serializa** → La transacción no hace entrada/salida de red y dura milisegundos, así que la espera posible es corta y solo contra otra concesión simultánea. Si alguna vez dejara de alcanzar, el lock se puede tomar solo cuando el total esté cerca del límite, sin tocar ninguna spec.

**El total contado no es la ocupación real del proveedor** → Los objetos de permisos vencidos y los huérfanos de un borrado fallido ocupan lugar facturable y no cuentan. El margen de D6 los absorbe, y la limpieza que ya existe los elimina. El riesgo real no es la diferencia sino que nadie corra la limpieza nunca, que es lo que la pregunta abierta de más abajo plantea.

**La suma sin filtro crece con la instancia y se paga dentro del lock** → Acotada por el límite, con el peor caso realista calculado en D2, y con el acumulado como salida si algún día importa.

**Bajar el límite por cuenta a 120 MiB deja cuentas por encima** → No se borra nada y lo único que se les rechaza es agregar, que es lo que `account-quota` ya establece para este caso exacto. No hace falta migración ni aviso.

**El porcentaje de la instancia es visible para todos** → Expone que el espacio común se está llenando, que es el punto, y nada más: ni el total ni el límite en bytes, que revelarían la capacidad real de la instalación, ni ningún dato de ninguna cuenta en particular — los dos, excluidos del recurso por D3.

## Migration Plan

Ninguna migración de base de datos: no hay columnas nuevas y las sumas se calculan sobre las filas que ya existen.

El despliegue necesita la variable nueva del límite de la instancia y el valor nuevo del límite por cuenta. Si la variable nueva falta, rige el valor por omisión declarado en el código, así que un despliegue que la olvide queda limitado igual y no sin límite. `.env.example` la documenta junto a las otras dos.

El rollback es revertir el código: nada de lo que este change escribe queda persistido, y volver atrás devuelve el comportamiento anterior sin dejar estado que limpiar. Volver atrás el valor del límite por cuenta tampoco requiere nada, por la misma razón por la que bajarlo no requirió nada.

## Open Questions

**¿La limpieza de huérfanos tiene que pasar a correrse sola?** El comando existe y hoy se corre a mano, con una justificación escrita en su docstring: lo que descarta es invisible para todos hasta entonces. Este change debilita esa premisa, porque lo que descarta pasa a ocupar espacio facturable que el total contado no ve. Queda abierta porque es genuinamente diferible: el límite funciona igual se corra o no, el margen de D6 está dimensionado para absorber la diferencia mientras tanto, y agendarla es una decisión operativa que no cambia ningún spec, ningún enfoque ni ninguna tarea de este change. Responderla ahora, además, exigiría estimar a qué ritmo se acumulan huérfanos en una instancia que todavía no tiene uso real.

### Resueltas durante la redacción

- **¿Sumar un lock global al de persona o reemplazarlo?** Reemplazarlo. Lo cerró el propio D1 de `add-account-quota`: al descartar su alternativa dejó escrito que dos mecanismos para una misma exclusión admiten dos órdenes de adquisición y con ellos un abrazo mortal. El argumento aplica igual un alcance más arriba, y la aritmética de la exclusión —serializar globalmente ya serializa por persona— es la misma con la que aquel reemplazó el bloqueo del álbum.
- **¿El consumo de la instancia dentro del recurso de la cuenta o aparte?** Aparte. Lo cerró el propósito escrito de `account-quota`, que define su alcance como el espacio de una persona y reserva los tres niveles a su dueño; un número igual para todos no cabe ahí sin ensanchar ese propósito.
- **¿El recurso de la instancia devuelve el total y el límite en bytes, o solo el porcentaje?** Solo el porcentaje, a pedido explícito del usuario después de una primera implementación que sí devolvía los dos números en bytes. El total y el límite reales de la instalación no le sirven a quien pide subir para decidir nada que el porcentaje no le diga ya, y publicarlos a cualquier sesión iniciada expone la capacidad de la infraestructura de quien hospeda. D3 quedó actualizado para reflejar esto.
- **¿Qué motivo se informa cuando la cuenta y la instancia están llenas a la vez?** El de la cuenta. Derivado de que eliminar fotos propias baja los dos totales: el de la cuenta es el único de los dos sobre el que quien pide puede actuar, así que informar el otro escondería la acción que sirve.
- **¿Los valores son binarios o decimales?** Binarios, confirmado por el usuario, siguiendo la convención del código existente.
- **¿Cuántas cuentas llenas entran en el límite de la instancia?** 51, por derivación aritmética: 6144 MiB dividido 120 MiB.
- **¿El total contado equivale a lo que R2 factura?** No. Lo cerró la lectura del docstring de `src.maintenance.reconcile` junto con los requirements de `photo-upload` sobre permisos vencidos y sobre el huérfano que deja un borrado fallido: hay objetos que existen, ocupan y no cuentan. De ahí el margen de D6 y la pregunta abierta de más arriba.
- **¿Hace falta un rol de administrador para ver el porcentaje?** No, resuelto por el usuario al elegir que lo vea todo el mundo, lo que además evita introducir en el producto un concepto que hoy no tiene.
