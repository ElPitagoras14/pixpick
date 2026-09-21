## MODIFIED Requirements

### Requirement: Las versiones de las imágenes de terceros están fijadas

Toda imagen de terceros que use el entorno SHALL declararse con una versión explícita. SHALL NOT usarse etiquetas móviles, para que reconstruir el entorno en otro momento no traiga silenciosamente una versión distinta.

Eso alcanza tanto a las imágenes que el entorno declara y levanta como a las imágenes base desde las que se construyen los servicios propios. Una base declarada con una etiqueta móvil cambia sin que nada en el repositorio lo registre, de modo que la forma que construye desde el código fuente deja de ser reproducible: dos personas que levantan el mismo commit con semanas de diferencia obtienen runtimes distintos. Actualizar una base SHALL ser una modificación explícita del archivo que la declara.

#### Scenario: Cada imagen declara su versión

- **WHEN** se inspecciona la declaración del entorno
- **THEN** cada imagen de terceros indica una versión explícita
- **AND** ninguna usa una etiqueta que se mueva con el tiempo

#### Scenario: Cada imagen base declara su versión

- **WHEN** se inspeccionan las imágenes base desde las que se construyen los servicios propios
- **THEN** cada una indica una versión explícita
- **AND** ninguna usa una etiqueta que se mueva con el tiempo

#### Scenario: Reconstruir más tarde da lo mismo

- **WHEN** se reconstruye el entorno tiempo después sin cambiar la declaración
- **THEN** se obtienen las mismas versiones de los servicios de terceros
- **AND** también las mismas versiones de las bases sobre las que corren los servicios propios

#### Scenario: Actualizar una base queda registrado

- **WHEN** un servicio propio pasa a construirse sobre una versión distinta de su imagen base
- **THEN** el cambio consta como una modificación del archivo que declara esa base
