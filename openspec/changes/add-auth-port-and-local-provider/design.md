## Context

El estado de partida es el que dejan los dos changes anteriores: un entorno donde el navegador entra por un único edge que comparte origen entre la interfaz y la API, migraciones con dbmate que se aplican antes de que el backend atienda, una capa de acceso en SQL crudo con la conexión como parámetro explícito, y una suite que corre contra Postgres real con aislamiento por rollback. Este change es el primero que crea tablas de dominio y el primero que expone endpoints más allá del healthcheck.

Tres cosas del contexto condicionan el diseño. La primera es que el edge no ve TLS —lo termina el proxy de la plataforma—, así que toda URL absoluta se deriva de la configuración y no del request, según D9 de `add-local-environment`. La segunda es que el proveedor real va a ser Google, que redirige de vuelta desde otro sitio, y eso impone restricciones sobre las cookies que hay que respetar desde ahora o el change de Google rompe el flujo. La tercera es que el link compartido del change 6 se va a abrir desde otra aplicación —un mensajero, un correo—, y eso también impone restricciones sobre las cookies.

## Goals / Non-Goals

**Goals:**

- Que agregar Google sea escribir un adapter y cambiar una variable, sin tocar el flujo de sesión ni los endpoints.
- Que el proveedor local permita verificar todo el resto del proyecto sin credenciales de terceros ni pantallas de consentimiento.
- Que las restricciones que impondrán Google y los links compartidos estén satisfechas desde este change, no descubiertas más adelante.
- Que el usuario autenticado llegue al código de una sola forma, para que los changes siguientes no inventen la suya.

**Non-Goals:**

- Vinculación de cuentas entre proveedores. Una identidad externa es un usuario; no hay flujo para unificar dos.
- Roles, permisos y cualquier noción de autorización que no sea pertenencia.
- Sesiones administrables por la persona, del tipo "ver mis dispositivos y cerrar sesión en otro". La capacidad técnica existe porque las sesiones son filas, pero no hay interfaz para eso.
- Limitación de intentos y protección contra fuerza bruta. Sin credenciales propias no hay nada que adivinar.

## Decisions

### D1 - El adapter local recorre el ciclo completo y la pantalla de desarrollo la sirve el backend

El adapter local no atajará el flujo: produce una dirección de autorización, la persona llega a una pantalla, y el retorno trae un código que se canjea. Esa pantalla la sirve el propio backend como un documento mínimo, no una ruta de la interfaz.

Servirla desde el backend es lo que mantiene al adapter autocontenido y lo que hace que el ciclo tenga la misma forma que tendrá con Google: desde el punto de vista de la interfaz, la pantalla de autenticación es un lugar externo al que se la envía y del que vuelve. Si fuera una ruta de la interfaz, el adapter del backend tendría que conocer una ruta del frontend, y el flujo dejaría de parecerse al real justo en el punto que interesa ensayar.

**Alternativa descartada:** un login local que devuelva la sesión directamente, sin redirección ni código. Es mucho menos código y para desarrollar alcanzaría. Se descarta porque entonces el puerto no estaría ejercitado: el ciclo de redirección y canje, que es donde están los errores difíciles —la correspondencia del estado, el destino de retorno, la cookie que sobrevive a la navegación de vuelta—, quedaría sin probar hasta el día que se conecte Google.

### D2 - El adapter local se niega a activarse fuera de desarrollo

El código que el adapter local canjea no está respaldado por nada: es un valor que la pantalla de desarrollo emite y que el adapter acepta. Eso significa que quien pueda llamar al retorno con un código arbitrario obtiene una sesión como esa persona.

Es aceptable porque el adapter existe para desarrollar, y para que no deje de ser aceptable la selección de proveedor rechaza activarlo cuando el entorno declarado no es de desarrollo. El servicio no arranca en ese caso. Es una decisión de seguridad que se toma acá y no en el change de Google, porque el riesgo aparece acá.

### D3 - El estado y el destino de retorno viajan en una cookie de un solo uso, sin firmar

Al iniciar sesión se genera un valor impredecible que se manda al proveedor y se guarda, junto al destino de retorno, en una cookie httpOnly de vida corta. El retorno exige que el valor que trae la query sea igual al de la cookie, y la cookie se elimina al consumirse.

No hace falta firmar nada porque no se confía en el contenido de la cookie: se compara por igualdad contra lo que el proveedor devuelve. Un tercero no puede escribir esa cookie en el navegador de la víctima, y sin ella el retorno se rechaza. Es lo que permite que este change no introduzca ningún secreto de firma.

