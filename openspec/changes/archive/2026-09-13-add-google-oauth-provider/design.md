## Context

El estado de partida es el puerto de identidad que dejó `add-auth-port-and-local-provider`: dos operaciones —producir la dirección de autorización y canjear el código por una identidad—, una identidad con forma fija donde el proveedor y el identificador de la persona son obligatorios, una sesión propia que no depende del proveedor, y un adapter local que recorre el ciclo completo y se niega a activarse fuera de desarrollo.

Este change es pequeño a propósito, y su tamaño es el resultado que interesa medir. Si el puerto está bien, lo único que hace falta es un archivo de adapter y configuración; si aparece cualquier otra cosa, es un hallazgo sobre aquel diseño y no una tarea de este change.

Hay un dato del contexto que reduce el trabajo más de lo esperado. La documentación del proveedor establece que cuando el token de identidad se recibe en el intercambio directo del código —por un canal cifrado en el que la aplicación se autentica con su secreto— no hace falta validar su firma, porque la confianza la da el canal. La validación sí es obligatoria cuando ese token se pasa a otros componentes, y en este diseño no se pasa a ninguno.

## Goals / Non-Goals

**Goals:**

- Que el change se agote en un adapter y su configuración, y que cualquier desvío se trate como un hallazgo.
- Que desarrollar siga sin requerir credenciales de terceros ni pantallas de consentimiento.
- Que una discrepancia de configuración externa se diagnostique en un minuto y no en una tarde.

**Non-Goals:**

- Vincular cuentas, otros proveedores, y pedir del proveedor cualquier cosa que no sea la identidad.
- Tocar la sesión, los endpoints, la interfaz o el esquema.
- Automatizar la creación de la aplicación en la consola del proveedor.

## Decisions

### D1 - No se verifica la firma del token, y la garantía queda explicitada en lugar de omitida

El token de identidad llega en el intercambio directo del código, sobre un canal cifrado en el que la aplicación se autentica con su secreto. Esa es la garantía de autenticidad y está documentada por el propio proveedor: verificar la firma sería redundante con lo que el canal ya asegura.

Lo importante no es la omisión sino la condición: la garantía vale **porque** la identidad no sale de ese canal. Por eso el spec exige que la consuma el mismo proceso que la obtuvo y que, si alguna vez tuviera que reenviarse, quien la reciba la verifique por su cuenta. Así la decisión queda atada a la propiedad que la sostiene, y el día que esa propiedad cambie el requirement dice qué hacer.

Sí se comprueban, sin verificar firma, que la audiencia del token corresponda a las credenciales configuradas y que el emisor sea el esperado. **No son controles de seguridad** —sin verificar la firma no lo serían— sino una comprobación de configuración: atrapan el caso de tener credenciales cruzadas entre dos aplicaciones registradas, que de otro modo se manifestaría como sesiones creadas contra el proyecto equivocado.

### D2 - Se piden los ámbitos mínimos, y eso también es una decisión de producto

Se piden identidad, perfil básico y correo. Nada más.

No es solo higiene de permisos: el conjunto de ámbitos determina literalmente lo que la pantalla de consentimiento le dice a la persona. Pedir lo mínimo produce una pantalla que menciona el nombre y el correo, que es aceptable para alguien que llegó desde un link para calificar fotos de un amigo. Pedir de más produce una pantalla más alarmante, y en algunos casos obliga a un proceso de revisión del proveedor. La primera impresión del producto para un invitado es esa pantalla.

### D3 - El adapter local no se reemplaza: pasa a ser el de desarrollo y el otro el de producción

Después de este change hay dos adapters y la variable de entorno elige uno por entorno. En desarrollo sigue el local, y eso mantiene barato lo que se abarató en su momento: probar el ciclo entero sin credenciales ajenas ni consentimiento.

Lo que hace segura esa convivencia es una decisión del change anterior: el adapter local se niega a activarse cuando el entorno no es de desarrollo. Sin esa negativa, tener dos adapters sería tener una puerta trasera esperando una variable mal puesta.

### D4 - El identificador de la persona es el del proveedor, nunca el correo

