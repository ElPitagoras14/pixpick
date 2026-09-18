# account-quota Specification

## Purpose

Gobierna cuánto almacenamiento puede ocupar una persona y cómo lo conoce: de dónde sale el límite, qué bytes se cuentan y cuáles no, a quién se le imputan los de un álbum que otros ven, y en qué niveles se puede consultar el consumo. No se solapa con `photo-upload`, que gobierna el acto de subir y es donde el límite se hace valer; aquí se define qué es el límite, allá qué pasa cuando se alcanza.

## Requirements

### Requirement: Cada persona tiene el mismo límite de almacenamiento, declarado en el entorno

El almacenamiento que una persona puede ocupar SHALL tener un máximo declarado en la configuración del entorno. El máximo SHALL ser el mismo para todas las personas: no hay cuentas con más espacio que otras, ni forma de ampliarlo para una en particular. Cambiar su valor SHALL NOT requerir modificar el código.

#### Scenario: El límite sale de la configuración

- **WHEN** se cambia el valor declarado en el entorno y se vuelve a levantar el proyecto
- **THEN** el espacio disponible de cada persona pasa a medirse contra el valor nuevo

#### Scenario: El límite no distingue entre personas

- **WHEN** se comparan los límites de dos personas distintas
- **THEN** son el mismo

### Requirement: Se cuenta el original de cada foto y nada más

El consumo de una persona SHALL ser la suma del tamaño de los originales de las fotos que están en sus álbumes. Una foto disponible SHALL contar su tamaño real, el verificado al confirmarla. Una foto a la espera de confirmarse con su permiso vigente SHALL contar el tamaño declarado al pedirlo, porque de lo contrario pedir permisos repetidamente permitiría superar el límite entre varios lotes simultáneos. Una foto cuyo permiso venció SHALL NOT contar, porque ya no puede completarse.

SHALL NOT contarse ninguna representación derivada de una foto. Esas no ocupan almacenamiento propio del proyecto: se producen al pedido y lo que las conserva se puede descartar sin pérdida. Contarlas haría que el consumo de una persona cambiara sin que ella hiciera nada.

#### Scenario: Una foto a la espera ya ocupa espacio

- **WHEN** se pide permiso para subir una foto y todavía no se confirma
- **THEN** el consumo de la persona ya incluye el tamaño declarado de esa foto

#### Scenario: Un permiso vencido deja de ocupar espacio

- **WHEN** un permiso vence sin que se haya subido el archivo
- **THEN** el consumo de la persona vuelve a no incluir esa foto

#### Scenario: Confirmar reemplaza lo declarado por lo real

- **WHEN** una foto se confirma
- **THEN** el consumo pasa a contar su tamaño real en lugar del declarado

#### Scenario: Ver fotos no cambia el consumo de nadie

- **WHEN** se ven las fotos de un álbum en cualquiera de sus representaciones
- **THEN** el consumo de su dueño es el mismo antes y después

### Requirement: El consumo de un álbum se le imputa a su dueño

Las fotos de un álbum SHALL contar contra el límite de quien lo posee, sin importar quién más pueda verlo o calificarlo. Compartir un álbum SHALL NOT trasladar consumo a quien lo recibe, y calificar fotos ajenas SHALL NOT afectar el consumo de quien califica.

#### Scenario: Recibir un álbum compartido no consume espacio propio

- **WHEN** una persona accede a un álbum compartido y califica sus fotos
- **THEN** su propio consumo no cambia
- **AND** el del dueño tampoco

### Requirement: El dueño puede consultar su consumo en tres niveles

El consumo SHALL poder consultarse en tres niveles: el total de la persona junto con su límite, lo que ocupa cada uno de sus álbumes, y lo que ocupa cada foto de un álbum suyo. Los tres niveles SHALL responder al estado del momento en que se los pide.

El total SHALL ser accesible únicamente a la persona a la que corresponde. El consumo de un álbum y el de sus fotos SHALL ser accesibles únicamente a su dueño: para quien accede a un álbum compartido, esa información SHALL NOT estar disponible, porque no es su espacio ni puede hacer nada al respecto.

#### Scenario: El total acompaña al límite

- **WHEN** una persona consulta su consumo total
- **THEN** obtiene cuánto ocupa y cuánto es su límite
- **AND** con esos dos valores puede saber cuánto le queda

#### Scenario: Quien no es dueño no accede al consumo del álbum

- **WHEN** alguien que accede a un álbum compartido intenta conocer lo que ocupa ese álbum o sus fotos
- **THEN** no obtiene esa información

#### Scenario: Lo consultado refleja el momento

- **WHEN** se elimina una foto y se vuelve a consultar el consumo
- **THEN** el valor ya no la incluye

### Requirement: El límite condiciona agregar, nunca lo ya guardado

El límite SHALL condicionar únicamente la incorporación de fotos nuevas. Una persona que lo alcanzó SHALL conservar todo lo suyo y SHALL poder seguir viendo, calificando, compartiendo y eliminando con normalidad; lo único que SHALL rechazarse es agregar más.

Una cuenta que supera el límite —porque el límite se redujo después de que sus fotos ya estaban— SHALL conservarlas todas. SHALL NOT eliminarse nada de forma automática por haber alcanzado o superado el límite, en ningún caso. Eliminar fotos SHALL volver a habilitar la incorporación en cuanto quede espacio.

#### Scenario: Estar lleno no rompe nada de lo guardado

- **WHEN** una persona alcanza su límite
- **THEN** sus álbumes se siguen viendo, calificando y compartiendo igual que antes

#### Scenario: Reducir el límite no borra nada

- **WHEN** se reduce el límite por debajo de lo que una cuenta ya ocupa
- **THEN** esa cuenta conserva todas sus fotos
- **AND** lo único que se le rechaza es agregar fotos nuevas

#### Scenario: Liberar espacio vuelve a habilitar la incorporación

- **WHEN** se eliminan fotos hasta quedar por debajo del límite
- **THEN** se puede volver a agregar fotos hasta alcanzarlo de nuevo
