## Context

El estado de partida son los dos puertos de medios con sus adapters locales y una suite de contrato ejecutable, más seis changes de dominio construidos encima sin saber qué proveedor hay detrás. Este change agrega el segundo adapter de cada puerto y es el último del plan.

Lo que más condiciona el diseño es una asimetría entre los dos puertos que recién ahora se vuelve visible. El de almacenamiento **tiene estado**: los objetos están en algún lado y cambiar de proveedor significa moverlos. El de transformación **no tiene ninguno**: lee del almacenamiento y produce al pedido, así que cambiarlo no deja nada atrás. Por eso hay un único punto de migración en todo el proyecto, y por eso los dos adapters de este change tienen dificultades muy distintas.

El segundo condicionante es que el adapter de almacenamiento cloud habla el mismo protocolo que el local, mientras que el de transformación es genuinamente otro: otra manera de expresar una transformación y otro esquema de firma. Uno es configuración; el otro es trabajo.

## Goals / Non-Goals

**Goals:**

- Que el adapter de almacenamiento pase la suite de contrato sin que la suite se toque.
- Que el conjunto de variantes se defina una sola vez y valga para los dos proveedores.
- Que alternar entre proveedores durante el desarrollo no destruya nada ni obligue a rehacer datos de prueba.
- Que cambiar de proveedor en un entorno con datos sea una operación con una comprobación previa, no un acto de fe.

**Non-Goals:**

- Copiar objetos desde la aplicación, servir desde dos proveedores a la vez, y todo lo que el proposal dejó fuera.
- Cualquier cambio en el dominio, los endpoints, la interfaz o el esquema.
- Aprovechar capacidades del proveedor cloud que el puerto no expone.

## Decisions

### D1 - El catálogo de variantes ya está unificado, y el adapter cloud solo lo traduce

El catálogo —nombre, medidas, calidad, formato y la regla de no ampliar— se declara una sola vez en el proyecto desde que se construyeron los puertos locales. El adapter cloud no lo modifica ni lo duplica: lo lee y lo traduce al vocabulario de su proveedor, igual que el local lo traduce al suyo.

Que el catálogo estuviera en el proyecto y no en la configuración del transformador es lo que vuelve a este change pequeño. Con las variantes declaradas en el transformador local, agregar un proveedor cloud habría obligado a duplicarlas en el código del adapter nuevo —porque ese proveedor no tiene un archivo de configuración equivalente— y cambiar una medida habría dejado de ser un cambio de configuración en la mitad de los casos.

También hereda de allá que la invalidación sea automática: como la definición viaja en la dirección, un cambio en el catálogo produce direcciones nuevas con los dos proveedores, sin ningún mecanismo aparte.

### D2 - El adapter de almacenamiento cloud es el mismo cliente con otra configuración

El proveedor cloud habla el protocolo del local, así que el adapter comparte el cliente y difiere en la dirección, las credenciales y poco más. No es un atajo: es el resultado de haber elegido un proveedor que habla ese protocolo, y fue una de las razones para elegirlo.

La afirmación de que "es casi lo mismo" no se acepta por argumento sino por evidencia: la suite de contrato corre contra él sin modificaciones. Si hubiera que ajustar la suite para que pase, lo que falló es el contrato — o el proveedor no sirve.

### D3 - La suite de contrato corre contra el doble y contra el proveedor que esté activo

Correr el contrato contra un proveedor cloud requiere red y credenciales, y `backend-testing` exige que la suite completa pase sin acceso a internet. Las dos cosas se concilian así: el contrato corre siempre contra el doble, y contra el proveedor real que `STORAGE_PROVIDER` nombre en ese momento -- nunca contra los dos reales a la vez.

**Corrección durante la implementación.** La primera versión de esta decisión probaba siempre contra `local` y, además, contra `r2` cuando hubiera un segundo juego de credenciales dedicado a la prueba (`R2_TEST_*`), para tener los dos proveedores reales cubiertos en la misma corrida. Se descartó porque duplicaba `STORAGE_ACCESS_KEY_ID`/`STORAGE_SECRET_ACCESS_KEY` bajo otro nombre sin necesidad real: el puerto ya tiene un único conjunto de credenciales activo por diseño (un proveedor activo por entorno), y sostener un segundo juego paralelo solo para las pruebas iba contra esa misma idea. Probar el otro proveedor pasó a ser lo mismo que usarlo: cambiar `STORAGE_*` y correr la suite de nuevo, sin infraestructura de prueba aparte.

