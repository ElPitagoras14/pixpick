## Why

El único techo de almacenamiento que existe hoy es por persona. Nada acota el total: el techo real de la instalación es "el límite de una cuenta por la cantidad de cuentas que existan", y como cualquiera con una cuenta de Google puede entrar, esa cantidad no la decide nadie. Con el proveedor cloud eso se factura —el free tier de R2 son 10 GB y no hay ningún corte de gasto del lado de Cloudflare que lo frene—, y con el local llena el disco de quien lo hospeda.

Y del lado de quien mira pasa lo mismo que pasaba con el consumo de la cuenta antes de `add-account-quota`: no hay forma de saber cuán cerca del techo está la instalación. Quien la hospeda se entera el día que llega la factura, y quien la usa se entera el día que un archivo no recibe permiso por un motivo que no depende de él.

## What Changes

- **La instancia entera tiene un límite de almacenamiento**, de 6 GiB, declarado en la configuración del entorno al lado del límite por cuenta y del máximo de fotos por álbum.
- **Ese límite no impide tener cuenta.** Registrarse, iniciar sesión, ver, calificar, compartir y eliminar siguen funcionando igual con la instancia llena. Lo único que se rechaza es incorporar fotos nuevas. Un límite de capacidad que además cierra la puerta castiga a quien todavía no ocupó nada.
- **Cuenta lo mismo que ya cuenta el límite por cuenta**: los originales de las fotos, las disponibles con su tamaño real y las que esperan confirmación con su permiso vigente por el declarado, sin las vencidas y sin ninguna representación derivada. Es la misma suma, sin el filtro por dueño.
- **El límite por cuenta baja de 150 MiB a 120 MiB.** Es un cambio de valor en la configuración y no de comportamiento: `account-quota` ya establece que reducir el límite no borra nada, así que quien hoy esté entre ambos valores conserva todas sus fotos y solo deja de poder agregar.
- **Conceder pasa a evaluar tres límites y no dos.** Un archivo recibe permiso solo si entra en el máximo del álbum, en el espacio de la cuenta y en el de la instancia.
- **El motivo del rechazo distingue cuál de los tres se alcanzó.** Que la instancia esté llena no se resuelve como que lo esté la cuenta: eliminar fotos propias libera espacio en ambas, pero cuando a la cuenta le sobra lugar y a la instancia no, no hay nada que quien pide pueda hacer, y decirle que borre fotos sería mandarlo a hacer algo inútil.
- **Cuando los dos se alcanzaron a la vez gana el de la cuenta**, porque es sobre el que quien pide puede actuar. El motivo de instancia aparece solo cuando su cuenta tiene lugar y la instancia no.
- **La primera pantalla después de iniciar sesión muestra qué porcentaje está ocupado de la instancia**, junto al consumo de la cuenta que ya muestra. Lo ve todo el mundo: no hay rol de administrador en el producto, y el estado del espacio compartido es lo que explica un rechazo que no depende de quien lo recibe. Nunca el total ni el límite en bytes: esos números describen la capacidad real de la instalación, no algo que quien pide subir necesite para decidir nada que el porcentaje no le diga ya.
- **Evaluar el total de la instancia obliga a serializar entre personas distintas.** Hoy conceder excluye por persona, que alcanza para un límite de la persona; dos lotes simultáneos de dos dueños distintos leerían el mismo total y podrían superarlo entre ambos sin verse.

### Fuera de alcance

- **Un rol de administrador.** El producto no tiene ninguno y este change no lo introduce: el porcentaje de la instancia lo ve todo el mundo o no lo ve nadie, y se eligió que lo vea todo el mundo.
- **Cerrar el registro o el inicio de sesión al llenarse.** Es una decisión de producto distinta, con su propia pregunta sobre qué ve quien no puede entrar. El pedido acá es explícito en lo contrario: se puede tener cuenta aunque no se pueda subir.
- **Borrar nada automáticamente al llegar al tope**, ni de la cuenta que más ocupa ni de la más vieja. Lo mismo que `account-quota` ya establece para el límite por cuenta, por las mismas razones.
- **Avisar cuando falte poco.** El porcentaje va a estar a la vista; un aviso con su umbral es una decisión aparte.
- **Cuotas distintas por persona o por instancia según el proveedor.** El límite es uno solo y su valor sale de la configuración, igual que el de la cuenta.
- **Cortar el gasto del lado de Cloudflare.** R2 no ofrece un corte duro de facturación, solo notificaciones; esta capability es justamente la defensa que reemplaza al corte que el proveedor no da.

## Capabilities

### New Capabilities

