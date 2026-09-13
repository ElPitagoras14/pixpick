## Why

Es el segundo momento de la verdad del proyecto, y la vara es más alta que en el anterior: no hay un puerto sino dos, y existe una suite de contrato ejecutable que se escribió precisamente para que este change fuera seguro. La medida es concreta: **el adapter de almacenamiento cloud tiene que pasar esa suite sin que la suite se modifique**. Si hubiera que ajustarla para que pase, lo que falló es el contrato y no el adapter.

Del lado del producto, el modo cloud no es solo lo mismo en otro lugar. El almacenamiento cloud elegido no cobra por el tráfico de salida, y el transformador cloud es además una red de distribución, así que quien mira fotos desde un teléfono lejos del servidor las recibe desde un punto cercano. El modo local sigue siendo el de desarrollo; el cloud existe para cuando las fotos las miran otras personas.

## What Changes

- **Un adapter de almacenamiento cloud** construido sobre el mismo protocolo y el mismo cliente que ya usa el local, porque el proveedor elegido habla ese protocolo.
- **Un adapter de transformación cloud**, que sí es genuinamente distinto: tiene su propio esquema de firma y su propia manera de expresar una transformación.
- **El adapter cloud traduce el catálogo de variantes que ya existe en el proyecto**, sin duplicarlo ni modificarlo. Que el catálogo estuviera en el proyecto y no en la configuración del transformador local es lo que hace pequeño a este change: de otro modo, un proveedor sin archivo de configuración equivalente habría obligado a escribir las medidas en el código del adapter nuevo.
- **La suite de contrato del almacenamiento corre también contra el proveedor cloud**, sin modificarse.
- **La declaración de orígenes admitidos** se configura también en el almacenamiento cloud, con la interfaz que ese proveedor ofrezca.
- **Credenciales y direcciones** de los proveedores cloud entran en la configuración, junto al resto de los valores que cambian al alternar de conjunto de proveedores.
- **Un procedimiento de cambio de proveedor de almacenamiento, documentado y verificable**, para un entorno que ya tiene datos reales. Es el único punto del sistema con estado que mover: copiar los objetos al proveedor nuevo, **comprobar que no falta ninguno** y recién entonces cambiar la variable que elige el proveedor. La base no se toca, porque las claves de los objetos no dependen del proveedor. La comprobación no requiere código nuevo — el puerto ya ofrece consultar un objeto, y el comando de reconciliación existente compara las filas contra el almacenamiento; apuntado al proveedor nuevo antes de cambiar, dice exactamente qué falta.
- **Hay una base de datos por conjunto de proveedores.** Alternar entre proveedores durante el desarrollo dejaría, con una base compartida, álbumes cuyas fotos viven en el otro almacenamiento. La solución no es esconderlas ni empezar de cero: es que el nombre de la base sea uno más de los valores que cambian junto con los proveedores, como ya lo son la dirección del almacenamiento y sus credenciales. El modo de ejecución —contenedores o nativo— es un eje distinto y solo cambia el host con el que se alcanza esa base, nunca cuál es. Así cada proveedor tiene su conjunto completo y coherente —álbumes, fotos y calificaciones junto al bucket que les corresponde—, alternar no destruye nada, y volver al conjunto anterior encuentra todo como se dejó. No requiere ninguna columna, ningún filtro ni tocar la vista de fotos disponibles: es un valor de configuración. El patrón ya existe en el proyecto, porque la suite de pruebas usa su propia base desde que se estableció la capa de datos.
- **Documentación de la puesta en marcha**: qué crear en cada proveedor, qué credenciales emitir y qué orígenes declarar.

### Fuera de alcance

- **Copiar los objetos de un proveedor a otro desde la aplicación.** Mover objetos es una operación puntual que se hace con las herramientas del proveedor y no pertenece al código de un producto que, el resto del tiempo, no mueve nada. Lo que sí entra en el alcance es el procedimiento y su comprobación, para que cambiar de proveedor sin copiar no pueda pasar inadvertido.
- **Servir fotos desde dos proveedores a la vez.** Sería la otra forma de evitar el problema —que cada foto recordara dónde vive— y no funciona con este diseño: obligaría a construir varios adapters de almacenamiento simultáneos, contra la regla de un proveedor activo por entorno, y sobre todo exigiría que el transformador leyera de varios orígenes, cuando se configura apuntando a uno. Terminaría en pares de proveedores acoplados, que es justamente lo que los dos puertos independientes evitan. El esquema de claves resuelve el mismo problema sin nada de eso.
- Elegir proveedor por álbum, por persona o por petición. Sigue habiendo uno activo por entorno.
- **Registrar en cada foto con qué proveedor se subió, para ocultar las que no están en el activo.** Resolvería el caso de una base de desarrollo que sobrevive a un cambio de proveedor, y se descarta por tres motivos.

  Primero, es una necesidad de desarrollo y no de producto: en producción se copian los objetos antes de cambiar, y entonces ningún álbum queda huérfano. Y el caso de desarrollo lo cubre que cada conjunto de proveedores tenga su propia base, sin agregar nada al esquema.

  Segundo, filtrar por proveedor cuesta más de lo que parece, aunque menos de lo que podría creerse. La aplicación conoce el proveedor activo, así que el valor está disponible; el costo está en dónde se aplica la condición. O se agrega a cada consulta que lea fotos, y entonces vuelve a ser algo que cada consulta nueva tiene que recordar —el olvido que la vista de fotos disponibles se creó para eliminar—, o se fija como un valor de sesión de la base en cada conexión para que la vista lo lea, que es posible y devuelve el filtro al terreno estructural, pero agrega un mecanismo con su propio modo de falla: una conexión que no lo fijó.

  Tercero, haría que el significado de una fila dependa de cómo se arrancó la aplicación. Ante un "está en la base pero no la veo" habría dos causas posibles en lugar de una, y eso se paga cada vez que algo falla, no solo cuando se cambia de proveedor.
