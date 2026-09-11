## Context

Lo relevante para el enfoque es el estado de partida: el backend expone un único `main.py` sin router ni configuración, el frontend tiene una ruta y ya trae el andamiaje de TanStack Router con generación de rutas por archivos, y no existe ninguna declaración de infraestructura. El repositorio de referencia del autor (`ElPitagoras14/aniseek`) fija las convenciones que este proyecto replica: `compose.yaml` más `compose.dev.yaml` en la raíz, imágenes propias por servicio con la configuración horneada, y el frontend servido por su propio nginx con la configuración inyectada al arrancar el contenedor.

Dos restricciones condicionan el diseño. La primera es que el entorno de desarrollo corre en Windows, así que todo lo que sea un script de shell dentro de una imagen tiene que ser inmune al final de línea que Git deje en el working tree. La segunda es que este change no tiene base de datos utilizable todavía: el acceso a datos y las migraciones llegan en `add-backend-data-layer`, de modo que el backend arranca sin conectarse a Postgres y su healthcheck solo prueba que el proceso está en pie.

El destino de despliegue ya existe y condiciona dos decisiones. Los servicios corren en un VPS gestionado por Dokploy, cuyo proxy —Traefik— termina TLS con certificados que emite y renueva por su cuenta, y alcanza los contenedores de un stack de compose por la red de Docker en vez de por puertos del host. Delante del dominio está Cloudflare.

## Goals / Non-Goals

**Goals:**

- Que la topología local sea la misma que tendrá la topología cloud: el navegador siempre habla con un único edge, que reparte hacia la interfaz y hacia la API.
- Que el edge tenga lugar para crecer: en `add-media-ports-and-local-adapters` va a sumar la ruta de imágenes con su zona de cache, y eso no debe obligar a reorganizar nada.
- Que una misma construcción del frontend sirva en cualquier entorno, y que un valor de entorno faltante se manifieste al arrancar y no como un error difuso en el navegador.
- Que el flujo nativo siga siendo viable: correr el backend con `uv` y el frontend con `pnpm` contra los servicios del compose, sin obligar a levantar todo en contenedores para desarrollar.

**Non-Goals:**

- Terminación de TLS, dominios y certificados: no son del proyecto. En local se sirve por HTTP, y en el VPS lo resuelve Traefik bajo Dokploy sin que el compose participe. El edge de este diseño habla HTTP siempre.
- Configurar el despliegue. La plataforma ya existe y el compose está pensado para alimentarla, pero asignar dominios, variables de producción y triggers de deploy queda fuera de este change.
- Healthchecks de compose y dependencias ordenadas entre servicios: hacen falta cuando aparezca un servicio que dependa de que Postgres esté listo, y eso ocurre en el change siguiente.

## Decisions

### D1 - El edge es un servicio propio, y el frontend conserva su nginx interno

Hay dos capas de nginx: un servicio `edge` que es la única puerta al host, y el nginx que vive dentro de la imagen del frontend sirviendo los estáticos. El edge rutea; el nginx del frontend solo sabe servir archivos y aplicar el fallback del enrutado del cliente.

El costo aceptado es duplicación de configuración de nginx en dos lugares. Se contiene con una regla: el edge decide **a dónde va** cada petición y qué se cachea; el nginx del frontend decide **cómo se entregan** los estáticos. Ninguna decisión de ruteo en el frontend, ninguna decisión sobre estáticos en el edge.

Las dos capas no son un costo transitorio a revisar más adelante: son consecuencia de que la configuración en runtime sea responsabilidad de quien entrega los archivos. Colapsarlas mudaría el entrypoint de D4 y D5 al edge, y el edge pasaría a sustituir la configuración del SPA, que es precisamente lo que esta decisión evita.

**Alternativa descartada:** extender el nginx de la imagen del frontend para que además proxeara la API, que es exactamente la topología de aniseek y ahorra un contenedor. Se descarta por dos razones. Primero, en el change 4 el edge suma la ruta de imágenes con `proxy_cache`, un volumen de cache y su propia política de invalidación; meter eso en la imagen del frontend haría que servir el SPA y cachear derivados de imagen convivan en el mismo archivo, y son responsabilidades que cambian por motivos distintos. Segundo, la imagen del frontend quedaría enterada de la existencia del backend y de imgproxy, cuando lo único que necesita saber es cómo entregar sus archivos.

