## MODIFIED Requirements

### Requirement: La primera pantalla después de iniciar sesión responde qué hacer ahora

La pantalla a la que se llega al iniciar sesión SHALL NOT estar vacía ni ser un mero aviso de que la sesión está activa. SHALL mostrar cuatro cosas: cuánto espacio se está ocupando contra el límite de la cuenta, qué porcentaje está ocupado de la instancia, qué álbumes tienen fotos esperando la calificación de quien mira, y por dónde crear un álbum.

Los dos consumos SHALL distinguirse entre sí a simple vista, sin deducir cuál es cuál a partir de los números. Presentados como si fueran lo mismo, una cuenta casi vacía dentro de una instancia casi llena se leería como una contradicción, y es exactamente la situación en la que saber cuál es cuál importa.

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

#### Scenario: El espacio de la instancia se ve junto al propio

- **WHEN** se abre esta pantalla
- **THEN** muestra también qué porcentaje está ocupado de la instancia
- **AND** se distingue de lo que ocupa la cuenta de quien mira

#### Scenario: Nada pendiente se distingue de nada cargado

- **WHEN** alguien con álbumes pero sin fotos por calificar llega a esta pantalla
- **THEN** se le indica que no le queda nada por calificar
- **AND** eso no se confunde con no tener álbumes
