## Purpose

Gobierna cómo se circula dentro de la aplicación una vez autenticado: qué pantallas son destinos a los que se llega por la navegación principal, cuáles son subvistas que dependen de otra pantalla, y cómo se sale de una subvista hacia aquella de la que depende. No cubre cuáles son las pantallas por las que se entra al producto ni qué tiene que resolver cada una, que es asunto de `app-entry`, ni cómo se construye y se entrega la interfaz, que es asunto de `frontend-delivery`.

## ADDED Requirements

### Requirement: Toda subvista ofrece una salida visible hacia la pantalla de la que depende

Una pantalla que no es destino de la navegación principal SHALL ofrecer un control visible que lleve a la pantalla de la que depende. Ese control SHALL NOT depender de la navegación hacia atrás del navegador, de un gesto del sistema operativo ni de escribir la dirección a mano, porque ninguno de los tres está garantizado cuando se llegó por un enlace directo.

La salida SHALL estar disponible en toda pantalla que la necesite, incluidas aquellas donde la navegación principal se oculta deliberadamente. SHALL NOT presentarse más de una salida a la vez: dos controles que hacen lo mismo obligan a decidir cuál usar.

Una pantalla que sí es destino de la navegación principal SHALL NOT ofrecer esta salida, porque no depende de ninguna otra.

#### Scenario: Una subvista abierta directamente tiene salida

- **WHEN** se abre directamente la dirección de una subvista, sin haber pasado por la pantalla de la que depende
- **THEN** hay un control visible que lleva a esa pantalla
- **AND** no hace falta recurrir a la navegación hacia atrás del navegador

#### Scenario: La salida sobrevive donde se oculta la navegación principal

- **WHEN** se está en una pantalla que oculta la navegación principal
- **THEN** la salida sigue estando visible
- **AND** sigue siendo posible abandonar esa pantalla

#### Scenario: Un destino de la navegación principal no ofrece salida

- **WHEN** se está en una pantalla a la que se llega por la navegación principal
- **THEN** no se ofrece esta salida

#### Scenario: Nunca se ofrecen dos salidas simultáneas

- **WHEN** se observa cualquier subvista en cualquier ancho de pantalla
- **THEN** se cuenta exactamente un control de salida

### Requirement: La salida sube un nivel y no depende de cómo se llegó

El destino de la salida SHALL ser la pantalla inmediatamente superior en la jerarquía del producto, no la pantalla de entrada ni un salto de varios niveles. Calificar fotos de un álbum y cargar fotos a un álbum SHALL volver a ese álbum; un álbum y la creación de un álbum SHALL volver a la lista de álbumes.

El destino SHALL depender únicamente de qué pantalla se está mirando, no del recorrido previo. Dos personas en la misma pantalla, una que llegó navegando y otra que abrió un enlace directo, SHALL terminar en el mismo lugar al usar la salida.

#### Scenario: Calificar vuelve al álbum que se está calificando

- **WHEN** se usa la salida mientras se califican las fotos de un álbum
- **THEN** se llega a ese álbum
- **AND** no a la lista de álbumes

#### Scenario: Cargar fotos vuelve al álbum

- **WHEN** se usa la salida mientras se cargan fotos a un álbum
- **THEN** se llega a ese álbum

#### Scenario: Un álbum vuelve a la lista

- **WHEN** se usa la salida estando dentro de un álbum
- **THEN** se llega a la lista de álbumes

#### Scenario: Crear un álbum también tiene por dónde salir

- **WHEN** se abandona la creación de un álbum sin haberlo creado
- **THEN** se llega a la lista de álbumes

#### Scenario: El enlace directo no cambia el destino

- **WHEN** se abre una subvista por un enlace directo y se usa la salida
- **THEN** se llega a la misma pantalla a la que se habría llegado navegando hasta ahí

### Requirement: La salida se puede accionar con el dedo

El control de salida SHALL ser accionable con la imprecisión de un dedo, no solo con un puntero: donde se apunta tocando la pantalla, su área activable SHALL medir al menos 44 por 44 píxeles CSS, el umbral que fijan las guías de las plataformas táctiles. SHALL NOT quedar reducido a un texto cuya altura sea la de su propia línea.

El control SHALL ser alcanzable también por teclado, con el foco visible, para que abandonar una pantalla no dependa de apuntar.

#### Scenario: Un toque impreciso en un teléfono alcanza

- **WHEN** se toca el control de salida en un teléfono sin apuntar con precisión
- **THEN** el control responde
- **AND** su área activable mide al menos 44 por 44 píxeles CSS

#### Scenario: Se puede salir sin apuntar

- **WHEN** se recorre la pantalla con el teclado
- **THEN** el control de salida recibe el foco de forma visible
- **AND** puede accionarse desde ahí
