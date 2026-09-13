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

En este alcance el álbum no es accesible para nadie más que su dueño. Pedir un álbum ajeno SHALL responderse igual que pedir uno que no existe, porque el identificador del álbum es impredecible y confirmar su existencia a quien no tiene acceso sería una filtración.

#### Scenario: El dueño accede a su álbum

- **WHEN** el dueño pide su álbum
- **THEN** lo obtiene

#### Scenario: Un álbum ajeno responde como inexistente

- **WHEN** una persona autenticada pide un álbum del que no es dueña
- **THEN** la respuesta es la misma que para un álbum que no existe
- **AND** no permite deducir que el álbum existe

#### Scenario: Modificar o eliminar un álbum ajeno tampoco es posible

- **WHEN** una persona autenticada intenta renombrar o eliminar un álbum del que no es dueña
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

La lista SHALL incluir únicamente los álbumes de quien pide. Cada entrada SHALL traer lo necesario para reconocer el álbum y decidir si abrirlo —su título, cuántas fotos disponibles tiene y una imagen de portada— sin que el cliente tenga que pedir nada más por cada álbum.

#### Scenario: Solo aparecen los propios

- **WHEN** una persona lista sus álbumes
- **THEN** aparecen todos los suyos
- **AND** ninguno ajeno

#### Scenario: Cada entrada alcanza para reconocerla

- **WHEN** se recibe la lista de álbumes
- **THEN** cada entrada trae su título, su cantidad de fotos disponibles y su portada
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
