## Purpose

Gobierna cuánto almacenamiento puede ocupar la instancia entera —la suma de todas las cuentas que viven en ella—: de dónde sale ese techo, qué bytes cuentan para él, qué condiciona alcanzarlo y quién puede ver cuán cerca está. No se solapa con `account-quota`, que gobierna el espacio de una persona y se lo imputa a alguien; acá el sujeto es la instalación, que no es de nadie y por eso no se reparte ni se consulta por dueño.

## ADDED Requirements

### Requirement: La instancia entera tiene un límite de almacenamiento, declarado en el entorno

El almacenamiento que la instancia puede ocupar en total SHALL tener un máximo declarado en la configuración del entorno. Cambiar su valor SHALL NOT requerir modificar el código.

El máximo SHALL ser uno solo para toda la instancia y SHALL NOT derivarse de la cantidad de cuentas ni moverse cuando se crean o se eliminan. Un techo que creciera con cada cuenta nueva no sería un techo: es justamente lo que este límite existe para evitar, porque quién se registra no lo decide quien hospeda.

#### Scenario: El límite sale de la configuración

- **WHEN** se cambia el valor declarado en el entorno y se vuelve a levantar el proyecto
- **THEN** el espacio disponible de la instancia pasa a medirse contra el valor nuevo

#### Scenario: Crear cuentas no mueve el límite

- **WHEN** se crean cuentas nuevas en la instancia
- **THEN** el límite de la instancia sigue siendo el mismo

### Requirement: Cuenta lo mismo que el límite de una cuenta, sin distinguir de quién es

El consumo de la instancia SHALL ser la suma del consumo de todas sus cuentas, computado con las mismas reglas que `account-quota` fija para una sola: el original de cada foto y nada más, su tamaño real una vez confirmada, el declarado mientras espera con su permiso vigente, nada cuando el permiso venció, y ninguna representación derivada.

Las dos sumas SHALL contar lo mismo y diferir únicamente en el alcance. Si una foto cuenta para el consumo de su dueño, SHALL contar para el de la instancia, y si no cuenta para aquel, SHALL NOT contar para este. Que las dos respondan a criterios distintos haría que un archivo rechazado por la instancia no apareciera en ninguna cuenta.

#### Scenario: El total abarca a todas las personas

- **WHEN** dos personas distintas tienen fotos en sus álbumes
- **THEN** el consumo de la instancia incluye las de ambas

#### Scenario: Una foto a la espera ya ocupa espacio de la instancia

- **WHEN** se pide permiso para subir una foto y todavía no se confirma
- **THEN** el consumo de la instancia ya incluye el tamaño declarado de esa foto

#### Scenario: Un permiso vencido deja de ocupar espacio de la instancia

- **WHEN** un permiso vence sin que se haya subido el archivo
- **THEN** el consumo de la instancia vuelve a no incluir esa foto

#### Scenario: Las representaciones derivadas no cuentan

- **WHEN** se ven las fotos de cualquier álbum en cualquiera de sus representaciones
- **THEN** el consumo de la instancia es el mismo antes y después

### Requirement: El límite de la instancia condiciona incorporar, y nunca tener cuenta ni lo ya guardado

Alcanzar el límite de la instancia SHALL condicionar únicamente la incorporación de fotos nuevas. SHALL NOT impedir crear una cuenta, iniciar sesión, ni usar el producto en todo lo demás: ver, calificar, compartir y eliminar SHALL seguir funcionando igual para todas las cuentas. Cerrar la puerta a quien todavía no ocupó nada no libera un solo byte.

SHALL NOT eliminarse nada de forma automática por haber alcanzado o superado el límite, ni de la cuenta que más ocupa, ni de la más antigua, ni de ninguna otra. Una instancia que supera el límite —porque el límite se redujo después de que sus fotos ya estaban— SHALL conservarlas todas.

El espacio SHALL ser común: liberar espacio en cualquier cuenta SHALL volver a habilitar la incorporación para todas, y no solo para aquella que lo liberó.

#### Scenario: Con la instancia llena se puede tener cuenta igual

- **WHEN** alguien crea su cuenta e inicia sesión mientras la instancia está llena
- **THEN** entra y usa el producto con normalidad
- **AND** lo único que se le rechaza es agregar fotos

#### Scenario: Estar llena no rompe nada de lo guardado

- **WHEN** la instancia alcanza su límite
- **THEN** los álbumes de todas las cuentas se siguen viendo, calificando y compartiendo igual que antes

#### Scenario: Reducir el límite no borra nada

- **WHEN** se reduce el límite por debajo de lo que la instancia ya ocupa
- **THEN** todas las cuentas conservan todas sus fotos
- **AND** lo único que se rechaza es agregar fotos nuevas

#### Scenario: Liberar espacio en una cuenta habilita a las demás

- **WHEN** una persona elimina fotos hasta que la instancia queda por debajo de su límite
- **THEN** cualquier otra persona puede volver a agregar fotos

### Requirement: Cuánto ocupa la instancia es visible para cualquiera que la use

El estado del espacio de la instancia SHALL poder consultarlo cualquier persona con la sesión iniciada. SHALL NOT exigir ser dueño de nada ni pertenecer a una categoría distinta de la de cualquier otra persona: el producto no define ninguna, y el estado del espacio común es lo que explica un rechazo que quien lo recibe no provocó ni puede resolver.

Lo consultado SHALL ser únicamente el porcentaje ocupado, redondeado. SHALL NOT revelarse el total ni el límite en bytes: son la capacidad real de la instalación, y ese dato no le sirve a quien pide más que para saber qué tan cerca está de llenarse -- que el porcentaje ya responde -- mientras que expuesto en bytes describe la infraestructura de quien la hospeda a cualquiera con una sesión iniciada. SHALL NOT revelarse tampoco cuánto ocupa cada cuenta ni a quién pertenece lo ocupado, porque `account-quota` reserva el consumo de una persona a esa persona y un desglose de la instancia lo expondría por la puerta de al lado.

Lo consultado SHALL responder al estado del momento en que se lo pide.

#### Scenario: Cualquiera con sesión ve el estado de la instancia

- **WHEN** una persona cualquiera consulta el consumo de la instancia
- **THEN** obtiene el porcentaje ocupado

#### Scenario: El total y el límite no viajan en la respuesta

- **WHEN** se consulta el consumo de la instancia
- **THEN** no se obtiene el total ni el límite en bytes, solo el porcentaje

#### Scenario: El total no dice de quién es lo ocupado

- **WHEN** se consulta el consumo de la instancia
- **THEN** no se obtiene cuánto ocupa ninguna cuenta en particular

#### Scenario: Lo consultado refleja el momento

- **WHEN** se eliminan fotos y se vuelve a consultar el consumo de la instancia
- **THEN** el valor ya no las incluye