**Alternativas descartadas:** guardar el estado en una tabla, que es durable y sobrevive a varios procesos, pero agrega una escritura por inicio de sesión y basura que hay que limpiar, para proteger algo que ya es por navegador. Y firmar la cookie, que obligaría a introducir un secreto sin agregar garantía, porque la comparación no depende de que el contenido sea confiable.

### D4 - Las cookies son SameSite en modo laxo, y por eso cerrar sesión no puede ser una lectura

El modo estricto no manda la cookie en una navegación de nivel superior que venga de otro sitio, y este sistema tiene dos situaciones que son exactamente eso: el retorno del proveedor, que en el caso de Google llega desde otro dominio, y el link compartido, que la gente va a abrir desde un mensajero. Con el modo estricto, la cookie de estado no llegaría al retorno y el login fallaría; y quien abriera el link compartido desde un chat aparecería como no autenticado aunque tuviera sesión.

La contrapartida hay que asumirla explícitamente: el modo laxo sí manda la cookie en navegaciones de nivel superior originadas en otro sitio, así que ninguna operación que cambie estado puede responder a una lectura. En particular **cerrar sesión es una escritura, no una lectura** — si fuera una lectura, bastaría una imagen incrustada en otro sitio para cerrarle la sesión a quien la visite.

### D5 - La sesión vence en un plazo fijo y no se renueva

La sesión vence treinta días después de su creación, y la cookie lleva la misma vigencia. No hay renovación deslizante.

El plazo sale de comparar los dos costos. Que la sesión venza cuesta casi nada: volver a entrar es un clic, y el proveedor externo normalmente no vuelve a preguntar nada. Acotar el plazo, en cambio, sí tiene valor: evita que una credencial quede viva indefinidamente en un dispositivo que nadie usa más. Treinta días es el punto donde la sesión sobrevive a los huecos de uso normal —alguien califica un álbum esta semana y mira las estadísticas la siguiente sin volver a autenticarse— sin quedar abierta para siempre.

**Alternativa descartada:** extender el vencimiento con cada uso. Es más amable para quien entra de vez en cuando, pero implica una escritura en cada petición, o una regla de umbral que decide cuándo vale la pena escribir. A cambio de esa complejidad, lo que se evita es volver a iniciar sesión, que con un proveedor externo es un clic. No se paga.

### D6 - Dos tablas, con la identidad en el par proveedor e identificador y el correo sin unicidad

La tabla de usuarios lleva como clave única el par formado por el proveedor y el identificador que ese proveedor asigna a la persona. El correo, el nombre y la imagen son atributos que se refrescan en cada inicio de sesión, y **el correo no es único**.

La unicidad del correo parecía natural y es un error: la misma persona autenticada por dos proveedores distintos produce dos pares distintos con el mismo correo, y la unicidad rompería el segundo inicio de sesión — justo en la transición de la fase local a la cloud, contra una base que ya tiene datos. La consecuencia de no imponerla hay que asumirla: la misma persona por dos proveedores son dos usuarios. Es tolerable porque la configuración activa un solo proveedor por entorno, así que la situación no se da dentro de un entorno.

La tabla de sesiones lleva el hash del identificador como único, el usuario al que pertenece con eliminación en cascada, y su vencimiento.

**Alternativa descartada:** tratar el correo como la clave de la persona y vincular proveedores a un mismo usuario. Resuelve la duplicación, pero obliga a confiar en que el proveedor verificó el correo antes de entregarlo, y agrega un flujo de vinculación para un problema que este proyecto no tiene.

### D7 - El identificador de sesión se guarda con un hash rápido, no con uno lento

Se genera un valor de suficiente entropía con una fuente aleatoria criptográfica, y se almacena su resumen con una función de hash rápida.

Usar una función lenta de las que se usan para contraseñas sería un error de razonamiento por analogía. Esas funciones existen para encarecer el intento de adivinar un secreto de baja entropía elegido por una persona; acá el secreto lo genera el sistema y es inadivinable, así que no hay nada que encarecer. Lo único que agregaría una función lenta es latencia en cada petición autenticada, que es precisamente el camino más caliente del sistema.

### D8 - Las sesiones vencidas se ignoran al validar y se eliminan cuando conviene

La consulta que valida una sesión filtra por vencimiento, así que una fila vencida nunca autentica. Eliminarla es higiene, no corrección: se borran las sesiones vencidas del usuario cuando ese usuario inicia sesión de nuevo, lo que mantiene la tabla acotada sin trabajo periódico.