- `instance-quota`: gobierna cuánto almacenamiento puede ocupar la instalación entera y cómo se conoce ese estado. Define que el límite existe y de dónde sale su valor, qué bytes cuentan —los mismos que cuenta el límite por cuenta, sin el filtro por dueño—, que alcanzarlo condiciona incorporar y nada más, y que el consumo de la instancia es visible para cualquiera que use el producto. Es una capability propia y no un requirement más de `account-quota` porque el sujeto es otro: `account-quota` gobierna el espacio de una persona, y su regla central es que el límite es igual para todas y que el consumo de un álbum se le imputa a su dueño. El de la instancia no es de nadie en particular, no se imputa, y no se consulta en los tres niveles que aquella define.

### Modified Capabilities

- `photo-upload`: el requirement que hoy dice que conceder evalúa dos límites y distingue cuál se alcanzó pasa a evaluar tres. Gana el límite de la instancia como tercero, la regla de precedencia entre el de la cuenta y el de la instancia cuando los dos se alcanzaron, y la exigencia de exclusión entre personas distintas —hoy el requirement solo exige que dos lotes de la misma persona en álbumes distintos no se superen entre sí, que es lo que alcanzaba para un límite de la persona—.

- `upload-feedback`: el requirement que gobierna cómo se lee el motivo de un archivo que no terminó bien hoy contempla el motivo que trae un dato para corregir la situación y el que admite reintentar. El rechazo por instancia llena no es ninguno de los dos: no hay dato que le sirva a quien pide y reintentar no cambia nada hasta que otra persona libere espacio. Gana que un motivo que quien lo recibe no puede resolver SHALL decirlo como tal, en lugar de indicarle una acción que no va a servir de nada.

- `app-entry`: el requirement de la primera pantalla después de iniciar sesión enumera las tres cosas que muestra, una de ellas el espacio de la cuenta contra su límite. Pasa a enumerar cuatro, con el de la instancia entre ellas.

`account-quota` no se modifica. Que su límite baje de 150 MiB a 120 MiB no toca ninguno de sus requirements: el spec dice que el máximo está declarado en la configuración del entorno y que cambiar su valor no requiere modificar el código, así que el cambio de valor es exactamente el caso que ese requirement ya describe. Y el límite de la instancia no entra ahí porque esa capability define el espacio de una persona: agregarle un techo que no es de nadie la obligaría a gobernar dos sujetos distintos bajo el mismo propósito.

## Impact

**Base de datos**

Ninguna columna nueva y ninguna migración. El total de la instancia es la misma suma que ya se calcula por cuenta, sin la condición de dueño. Queda para el diseño si esa suma sobre todas las fotos de la instalación se sostiene calculada al momento, como la de la cuenta, o necesita otra cosa.

**Concurrencia**

Es el punto delicado del change, por la misma razón que lo fue en `add-account-quota` y un escalón más arriba. Ahí el punto de exclusión pasó del álbum a la persona porque el límite abarcaba todos los álbumes de un dueño. Acá el límite abarca a todas las personas, así que la exclusión por persona ya no alcanza: dos dueños distintos concediendo a la vez no se ven entre sí. El diseño tiene que resolver cómo se serializa eso sin volver la concesión un cuello de botella, y qué relación guarda con el bloqueo por persona que ya existe.

**Backend**

- `packages/photos/config.py` y `.env.example`: el límite de la instancia, junto a los dos que ya viven ahí, y el valor nuevo del límite por cuenta.
- `packages/quota/repository.py`: el total de la instancia, reusando las condiciones que ya definen qué bytes cuentan, para que los dos totales no puedan contar cosas distintas.
- `packages/photos/service.py`: la tercera evaluación al conceder, con su precedencia, y el punto de exclusión que abarque a toda la instancia.
- `packages/photos/schemas.py` y `responses.py`: el motivo nuevo entre los que un archivo sin permiso puede traer. Alcanza a todo cliente que hoy trate la lista de motivos como cerrada.
- Un recurso nuevo para consultar el consumo de la instancia, que no cuelga del de la cuenta porque no es información de una persona.

**Interfaz**

- La primera pantalla después de iniciar sesión muestra el segundo medidor.
- El medidor que hoy existe se usa para las dos cosas en lugar de duplicarse, porque la barra, el porcentaje y el estado de lleno son idénticos y lo único que cambia es qué nombra y qué dice cuando no queda lugar.
- La cola de subida gana el texto del motivo nuevo, junto a los dos que ya muestra.

**Precedencia**

Depende de `add-account-quota`, que ya está aplicado: reusa su forma de contar y el recurso donde se consulta el consumo. No depende de los changes de rediseño en curso, aunque toca la misma pantalla que `redesign-landing-page` deja intacta —el medidor vive después de iniciar sesión, y ese change gobierna lo anterior—.
