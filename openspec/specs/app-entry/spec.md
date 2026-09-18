# app-entry Specification

## Purpose

Gobierna las dos pantallas por las que se entra al producto —la pública y la primera después de iniciar sesión— y qué tiene que resolver cada una. Define qué preguntas contesta cada pantalla, no cómo se ve. No se solapa con `frontend-delivery`, que gobierna cómo se construye y se entrega la interfaz, ni con `album-management` o `rating-gallery`, que gobiernan la lista de álbumes y la galería.

## Requirements

### Requirement: La raíz es pública, dice qué es el producto y siempre ofrece entrar

La dirección raíz SHALL ser accesible sin sesión y SHALL NOT redirigir a autenticarse. SHALL decir qué es el producto y para qué sirve en términos que entienda alguien que no lo conoce, sin nombrar piezas internas.

SHALL ofrecer un acceso visible a la aplicación en cualquier estado de sesión, y ese acceso SHALL distinguir los dos casos: para quien no tiene sesión lleva a autenticarse, y para quien ya la tiene entra directo, sin volver a pedirle credenciales. SHALL NOT quedar quien no está autenticado sin forma de iniciar sesión desde esta pantalla.

#### Scenario: Alguien que nunca entró puede entender y entrar

- **WHEN** alguien sin sesión abre la raíz
- **THEN** encuentra qué es el producto y para qué sirve
- **AND** encuentra un acceso que lo lleva a iniciar sesión

#### Scenario: Quien ya tiene sesión entra sin autenticarse de nuevo

- **WHEN** alguien con sesión vigente abre la raíz
- **THEN** sigue viendo la misma pantalla de presentación
- **AND** su acceso lo lleva dentro de la aplicación sin pedirle credenciales

#### Scenario: La raíz no exige sesión

- **WHEN** alguien sin sesión abre la raíz
- **THEN** la ve completa
- **AND** no es enviado a ninguna pantalla de autenticación

### Requirement: La primera pantalla después de iniciar sesión responde qué hacer ahora

La pantalla a la que se llega al iniciar sesión SHALL NOT estar vacía ni ser un mero aviso de que la sesión está activa. SHALL mostrar tres cosas: cuánto espacio se está ocupando contra el límite de la cuenta, qué álbumes tienen fotos esperando la calificación de quien mira, y por dónde crear un álbum.

Una cuenta sin álbumes y sin nada pendiente SHALL mostrar igualmente un estado que indique por dónde empezar. SHALL NOT quedar en blanco por no tener contenido: no tener nada todavía es el caso más importante de esta pantalla, no una excepción.

#### Scenario: Una cuenta recién creada sabe por dónde empezar

- **WHEN** alguien que acaba de crear su cuenta llega a esta pantalla
- **THEN** encuentra cómo crear su primer álbum
- **AND** no ve una página vacía

#### Scenario: Lo que espera calificación aparece primero que la lista completa

- **WHEN** alguien con álbumes que tienen fotos sin calificar llega a esta pantalla
- **THEN** ve esos álbumes con la cantidad que le falta en cada uno
- **AND** puede ir directo a calificarlos sin recorrer la lista completa

#### Scenario: El espacio se ve sin entrar a ningún álbum

- **WHEN** se abre esta pantalla
- **THEN** muestra cuánto espacio se está ocupando y cuál es el límite

#### Scenario: Nada pendiente se distingue de nada cargado

- **WHEN** alguien con álbumes pero sin fotos por calificar llega a esta pantalla
- **THEN** se le indica que no le queda nada por calificar
- **AND** eso no se confunde con no tener álbumes

### Requirement: Lo pendiente de la pantalla de entrada coincide con lo que dice cada álbum

La cantidad que esta pantalla muestra junto a un álbum SHALL ser la misma que ese álbum informa por su cuenta. SHALL contemplar tanto los álbumes propios como aquellos a los que se accedió por un enlace compartido: lo que espera una calificación de quien mira no depende de quién sea el dueño.

#### Scenario: El mismo número en los dos lugares

- **WHEN** se compara lo que la pantalla de entrada dice de un álbum con lo que ese álbum muestra al abrirlo
- **THEN** coinciden

#### Scenario: Un álbum compartido también aparece

- **WHEN** alguien tiene fotos por calificar en un álbum que no es suyo
- **THEN** ese álbum aparece igual en su pantalla de entrada

#### Scenario: Calificar lo hace desaparecer

- **WHEN** se terminan de calificar todas las fotos pendientes de un álbum y se vuelve a la pantalla de entrada
- **THEN** ese álbum ya no figura entre los que esperan calificación

### Requirement: Se puede volver a la pantalla de entrada desde cualquier lugar

Estando autenticado, SHALL existir un acceso permanente de vuelta a la pantalla de entrada, disponible desde cualquier pantalla de la aplicación. SHALL NOT depender de escribir la dirección a mano ni de usar la navegación hacia atrás del navegador.

#### Scenario: Hay una vuelta desde adentro de un álbum

- **WHEN** se está dentro de un álbum
- **THEN** hay un acceso visible que lleva de vuelta a la pantalla de entrada