**Segunda corrección, sobre la primera.** "Cambiar `STORAGE_*` y correr de nuevo" seguía asumiendo un único juego de credenciales compartido entre los dos proveedores -- lo que en su momento se llamó "un proveedor activo por diseño" resultó ser, mirado de nuevo, la misma clase de problema que `identity` y `images` ya habían resuelto cada una por su cuenta: un campo por proveedor, opcional, validado por la factory solo para el que está activo. Se corrigió así: `MINIO_*` y `R2_*` son grupos de variables enteramente separados (D9), cada uno con sus propias credenciales, bucket y direcciones. Ninguno de los dos es obligatorio en el tipo -- la factory de almacenamiento gana el mismo `MissingCredentialsError` que las otras dos ya tenían, evaluado solo para el proveedor seleccionado.

Esto deja la omisión visible de la primera corrección exactamente donde tenía que estar: no hay "activo sin credenciales" que saltear en la suite porque el proveedor activo por omisión (`local`) tiene su propio grupo completo desde `.env.example`; la garantía de `backend-testing` -- la suite completa pasa sin acceso a internet -- se sostiene con esos valores por omisión. Y de regalo, la comprobación de migración (D6) deja de depender de pisar `STORAGE_*` con los valores del destino antes de correrla: como cada proveedor tiene su propio grupo, nombrar uno explícitamente nunca depende de que sea también el activo.

### D4 - La base de datos acompaña al conjunto de proveedores, no al modo de ejecución

La configuración del proyecto tiene **dos ejes independientes** y conviene nombrarlos antes de nada, porque hasta acá se los llamó a los dos "perfil". Uno es el **modo de ejecución** —todo en contenedores, o backend e interfaz corriendo nativos— que determina desde dónde se alcanza cada servicio. El otro es el **conjunto de proveedores** activos —los locales o los cloud— que determina contra qué se trabaja.

La base de datos acompaña al segundo eje: hay una base por conjunto de proveedores, y el modo de ejecución solo cambia el host con el que se la alcanza. Cambiar de modo de ejecución muestra los mismos datos; cambiar de conjunto de proveedores muestra el conjunto que le corresponde.

Que la base siguiera al modo de ejecución sería un error: correr el backend nativo daría una base distinta que correrlo en contenedor, y se perderían los datos cada vez que se cambia la forma de arrancar, que es algo que se hace todo el tiempo y no tiene nada que ver con dónde están las fotos.

Con esto cada conjunto de proveedores tiene sus datos completos —álbumes, fotos y calificaciones junto al bucket que les corresponde—, alternar durante el desarrollo no destruye nada, y volver encuentra todo como se dejó.

**Alternativa descartada:** registrar en cada foto con qué proveedor se subió y filtrar por el activo. Resolvería el mismo caso y cuesta más: el filtro tendría que aplicarse en cada consulta que lea fotos —el olvido que la vista de fotos disponibles se creó para eliminar— o fijarse como un valor de sesión que el pool debe establecer en cada conexión, con su propio modo de falla. Y sobre todo haría que el significado de una fila dependa de cómo se arrancó la aplicación, agregando una segunda causa posible a "está en la base pero no la veo".

Esta decisión vive en este change y no en el que estableció los perfiles, porque hasta acá no había un segundo proveedor de almacenamiento: dos bases allá habrían sido una distinción sin motivo.

### D5 - El edge conserva su ruta de imágenes aunque en modo cloud no se use

En modo cloud las direcciones de las variantes apuntan al proveedor, así que la ruta de imágenes del edge simplemente no recibe tráfico. Se la conserva tal cual, sin condicionales.

Quitarla según el proveedor activo obligaría a que la configuración del edge tuviera ramas, y una configuración con ramas es más difícil de leer que una ruta que no se usa. El costo de dejarla es nulo; el de condicionarla, permanente.

### D6 - La comprobación previa a una migración reutiliza la reconciliación existente

El comando que ya compara las filas contra el almacenamiento acepta contra qué proveedor comparar, con el activo por omisión. Apuntado al proveedor de destino antes de cambiar la variable, enumera exactamente qué objetos faltan.

