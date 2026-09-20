## ADDED Requirements

### Requirement: La identidad de un álbum se presenta como un bloque contiguo

La pantalla de un álbum SHALL presentar juntos su nombre, cuándo vence y —para su dueño— cuántas personas participaron y cuántas calificaciones acumula. Los tres describen lo mismo: qué álbum es este y en qué estado está. SHALL NOT quedar separados por controles, por secciones intermedias ni por el contenido del álbum, porque repartirlos obliga a recorrer la pantalla para reconstruir una sola idea.

El resumen de participación SHALL acompañar a la identidad únicamente en la pantalla del álbum. Las subvistas que dependen de un álbum SHALL seguir informando de qué álbum se trata y cuándo vence, pero SHALL NOT mostrar ese resumen: quien está cargando o calificando fotos no decide nada con él.

Para quien no es dueño, la ausencia del resumen SHALL ser indistinguible de que no exista, no un espacio reservado sin contenido.

#### Scenario: El dueño ve los tres datos juntos

- **WHEN** el dueño abre un álbum que ya tiene calificaciones
- **THEN** el nombre, el vencimiento y la cantidad de participantes y de calificaciones aparecen contiguos
- **AND** no hay entre ellos ningún control ni ninguna otra sección de la pantalla

#### Scenario: Un miembro ve la identidad sin el resumen

- **WHEN** alguien que no es dueño abre un álbum compartido
- **THEN** ve el nombre del álbum y cuándo vence
- **AND** no aparece ningún espacio vacío donde iría el resumen de participación

#### Scenario: Las subvistas conservan la identidad pero no el resumen

- **WHEN** el dueño entra a cargar fotos al álbum o a calificarlas
- **THEN** sigue viendo de qué álbum se trata y cuándo vence
- **AND** no se muestra el resumen de participación

### Requirement: Las acciones del álbum no compiten con su identidad por el ancho

En un viewport de teléfono, los controles que operan sobre el álbum SHALL ocupar su propia zona, debajo del bloque de identidad, y el nombre del álbum SHALL disponer del ancho completo del contenido. SHALL NOT compartir línea con la identidad: cuando lo hacen, el ancho que toman los controles es el que le falta al nombre, y el nombre se fragmenta aunque sea corto.

Donde el ancho disponible alcanza para las dos cosas, los controles SHALL poder ubicarse al costado de la identidad. Lo que la pantalla angosta impone es el orden de lectura, no una única disposición para todo ancho.

#### Scenario: En un teléfono las acciones van debajo

- **WHEN** el dueño abre su álbum en un viewport de ancho de teléfono
- **THEN** las acciones del álbum aparecen debajo del bloque de identidad
- **AND** el nombre del álbum dispone del ancho completo del contenido

#### Scenario: En una pantalla ancha conviven en la misma fila

- **WHEN** el dueño abre el mismo álbum en un viewport ancho
- **THEN** las acciones pueden ubicarse al costado de la identidad
- **AND** el bloque de identidad conserva el mismo orden de lectura
