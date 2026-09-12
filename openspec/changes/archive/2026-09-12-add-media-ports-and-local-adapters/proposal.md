## Why

Las fotos son el contenido del producto, y todo lo que se haga con ellas pasa por dos servicios externos: uno que las guarda y otro que las transforma para entregarlas. La promesa del proyecto —funcionar igual en local que contra servicios cloud según variables de entorno— se sostiene o se rompe exactamente en esos dos puntos, así que es donde tiene que haber un puerto y no una llamada directa.

Estos puertos van en su propio change, sin interfaz ni dominio, por un motivo concreto: así se pueden verificar **por contrato**. La misma suite corre contra un doble y contra el servicio real, y lo que ese contrato garantice es exactamente lo que el change de los adapters cloud va a poder reemplazar sin miedo. Si los puertos nacieran dentro del change que sube fotos, su contrato quedaría entremezclado con la lógica de álbumes y nadie podría afirmar que un proveedor distinto se comporta igual.

## What Changes

- **Almacenamiento de objetos y transformador de imágenes entran al entorno local**, con el contenedor de almacenamiento dejando creado su espacio de trabajo al arrancar, para que un clon limpio no requiera prepararlo a mano.
- **Puerto de almacenamiento con tres operaciones**: conceder una subida directa, consultar un objeto ya subido y eliminar objetos. Deliberadamente **no lee bytes**: el transformador de imágenes lee del almacenamiento por su cuenta, y ningún otro consumidor necesita el contenido.
- **Puerto de transformación con una sola operación**: construir la dirección firmada de una variante. Es sincrónica y sin entrada ni salida de datos, porque construir y firmar una dirección no habla con nadie.
- **Tres variantes fijas** —miniatura, calificación y visor— declaradas en un catálogo del proyecto que el adapter traduce a la transformación completa. Quien pide una imagen nombra la variante y nunca sus medidas; el transformador no necesita configuración de presets.
- **Las direcciones de variante van firmadas**, para que nadie pueda pedir transformaciones arbitrarias y convertir el transformador en cómputo gratis.
- **El edge gana el espacio reservado de las imágenes**, con cache en disco, colapso de peticiones simultáneas por la misma variante, y capacidad de seguir sirviendo una respuesta vieja si el transformador no responde.
- **La subida es de origen cruzado y el almacenamiento declara quién puede hacerla.** El navegador escribe directo contra el almacenamiento, que en local es un servicio con su propia dirección y en cloud un dominio del proveedor, así que en los dos casos el origen es distinto del de la aplicación. Eso obliga a declarar los orígenes admitidos en el almacenamiento, y a distinguir la dirección por la que lo alcanza el navegador de la dirección por la que lo alcanzan el backend y el transformador.
- **La invalidación es automática**: como la definición de la variante viaja en la dirección, cambiar una medida produce direcciones nuevas y lo ya cacheado deja de pedirse. No hace falta ningún mecanismo aparte ni tocar el cache.
- **Esquema de nombres de los objetos**, prefijado por álbum, para que eliminar un álbum sea eliminar un prefijo.
- **Suite de contrato parametrizada** que se ejecuta contra el doble y contra el servicio real sin duplicarse.

### Fuera de alcance

- Álbumes, fotos y cualquier endpoint que consuma estos puertos: llegan en el change siguiente, que es el primer consumidor real.
- El calentamiento de variantes al confirmar una subida. Depende del cache que este change establece, pero pertenece al flujo de subida.
- Los adapters cloud de almacenamiento y de transformación.
- Pre-generar derivados y guardarlos: la transformación es al vuelo y el cache es lo que la hace barata.
- Conversión de formatos de entrada que el navegador no produce por sí solo.
- Recorte inteligente, detección de objetos, marca de agua y autoformato: son capacidades de la edición paga del transformador y el diseño no depende de ninguna.

## Capabilities

### New Capabilities

- `object-storage`: cómo el sistema guarda archivos binarios, cómo concede subidas directas sin que el contenido pase por la API, cómo se nombran los objetos, cómo se verifica lo que llegó y qué se le exige a un proveedor para ser intercambiable con otro.
- `image-delivery`: qué variantes de una imagen existen, cómo se autoriza pedirlas, cómo se entregan al navegador, cómo se cachean y cómo se invalida ese cache.

### Modified Capabilities

- `local-environment`: el requirement de que todo el tráfico entre por un único punto sigue valiendo, pero su escenario de reparto asumía dos destinos —la API y la interfaz—. Este change agrega dos espacios reservados más, así que el reparto pasa a describirse en términos de un conjunto de espacios reservados en lugar de enumerar dos.
- `frontend-delivery`: por el mismo motivo, el requirement de que una ruta profunda entregue la aplicación tiene un escenario que protege al espacio de la API de ser absorbido por el fallback. Ese escenario pasa a cubrir todos los espacios reservados, no solo el de la API.

No hace falta modificar el requirement de qué se expone al host: ya está formulado como un principio —se exponen los servicios de terceros que el modo nativo necesita alcanzar— y el almacenamiento de objetos entra bajo esa regla sin enmendarla.

Ambas capabilities se materializan al archivar `add-local-environment`, así que estos deltas asumen que los changes se archivan en el orden en que fueron planificados.

## Impact

**Archivos nuevos**

- `backend/src/storage/port.py`, `factory.py`, `config.py`, `adapters/minio.py`
- `backend/src/images/port.py`, `factory.py`, `config.py`, `adapters/imgproxy.py`
- `backend/tests/fakes.py` y las suites de contrato de almacenamiento y de direcciones de variante

**Archivos modificados**

- `compose.yaml` y `compose.dev.yaml`: almacenamiento de objetos, transformador de imágenes, creación del espacio de trabajo al arrancar y el volumen del cache del edge.
- `edge/nginx.conf`: los dos espacios reservados nuevos, la zona de cache y sus políticas.
- `.env.example`: proveedor de almacenamiento y de transformación activos, direcciones y credenciales del almacenamiento, y las claves de firma del transformador.
- `README.md`: qué son las variantes, dónde se declaran, por qué cambiarlas invalida sola, y cómo inspeccionar el almacenamiento local.

**Dependencias**

- Una dependencia nueva de Python: un cliente del protocolo de almacenamiento de objetos. Es la única que este change agrega, y la usa únicamente el adapter local, que en el change cloud se reutiliza porque el proveedor cloud habla el mismo protocolo.
- Dos imágenes de terceros nuevas, ambas con versión exacta.
- Sin dependencias nuevas de npm: este change no toca la interfaz.

**Precedencia**

Depende de `add-local-environment` por el compose y el edge, y de `add-backend-data-layer` por la suite de pruebas y la traducción de errores a dominio. No depende de `add-auth-port-and-local-provider`: los puertos no tienen noción de quién pide.
