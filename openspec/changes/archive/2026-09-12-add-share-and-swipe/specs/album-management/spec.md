## MODIFIED Requirements

### Requirement: Solo el dueño puede ver y modificar su álbum

Un álbum es accesible para su dueño y para quienes se incorporaron como miembros. Pedir un álbum sin ser ninguna de las dos cosas SHALL responderse igual que pedir uno que no existe, porque el identificador del álbum es impredecible y confirmar su existencia a quien no tiene acceso sería una filtración.

Acceder y modificar son cosas distintas. Un miembro SHALL poder ver el álbum y sus fotos, pero renombrarlo, eliminarlo, agregarle o quitarle fotos y administrar su link SHALL seguir siendo potestad exclusiva del dueño. Un intento de modificar por parte de un miembro SHALL rechazarse indicando que la acción está prohibida, porque su existencia ya le consta y ocultársela no protegería nada.

#### Scenario: El dueño accede a su álbum

- **WHEN** el dueño pide su álbum
- **THEN** lo obtiene

#### Scenario: Un miembro accede al álbum

- **WHEN** un miembro pide el álbum del que es miembro
- **THEN** lo obtiene

#### Scenario: Un álbum del que no se es dueño ni miembro responde como inexistente

- **WHEN** una persona autenticada pide un álbum del que no es dueña ni miembro
- **THEN** la respuesta es la misma que para un álbum que no existe
- **AND** no permite deducir que el álbum existe

#### Scenario: Un miembro no puede modificar el álbum

- **WHEN** un miembro intenta renombrar o eliminar el álbum, o agregarle o quitarle fotos
- **THEN** la respuesta indica que la acción está prohibida
- **AND** el álbum no se modifica

#### Scenario: Modificar un álbum ajeno del que no se es miembro responde como inexistente

- **WHEN** una persona autenticada intenta renombrar o eliminar un álbum del que no es dueña ni miembro
- **THEN** la respuesta es la misma que para un álbum que no existe
- **AND** el álbum no se modifica

### Requirement: Listar devuelve solo los álbumes propios con lo necesario para reconocerlos

La lista SHALL incluir los álbumes de quien pide y también aquellos de los que es miembro, distinguiendo unos de otros, porque quien calificó un álbum ajeno necesita volver a él sin depender de conservar el link que lo llevó la primera vez.

Cada entrada SHALL traer lo necesario para reconocer el álbum y decidir si abrirlo —su título, cuántas fotos disponibles tiene, una imagen de portada y cuántas le faltan calificar a quien pide— sin que el cliente tenga que pedir nada más por cada álbum.

#### Scenario: Aparecen los propios y aquellos de los que se es miembro

- **WHEN** una persona lista sus álbumes
- **THEN** aparecen todos los suyos
- **AND** aparecen aquellos de los que es miembro
- **AND** ninguno al que no tiene acceso

#### Scenario: Se distingue lo propio de lo compartido

- **WHEN** se recibe la lista de álbumes
- **THEN** puede distinguirse cuáles son propios y cuáles son de otra persona

#### Scenario: Cada entrada alcanza para reconocerla

- **WHEN** se recibe la lista de álbumes
- **THEN** cada entrada trae su título, su cantidad de fotos disponibles, su portada y cuántas le faltan calificar a quien pide
- **AND** no hace falta una petición adicional por álbum

#### Scenario: Un álbum vacío aparece en la lista

- **WHEN** se lista un álbum al que todavía no se le subió ninguna foto
- **THEN** aparece con cero fotos y sin portada