Es el tercer uso de una pieza que se construyó para otra cosa, y no requiere código nuevo más que el parámetro: el puerto ya ofrece consultar un objeto, que es todo lo que la comprobación necesita.

### D7 - Las dos direcciones del almacenamiento coinciden en cloud, y eso no es un caso especial

El puerto distingue la dirección por la que el navegador alcanza el almacenamiento de la que usa el servidor. En cloud las dos son la misma, porque el proveedor es público desde los dos lados.

No hay una rama para eso: son dos valores de configuración que en un perfil difieren y en otro coinciden. Es exactamente lo que la decisión original preveía, y vale anotarlo porque la tentación al implementarlo es "simplificar" reduciéndolos a uno solo, lo que rompería el modo local.

### D8 - Firmar las direcciones del transformador cloud no requiere ninguna dependencia

El esquema de firma del proveedor cloud es un cálculo criptográfico estándar que la biblioteca del lenguaje ya provee. Sumado a que el adapter de almacenamiento reutiliza el cliente existente, el change no agrega ninguna dependencia — igual que el de identidad cloud.

### D9 - La concesión de subida firma un PUT, no un POST, y el límite de tamaño se verifica después de subir

Implementar el adapter cloud reveló que D2 estaba escrito contra una operación que el proveedor elegido no ofrece: Cloudflare R2 no implementa `POST` presignado con política (el mecanismo que permite condicionar un rango de tamaño en la firma), solo `PUT` presignado — verificado contra su propia documentación y confirmado por la comunidad. Esto no es una particularidad de R2: ningún esquema de firma por query string (el que usa un PUT presignado, en cualquier proveedor S3, incluido AWS mismo) puede expresar una condición de rango; esa capacidad es exclusiva del POST con política, que es justamente la operación que falta.

La consecuencia alcanza al puerto, no solo al adapter: `UploadGrant` traía `fields` pensado para un formulario multipart, y la prueba de contrato `test_the_size_limit_is_enforced_by_the_storage_itself` exige que el almacenamiento rechace un archivo por encima de un tope al recibirlo — una garantía que ningún PUT presignado puede sostener. Sostenerla habría exigido descartar R2 (la razón de producto para elegirlo, sin costo de tráfico de salida, sigue siendo válida) o cambiar a un proveedor que sí ofrezca POST con política — se evaluaron Wasabi (lo soporta, pero sin nivel gratuito permanente) y Backblaze B2 (tampoco lo soporta, mismo problema que R2). Se optó por conservar R2 y corregir la garantía.

La concesión pasa a describir un único `PUT`, con los encabezados que hay que enviar (el `Content-Type` concedido, firmado en la URL). El límite de tamaño deja de imponerlo el almacenamiento al recibir y pasa a verificarlo la aplicación al confirmar, comparando el tamaño real del objeto contra el declarado — mecanismo que `photo-upload` ya exige y que `confirm_batch` ya implementa (rechaza y borra el objeto si no coincide). El adapter local de MinIO migra al mismo mecanismo por la misma razón que motivó D2: si los dos proveedores no comparten la operación, el adapter cloud no es "el mismo cliente con otra configuración", es otra cosa — con los dos en PUT, la afirmación de D2 vuelve a ser literalmente cierta, en vez de asumida.

**Alternativas descartadas:** fijar el tamaño exacto en la firma del PUT (pinning `Content-Length`) en lugar de un rango — se descarta porque el archivo real casi nunca mide exactamente el tope declarado, así que habría rechazado subidas legítimas de cualquier tamaño menor al máximo. Un servicio intermediario (p. ej. un Worker) que reciba el POST del navegador y lo traduzca a un PUT contra R2 — se descarta porque reintroduce un intermediario que retiene bytes de imagen, exactamente lo que los dos puertos existen para evitar (D2 de `add-media-ports-and-local-adapters`).

**Nota sobre D8:** el comando de reconciliación extendido en D6 usa `typer` para su CLI en lugar de la biblioteca estándar (`argparse`), por pedido explícito del usuario. Es la única dependencia que este change agrega -- ya estaba resuelta transitivamente (la trae `fastapi[standard]`), así que pasa a declararse como dependencia directa sin cambiar el lockfile de forma sustancial.