- Cualquier cambio en el dominio, los endpoints, la interfaz o el esquema. Como en el change anterior, si alguno hiciera falta es un hallazgo sobre el diseño de los puertos.
- Capacidades exclusivas del proveedor cloud que el puerto no expone.
- Pre-generar derivados, que sigue estando fuera por decisión del change que definió la entrega de imágenes.

## Capabilities

### New Capabilities

Ninguna. Este change agrega implementaciones de comportamientos que ya están especificados.

### Modified Capabilities

- `image-delivery`: se le agrega un requirement que hasta ahora no tenía sentido escribir, porque había un solo transformador. Con dos, hace falta decir que **una variante produce un resultado equivalente sea cual sea el proveedor activo**: el mismo nombre tiene que dar una imagen con las mismas medidas y el mismo formato, o cambiar de proveedor rompería la presentación sin que nada lo señale. Ese requirement es el que convierte al catálogo unificado de variantes en una exigencia y no en una preferencia de implementación.
- `object-storage`: se le agrega que **el nombre de un objeto no depende del proveedor y que cambiar de proveedor es copiar contenido**. Es una propiedad que el esquema de nombres ya tenía por construcción, pero que nadie había declarado como garantía, y es la que hace que la migración sea una copia en lugar de una transformación de datos. Junto con ella se exige poder comprobar qué objetos faltan en el destino **antes** de cambiar el proveedor activo, usando la operación de consulta que el puerto ya ofrece.

  Además se corrige, por un hallazgo hecho al implementar (D9): el proveedor cloud elegido no soporta la operación de subida que el puerto asumía (POST presignado con un rango de tamaño), así que la concesión pasa a describir un PUT y el límite de tamaño deja de imponerlo el almacenamiento al recibir -- pasa a verificarlo la aplicación al confirmar, contra el tamaño real del objeto. El adapter local migra a la misma operación, para que los dos proveedores sigan compartiendo exactamente el mismo mecanismo.

Las dos capabilities se materializan al archivar `add-media-ports-and-local-adapters`, así que estos deltas asumen que los changes se archivan en el orden en que fueron planificados.

## Impact

**Archivos nuevos**

- `backend/src/storage/adapters/` gana el adapter del proveedor cloud
- `backend/src/images/adapters/` gana el suyo
- Pruebas de las direcciones firmadas del transformador cloud, y la ejecución de la suite de contrato del almacenamiento contra el proveedor cloud

**Archivos modificados**

- `backend/src/storage/port.py`: `UploadGrant` pasa de describir un formulario POST a describir un PUT con sus encabezados (D9), y `grant_upload` deja de recibir un tope de tamaño que ningún proveedor puede honrar en la firma.
- `backend/src/storage/adapters/minio.py` y el frontend (`uploadQueue.ts`): migran a la misma operación PUT, por la misma razón (D9).
- `backend/src/storage/factory.py` y `config.py`, y sus equivalentes de imágenes: registro de los adapters y sus credenciales.
- `.env.example`: credenciales y direcciones de los dos proveedores, en el perfil correspondiente.
- `compose.yaml` y `compose.dev.yaml`: los servicios locales de almacenamiento y transformación dejan de hacer falta cuando los proveedores activos son los cloud, aunque se conserven para el modo local.
- `README.md`: la puesta en marcha de cada proveedor.

**Dependencias**

El adapter de almacenamiento reutiliza el cliente que ya existe, porque el proveedor habla el mismo protocolo. Y firmar las direcciones del transformador cloud es un cálculo criptográfico que la biblioteca estándar del lenguaje ya provee, así que tampoco hace falta traer nada para eso. La única dependencia nueva es `typer`, para el CLI del comando de reconciliación extendido (D6, D9): ya estaba resuelta de forma transitiva (la trae `fastapi[standard]`), así que declararla como dependencia directa no cambia sustancialmente el lockfile.

**Configuración fuera del repositorio**

Como en el change anterior, hay configuración en sistemas que no controlamos: el espacio de almacenamiento creado en su proveedor con sus credenciales y sus orígenes admitidos, y la cuenta del transformador apuntada a ese almacenamiento como origen.

**Estado que hay que mover**

De los dos puertos, **solo el almacenamiento tiene estado**. El transformador no guarda nada: lee del almacenamiento y produce al pedido, así que cambiarlo es gratis y no deja nada atrás. Por eso hay un único punto de migración en todo el proyecto, y por eso las claves de los objetos se derivan de identificadores del dominio y nunca del proveedor: la misma clave vale en cualquiera, y copiar el contenido alcanza para que el cambio sea sin pérdida.

**Precedencia**

Depende de `add-media-ports-and-local-adapters`, que define los dos puertos, sus contratos y la suite que este change tiene que pasar. No depende del change de autenticación cloud: los puertos de medios no saben quién pide.
