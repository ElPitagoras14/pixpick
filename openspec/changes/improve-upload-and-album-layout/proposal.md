## Why

La vista de subida informa mal dos cosas que importan justo cuando algo tarda o falla.

El avance de cada archivo vive en una franja de 160 píxeles fijos, al final de una fila de una línea que comparte con el nombre del archivo. En esa franja no entra una barra que se lea de un vistazo, y tampoco entra el texto cuando el estado no es un porcentaje: los siete estados posibles —en espera, subiendo, confirmando, subida, pendiente, rechazada, fallida— se truncan en el mismo espacio donde iba la barra. Cuando algo sale mal, el motivo es lo que menos lugar tiene.

Y la vista de subida ofrece volver al álbum con un enlace que queda **debajo** del título del álbum, no encima. No es un descuido de orden de líneas: el encabezado del álbum esconde su propio enlace de vuelta cuando la subvista es la de subir, y deja que esa subvista dibuje el suyo dentro del área de contenido, que va después del título. El resultado es que en toda la aplicación el acceso de vuelta está arriba del título menos acá.

## What Changes

- **Cada archivo pasa a ser una card**, con su nombre y su tamaño arriba, la barra de avance a todo el ancho disponible, y su estado o su motivo de fallo debajo, con lugar para leerse completo.
- **La barra deja de competir por el renglón del nombre.** Esa era la limitación que obligaba a los 160 píxeles: en una card ocupa el ancho del contenedor.
- **Un motivo de fallo puede ocupar dos renglones sin romper nada.** Es lo que hace falta para el estado que introduce el límite de la cuenta —un archivo pedido y no concedido, con su motivo y cuánto espacio queda—, que en una fila de una línea obligaría a truncar justo la parte útil.
- **El enlace de vuelta se muda al encabezado**, por encima del título, que es donde está en todas las demás pantallas. Lo que cambia entre subvistas es a dónde apunta —al álbum desde la subida, a la lista desde el álbum—, no dónde vive.
- **La vista de subida sigue siendo un flujo propio**: su encabezado no ofrece las acciones del álbum, que es la regla que ya rige hoy y que este change conserva; lo único que se corrige es dónde aparece la salida.

### Fuera de alcance

- **Cambiar cómo funciona la subida.** Ni la concurrencia, ni el reintento por archivo, ni el tamaño de los lotes, ni la validación previa. Este change cambia cómo se informa, no qué ocurre.
- **Rediseñar el encabezado del álbum más allá del enlace de vuelta.** Los botones de compartir, subir y calificar quedan como están.
- **Tocar la grilla de fotos o la vista de calificación.** La grilla cambia en el change del visor, no en este.
- **Mostrar una miniatura de cada archivo mientras sube.** Se puede leer localmente antes de enviarlo y haría la lista más reconocible, pero es trabajo propio —generar y liberar las vistas previas, y decidir qué pasa con cincuenta a la vez— y no es lo que las observaciones piden.

## Capabilities

### New Capabilities

- `upload-feedback`: gobierna cómo la interfaz informa una subida en curso. Define que cada archivo se informe por separado y con su propia identidad visible, que su avance y su desenlace tengan lugar suficiente para leerse —incluido el motivo cuando algo no sale—, que el fallo de uno no confunda el estado de los demás, y que esta vista se presente como un flujo propio con su salida donde está en todas las demás pantallas. Es lo que hoy no está escrito: `photo-upload` gobierna el contrato de subir —qué se concede, qué se verifica, qué se rechaza— y nada gobierna qué ve quien está esperando a que termine.

### Modified Capabilities

Ninguna. `photo-upload` no cambia: se conceden, se suben y se confirman exactamente las mismas fotos de la misma manera, y lo que este change toca es únicamente cómo se presenta ese proceso.

## Impact

**Interfaz**

- `routes/_app/albums/$albumId/upload.tsx`: la lista de archivos pasa de filas a cards, y pierde su enlace de vuelta propio.
- `routes/_app/albums/$albumId/route.tsx`: el encabezado pasa a decidir el destino del enlace de vuelta según la subvista activa, en lugar de esconderlo.
- Probablemente un componente propio para la card de un archivo, por la misma razón que el proyecto ya separó la tarjeta de la galería y la del mazo de calificación: una pieza con varios estados se lee mejor sola que embebida en la ruta.

**Sin backend**

Nada de este change toca el servidor. Los estados que se muestran ya existen en la cola de subida del cliente.

**Precedencia**

Después de `add-account-quota`. Ese change agrega el estado "pedido y no concedido" con su motivo, que es justamente el que no entra en la forma actual; si este se hiciera antes, habría que rediseñar la misma lista dos veces.