## Risks / Trade-offs

**Probar contra el proveedor cloud consume red y puede consumir cuota** → Solo ocurre cuando alguien configura `STORAGE_PROVIDER`/`IMAGE_PROVIDER` hacia el cloud y corre la suite en ese estado (D3); el desarrollo cotidiano, con los proveedores locales activos, no toca la red. El riesgo restante es que nadie haga ese cambio nunca y el adapter cloud quede sin verificar contra el proveedor real; por eso la verificación manual del ciclo completo queda como tarea explícita.

**La declaración de orígenes admitidos del proveedor cloud tiene otra interfaz y el mismo modo de falla** → Una subida rechazada por origen falla en el navegador con poca información, igual que en local. Se verifica subiendo desde el navegador contra el proveedor cloud, no solo con pruebas del backend.

**Un proveedor cloud podría no soportar alguna operación del contrato** → Ocurrió: R2 no soporta POST presignado. A diferencia de una variante de imagen (donde ablandar el contrato no tiene sentido, D1), acá la operación en falta no es exclusiva de R2 -- ningún PUT presignado, en ningún proveedor, puede expresar la misma condición -- así que el hallazgo no señala que R2 no sirva, señala que el contrato asumió una capacidad de un solo mecanismo (POST) sin haber probado el proveedor elegido contra él. Se resolvió en D9 corrigiendo esa garantía en lugar de descartar R2.

**La migración verificada depende de que alguien la ejecute** → El spec la exige como capacidad disponible, no como hábito. La mitigación práctica es que el procedimiento documentado tenga el orden correcto —comprobar antes de cambiar— y que el README lo presente como los pasos del cambio y no como una recomendación.

## Migration Plan

Este change no toca el esquema. Poner un entorno en modo cloud es crear el espacio de almacenamiento con sus credenciales y sus orígenes admitidos, apuntar el transformador a ese almacenamiento, y cambiar las dos variables que eligen los proveedores.

Si el entorno ya tenía datos, antes de cambiar esas variables hay que copiar los objetos y ejecutar la comprobación de D6 hasta que no falte ninguno. La base no se toca en ningún caso, porque las claves de los objetos no dependen del proveedor.

El rollback es volver las variables a su valor anterior, y funciona mientras el almacenamiento anterior siga existiendo con su contenido. Por eso conviene no eliminar el origen viejo hasta haber comprobado el nuevo en uso real, y no solo en la verificación previa.

## Open Questions

Ninguna. Las cuatro que aparecieron al escribir el diseño se resolvieron, y una de ellas produjo una corrección en el change de los puertos locales, ya aplicada. Una quinta apareció durante la implementación misma y se resolvió en D9: R2 no soporta POST presignado, así que la concesión pasa a firmar un PUT y el límite de tamaño se verifica al confirmar en lugar de al firmar.

**Resueltas durante la redacción**

- **Cómo evitar que el adapter cloud tenga las medidas escritas en el código.** Se resolvió corrigiendo el change de los puertos locales para que el catálogo naciera unificado en el proyecto, en lugar de vivir en la configuración del transformador. Así este change no tiene que unificar nada: el adapter cloud traduce el catálogo que ya existe. La corrección además eliminó allá un contrato entre dos lugares y el mecanismo de invalidación que hacía falta para sostenerlo.
- **Cómo conciliar correr el contrato contra un proveedor cloud con la exigencia de que la suite no dependa de internet.** Se cerró en D3: se ejecuta solo con credenciales presentes y se omite de forma visible sin ellas, para que nadie confunda "no se probó" con "pasó".
- **Qué hacer con los álbumes cuyas fotos quedan en el otro almacenamiento al alternar proveedores en desarrollo.** Surgió de una pregunta del usuario y se cerró en D4, después de descartar dos respuestas peores: resetear la base, que destruye datos de prueba sin necesidad, y filtrar por proveedor, que reintroduce una condición por consulta y hace depender el significado de una fila de cómo se arrancó la aplicación.
- **Si el edge debía dejar de exponer su ruta de imágenes en modo cloud.** Se cerró en D5 por el mismo criterio con que se evitan condicionales en la configuración del entorno: una ruta que no recibe tráfico cuesta menos que una configuración con ramas.