**Alternativa descartada:** un proceso que limpie la tabla cada tanto. Requiere trabajo programado, que este proyecto decidió no tener, para resolver algo que no afecta la corrección.

### D9 - El guard del layout y el tratamiento del no autorizado son dos mecanismos con responsabilidades distintas

El layout autenticado consulta la sesión antes de entrar y, si no hay, redirige a la vista de inicio de sesión llevando la ubicación pretendida como destino de retorno. Eso cubre el caso de entrar sin sesión.

El cliente HTTP, en cambio, trata la respuesta no autorizada que puede llegar en cualquier momento: la sesión venció o se cerró desde otro lado mientras la persona usaba la aplicación. Ahí invalida la sesión en caché y manda a iniciar sesión.

Conviene tener los dos y no confundirlos: el primero evita renderizar una vista que no va a poder cargar datos, y el segundo atiende lo que el primero no puede prever. La sesión se lee de una sola consulta compartida, así que ninguno de los dos mantiene su propia copia del estado.

### D10 - La imagen de la persona se muestra desde la dirección que el proveedor entrega

No se copia ni se sirve a través de este sistema: la interfaz usa la dirección tal como llegó. Es lo más simple y no requiere storage, que además todavía no existe en el proyecto. Si alguna vez importara que el proveedor sepa cuándo se muestra un avatar, o que la imagen sobreviva a que el proveedor la mueva, la salida sería copiarla al almacenamiento de objetos, y eso es un cambio contenido en un solo lugar de la interfaz.

## Risks / Trade-offs

**El adapter local permite obtener una sesión como cualquiera** → Mitigado por D2: la selección de proveedor se niega a activarlo cuando el entorno no es de desarrollo, y el servicio no arranca. Sin esa negativa, un despliegue mal configurado sería una suplantación trivial.

**El modo laxo de las cookies deja pasar navegaciones de nivel superior desde otros sitios** → La mitigación es la regla de D4: ninguna operación que cambie estado responde a una lectura. Conviene verificarla en cada change que agregue endpoints, no solo en este.

**La validación del destino de retorno mal hecha convierte el login en un redirector abierto** → No alcanza con exigir que el destino empiece con una barra: una dirección que empieza con dos barras es una dirección hacia otro sitio y pasaría ese control. La validación rechaza también el esquema explícito y la doble barra inicial, y hay una prueba por cada forma de evasión.

**La cookie de estado se pierde si la persona vuelve en otra pestaña o el navegador la descarta** → El retorno se rechaza, que es lo correcto, pero el mensaje tiene que decir que se puede volver a intentar en lugar de parecer un error del sistema.

**Dos usuarios para la misma persona al cambiar de proveedor** → Consecuencia aceptada de D6. No ocurre dentro de un entorno porque solo hay un proveedor activo; el caso a vigilar es apuntar un entorno nuevo a una base que ya tiene usuarios del proveedor anterior.

**El envelope de respuestas y el mapeo de errores se estrenan con pocos endpoints** → Se van a tensionar recién en los changes siguientes, cuando aparezcan validaciones y autorizaciones de verdad. Se define ahora con el alcance mínimo y se espera que gane requirements por delta, no que se reescriba.

## Migration Plan

La migración es aditiva: dos tablas nuevas sobre un esquema que no tiene dominio, así que no hay datos que transformar. El orden de despliegue lo impone la orquestación que ya existe.

El rollback de la migración elimina las dos tablas y con ellas todas las sesiones activas, lo que obliga a volver a iniciar sesión. No hay pérdida real: los usuarios se recrean al volver a entrar, porque su identidad la sostiene el proveedor y no este sistema. Esa propiedad —que la identidad viva afuera— es lo que hace que este esquema sea seguro de revertir, y dejará de serlo en cuanto los usuarios tengan álbumes asociados.

## Open Questions

Ninguna. La que quedó abierta se resolvió comparando los dos costos en juego en lugar de elegir un número convencional.

**Resueltas durante la redacción**

- **El plazo de vencimiento de la sesión.** Se cerró dentro de D5 en treinta días. Lo que la resolvió fue notar que los dos costos son asimétricos: que la sesión venza cuesta un clic, porque el proveedor externo normalmente no vuelve a preguntar nada, mientras que dejarla viva indefinidamente deja una credencial abierta en un dispositivo que nadie usa más. Treinta días es el punto donde la sesión sobrevive a los huecos de uso normal sin quedar abierta para siempre.
