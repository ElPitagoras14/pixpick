## Why

El backend tiene 193 importaciones internas repartidas en dos formas. 117 son absolutas hacia paquetes ajenos y 59 relativas al mismo directorio: esas 176 siguen una regla coherente. Las 17 restantes son absolutas apuntando dentro del subárbol del propio archivo, donde una relativa diría lo mismo — y son las que hacen que un archivo mezcle estilos sin que la diferencia signifique nada. `src/main.py` es el caso visible: importa `from src.database.client` y tres líneas más abajo `from .config`, `.handlers`, `.log`. Las dos formas resuelven igual, así que no es un problema de corrección; es que quien lee tiene que detenerse a averiguar si la diferencia quiere decir algo, y quien escribe un archivo nuevo adivina cuál usar, porque la regla que los otros 176 casos respetan no está escrita en ninguna parte.

En el frontend pasa lo mismo a menor escala: todos los módulos propios se importan por el alias del proyecto salvo dos líneas, en `main.tsx` y en `router.tsx`.

Y la pantalla de ingreso del proveedor local sirve su HTML desde un f-string de veinte líneas dentro de `identity/adapters/local.py`. Ahí el marcado no tiene resaltado ni formateo, el formateador de Python no lo toca, y una llave de más no da un error de plantilla sino que rompe la interpolación del literal.

Eso último tiene una consecuencia que no es de estilo: ese f-string interpola dentro de un atributo del formulario el parámetro `state` tal como llegó en la dirección, sin neutralizarlo. Un valor preparado a propósito cierra el atributo y agrega marcado propio. Solo alcanza a este adapter, que el factory se niega a construir fuera de desarrollo, así que no llega a producción — pero es la clase de problema que la plantilla elimina por construcción, porque un motor de plantillas neutraliza lo que inserta salvo que se le pida explícitamente lo contrario.

## What Changes

- **Se escribe la regla de importaciones del backend**, que hoy solo existe como práctica: dentro del propio subárbol el import es relativo, fuera es absoluto, y un import relativo nunca sube de nivel. Esa última parte ya se cumple sin excepciones —`from ..` no aparece una sola vez en el proyecto— y pasa a quedar fijada en lugar de depender de que nadie la rompa.
- **Se corrigen las 17 importaciones que la incumplen**, en siete archivos: los cuatro de la raíz de `src/` y los tres factories que importan sus propios adapters.
- **Los dos imports relativos del frontend pasan al alias del proyecto**, que es lo que usa el resto.
- **El HTML de la pantalla de ingreso local sale a una plantilla**, servida con el motor de plantillas que el proyecto ya tiene en su lockfile por venir con FastAPI. La pantalla no cambia: cambia dónde vive su marcado.
- **Las convenciones se hacen cumplir con herramienta, no con revisión.** La mitad de la regla de importaciones —nunca subir— la cubre el linter del backend activando un grupo de reglas que hoy no está seleccionado, y hacerlo no reporta ninguna violación existente. La otra mitad —dentro del subárbol, relativo— no la trae ninguna herramienta, y se cubre con una comprobación propia en la suite de pruebas, del mismo tipo que las que ya verifican la estructura del esquema de la base. Para el frontend, la regla equivalente se configura en su linter.

### Fuera de alcance

- **Ordenar u organizar importaciones.** Ya está resuelto: el linter del backend tiene activo el grupo que las ordena, y el del frontend hace lo propio como acción de asistencia. Este change es sobre qué forma tiene cada import, no sobre en qué orden aparecen.
- **Mover, renombrar o dividir módulos.** Las 17 líneas cambian de forma, no de destino.
- **Cambiar la pantalla de ingreso local.** Sale el marcado del código de Python; lo que se ve y lo que hace el formulario queda idéntico, y el ciclo que recorre —dirección de autorización, pantalla, código de un solo uso— no se toca.
- **Servir cualquier otra respuesta con plantillas.** La API devuelve JSON, y esta pantalla es la única excepción del proyecto. La plantilla existe para ella, no como una capa nueva de presentación.
- **Convenciones de estilo que las herramientas ya resuelven** (comillas, sangría, longitud de línea, orden de miembros). Están configuradas y aplicadas.

## Capabilities

### New Capabilities

- `code-conventions`: gobierna las convenciones de código que ninguna herramienta trae configurada de fábrica y que, sin quedar escritas, se resuelven por imitación del archivo de al lado. Cubre qué forma tiene una importación interna en cada lado del proyecto, dónde vive el marcado que el backend sirve, y —la parte que le da valor— que cada una de esas reglas se compruebe de forma automática en lugar de depender de que alguien la note al revisar. Es el lugar natural de las convenciones que vengan después, que hoy no tienen dónde ir: `api-conventions` gobierna la forma de la API HTTP y `backend-testing` la de las pruebas, ninguna de las dos el código en general.

### Modified Capabilities

Ninguna. Las importaciones resuelven a los mismos módulos y la pantalla de ingreso sirve el mismo marcado desde otro archivo.

Con una salvedad, que queda cubierta por un requirement de la capability nueva y no por un delta sobre `identity-provider`: la pantalla pasa a neutralizar el valor que recibe en la dirección, cosa que hoy no hace. No es un cambio en el ciclo de autenticación —la pantalla, el código de un solo uso y el retorno siguen igual—, sino en cómo se construye la respuesta, que es justamente lo que la capability nueva gobierna.

## Impact

**Archivos nuevos**

- La plantilla de la pantalla de ingreso local, junto al adapter que la sirve.
- La comprobación automática de la regla de importaciones, en la suite del backend.

**Archivos modificados**

- `backend/pyproject.toml`: se agrega el grupo de reglas de importaciones al conjunto seleccionado del linter, con la opción que prohíbe subir de nivel.
- Siete archivos de `backend/src/`: `main.py`, `routes.py`, `handlers.py`, `health.py`, y los factories de `identity/`, `images/` y `storage/`. Diecisiete líneas en total.
- `backend/src/identity/adapters/local.py`: el f-string con el HTML se reemplaza por la carga de la plantilla.
- `frontend/src/main.tsx` y `frontend/src/router.tsx`: una línea cada uno.
- `frontend/biome.json`: la regla equivalente para el frontend.

**Dependencias**

Ninguna nueva. El motor de plantillas ya está en el lockfile del backend, arrastrado por `fastapi[standard]`, así que servir una plantilla no agrega nada que instalar.

**Riesgo de regresión**

Bajo y acotado: un import mal corregido falla al importar el módulo, y la suite completa recorre todos los paquetes. El único cambio con comportamiento posible es la plantilla, y se verifica pidiendo la pantalla y comparando lo que devuelve contra lo que devolvía.

**Precedencia**

Ninguna. Es independiente de `slim-docs-and-compose` y de los cinco changes que siguen: no comparte archivos con ninguno.
