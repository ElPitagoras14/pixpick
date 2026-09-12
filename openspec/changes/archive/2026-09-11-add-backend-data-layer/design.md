## Context

El estado de partida es el que deja `add-local-environment`: un compose con Postgres 18.6 y un edge, un backend que expone su healthcheck bajo el prefijo de la API y que todavía no se conecta a ninguna base, y un `.env.example` que declara los valores del servidor de Postgres pero ninguna variable de conexión, porque hasta ahora nadie la consumía.

El scaffold ya trae `sqlalchemy` y `psycopg` en las dependencias, y el `DB_URL` de la convención del repositorio de referencia usa el dialecto `postgresql+psycopg`, que es psycopg3. No hay que elegir driver: hay que decidir cuánto de SQLAlchemy se usa.

Dos restricciones enmarcan el diseño. La primera es que este change no crea ninguna tabla de dominio, así que todo lo que se decida acá se verifica sobre estructuras mínimas y su valor real se cobra en los changes siguientes; eso obliga a que las decisiones sean verificables por sí mismas y no "se verá cuando haya tablas". La segunda es que las consultas que este proyecto va a necesitar —conteos agregados con filtro, upsert por clave compuesta, anti-join para saber qué le falta calificar a un usuario— son conocidas de antemano, así que se pueden usar como prueba de que la capa de acceso elegida las expresa con naturalidad.

## Goals / Non-Goals

**Goals:**

- Que agregar una tabla en un change posterior sea mecánico: una migración, un modelo de fila, funciones de acceso, y nada más que decidir.
- Que el esquema sea auditable sin ejecutar nada, y que el efecto de cada migración sea visible en la revisión del cambio.
- Que una discrepancia entre lo que el esquema tiene y lo que el código espera falle en la frontera de la capa de datos, no aguas abajo.
- Que las pruebas se ejecuten contra el mismo motor y el mismo esquema que la aplicación, con aislamiento que no cueste tiempo de ejecución.

**Non-Goals:**

- Tablas de dominio, y con ellas cualquier consulta de negocio.
- El envelope de respuestas de la API y el manejo de errores de cara al cliente más allá de lo que el healthcheck necesita.
- Concurrencia, réplicas de lectura, particionado o cualquier consideración de escala. El proyecto no la tiene y diseñar para ella ahora sería adivinar.
- Semillas de datos y entornos de demostración.

## Decisions

### D1 - Las migraciones se declaran en SQL con dbmate

El esquema se escribe en SQL plano, en archivos numerados, con la sección de aplicación y la de rollback en el mismo archivo. La herramienta no conoce el código de la aplicación: lee un directorio y una tabla de control. Eso significa que lo que se revisa en un cambio es exactamente lo que se va a ejecutar contra la base, sin una capa que traduzca.

**Alternativa descartada:** Alembic. Su ventaja decisiva es autogenerar migraciones comparando modelos declarativos contra el esquema vivo, y sin ORM no hay modelos de los que derivar nada. Sin esa ventaja queda un ejecutor de migraciones escrito en Python, con más piezas y más indirección que uno que ejecuta SQL, y con la posibilidad de que la migración que se revisa no sea idéntica al SQL que corre.

### D2 - SQLAlchemy queda como controlador, pool y binding de parámetros, no como ORM

No se quita la dependencia: se usa su motor asincrónico sobre el dialecto de psycopg3 para obtener el pool y la conexión, y su función de texto para ligar parámetros con nombre. Lo que no se usa es nada por encima de eso — ni modelos declarativos, ni sesión, ni lenguaje de expresiones.

Ligar parámetros a través de esa capa es lo que hace cumplible el requirement de que ningún valor se interpole en el texto de la consulta: la consulta se escribe con placeholders `:nombre` y los valores viajan aparte.

