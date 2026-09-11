## MODIFIED Requirements

### Requirement: Cualquier ruta de la aplicación cargada directamente entrega la aplicación

El enrutado es del lado del cliente, así que pedir directamente una ruta interna SHALL devolver el documento de la aplicación con una respuesta satisfactoria y dejar que el cliente resuelva qué vista mostrar. SHALL NOT devolverse una respuesta de recurso no encontrado por el hecho de que la ruta solo exista en el cliente.

El fallback que devuelve el documento SHALL NOT alcanzar a ninguno de los espacios reservados. Una ruta que pertenece a un espacio reservado SHALL responderla el servicio de ese espacio, incluso cuando lo pedido no exista, porque entregar el documento de la interfaz donde se esperaba otra cosa convierte un error claro en uno indescifrable.

#### Scenario: Recargar en una ruta profunda funciona

- **WHEN** se abre o se recarga directamente una ruta interna de la aplicación
- **THEN** se recibe el documento de la aplicación con una respuesta satisfactoria
- **AND** el cliente muestra la vista correspondiente a esa ruta

#### Scenario: Una ruta inexistente la resuelve la aplicación

- **WHEN** se pide una ruta que la aplicación no conoce
- **THEN** se recibe igualmente el documento de la aplicación
- **AND** es la aplicación la que muestra su propia pantalla de recurso no encontrado

#### Scenario: Ningún espacio reservado se confunde con una ruta de la aplicación

- **WHEN** se pide una ruta inexistente dentro de cualquiera de los espacios reservados
- **THEN** la respuesta proviene del servicio de ese espacio
- **AND** no se entrega el documento de la interfaz

#### Scenario: Un recurso inexistente de un espacio reservado falla como ese tipo de recurso

- **WHEN** se pide una imagen que no existe
- **THEN** la respuesta es un error
- **AND** no es un documento con respuesta satisfactoria
