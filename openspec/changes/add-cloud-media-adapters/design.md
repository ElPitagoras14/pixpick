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

### D3 - La suite de contrato corre contra el proveedor cloud solo si hay credenciales, y se omite sin ellas

Correr el contrato contra un proveedor cloud requiere red y credenciales, y `backend-testing` exige que la suite completa pase sin acceso a internet. Las dos cosas se concilian así: el contrato corre siempre contra el doble y contra el proveedor local, y contra el cloud únicamente cuando hay credenciales configuradas; sin ellas esa ejecución se omite de forma visible.

Omitir no es lo mismo que no tener: la omisión aparece en la salida de la suite, de modo que nadie confunda "no se probó" con "pasó". Y la garantía de que la suite funciona sin internet se mantiene intacta, que era la razón por la que se escribió ese requirement.

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

## Risks / Trade-offs

**Probar contra el proveedor cloud consume red y puede consumir cuota** → Mitigado por D3, que lo vuelve opcional y visible. El riesgo restante es que nadie ejecute nunca esa parte y el adapter cloud quede sin verificar contra el proveedor real; por eso la verificación manual del ciclo completo queda como tarea explícita.

**La declaración de orígenes admitidos del proveedor cloud tiene otra interfaz y el mismo modo de falla** → Una subida rechazada por origen falla en el navegador con poca información, igual que en local. Se verifica subiendo desde el navegador contra el proveedor cloud, no solo con pruebas del backend.

**Un proveedor cloud podría no soportar alguna operación del contrato** → Si ocurre, el spec ya dice qué hacer: no se considera utilizable. Lo que no corresponde es ablandar el contrato para que entre, porque el contrato es lo único que sostiene que los adapters sean intercambiables.

**La migración verificada depende de que alguien la ejecute** → El spec la exige como capacidad disponible, no como hábito. La mitigación práctica es que el procedimiento documentado tenga el orden correcto —comprobar antes de cambiar— y que el README lo presente como los pasos del cambio y no como una recomendación.

## Migration Plan

Este change no toca el esquema. Poner un entorno en modo cloud es crear el espacio de almacenamiento con sus credenciales y sus orígenes admitidos, apuntar el transformador a ese almacenamiento, y cambiar las dos variables que eligen los proveedores.

Si el entorno ya tenía datos, antes de cambiar esas variables hay que copiar los objetos y ejecutar la comprobación de D6 hasta que no falte ninguno. La base no se toca en ningún caso, porque las claves de los objetos no dependen del proveedor.

El rollback es volver las variables a su valor anterior, y funciona mientras el almacenamiento anterior siga existiendo con su contenido. Por eso conviene no eliminar el origen viejo hasta haber comprobado el nuevo en uso real, y no solo en la verificación previa.

## Open Questions

Ninguna. Las cuatro que aparecieron al escribir el diseño se resolvieron, y una de ellas produjo una corrección en el change de los puertos locales, ya aplicada.

**Resueltas durante la redacción**

- **Cómo evitar que el adapter cloud tenga las medidas escritas en el código.** Se resolvió corrigiendo el change de los puertos locales para que el catálogo naciera unificado en el proyecto, en lugar de vivir en la configuración del transformador. Así este change no tiene que unificar nada: el adapter cloud traduce el catálogo que ya existe. La corrección además eliminó allá un contrato entre dos lugares y el mecanismo de invalidación que hacía falta para sostenerlo.
- **Cómo conciliar correr el contrato contra un proveedor cloud con la exigencia de que la suite no dependa de internet.** Se cerró en D3: se ejecuta solo con credenciales presentes y se omite de forma visible sin ellas, para que nadie confunda "no se probó" con "pasó".
- **Qué hacer con los álbumes cuyas fotos quedan en el otro almacenamiento al alternar proveedores en desarrollo.** Surgió de una pregunta del usuario y se cerró en D4, después de descartar dos respuestas peores: resetear la base, que destruye datos de prueba sin necesidad, y filtrar por proveedor, que reintroduce una condición por consulta y hace depender el significado de una fila de cómo se arrancó la aplicación.
- **Si el edge debía dejar de exponer su ruta de imágenes en modo cloud.** Se cerró en D5 por el mismo criterio con que se evitan condicionales en la configuración del entorno: una ruta que no recibe tráfico cuesta menos que una configuración con ramas.