**Alternativa descartada:** usar psycopg3 directamente con su propio pool. Quita una capa, que es tentador dado que del ORM no usamos nada. Se descarta por dos razones concretas: habría que administrar el ciclo de vida del pool a mano, y el estilo de parámetros cambia a `%(nombre)s`, que es más ruidoso dentro del SQL y menos habitual de leer. El precedente del repositorio de referencia además ya está probado con esta combinación.

### D3 - La capa de acceso son cinco funciones, y todas reciben la conexión

`src/database/` concentra la infraestructura: el motor y su ciclo de vida, la configuración de conexión, y cinco funciones que ejecutan SQL — una para escribir, una para escribir en lote, y tres para leer una fila, todas las filas o un único valor. Todas reciben la conexión como primer parámetro. No hay una sexta que abstraiga un caso particular: si una consulta no encaja en esas cinco formas, la señal es que la consulta debería replantearse, no que falta un helper.

**Alternativa descartada:** una clase base de repositorio con métodos genéricos que administre su propia conexión. Es la forma más común y la que más código ahorra al escribir, pero devuelve la conexión al terreno del estado implícito: dejaría de poder saberse, mirando el punto de llamada, si una operación participa de una transacción, que es justamente lo que el spec exige que sea visible.

### D4 - Las funciones de acceso devuelven modelos, y el mapeo vive en el repository

Cada función de acceso valida la fila que obtuvo contra un modelo declarado en su propio package y devuelve ese modelo. El resto de la aplicación nunca ve una fila ni una estructura de claves arbitrarias.

Estos modelos son internos: describen la forma de lo que la consulta devuelve, en la misma nomenclatura que el esquema. Los modelos de respuesta de la API, con su nomenclatura de cara al cliente, son otra familia y llegan con el primer endpoint real en el change siguiente. Mezclarlas haría que un cambio de presentación arrastre un cambio en la capa de datos.

**Alternativa descartada:** devolver diccionarios y mapear en el servicio, que es la convención del repositorio de referencia. Se aparta a propósito: con diccionarios, una consulta que deja de devolver una columna se propaga como una clave ausente y estalla en el consumidor, lejos de la causa. Validar en la frontera hace que el fallo ocurra donde está el error. El costo es unas pocas líneas de modelo por consulta, y se acepta.

### D5 - El campo de última modificación lo mantiene un trigger de la base

La migración inicial crea una función que actualiza ese campo y cada tabla que lo tenga declara un trigger que la invoca antes de cada modificación. Las sentencias de actualización no mencionan el campo.

**Alternativa descartada:** asignarlo explícitamente en cada sentencia de actualización, como hace el repositorio de referencia. Funciona mientras nadie lo olvide, y el olvido no produce un error sino un dato desactualizado en silencio — el peor tipo de falla, porque nada la señala. Con varias sentencias de actualización por tabla en los changes que vienen, el trigger convierte una regla de disciplina en una garantía.

### D6 - Un servicio de un solo uso aplica las migraciones antes de que arranque el backend

El compose declara un servicio que ejecuta las migraciones y termina. Espera a que Postgres esté disponible mediante su healthcheck, y el backend espera a que ese servicio haya terminado satisfactoriamente. Así la garantía de que el esquema esté al día antes de atender la sostiene la orquestación, y no hay lógica de migración en el arranque de la aplicación.

Esto incorpora el healthcheck de Postgres y el arranque ordenado que el diseño anterior dejó fuera por no tener todavía un servicio que dependiera de la base.

**Alternativa descartada:** que el backend aplique las migraciones al arrancar. Ahorra un servicio, pero acopla dos responsabilidades con ciclos de vida distintos y se rompe en cuanto haya más de una réplica: dos procesos intentarían migrar a la vez. Además convierte un fallo de migración en un fallo de arranque de la aplicación, que es más difícil de leer que el fallo de un servicio cuya única tarea era migrar.

### D7 - La aplicación se configura con una sola variable de conexión; la de las migraciones la compone la orquestación

La aplicación lee un único valor con todo lo necesario para conectarse. La herramienta de migraciones necesita ese mismo destino expresado en otra forma, así que el compose se la arma a partir de los valores del servidor de Postgres que ya están declarados. Nadie escribe dos veces la misma cadena a mano.