### D2 - El prefijo de la API se proxea tal cual, sin reescritura

El backend monta su router bajo el mismo prefijo con el que el navegador pide, y el edge proxea la ruta sin tocarla. Así la URL que ve el backend es idéntica a la que envió el navegador, y no hay dos vocabularios de rutas que mantener en correspondencia.

**Alternativa descartada:** que el edge quite el prefijo y el backend viva en la raíz, con `root_path` para que la documentación siga funcionando. Ahorra el prefijo en el código del backend, pero introduce una clase entera de errores: cualquier URL que el backend genere —una redirección, un `Location`, los enlaces del esquema OpenAPI— sale sin el prefijo y apunta a un lugar inexistente desde el navegador.

### D3 - El fallback del SPA no alcanza al espacio de la API

Es la consecuencia operativa de D2 y merece nombrarse aparte porque es el error que el spec vigila con un escenario propio. El `try_files` que devuelve el documento de la aplicación para cualquier ruta desconocida vive únicamente en el nginx del frontend. La ruta de la API en el edge no tiene fallback: si el backend no responde, el edge devuelve su propio error de gateway. Sin esta separación, un backend caído se manifestaría como el HTML del SPA con estado 200, que es la falla más confusa posible: el cliente recibe un documento donde esperaba datos y el error aparece recién al intentar interpretarlo.

### D4 - La configuración del frontend viaja en un archivo generado al arrancar, cargado de forma sincrónica

El frontend construye una vez. La imagen incluye una plantilla con placeholders, y al arrancar el contenedor un entrypoint la convierte en un archivo de configuración servido junto al documento de entrada. El documento lo carga con una etiqueta de script común, antes del bundle de la aplicación, de modo que cuando el código de la aplicación se ejecuta la configuración ya está en el ámbito global. La carga sincrónica antes del bundle es lo que hace que la garantía sea estructural en vez de disciplinada.

**Alternativas descartadas:** resolver la configuración en tiempo de construcción con las variables del bundler es lo más simple, pero obliga a una imagen por entorno y contradice el requirement de que una misma construcción sirva en todos. Pedir un archivo de configuración por red al arrancar la aplicación evita el entrypoint, pero introduce una ventana en la que la aplicación ya corre sin configuración: cada consumidor tendría que tolerar el valor ausente, y el spec pide explícitamente que ese estado no exista.

### D5 - El entrypoint valida antes de sustituir, porque la sustitución no falla sola

El entrypoint tiene dos fases: primero recorre la lista de variables requeridas y termina con código de error nombrando la primera que falte, y solo después sustituye y arranca nginx. La lista de requeridas es explícita en el script, no derivada de la plantilla, para que agregar un placeholder sin declararlo como requerido sea un error visible en revisión.

**Alternativa descartada:** confiar en la herramienta de sustitución para detectar el problema. No sirve: reemplaza un placeholder sin valor por una cadena vacía y termina con éxito, así que serviría una interfaz configurada con valores vacíos, que es justo lo que el spec prohíbe.

### D6 - Las versiones de las imágenes se fijan exactas, y subirlas es un cambio deliberado

Toda imagen de terceros lleva versión exacta. Se fija `postgres:18.6`, que es la estable vigente, y nginx se fija en su estable vigente al momento de implementar. La contrapartida es que los parches de seguridad requieren un bump manual; se acepta porque a cambio el bump aparece en el diff y se puede correlacionar con cualquier cambio de comportamiento, que es más valioso que la actualización silenciosa en un proyecto de este tamaño.

**Alternativa descartada:** una etiqueta de familia como `postgres:18`, que traería parches de seguridad sin intervención. Se descarta porque es una etiqueta que se mueve: reconstruir el entorno dentro de seis meses daría una versión distinta, y el spec pide explícitamente lo contrario.

