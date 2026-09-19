## ADDED Requirements

### Requirement: Conceder evalúa el límite del álbum, el de la cuenta y el de la instancia, y distingue cuál se alcanzó

Al conceder permisos de subida SHALL evaluarse tres límites independientes: el máximo de fotos del álbum, el espacio disponible de la cuenta de su dueño y el espacio disponible de la instancia. Un archivo SHALL recibir permiso solo si entra en los tres.

Cuando un archivo no reciba permiso, la respuesta SHALL indicar cuál de los tres límites lo impidió. No son intercambiables y se resuelven distinto: quedarse sin lugar en el álbum se resuelve creando otro álbum, quedarse sin espacio en la cuenta se resuelve eliminando algo propio, y quedarse sin espacio en la instancia no lo resuelve quien pide, porque el espacio que falta puede no ser suyo.

Cuando el de la cuenta y el de la instancia se hayan alcanzado los dos, el motivo informado SHALL ser el de la cuenta. Es el único de los dos sobre el que quien pide puede actuar, y eliminar fotos propias libera espacio en los dos a la vez; informar el de la instancia mientras la cuenta también está llena escondería la acción que sí sirve.

La evaluación del espacio de la cuenta SHALL considerar todos los álbumes de esa persona, y no solo aquel al que se está subiendo. Dos lotes pedidos al mismo tiempo en álbumes distintos de la misma persona SHALL NOT poder superar el límite entre ambos por no haberse visto entre sí.

La evaluación del espacio de la instancia SHALL considerar las fotos de todas las cuentas. Dos lotes pedidos al mismo tiempo por personas distintas SHALL NOT poder superar el límite de la instancia entre ambos por no haberse visto entre sí. Es la misma exigencia que el párrafo anterior hace para una persona, un alcance más arriba: excluir por persona alcanza para un límite de la persona y no para uno que abarca a todas.

#### Scenario: Un archivo necesita entrar en los tres límites

- **WHEN** un archivo entra en el espacio disponible de la cuenta y en el de la instancia pero el álbum ya está lleno
- **THEN** no recibe permiso

#### Scenario: El motivo del rechazo identifica el límite

- **WHEN** un archivo no recibe permiso porque no hay espacio en la cuenta
- **THEN** la respuesta lo distingue de un rechazo por álbum lleno y de uno por instancia llena
- **AND** indica cuánto espacio queda

#### Scenario: El espacio se mide sobre toda la cuenta

- **WHEN** una persona sube a un álbum vacío teniendo su cuenta llena por fotos de otros álbumes
- **THEN** no recibe permiso
- **AND** el motivo es el espacio de la cuenta, no el álbum

#### Scenario: La instancia llena rechaza aunque la cuenta tenga lugar

- **WHEN** una persona con espacio de sobra en su cuenta pide subir a un álbum con lugar, estando la instancia llena
- **THEN** no recibe permiso
- **AND** el motivo es el espacio de la instancia, y no el de su cuenta ni el del álbum

#### Scenario: La cuenta llena gana sobre la instancia llena

- **WHEN** una persona con la cuenta llena pide subir estando también llena la instancia
- **THEN** el motivo informado es el espacio de la cuenta

#### Scenario: Dos lotes simultáneos en álbumes distintos no superan el límite

- **WHEN** se piden a la vez dos lotes en dos álbumes de la misma persona y entre los dos excederían su espacio
- **THEN** lo concedido entre ambos no supera el límite

#### Scenario: Dos lotes simultáneos de personas distintas no superan el límite de la instancia

- **WHEN** dos personas distintas piden a la vez sendos lotes que entre los dos excederían el espacio de la instancia
- **THEN** lo concedido entre ambos no supera el límite de la instancia

## REMOVED Requirements

### Requirement: Conceder evalúa el límite del álbum y el de la cuenta, y distingue cuál se alcanzó

**Reason**: Su regla central —"SHALL evaluarse dos límites independientes"— deja de valer, y su nombre nombra la cantidad que cambió. Conceder pasa a evaluar tres, con dos reglas que el requirement anterior no tenía ni podía tener: cuál de los dos límites de espacio se informa cuando los dos se alcanzaron, y que la exclusión entre pedidos simultáneos abarque a personas distintas y no solo a los álbumes de una misma. Lo reemplaza el requirement agregado más arriba, que conserva íntegros los dos límites que ya evaluaba, su distinción y su exigencia de exclusión por persona, y les suma el tercero.

**Migration**: Ninguna migración de datos: los dos límites que ya existían se computan igual y sobre las mismas filas, y el tercero es una suma sobre lo mismo sin el filtro por dueño. Lo que cambia para un cliente es que el motivo con el que vuelve un archivo sin permiso admite un valor más, así que todo cliente que trate esa lista como cerrada tiene que contemplarlo. El único cliente del proyecto es su propia interfaz, y este change la actualiza.
