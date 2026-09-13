# album-management Specification

## Purpose

Gobierna qué es un álbum, quién puede crearlo, verlo y modificarlo, cómo se listan los propios, qué información se necesita para reconocerlos, y qué se elimina cuando se elimina uno. No se solapa con `photo-upload`, que gobierna cómo las fotos llegan a formar parte de un álbum.

## Requirements

### Requirement: Un álbum pertenece a quien lo creó y esa pertenencia no cambia

Todo álbum SHALL tener exactamente un dueño, que es la persona autenticada que lo creó. El dueño SHALL asignarse al crear y SHALL NOT poder cambiarse después, porque no existe ninguna operación de transferencia ni ningún caso de uso que la requiera.

#### Scenario: Crear un álbum asigna al creador como dueño

- **WHEN** una persona autenticada crea un álbum
- **THEN** queda registrada como su dueño

#### Scenario: La pertenencia no se puede cambiar

- **WHEN** se inspeccionan las operaciones disponibles sobre un álbum
- **THEN** ninguna permite cambiar quién es su dueño

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

### Requirement: Un álbum tiene un título obligatorio y una descripción opcional

El título SHALL ser obligatorio y SHALL tener contenido: un valor compuesto solo de espacios SHALL rechazarse. La descripción SHALL ser opcional y su ausencia SHALL ser un estado válido, no un valor vacío que haya que interpretar.

#### Scenario: Sin título no se crea

- **WHEN** se intenta crear un álbum sin título
- **THEN** la respuesta indica que el título es obligatorio y nombra el campo

#### Scenario: Un título en blanco se rechaza

- **WHEN** se intenta crear un álbum con un título compuesto únicamente de espacios
- **THEN** se rechaza igual que si faltara

#### Scenario: Sin descripción se crea igual

- **WHEN** se crea un álbum sin descripción
- **THEN** el álbum queda creado

### Requirement: Listar devuelve solo los álbumes propios con lo necesario para reconocerlos

La lista SHALL incluir los álbumes de quien pide y también aquellos de los que es miembro, distinguiendo unos de otros, porque quien calificó un álbum ajeno necesita volver a él sin depender de conservar el link que lo llevó la primera vez.

Cada entrada SHALL traer lo necesario para reconocer el álbum y decidir si abrirlo —su título, cuántas fotos disponibles tiene, una imagen de portada y cuántas le faltan calificar a quien pide— sin que el cliente tenga que pedir nada más por cada álbum.

Los álbumes propios y los compartidos SHALL presentarse en grupos separados y SHALL NOT mezclarse en una única enumeración, porque responden a intenciones distintas: en los propios se entra a administrar y ver resultados, y en los compartidos a calificar o a revisar lo que uno opinó. La selección del grupo SHALL formar parte de la dirección, igual que el filtro de la galería, de modo que recargar la página la conserve. Cada grupo SHALL indicar cuántos álbumes contiene, y un grupo sin álbumes SHALL decir que está vacío en lugar de presentarse como una lista que no cargó.

#### Scenario: Aparecen los propios y aquellos de los que se es miembro

- **WHEN** una persona lista sus álbumes
- **THEN** aparecen todos los suyos
- **AND** aparecen aquellos de los que es miembro
- **AND** ninguno al que no tiene acceso

#### Scenario: Se distingue lo propio de lo compartido

- **WHEN** se recibe la lista de álbumes
- **THEN** puede distinguirse cuáles son propios y cuáles son de otra persona

#### Scenario: Los dos grupos no se mezclan

- **WHEN** se mira el grupo de los álbumes propios
- **THEN** aparecen únicamente los propios
- **WHEN** se mira el grupo de los compartidos
- **THEN** aparecen únicamente aquellos de los que se es miembro sin ser dueño

#### Scenario: El grupo seleccionado sobrevive a recargar

- **WHEN** se selecciona un grupo y se recarga la página
- **THEN** sigue mostrándose ese grupo

#### Scenario: Cada grupo dice cuántos álbumes tiene

- **WHEN** se mira la lista de álbumes
- **THEN** cada grupo indica su cantidad sin necesidad de abrirlo

#### Scenario: Un grupo vacío se distingue de uno que no cargó

- **WHEN** una persona no tiene ningún álbum compartido
- **THEN** ese grupo indica que está vacío
- **AND** no se presenta como una lista pendiente de cargar

#### Scenario: Cada entrada alcanza para reconocerla

- **WHEN** se recibe la lista de álbumes
- **THEN** cada entrada trae su título, su cantidad de fotos disponibles, su portada y cuántas le faltan calificar a quien pide
- **AND** no hace falta una petición adicional por álbum

#### Scenario: Un álbum vacío aparece en la lista

- **WHEN** se lista un álbum al que todavía no se le subió ninguna foto
- **THEN** aparece con cero fotos y sin portada

### Requirement: La portada es la primera foto disponible del álbum

La portada SHALL ser la primera foto disponible según el orden del álbum, y SHALL NOT ser elegible a mano. Un álbum sin fotos disponibles SHALL NOT tener portada, y esa ausencia SHALL ser un estado que el cliente pueda representar.

#### Scenario: La portada es la primera foto

- **WHEN** un álbum tiene fotos disponibles
- **THEN** su portada es la primera según el orden del álbum

#### Scenario: Sin fotos disponibles no hay portada

- **WHEN** un álbum no tiene ninguna foto disponible
- **THEN** no tiene portada

### Requirement: Eliminar un álbum elimina sus fotos y los objetos de todas ellas

Eliminar un álbum SHALL eliminar sus fotos y los objetos almacenados de cada una. El orden SHALL ser eliminar primero los registros y después los objetos: si la eliminación de objetos falla, el resultado SHALL ser objetos huérfanos y SHALL NOT ser registros que apunten a objetos inexistentes.

#### Scenario: Se eliminan las fotos y sus objetos

- **WHEN** el dueño elimina un álbum con fotos
- **THEN** el álbum y sus fotos dejan de existir
- **AND** los objetos almacenados de esas fotos dejan de existir

#### Scenario: Un fallo al eliminar objetos no deja referencias rotas

- **WHEN** la eliminación de los objetos falla después de eliminar los registros
- **THEN** no queda ningún registro que apunte a un objeto inexistente
- **AND** los objetos que no se pudieron eliminar quedan como huérfanos identificables

#### Scenario: Un álbum vacío se elimina sin más

- **WHEN** el dueño elimina un álbum sin fotos
- **THEN** el álbum deja de existir

### Requirement: Renombrar un álbum no afecta a sus fotos

Cambiar el título o la descripción SHALL afectar únicamente a esos campos. SHALL NOT alterar las fotos, su orden, su disponibilidad ni los objetos almacenados.

#### Scenario: Cambiar el título no toca las fotos

- **WHEN** el dueño cambia el título de un álbum con fotos
- **THEN** las fotos, su orden y su disponibilidad quedan igual