### D7 - El compose base describe el despliegue y el archivo de desarrollo agrega lo que solo sirve en la máquina

`compose.yaml` declara los servicios, la red y los volúmenes, y **no publica ningún puerto al host**: el edge declara el puerto que atiende y el proxy de la plataforma lo alcanza por la red de Docker. `compose.dev.yaml` agrega lo que existe solo para desarrollar: el puerto del edge para poder abrir la aplicación en el navegador, el de Postgres para inspeccionarlo con un cliente, y los montajes que permiten iterar sin reconstruir imágenes. Mantiene honesto al archivo base — lo que está ahí es lo que correría en un servidor, sin condicionales que haya que leer para saberlo.

**Alternativa descartada:** perfiles dentro de un solo archivo. Funciona, pero obliga a leer condicionales para saber qué corre en cada caso, y se aparta de la convención de dos archivos del repositorio de referencia.

### D8 - Las rutas del frontend orquestan y la lógica vive en features

Este change crea las primeras rutas, así que fija la convención. Un archivo de ruta contiene la definición de la ruta —guardas, carga de datos, validación de parámetros de búsqueda, componentes de error y de pendiente—, la lectura de parámetros, y la composición de componentes de feature. Puede contener lógica básica: un valor derivado, una condición entre dos vistas, un handler que dispara una mutación y navega. Lo que se mueve a `features/` es lo que se reutiliza, lo que tiene estado propio coordinándose, lo que necesita pruebas, o lo que es conocimiento de dominio y no armado de página.

La contracara importa tanto como la regla: no se crea un hook que solo envuelva una consulta, ni un componente que solo reenvíe props, ni un archivo de utilidades para una función de dos líneas usada en un lugar, ni carpetas con un solo archivo dentro. La prueba es si la división permite entender o cambiar una parte sin leer las otras; cuando las piezas solo tienen sentido juntas, un archivo es el mejor diseño.

### D9 - Las URLs absolutas se derivan de la configuración, no del request entrante

El edge habla HTTP incluso en producción, porque TLS lo termina el proxy de la plataforma. Eso significa que el esquema y el host que el backend ve en la petición no son los que ve el navegador. Cualquier URL absoluta que el sistema genere se construye a partir del valor configurado de la URL pública, nunca a partir del esquema o el host del request.

Sin esta regla el síntoma es característico y tardío: en local todo funciona, y en producción los enlaces generados salen con `http://` y con el host interno del contenedor. Es un error que solo se manifiesta detrás de un proxy que termina TLS, o sea recién al desplegar. En este change todavía no se generan URLs absolutas, pero la regla se fija acá porque es donde queda establecido que el edge no ve TLS; las capabilities que después generen enlaces —el de compartir un álbum, el de retorno tras iniciar sesión— la heredan como requirement.

### D10 - Los dos modos de trabajo son perfiles de configuración con los mismos nombres de variable

Hay dos modos: todo en contenedores, y servicios de terceros en contenedores con el backend y la interfaz corriendo nativos. Cada uno es un perfil de configuración, y el invariante que los separa es que **los nombres de las variables son idénticos y solo cambian los valores**. Ninguna parte del código pregunta en qué modo corre.

Es la misma propiedad que el proyecto ya busca entre componentes locales y cloud, aplicada a otra dimensión. En modo nativo el valor que nombra al host de la base deja de ser el nombre del servicio y pasa a ser el host local, y lo mismo ocurrirá con las direcciones que los changes siguientes introduzcan. Como los nombres no cambian, agregar un modo no agrega condicionales en ningún lado.

En modo nativo la interfaz corre en su propio servidor de desarrollo, en otro puerto que el edge. Para que el origen siga siendo único —que es la propiedad de la que depende todo el diseño— ese servidor de desarrollo reenvía los espacios reservados a quien corresponda. Así la interfaz sigue pidiendo rutas relativas y no hay una versión distinta del cliente HTTP para desarrollar.

La contrapartida es que el modo nativo necesita alcanzar desde el host los servicios de terceros de los que depende, lo que obliga a exponerlos. Se acepta con una regla: se expone un servicio de terceros cuando el modo nativo lo alcanza, y nunca un servicio propio del proyecto, que siempre entra por el edge.

