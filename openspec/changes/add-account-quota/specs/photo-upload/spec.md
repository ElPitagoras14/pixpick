## ADDED Requirements

### Requirement: Conceder evalúa el límite del álbum y el de la cuenta, y distingue cuál se alcanzó

Al conceder permisos de subida SHALL evaluarse dos límites independientes: el máximo de fotos del álbum y el espacio disponible de la cuenta de su dueño. Un archivo SHALL recibir permiso solo si entra en los dos.

Cuando un archivo no reciba permiso, la respuesta SHALL indicar cuál de los dos límites lo impidió. No son intercambiables y se resuelven distinto: quedarse sin lugar en el álbum se resuelve creando otro álbum, y quedarse sin espacio en la cuenta no se resuelve creando nada, sino eliminando algo.

La evaluación del espacio de la cuenta SHALL considerar todos los álbumes de esa persona, y no solo aquel al que se está subiendo. Dos lotes pedidos al mismo tiempo en álbumes distintos de la misma persona SHALL NOT poder superar el límite entre ambos por no haberse visto entre sí.

#### Scenario: Un archivo necesita entrar en los dos límites

- **WHEN** un archivo entra en el espacio disponible de la cuenta pero el álbum ya está lleno
- **THEN** no recibe permiso

#### Scenario: El motivo del rechazo identifica el límite

- **WHEN** un archivo no recibe permiso porque no hay espacio en la cuenta
- **THEN** la respuesta lo distingue de un rechazo por álbum lleno
- **AND** indica cuánto espacio queda

#### Scenario: El espacio se mide sobre toda la cuenta

- **WHEN** una persona sube a un álbum vacío teniendo su cuenta llena por fotos de otros álbumes
- **THEN** no recibe permiso
- **AND** el motivo es el espacio de la cuenta, no el álbum

#### Scenario: Dos lotes simultáneos en álbumes distintos no superan el límite

- **WHEN** se piden a la vez dos lotes en dos álbumes de la misma persona y entre los dos excederían su espacio
- **THEN** lo concedido entre ambos no supera el límite

### Requirement: Un álbum admite una cantidad máxima de fotos, configurable, y un lote que no entra se concede en parte

La cantidad de fotos que un álbum admite SHALL tener un máximo declarado en la configuración del entorno. El máximo SHALL evaluarse al conceder.

Un lote que no entre completo SHALL concederse en parte: SHALL recorrerse los archivos en el orden en que se pidieron y SHALL emitirse permiso para cada uno que entre, y los que no entren SHALL devolverse sin permiso, con su motivo y con cuánto lugar queda. SHALL NOT rechazarse el lote completo por esta causa. Quedarse sin lugar no es un error de quien pide sino un hecho del estado del álbum, y obligarlo a rehacer la selección entera no le da nada que no pueda decidir viendo qué entró y qué no.

El cómputo SHALL contar las fotos disponibles más las que están a la espera de confirmarse con su permiso vigente, y SHALL NOT contar las que quedaron a la espera con el permiso vencido, porque esas ya no pueden completarse. Sin contar las que están a la espera, pedir concesiones repetidamente permitiría superar el máximo.

El máximo SHALL condicionar únicamente la incorporación de fotos nuevas. Un álbum que ya supera el máximo —porque el máximo se redujo después— SHALL conservar todas sus fotos y SHALL seguir siendo legible y utilizable en todo sentido; lo único que SHALL rechazarse es agregarle más. Eliminar fotos de un álbum que supera el máximo SHALL volver a habilitar la incorporación en cuanto quede espacio.

#### Scenario: Un lote que excede el máximo se concede en parte

- **WHEN** se pide un lote más grande que el lugar que queda en el álbum
- **THEN** reciben permiso los archivos que entran, en el orden en que se pidieron
- **AND** los demás se devuelven sin permiso, indicando el motivo y cuánto lugar quedaba

#### Scenario: Un álbum sin lugar no concede ninguno

- **WHEN** se pide un lote en un álbum que ya alcanzó el máximo
- **THEN** ningún archivo del lote recibe permiso
- **AND** cada uno indica que el álbum está lleno

#### Scenario: Las fotos a la espera ocupan lugar

- **WHEN** se piden concesiones que llenan el álbum y, antes de confirmarlas, se piden más
- **THEN** el segundo pedido no recibe ningún permiso
- **AND** el álbum no supera el máximo

#### Scenario: Las esperas vencidas dejan de ocupar lugar

- **WHEN** un permiso vence sin que se haya subido el archivo
- **THEN** esa foto deja de contar para el máximo
- **AND** se puede volver a pedir una concesión en su lugar

#### Scenario: Reducir el máximo no toca los álbumes existentes

- **WHEN** se reduce el máximo por debajo de la cantidad de fotos de un álbum existente
- **THEN** el álbum conserva todas sus fotos
- **AND** sigue siendo legible y utilizable como cualquier otro
- **AND** solo se rechaza agregarle fotos nuevas

#### Scenario: Liberar espacio vuelve a habilitar la incorporación

- **WHEN** se eliminan fotos de un álbum que superaba el máximo hasta quedar por debajo
- **THEN** se puede volver a agregar fotos hasta el máximo

## REMOVED Requirements

### Requirement: Un álbum admite una cantidad máxima de fotos, configurable, que condiciona agregar y no lo ya guardado

**Reason**: Su regla central —"si el lote pedido haría que el álbum superara el máximo, SHALL rechazarse el lote completo"— deja de valer, y con ella su escenario "Un lote que excede el máximo se rechaza completo". No es una corrección de redacción: el comportamiento exigido es el opuesto, así que conservar el requirement con el mismo nombre dejaría un contrato cuyo título describe una regla que ya no rige. Lo reemplaza el requirement agregado más arriba, que conserva el máximo, su origen en la configuración y su cómputo, y cambia solo qué ocurre cuando un lote no entra.

**Migration**: Ninguna migración de datos: el máximo sigue siendo el mismo valor, declarado en la misma variable de entorno, y se computa igual —disponibles más pendientes vigentes—. Lo que cambia es la respuesta a un lote que no entra, de un rechazo total a una concesión parcial, así que todo cliente que asuma "pedí N permisos, recibo N o un error" tiene que pasar a leer qué se concedió y qué no. El único cliente del proyecto es su propia interfaz, y este change la actualiza.