La identidad se ancla en el identificador opaco y estable que el proveedor asigna. El correo viaja como dato descriptivo y se refresca en cada inicio de sesión.

Ya está especificado, pero acá se vuelve concreto y conviene recordar por qué: un correo puede cambiar, y en una cuenta corporativa puede incluso reasignarse a otra persona. Anclar la identidad en él haría que dos personas distintas se confundan en una, que es la peor falla posible de un sistema de identidad.

### D5 - Nuestra dirección de retorno queda a la vista al arrancar, porque también vive fuera del repositorio

Cuando el proveedor activo requiere una dirección de retorno declarada externamente, el sistema deja registrada al arrancar la dirección que va a usar, derivada de la dirección pública configurada. Se trata de una dirección **nuestra**, que el proveedor necesita conocer.

Es una línea de registro y resuelve el problema más caro de este change: la dirección declarada en la consola del proveedor y la que el sistema construye tienen que coincidir carácter por carácter, viven en dos lugares distintos, y cuando no coinciden el error lo reporta el proveedor con un mensaje que no dice cuál esperaba el sistema. Tenerla a la vista convierte una tarde de conjeturas en una comparación.

### D6 - Las credenciales se validan al construir el adapter, no en el primer inicio de sesión

La selección de proveedor construye el adapter durante el arranque, y ahí es donde la ausencia de credenciales falla. Un servicio que arranca sin ellas y falla recién cuando alguien intenta entrar convierte un error de despliegue en un incidente para las personas.

La comprobación se hace únicamente sobre el proveedor activo, para que trabajar en desarrollo con el adapter local no exija tener configuradas credenciales que no se van a usar.

### D7 - Que alguien no acepte el consentimiento no es un error del sistema

El proveedor distingue un fallo de un rechazo: si la persona cierra la pantalla de consentimiento o decide no continuar, eso vuelve como un resultado normal del ciclo, no como una falla.

Se tratan distinto. Un rechazo devuelve a la persona a la pantalla de inicio de sesión sin ningún mensaje alarmante, porque no pasó nada malo — decidió no entrar. Un fallo real muestra un error accionable y deja el detalle en los registros del servidor. Confundirlos haría que una decisión legítima se vea como un problema de la aplicación.

### D8 - Las direcciones del proveedor se declaran en el código en vez de descubrirse

Son las direcciones **del proveedor** —a dónde se envía a la persona a autorizar y contra dónde se canjea el código—, que somos nosotros quienes necesitamos conocer. Es el sentido inverso al de D5, que trata de una dirección nuestra que el proveedor necesita conocer, y el riesgo también es otro: allá el problema es que dos copias no coincidan, acá que una copia quede desactualizada.

El proveedor publica un documento de descubrimiento del que se pueden leer. Se opta por declararlas directamente, anotando de dónde salieron.

Descubrirlas agrega una petición de red en cada arranque —y por lo tanto una dependencia de red para poder arrancar— a cambio de mantenerse al día con valores que cambian muy rara vez y cuyo cambio, si ocurriera, sería anunciado. La forma de enterarse de un cambio así no es una petición en cada arranque sino leer el aviso.

### D9 - No se somete la aplicación a verificación, y es D2 quien lo permite

La aplicación se publica sin pasar por el proceso de revisión del proveedor. La regla documentada es que solo deben verificarse las aplicaciones que piden ámbitos clasificados como sensibles o restringidos; con ámbitos no sensibles la verificación no es obligatoria.

Lo interesante es de dónde sale el permiso: los ámbitos que pedimos son los básicos de identidad, y los pedimos mínimos por la razón de D2 —que la pantalla de consentimiento sea aceptable para alguien que llegó desde un link a calificar fotos—. Esa misma elección, hecha por un motivo de producto, es la que evita el trámite. Si se hubiera pedido de más, habría dos costos en lugar de uno: una pantalla más alarmante y una revisión que aprobar.

La comprobación no se deduce: la consola del proveedor etiqueta cada ámbito con su categoría al configurar el consentimiento, así que confirmar que los tres figuran como no sensibles es mirar la pantalla. Queda como tarea de la puesta en marcha.