**Alternativa descartada:** documentar el modo nativo en el README sin especificarlo ni verificarlo, que es lo que suele pasar. Se descarta porque un flujo de trabajo que nadie verifica se rompe en silencio, y se rompe justo cuando alguien lo necesita; y porque sin el invariante de los nombres, cada modo iría acumulando sus propias variables hasta que el código tuviera que distinguirlos.

## Risks / Trade-offs

**La herramienta de sustitución de variables puede no estar en la imagen base elegida** → La tarea de implementación verifica su presencia antes de depender de ella y, si falta, la instala explícitamente en el `Dockerfile` del frontend. No se asume disponible por venir de una imagen conocida.

**El entrypoint del frontend es un script de shell y el entorno de desarrollo es Windows** → Un final de línea CRLF dentro de la imagen hace fallar el arranque con un error que no menciona los finales de línea, que es de los más difíciles de diagnosticar. El `.gitattributes` del repositorio ya declara `*.sh text eol=lf`, así que la mitigación está en su lugar; lo que queda es verificar que la imagen arranque desde un clon hecho en Windows en vez de asumirlo.

**Dos capas de nginx pueden derivar en configuración de cacheo y de cabeceras duplicada o contradictoria** → La regla de reparto de D1 es la que gobierna: ruteo y cacheo en el edge, entrega de estáticos en el frontend. Cualquier directiva que aparezca en las dos capas es señal de que algo está en el lugar equivocado.

**El healthcheck de este change solo prueba que el proceso del backend responde** → No dice nada sobre la base de datos, porque en este alcance el backend no se conecta. `add-backend-data-layer` extiende la verificación para que cubra la conectividad, y hasta entonces una salud satisfactoria no debe leerse como que el sistema completo está operativo.

**Docker pasa a ser requisito del flujo de trabajo local** → Se mitiga manteniendo viable el flujo nativo: el backend con `uv` y el frontend con su servidor de desarrollo pueden correr en el host apuntando a los servicios del compose. Lo que Docker vuelve obligatorio es reproducir el entorno completo, no desarrollar.

**Fijar versiones exactas retrasa los parches de seguridad** → Aceptado y ya argumentado en D6. La mitigación es que el bump sea una acción explícita y no una sorpresa.

## Migration Plan

No hay despliegue previo ni datos que migrar: el proyecto no está en ningún servidor. La migración es de flujo de trabajo, y es aditiva. Los archivos que este change introduce no reemplazan nada, así que el flujo anterior —`uv run` para el backend y `pnpm dev` para el frontend— sigue funcionando durante y después del cambio, ahora con la opción de apuntar a un Postgres que el compose provee en lugar de uno instalado a mano.

El rollback es revertir el commit: al desaparecer los archivos de infraestructura, el repositorio queda como estaba. Ningún estado externo queda huérfano salvo el volumen de datos de Postgres, que se elimina con el comando de limpieza del compose.

## Open Questions

Ninguna. Las dos que el diseño tuvo abiertas se cerraron antes de terminarlo, y ninguna decisión quedó apoyada en un supuesto sin verificar.

**Resueltas durante la redacción**

- **Cuándo y cómo el edge termina TLS.** La cerró un dato del usuario: los servicios corren en un VPS gestionado por Dokploy con Cloudflare delante del dominio. Verificado en la documentación de la plataforma, su proxy termina TLS con certificados que emite y renueva por su cuenta, y alcanza los contenedores por la red de Docker. TLS deja de ser un problema del proyecto y pasa a Non-Goals, y de paso corrigió D7: el compose base no publica ningún puerto al host.
- **Si el nginx del frontend termina siendo innecesario.** La cerró el propio diseño al examinar las tres formas de colapsar las dos capas. La decisiva es que el entrypoint que resuelve la configuración en runtime tiene que vivir donde se sirven los archivos, así que colapsar mudaría esa responsabilidad al edge, que es justo lo que D1 evita. No es un costo transitorio sino una consecuencia, y quedó escrito dentro de D1.
