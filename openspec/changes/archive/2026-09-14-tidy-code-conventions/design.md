## Context

El backend tiene 193 importaciones internas: 117 absolutas hacia paquetes ajenos, 59 relativas al mismo directorio, y 17 absolutas que apuntan dentro del subárbol del propio archivo. Estas últimas viven en siete archivos —`main.py`, `routes.py`, `handlers.py`, `health.py` y los factories de `identity/`, `images/` y `storage/`— y son las únicas que rompen el patrón que las otras 176 siguen. Importaciones relativas que suban de nivel no existe ninguna: `from ..` no aparece en el proyecto.

El linter del backend selecciona hoy `["E", "F", "I", "UP", "B"]`. El grupo `TID`, que es el que trata las importaciones relativas, está disponible y no seleccionado.

En el frontend, todo módulo propio se importa por el alias `@/` salvo dos líneas: `main.tsx` importa `./router` y `router.tsx` importa `./routeTree.gen`. El linter corre con el preset recomendado, sin reglas configuradas una por una, y su configuración ya excluye `src/routeTree.gen.ts` de la revisión por ser generado.

La pantalla de ingreso del proveedor local se sirve desde `identity/adapters/local.py`, en un f-string de veinte líneas que interpola el parámetro `state` dentro de un atributo del formulario. La función devuelve `HTMLResponse` y no recibe el objeto de la petición. `jinja2` ya está en el lockfile, arrastrado por `fastapi[standard]`, y el Dockerfile del backend copia `src` entero.

## Goals / Non-Goals

**Goals:**

- Que la forma de una importación se deduzca del destino, sin memoria ni imitación del archivo de al lado.
- Que las tres reglas de la capability las verifique una herramienta, no una revisión.
- Que el marcado de la única pantalla que el backend sirve viva donde se lo puede leer y formatear, y que deje de insertar sin neutralizar lo que llega en la dirección.

**Non-Goals:**

- Uniformar por uniformar. Un archivo va a seguir conteniendo las dos formas de importación cuando sus destinos caigan de lados distintos de la línea; eso es la regla funcionando, no un resto por limpiar.
- Introducir una capa de plantillas. Es un archivo, para una pantalla, y la API sigue devolviendo JSON.

## Decisions

### D1 - El destino decide la forma, y el costo de esa elección es una comprobación propia

La regla es la que el 91% del código ya sigue: dentro del propio subárbol, relativo; fuera, absoluto; nunca subir.

La alternativa seria era "todo absoluto", y tenía una ventaja concreta que conviene dejar escrita: el linter del backend puede imponerla entera por sí solo, prohibiendo toda importación relativa con una línea de configuración. La regla elegida no se puede imponer entera con ninguna herramienta existente, y por eso arrastra la comprobación propia de D3. Se elige igual porque la regla ya está escrita en 176 lugares del código: adoptarla cuesta 17 líneas, mientras que "todo absoluto" cuesta 59 y convierte cada `from .config` en una ruta completa que repite dónde está parado el archivo. La comprobación propia es una vez; las 59 líneas y la verbosidad, todos los días.

### D2 - El linter del backend cubre la mitad que sabe cubrir

Se agrega `TID` al conjunto seleccionado, que prohíbe las importaciones relativas hacia paquetes superiores. Es exactamente la mitad "nunca subir" de la regla.

Activarlo hoy no reporta ni una violación, porque el proyecto ya no tiene ninguna. Eso es lo que lo hace barato y a la vez valioso: no hay nada que arreglar para encenderlo, y una vez encendido la propiedad deja de depender de que nadie la rompa.

### D3 - La otra mitad va como prueba de la suite

La parte que ninguna herramienta trae —"si el destino está bajo tu propio paquete, la importación va relativa"— se comprueba con una prueba que recorre los archivos de `src/`, mira cada importación absoluta que empiece por la raíz del código, y falla si el módulo importado cae dentro del paquete del archivo que la escribe. Es el mismo criterio con el que se midieron las 17 violaciones, así que la prueba nace con un resultado conocido.

Falla nombrando archivo y línea, que es lo que exige el spec. Vive en la suite del backend junto a las otras comprobaciones estructurales, no como un script aparte: un script aparte hay que acordarse de correrlo.

### D4 - El linter del frontend expresa su regla con una restricción de patrones

Se configura la regla de importaciones restringidas del linter con un grupo que cubre cualquier especificador que empiece por `./` o `../`. Verificado contra la versión que el proyecto tiene fijada: marca las dos importaciones relativas existentes y no toca las que usan el alias.

El archivo generado queda fuera por la exclusión que la configuración ya tiene, lo cual es correcto y no una omisión: su contenido lo escribe una herramienta. La importación *hacia* él, que está en `router.tsx` y sí se escribe a mano, queda dentro y se corrige.

Se descarta agregar un mensaje propio a la regla: la forma con patrones no lo admite, y el que trae —"no importes './router'"— ya dice qué línea cambiar.

### D5 - La plantilla se carga con un entorno propio, no con el envoltorio de plantillas del framework

El envoltorio que trae el framework devuelve un tipo de respuesta propio y exige recibir el objeto de la petición en el contexto. La función actual no recibe ese objeto y devuelve `HTMLResponse`; adoptarlo obligaría a cambiar la firma de un endpoint para mover un archivo de lugar.

