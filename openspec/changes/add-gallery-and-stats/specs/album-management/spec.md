## MODIFIED Requirements

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
