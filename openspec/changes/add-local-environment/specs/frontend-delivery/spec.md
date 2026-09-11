## Purpose

Gobierna cómo se construye la interfaz y cómo se entrega al navegador, incluida la resolución de rutas del lado del cliente y el comportamiento de cacheo de lo que se sirve. No cubre cómo la interfaz obtiene sus valores de entorno, que es asunto de `frontend-runtime-config`, ni por dónde entra el tráfico, que es asunto de `local-environment`.

## ADDED Requirements

### Requirement: La interfaz se entrega ya construida

Lo que se sirve al navegador SHALL ser el resultado de una construcción previa. SHALL NOT construirse, compilarse ni transformarse en el momento de atender la petición, para que servir la interfaz no dependa de herramientas de desarrollo ni de acceso a la red.

#### Scenario: Servir no requiere herramientas de construcción

- **WHEN** se atiende una petición de la interfaz
- **THEN** se entregan archivos ya construidos
- **AND** no se ejecuta ninguna herramienta de construcción

#### Scenario: Arrancar no requiere red

- **WHEN** el servicio que entrega la interfaz arranca sin acceso a internet
- **THEN** la interfaz se sirve igual

### Requirement: Cualquier ruta de la aplicación cargada directamente entrega la aplicación

El enrutado es del lado del cliente, así que pedir directamente una ruta interna SHALL devolver el documento de la aplicación con una respuesta satisfactoria y dejar que el cliente resuelva qué vista mostrar. SHALL NOT devolverse una respuesta de recurso no encontrado por el hecho de que la ruta solo exista en el cliente.

#### Scenario: Recargar en una ruta profunda funciona

- **WHEN** se abre o se recarga directamente una ruta interna de la aplicación
- **THEN** se recibe el documento de la aplicación con una respuesta satisfactoria
- **AND** el cliente muestra la vista correspondiente a esa ruta

#### Scenario: Una ruta inexistente la resuelve la aplicación

- **WHEN** se pide una ruta que la aplicación no conoce
- **THEN** se recibe igualmente el documento de la aplicación
- **AND** es la aplicación la que muestra su propia pantalla de recurso no encontrado

#### Scenario: El espacio de la API no se confunde con una ruta de la aplicación

- **WHEN** se pide una ruta del espacio reservado a la API que no existe
- **THEN** la respuesta proviene del backend
- **AND** no se entrega el documento de la interfaz

### Requirement: El cacheo permite que un despliegue nuevo se vea sin intervención

Los recursos cuyo nombre identifica su contenido SHALL servirse con un cacheo prolongado, y el documento de entrada SHALL servirse de forma que el navegador lo revalide. SHALL NOT quedar un navegador sirviendo una versión anterior de la interfaz después de un despliegue sin que el usuario vacíe el cache.

#### Scenario: Los recursos identificados por contenido se cachean largo

- **WHEN** el navegador recibe un recurso cuyo nombre identifica su contenido
- **THEN** la respuesta permite conservarlo en cache por un período prolongado

#### Scenario: Un despliegue nuevo se ve al recargar

- **WHEN** se despliega una versión nueva de la interfaz y el usuario recarga
- **THEN** el navegador obtiene la versión nueva
- **AND** no hace falta vaciar el cache a mano

### Requirement: La interfaz toma la pantalla de teléfono como caso base

La interfaz SHALL ser operable en un viewport de teléfono como caso de diseño primario. SHALL NOT producir desplazamiento horizontal en ese viewport, y los controles interactivos SHALL tener un área táctil suficiente para el pulgar.

#### Scenario: Un viewport angosto no genera desplazamiento horizontal

- **WHEN** se abre la interfaz en un viewport de ancho de teléfono
- **THEN** el contenido se acomoda al ancho disponible
- **AND** no aparece desplazamiento horizontal

#### Scenario: Los controles son accionables con el pulgar

- **WHEN** se examina cualquier control interactivo en un viewport de teléfono
- **THEN** su área accionable es suficiente para el toque de un pulgar
