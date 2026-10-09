## MODIFIED Requirements

### Requirement: El documento de entrada se dirige a quien va a trabajar en el proyecto

El repositorio SHALL tener un documento de entrada con dos audiencias declaradas en un orden: primero quien va a levantar el proyecto y mantenerlo andando, y después quien va a desarrollar sobre él. SHALL responder qué es el proyecto, cómo levantarlo, cómo operarlo, cómo ejecutar sus pruebas y dónde vive cada parte. Sus secciones SHALL ordenarse por el momento en que cada cosa hace falta, no por afinidad temática. El material dirigido a quien desarrolla SHALL quedar agrupado en un solo bloque ubicado después del que sirve a quien opera, de modo que ninguno de los dos lectores tenga que atravesar el material del otro para llegar al suyo. Los comandos que el documento ofrece a quien opera SHALL poder ejecutarse con lo que esa persona tiene: el runtime de contenedores y su archivo de entorno. SHALL NOT justificar decisiones de diseño, registrar alternativas descartadas ni referirse a changes por su nombre: eso vive en las specs y en los artefactos de cada change, y quien lee para trabajar no lo necesita.

#### Scenario: Alcanza para empezar a trabajar

- **WHEN** alguien que nunca vio el proyecto lo lee de principio a fin
- **THEN** puede levantar el entorno, ejecutar las pruebas y ubicar dónde tocar cada cosa
- **AND** no le hizo falta abrir ninguna spec

#### Scenario: Quien solo va a levantar el proyecto no atraviesa material de desarrollo

- **WHEN** alguien que solo va a levantar el proyecto lo lee desde el principio
- **THEN** llega a levantarlo, configurarlo y mantenerlo andando sin cruzar instrucciones que supongan un clon del código o herramientas de desarrollo instaladas
- **AND** el material de desarrollo empieza después de todo lo que esa persona necesita

#### Scenario: Quien desarrolla encuentra lo suyo junto

- **WHEN** alguien que va a desarrollar busca cómo ejecutar las pruebas
- **THEN** lo encuentra dentro del mismo bloque que el resto del material de desarrollo
- **AND** no hay material de desarrollo fuera de ese bloque

#### Scenario: Un comando dirigido a quien opera se puede ejecutar

- **WHEN** se toma cualquier comando de las secciones dirigidas a quien opera
- **THEN** se ejecuta con el runtime de contenedores y el archivo de entorno
- **AND** no exige un clon del repositorio ni herramientas de desarrollo en la máquina

#### Scenario: No argumenta decisiones

- **WHEN** se busca en el documento por qué se eligió una tecnología o un enfoque sobre otro
- **THEN** no está
- **AND** lo que sí está es qué hay y cómo se usa

## ADDED Requirements

### Requirement: El documento de entrada y el archivo de ejemplo de variables se reparten la configuración

El archivo de ejemplo de variables de entorno SHALL ser el único lugar donde se explica qué controla cada variable, qué valores admite y qué cambia al cambiarla. El documento de entrada SHALL NOT repetir esa explicación ni parte de ella. Lo que SHALL llevar el documento de entrada es el procedimiento fuera del repositorio que hay que completar para obtener un valor —dar de alta una credencial en la consola de un proveedor, crear un recurso, elegir entre varias formas de componer un valor—, porque son pasos que no caben junto a la variable sin volver ilegible el archivo. Toda remisión del archivo de ejemplo al documento de entrada SHALL encontrar ahí el procedimiento que promete.

#### Scenario: Qué admite una variable se lee en un solo archivo

- **WHEN** se busca en todo el repositorio qué valores admite una variable de entorno
- **THEN** la respuesta está en el archivo de ejemplo
- **AND** el documento de entrada no la repite

#### Scenario: El procedimiento externo está donde el ejemplo lo promete

- **WHEN** el archivo de ejemplo remite al documento de entrada por los pasos para obtener el valor de una variable
- **THEN** el documento de entrada tiene esos pasos

#### Scenario: Los pasos en la consola de un proveedor no viven junto a la variable

- **WHEN** una variable exige crear o dar de alta algo fuera del repositorio para tener su valor
- **THEN** esos pasos están en el documento de entrada
- **AND** el archivo de ejemplo se limita a decir qué es la variable y a remitir
