## Purpose

Gobierna cómo se comparte un álbum: qué es el link, qué concede, cómo se revoca y se regenera, cómo se ingresa con él, y qué relación hay entre el token que circula y el acceso de quien ya lo usó. No se solapa con `photo-rating`, que gobierna qué hace quien ya entró.

## ADDED Requirements

### Requirement: Solo el dueño administra el link de su álbum

Generar, regenerar y revocar el link SHALL ser potestad exclusiva del dueño del álbum. Intentarlo sobre un álbum ajeno SHALL responderse igual que sobre un álbum inexistente. Ser miembro de un álbum SHALL NOT habilitar a administrar su link.

#### Scenario: El dueño obtiene el link de su álbum

- **WHEN** el dueño pide el link de compartir de su álbum
- **THEN** lo obtiene

#### Scenario: Un miembro no puede administrar el link

- **WHEN** un miembro que no es dueño intenta regenerar o revocar el link
- **THEN** la operación se rechaza
- **AND** el link no cambia

### Requirement: El link es una dirección impredecible construida desde la configuración

El link SHALL contener un token impredecible, no derivable del identificador del álbum ni de ningún otro dato observable. La dirección completa SHALL construirse a partir de la dirección pública configurada del sitio y SHALL NOT derivarse del esquema ni del host de la petición que la solicitó.

#### Scenario: El token no se puede derivar

- **WHEN** se conoce el identificador de un álbum y el token de otro
- **THEN** no permiten deducir el token del primero

#### Scenario: La dirección se construye desde la configuración

- **WHEN** el dueño obtiene el link de su álbum
- **THEN** la dirección usa el esquema y el host configurados como públicos
- **AND** no refleja el esquema ni el host con que llegó la petición

### Requirement: Un álbum tiene a lo sumo un link vigente, y regenerar revoca el anterior

Un álbum SHALL tener como máximo un link vigente a la vez. Regenerar SHALL revocar el vigente y emitir uno nuevo en la misma operación. Revocar SHALL dejar al álbum sin link vigente hasta que se genere otro. Los links revocados SHALL conservarse como registro y SHALL NOT reutilizarse.

#### Scenario: Regenerar invalida el link anterior

- **WHEN** el dueño regenera el link de su álbum
- **THEN** el link anterior deja de servir para ingresar
- **AND** el nuevo sirve

#### Scenario: Revocar deja al álbum sin link

- **WHEN** el dueño revoca el link
- **THEN** ningún link permite ingresar al álbum hasta que se genere otro

#### Scenario: Un token revocado no vuelve a emitirse

- **WHEN** se generan varios links sucesivos para el mismo álbum
- **THEN** ningún token se repite

### Requirement: Un token que no sirve responde como inexistente

Ingresar con un token desconocido, revocado o que no corresponde a ningún álbum SHALL responderse de la misma manera en los tres casos. La respuesta SHALL NOT permitir distinguir un token que alguna vez existió de uno que nunca existió, ni deducir que el álbum existe.

#### Scenario: Los tres casos son indistinguibles

- **WHEN** se ingresa con un token inventado, con uno revocado y con uno bien formado que no corresponde a nada
- **THEN** las tres respuestas son iguales

#### Scenario: La respuesta no revela la existencia del álbum

- **WHEN** se ingresa con un token revocado
- **THEN** la respuesta no permite deducir que hay un álbum detrás

### Requirement: Ingresar con un link vigente concede membresía persistente

Ingresar con un token vigente SHALL incorporar a quien ingresa como miembro del álbum, y esa membresía SHALL persistir con independencia de lo que ocurra después con el token. Ingresar de nuevo con el mismo token SHALL NOT duplicar la membresía ni alterar nada.

#### Scenario: Ingresar incorpora como miembro

- **WHEN** una persona autenticada ingresa con un token vigente
- **THEN** queda incorporada como miembro del álbum

#### Scenario: Volver a ingresar no cambia nada

- **WHEN** un miembro vuelve a ingresar con el mismo token
- **THEN** sigue siendo miembro
- **AND** no se registra una membresía adicional

### Requirement: Revocar el link no expulsa a quien ya es miembro

Revocar o regenerar un link SHALL afectar únicamente a quienes todavía no ingresaron. Quien ya es miembro SHALL conservar su acceso al álbum y sus calificaciones SHALL permanecer intactas, porque de lo contrario cambiar un link destruiría el trabajo que el dueño estaba esperando recibir.

#### Scenario: El miembro conserva el acceso tras una revocación

- **WHEN** el dueño revoca el link de un álbum que ya tiene miembros
- **THEN** cada miembro sigue accediendo al álbum
- **AND** sus calificaciones siguen existiendo

#### Scenario: Tras revocar, nadie nuevo puede ingresar

- **WHEN** alguien que no era miembro intenta ingresar con el token revocado
- **THEN** no ingresa
- **AND** no queda incorporado como miembro

### Requirement: El link funciona sin sesión previa y devuelve a la persona al álbum

Abrir un link sin haber iniciado sesión SHALL conducir a autenticarse conservando el álbum como destino, y una vez autenticada la persona SHALL terminar en ese álbum y no en la portada. El link SHALL funcionar igual cuando se lo abre desde otra aplicación, que es la forma habitual en que va a llegar.

#### Scenario: Abrir el link sin sesión termina en el álbum

- **WHEN** alguien sin sesión abre un link de compartir y se autentica
- **THEN** termina en el álbum al que el link apuntaba

#### Scenario: El link abierto desde otra aplicación funciona igual

- **WHEN** el link se abre desde una aplicación de mensajería o un cliente de correo
- **THEN** el ingreso se completa igual que si se hubiera abierto desde el propio sitio

### Requirement: Crear un álbum hace miembro a su dueño

Crear un álbum SHALL incorporar a su dueño como miembro. De ese modo el dueño califica su propio álbum por el mismo camino que cualquier otra persona, sin que el sistema necesite un caso especial para él.

#### Scenario: El dueño puede calificar su álbum sin ingresar por un link

- **WHEN** el dueño abre su álbum recién creado
- **THEN** puede calificar sus fotos
- **AND** no necesitó ingresar por el link de compartir