En su lugar se construye un entorno de plantillas apuntando a un directorio junto al adapter, con el escape automático activado, y la función sigue devolviendo `HTMLResponse` con el resultado de renderizar. La firma, el tipo de retorno y el ciclo de autenticación quedan idénticos.

El directorio se resuelve a partir de la ubicación del propio módulo y no del directorio de trabajo, para que funcione igual corriendo desde el repositorio que desde la imagen. La plantilla viaja a la imagen sin tocar el Dockerfile, que copia `src` completo.

### D6 - El escape queda activado y el valor de la dirección deja de insertarse crudo

El entorno se construye con el escape automático encendido, de modo que el parámetro que llega en la dirección se inserta como texto. No se usa ningún mecanismo para marcarlo como seguro.

Es el único cambio de comportamiento del change, y es el que justifica que la plantilla no sea solo prolijidad: hoy ese valor se concatena dentro de un atributo sin neutralizar, y un valor preparado cierra el atributo y agrega marcado propio.

## Risks / Trade-offs

**La regla elegida necesita código propio para comprobarse, la alternativa no (D1, D3)** → La comprobación es una prueba corta con un criterio ya validado contra el código real, y se escribe una sola vez. A cambio se evitan 42 líneas más de cambio y la verbosidad permanente de repetir la ruta completa hacia el archivo de al lado.

**Una prueba que lee el código fuente puede dar falsos positivos (D3)** → El criterio solo mira importaciones que empiecen por la raíz del código del proyecto; las de terceros y las de la biblioteca estándar no entran en la comparación.

**Mover el marcado puede cambiarlo sin querer (D5)** → Se verifica comparando la respuesta de la pantalla antes y después, ignorando espacios en blanco. No alcanza con que la página "se vea bien": el formulario tiene que seguir enviando los mismos campos al mismo destino.

**Encender una regla de linter puede reportar violaciones inesperadas en archivos que nadie miró (D2, D4)** → En los dos casos se midió el resultado antes de decidir: el del backend no reporta nada, y el del frontend reporta exactamente las dos líneas que este change corrige.

## Migration Plan

No hay nada que migrar: no hay datos, ni configuración de entorno, ni estado. El cambio es de código y de configuración de herramientas, y su efecto completo se observa corriendo el linter y la suite.

El rollback es revertir el commit. Ninguna de las dos reglas de linter deja rastro fuera del repositorio, y la plantilla desaparece con el archivo.

## Open Questions

Ninguna. Las tres incógnitas que tenía este change —si cada linter puede expresar su regla, y cómo cargar la plantilla sin cambiar la firma del endpoint— se resolvieron ejecutando las herramientas del propio proyecto, así que no quedó nada cuya respuesta hubiera que suponer.

### Resueltas durante la redacción

- **¿Existe una regla de linter para "importación absoluta que podría ser relativa"? (D1, D3)** No. Listando el catálogo completo del linter del backend, la única regla sobre importaciones relativas es la que las prohíbe hacia paquetes superiores, que va en la dirección contraria. De ahí sale la necesidad de la prueba propia. *Fuente: catálogo de reglas del linter instalado.*
- **¿Encender ese grupo de reglas rompe algo hoy? (D2)** No: el proyecto no tiene una sola importación relativa que suba de nivel. *Fuente: búsqueda sobre todo el código del backend.*
- **¿Puede el linter del frontend expresar "nada de rutas relativas"? (D4)** Sí, con un grupo de patrones que cubra `./*` y `../*`. Probado contra la versión fijada del proyecto: marca las dos líneas existentes y deja intactas las que usan el alias. *Fuente: ejecución del linter sobre un archivo de prueba.*
- **¿Admite esa forma un mensaje propio? (D4)** No, la variante con patrones no lo acepta; se usa el mensaje que trae. *Fuente: la misma ejecución y la documentación de la regla.*
- **¿El envoltorio de plantillas del framework o un entorno propio? (D5)** Entorno propio. El envoltorio exige el objeto de la petición y devuelve otro tipo de respuesta, así que usarlo obligaría a cambiar la firma de un endpoint para mover un archivo de lugar. *Fuente: contrato del envoltorio y la firma actual de la función.*
- **¿La plantilla llega a la imagen del backend? (D5)** Sí, sin tocar nada: el Dockerfile copia `src` completo. Resolver el directorio desde la ubicación del módulo, y no desde el directorio de trabajo, es lo que hace que funcione igual en los dos modos de ejecución. *Fuente: `backend/Dockerfile`.*
- **¿Cuántas líneas cambian y dónde? (D1)** Diecisiete, en siete archivos, contadas con el mismo criterio que después implementa la prueba. *Fuente: medición sobre el código.*
- **¿El valor que se interpola sin neutralizar es realmente alcanzable? (D6)** Sí: llega como parámetro de la dirección. El alcance está acotado a desarrollo, porque el factory se niega a construir este adapter con otro entorno (`identity/factory.py`), pero dentro de ese alcance el valor es de quien arma la dirección. *Fuente: el código del adapter y la comprobación del factory.*