Queda un punto de coherencia inevitable: el valor de la aplicación y los valores del servidor se declaran por separado en el archivo de entorno, porque la imagen de Postgres necesita los suyos. La mitigación es que la verificación de conectividad del arranque convierte cualquier desacuerdo en un fallo inmediato y explícito, en lugar de un error sutil más adelante.

**Alternativa descartada:** que la aplicación arme su cadena a partir de los componentes por separado. Elimina la duplicación, pero contradice el requirement de una sola variable y traslada a la aplicación la tarea de construir y escapar una cadena de conexión, que es exactamente el tipo de código que no conviene escribir a mano.

### D8 - Los identificadores los genera la aplicación, no la base

Las claves primarias se generan del lado de la aplicación antes de insertar. La base no declara valores por defecto que las produzcan.

La razón es concreta y viene del change 5: la clave con la que una foto se guarda en el almacenamiento de objetos se construye con el identificador de la foto, y hay que conocerlo **antes** de firmar la URL de subida, o sea antes de que exista la fila. Si el identificador lo generara la base, habría que insertar primero para saberlo, y el flujo de subida quedaría atado al orden de las escrituras.

Como beneficio lateral, esta decisión evita depender de una extensión de la base para generar identificadores, y deja abierto sin costo qué variante de identificador se use cuando se creen las primeras tablas.

### D9 - Cada prueba corre dentro de una transacción que se hace rollback al terminar

La preparación de cada prueba abre una conexión, inicia una transacción y la entrega. Al terminar, hace rollback. Nada queda escrito, no hay que truncar tablas entre pruebas, y el aislamiento no cuesta tiempo de ejecución.

Esto es posible precisamente por D3: como toda función de acceso recibe la conexión, la prueba controla el límite de la unidad de trabajo y puede envolver el código bajo prueba en una transacción que no confirma. Es el caso donde la regla de la conexión explícita se paga sola.

**Alternativa descartada:** limpiar truncando las tablas entre pruebas. Es más lento a medida que crecen las tablas, obliga a mantener la lista de qué truncar, y no protege si dos pruebas corrieran en paralelo. Una base por prueba aisla mejor todavía, pero el costo de crearla y migrarla en cada caso es desproporcionado.

### D10 - Las pruebas usan una base distinta en la misma instancia de Postgres

La suite no levanta su propio contenedor: usa el Postgres que el entorno ya provee, sobre una base de datos separada que ella misma crea si no existe y migra con las migraciones del proyecto. Un solo comando alcanza y no hay nada que preparar a mano.

**Alternativa descartada:** un contenedor efímero por corrida. Aísla más, y evita que una corrida pise el estado de desarrollo. Se descarta porque el aislamiento que hace falta ya lo da D9, y a cambio agregaría una dependencia nueva y varios segundos de arranque a cada ejecución de la suite.

### D11 - Cinco conexiones permanentes y quince de overflow, con el techo de Postgres como invariante

La aplicación declara cinco conexiones permanentes y quince alcanzables por encima, o sea un techo de veinte por proceso. El razonamiento no parte del tráfico esperado, que hoy no se puede estimar, sino de dos hechos que sí se conocen: las transacciones de este proyecto son cortas porque ningún bloque transaccional espera I/O externo, y el techo por defecto de Postgres son cien conexiones.

De ahí sale el invariante que importa mantener: la cantidad de procesos del backend multiplicada por veinte tiene que quedar holgadamente por debajo de cien, porque sobre la misma instancia también corren la suite de pruebas y el cliente de base de datos del desarrollador. Con un proceso hay margen de sobra; con cuatro se llega a ochenta y el margen desaparece. Mientras el backend corra con un solo proceso, veinte es cómodo y no hay nada que ajustar.

La suite de pruebas declara su propio pool, mucho más chico, porque ejecuta una prueba a la vez y no tiene por qué reservar veinte espacios que no va a usar.

