## Why

Es el primer change que produce algo que alguien puede ver y usar, y el que le da sentido a los cuatro anteriores: el entorno, la capa de datos, la identidad y los puertos existen para que una persona pueda crear un álbum y subirle fotos. Hasta acá el proyecto no hace nada observable para un usuario.

Álbumes y subida van juntos en un mismo change y no separados por una razón concreta: un álbum vacío no se puede verificar más allá de comprobar que la fila existe, y una foto no existe sin un álbum que la contenga. Separarlos daría un primer change que no demuestra nada y un segundo que arrastra toda la verificación.

Este change también es donde se estrena el punto más delicado del flujo: la fila de una foto nace **antes** de que sus bytes existan, porque la subida es directa al almacenamiento y la API solo concede el permiso. Ese intervalo entre "declarada" y "subida" es real, puede quedar abierto para siempre si alguien abandona la subida, y de cómo se modele depende que el resto del sistema no muestre fotos que no están.

## What Changes

- **Tablas de álbumes y fotos**, con el dueño del álbum, la posición de cada foto dentro de él y el estado que distingue una foto declarada de una efectivamente subida.
- **Gestión de álbumes acotada a lo necesario**: crear, listar los propios, ver uno, renombrar y eliminar. Solo el dueño puede verlos o modificarlos, porque todavía no existe ninguna forma de compartir.
- **El ciclo de subida en dos pasos**: pedir concesiones para un lote de archivos, y confirmar el lote una vez subido. La API nunca recibe el contenido.
- **La confirmación verifica contra el objeto real**: si el objeto no está, la foto queda pendiente; si su tamaño o su tipo no coinciden con lo declarado, se rechaza y el objeto se elimina. No se le cree al cliente.
- **El tipo y el tamaño se validan al conceder**, antes de que nada se suba, para que un archivo inadmisible no consuma ancho de banda.
- **Un álbum admite una cantidad máxima de fotos, configurable**, con cincuenta por omisión. Es una restricción de producto y no una cuota de consumo: calificar un álbum foto por foto deja de ser viable cuando son cientos. El máximo condiciona agregar fotos nuevas y **no invalida lo ya guardado**: un álbum que lo supera porque el valor se redujo después conserva todas sus fotos y sigue funcionando, y eliminar algunas vuelve a habilitar la incorporación.
- **Una foto que no está lista es invisible para el resto del sistema**, y eso se establece como propiedad y no como una condición que cada consulta recuerde repetir.
- **Calentamiento de la variante de calificación al confirmar un lote**, con una sola tarea diferida por lote, concurrencia acotada y un fallo que nunca llega al cliente.
- **Eliminar arrastra los objetos del almacenamiento**: borrar una foto borra su objeto, y borrar un álbum borra su prefijo completo. Las filas las arrastra la cascada del esquema, pero los objetos no los arrastra nadie.
- **Las dimensiones de la imagen las declara el cliente** y son una pista de presentación para reservar el espacio de cada foto antes de que cargue, no un dato del que dependa ninguna decisión.
- **Interfaz**: lista de álbumes, creación, grid del álbum con las miniaturas, y el selector de archivos con progreso por archivo y reintento del que falle.

### Fuera de alcance

- **Reordenar fotos dentro de un álbum.** La posición se asigna al subir y no se cambia. Reordenar agrega superficie —una operación, un endpoint, una interacción de arrastre— que nadie necesita todavía.
- **Elegir la portada del álbum a mano**: se usa la primera foto.
- Compartir, calificar, la galería con filtros y las estadísticas.
- Editar la imagen, rotarla o recortarla desde la aplicación.
- Coautores: el álbum tiene un único dueño y nadie más puede subir ni eliminar.
- Formatos de entrada que el navegador no produce por sí solo.
- Los adapters cloud de almacenamiento y transformación.

## Capabilities

### New Capabilities

- `album-management`: qué es un álbum, quién puede crearlo, verlo y modificarlo, cómo se listan los propios, y qué se elimina cuando se elimina uno.
- `photo-upload`: cómo una foto llega a formar parte de un álbum, qué se valida y en qué momento, cuántas admite, cómo se confirma que efectivamente llegó, qué estados atraviesa y qué se hace con lo que queda a medio camino.

### Modified Capabilities

- `image-delivery`: su requirement de que una variante se produzca al pedirla incluye la prohibición de pre-generar variantes al guardar la imagen. El calentamiento que este change introduce no es pre-generación —no produce ni almacena derivados por su cuenta, sino que pide la variante por el camino normal para que quede cacheada antes de que la pida una persona—, pero la redacción vigente no distingue las dos cosas. El delta hace explícita la diferencia y admite el calentamiento sin abrir la puerta a la pre-generación.
- `api-conventions`: el máximo de fotos por álbum introduce una situación de error que las convenciones no cubrían — una petición bien formada que no procede por el estado del recurso. Se agrega como requirement porque exige una acción distinta de la de un error de validación: liberar espacio y reintentar la misma petición sin modificarla, en lugar de corregir lo enviado.

Las dos capabilities se materializan al archivar los changes que las crean, así que estos deltas asumen que los changes se archivan en el orden en que fueron planificados.

## Impact

**Archivos nuevos**

- `dbmate/migrations/0003_create_albums_and_photos.sql`
- `backend/src/packages/albums/router.py`, `service.py`, `repository.py`, `dependencies.py`, `schemas.py`, `responses.py`
- `backend/src/packages/photos/router.py`, `service.py`, `repository.py`, `schemas.py`, `responses.py`
- Pruebas de álbumes, de concesión y confirmación, de límites de subida, de eliminación con arrastre de objetos, y de calentamiento
- `frontend/src/features/albums/` y `frontend/src/features/photos/`
- `frontend/src/routes/_app/albums/index.tsx`, `new.tsx`, y el directorio `$albumId/` con su layout, su índice y su vista de subida

**Archivos modificados**

- `dbmate/schema.sql`: regenerado con las dos tablas nuevas.
- `backend/src/routes.py`: montaje de los dos routers nuevos.
- `backend/tests/factories.py`: constructores de álbum y de foto.
- `.env.example`: el máximo de fotos por álbum, en los dos perfiles de configuración.
- `frontend/src/routes/_app/route.tsx`: la navegación del layout deja de estar vacía.
- `README.md`: el flujo de crear un álbum y subir fotos.

**Dependencias**

Ninguna nueva, ni de Python ni de npm. Sí agrega componentes del registro de la biblioteca de interfaz, que son archivos del proyecto y no dependencias.

Agrega **una** variable de entorno: el máximo de fotos por álbum. El límite de tamaño de archivo, los tipos admitidos, el techo del lote y la concurrencia del calentamiento siguen siendo constantes del código, porque son el contrato del producto y no algo que varíe entre entornos. El máximo por álbum sí varía: tiene sentido poder ajustarlo sin reconstruir, y ajustarlo no rompe nada de lo ya guardado.

**Precedencia**

Depende de `add-auth-port-and-local-provider`, porque un álbum tiene dueño y hace falta saber quién pide, y de `add-media-ports-and-local-adapters`, porque la subida y la entrega de miniaturas pasan por los dos puertos.