**Si resultara que no alcanza**, la salida no es apurar una revisión sino quedarse en modo de prueba con las personas declaradas explícitamente, que es suficiente para compartir entre conocidos y deja de serlo si el álbum se comparte con desconocidos. Es un plan de contingencia, no el plan.

## Risks / Trade-offs

**La dirección de retorno vive en dos lugares que tienen que coincidir** → Es el riesgo principal del change y la mitigación es D5. Conviene además verificar la coincidencia como parte de la puesta en marcha y no la primera vez que alguien intenta entrar.

**El secreto de la aplicación es el primer secreto real del proyecto** → Hasta ahora pixpick no tenía ninguno: la sesión usa un valor aleatorio sin firma y el estado del ciclo se compara por igualdad. Este change introduce uno que solo puede vivir en el entorno. Lo que ya lo protege del error más común es un requirement existente: la configuración que llega al navegador se limita a valores públicos, así que el secreto no tiene camino hacia el cliente aunque alguien se distraiga.

**Las pruebas automatizadas no pueden ejercitar al proveedor real** → Cubren lo que sí es nuestro: cómo se construye la dirección de autorización, qué identidad produce un canje, y qué pasa ante un rechazo y ante un fallo. El ciclo contra el proveedor real se verifica a mano una vez, y conviene que esa verificación quede anotada como tarea en lugar de asumirse.

**Cambiar un entorno de proveedor local a proveedor externo crea usuarios nuevos** → Es consecuencia de anclar la identidad en el par proveedor e identificador, y en un entorno de producción no puede ocurrir, porque el adapter local se niega a arrancar ahí. El caso a vigilar es un entorno de desarrollo que se apunte a datos que no son de desarrollo.

## Migration Plan

No hay migración: este change no toca el esquema ni agrega datos. Poner en marcha el proveedor externo en un entorno es configurar tres cosas —el identificador de la aplicación, su secreto y la dirección de retorno declarada en la consola— y cambiar la variable que elige el proveedor.

El rollback es volver la variable a su valor anterior. Las sesiones abiertas con el proveedor externo siguen siendo válidas mientras no venzan, porque la sesión es propia y no depende del proveedor; lo que deja de funcionar es iniciar sesiones nuevas por ese camino. Esa independencia entre la sesión y el proveedor es exactamente lo que el puerto buscaba, y es la razón por la que revertir este change no expulsa a nadie.

## Open Questions

Ninguna. La única que había quedado abierta se cerró al verificar la regla del proveedor, y resultó no ser una decisión sino una consecuencia de otra ya tomada.

**Resueltas durante la redacción**

- **Si conviene someter la aplicación al proceso de revisión del proveedor.** No hace falta, y quedó como D9. La cerró un criterio documentado —solo las aplicaciones que piden ámbitos sensibles o restringidos deben verificarse— aplicado a ámbitos que ya habíamos elegido mínimos en D2 por un motivo distinto. La comprobación de que los tres figuran efectivamente como no sensibles queda como tarea, porque la consola los etiqueta y mirarla es más confiable que deducirlo.
- **Si hay que verificar criptográficamente el token de identidad.** Parecía la única complejidad real del change —firma, emisor, audiencia y vencimiento contra claves públicas que rotan— y la cerró la documentación del proveedor: recibido en el intercambio directo, autenticado con el secreto de la aplicación, el canal es la garantía. Eso eliminó la necesidad de una biblioteca de criptografía y del manejo de claves rotativas, y dejó al change sin ninguna dependencia nueva. La contrapartida quedó escrita como requirement en D1: la garantía vale porque la identidad no sale de ese canal.
- **Si leer las direcciones del proveedor del documento de descubrimiento.** Se cerró en D8 comparando qué se gana con qué se paga: mantenerse al día con valores que cambian rara vez, a cambio de una dependencia de red para poder arrancar.
- **Qué hacer cuando alguien no acepta el consentimiento.** Surgió al enumerar los desenlaces del ciclo y se cerró en D7 distinguiendo un rechazo de un fallo. No es una diferencia técnica sino de trato: decidir no entrar es una decisión legítima y no debería verse como un problema de la aplicación.