Los tres valores se declaran en el código y no como variables de entorno: no son configuración por entorno, y exponerlos agregaría variables sin un consumidor que las diferencie.

**Alternativa descartada:** dejar los valores por defecto de la capa de acceso. El spec lo prohíbe explícitamente, y la razón es concreta — al no estar declarados, cambiar de capa de acceso o subir su versión puede alterar la capacidad del servicio sin que nadie lo haya decidido ni lo note hasta que se agoten las conexiones.

Vale anticipar la respuesta al caso en que veinte no alcancen, porque el reflejo natural es equivocado: si la concurrencia creciera, subir el pool no ayuda, porque el cuello pasa a ser Postgres. La salida sería un pooler delante de la base o más procesos con su techo recalculado, no un número más grande acá.

## Risks / Trade-offs

**El valor de conexión de la aplicación y los valores del servidor de Postgres pueden divergir** → La verificación de conectividad del arranque falla de inmediato y con un error explícito, así que la divergencia se manifiesta al levantar el entorno y no como un fallo intermitente. Es el compromiso aceptado en D7.

**Una tabla nueva puede quedarse sin el trigger de última modificación** → Se mitiga con una prueba que recorra las tablas que declaran ese campo y verifique que cada una tiene su trigger. Convierte la disciplina de D5 en una comprobación automática, y es baratísima de escribir.

**El aislamiento por rollback no ejercita el momento de confirmar** → Un constraint diferido al final de la transacción no se dispararía en una prueba que nunca confirma. Se mitiga no usando constraints diferidos, y si alguna vez hiciera falta una, la prueba correspondiente confirma y limpia explícitamente en lugar de apoyarse en el rollback.

**Sin autogeneración de migraciones, el esquema y los modelos de fila pueden divergir** → Es el costo estructural de D1 y no tiene solución dentro de la herramienta. La mitigación es que los modelos se validan contra filas reales en las pruebas: una columna renombrada en una migración sin actualizar el modelo hace fallar la suite. Es la razón principal por la que las pruebas corren contra una base real y no contra sustitutos.

**La versión de la herramienta de migraciones se referencia en más de un lugar** → El archivo que la fija lleva un comentario que enumera los lugares donde aparece, de modo que subirla sea una operación completa y no parcial. Una referencia olvidada haría que la suite y el entorno migraran con versiones distintas.

**Un desarrollador puede correr la suite apuntando sin querer a la base de desarrollo** → El nombre de la base de pruebas se deriva del entorno de pruebas y no del valor de desarrollo, y la preparación de la suite falla si el destino no es la base de pruebas esperada.

## Migration Plan

La primera migración se aplica sobre una base vacía, así que no hay datos que transformar ni compatibilidad hacia atrás que preservar. El orden de despliegue es el que D6 impone por construcción: Postgres disponible, migraciones aplicadas, backend atendiendo.

El rollback tiene dos niveles. Revertir el commit devuelve el código al estado anterior, en el que el backend no se conectaba a la base, y eso alcanza porque ninguna funcionalidad depende todavía del esquema. Si además hiciera falta deshacer el esquema, el rollback declarado en la migración inicial lo desarma, y en un entorno local eliminar el volumen de datos es equivalente y más rápido.

## Open Questions

Ninguna. La única que quedó abierta al redactar se resolvió con una derivación, no con una preferencia.

**Resueltas durante la redacción**

- **Los valores concretos del pool de conexiones.** Parecía depender de tráfico que hoy no se puede estimar, pero el número que importa no sale del tráfico: sale del techo por defecto de Postgres, cien conexiones, repartido entre el backend, la suite de pruebas y el cliente del desarrollador. De ahí salió D11 con cinco permanentes y quince de overflow, y con el invariante que realmente hay que cuidar —procesos por veinte, holgadamente bajo cien—, que es lo que se rompe al agregar réplicas y no al recibir más peticiones.
