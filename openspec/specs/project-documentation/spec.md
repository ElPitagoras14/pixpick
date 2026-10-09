# project-documentation Specification

## Purpose

Gobierna qué documenta el repositorio para quien va a trabajar en él: a quién se dirige cada texto, qué preguntas responde y dónde vive cada explicación. No se solapa con las specs, que registran qué tiene que hacer el sistema y por qué se decidió así; esta capability gobierna el material de lectura, no el de decisión.

## Requirements

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

### Requirement: El documento de entrada se lee con un nivel intermedio de inglés

El documento SHALL escribirse en inglés legible con nivel B1. Las oraciones SHALL ser cortas y de una sola idea. El vocabulario técnico SHALL limitarse a los nombres reales de cosas que la persona va a escribir o ver en pantalla: un comando, un archivo, un servicio, una variable. SHALL NOT usarse una palabra poco común cuando existe una corriente que dice lo mismo, ni metáforas ni giros idiomáticos.

#### Scenario: Una palabra técnica aparece solo si nombra algo real

- **WHEN** se toma cualquier término técnico del documento
- **THEN** corresponde al nombre de algo que la persona escribe, ejecuta o ve en el proyecto

#### Scenario: Ninguna oración exige releerla

- **WHEN** se revisa el documento oración por oración
- **THEN** cada una expresa una sola idea y se entiende en una lectura

### Requirement: Cada cosa se explica en un solo lugar

Una explicación SHALL vivir en el archivo donde se la va a necesitar, y SHALL NOT repetirse en otro. Cuando dos archivos podrían alojarla, la explicación SHALL quedar en aquel donde se toma la decisión que describe, y el otro SHALL limitarse a lo que solo se entiende leyéndolo a él.

#### Scenario: Una explicación no aparece dos veces

- **WHEN** se busca la explicación de un valor de configuración en todo el repositorio
- **THEN** aparece en un solo archivo

#### Scenario: Corregir una explicación es un solo cambio

- **WHEN** una explicación queda desactualizada y se la corrige
- **THEN** no queda ninguna otra copia diciendo lo anterior

### Requirement: La configuración efectiva se consulta, no se transcribe

Para saber qué configuración recibe realmente cada servicio, la documentación SHALL indicar cómo obtenerla del propio entorno. SHALL NOT mantenerse a mano una lista de valores efectivos, porque una lista así no tiene forma de avisar cuando deja de coincidir con el entorno que describe.

#### Scenario: Lo que se consulta refleja el entorno real

- **WHEN** se sigue lo que el documento indica para ver la configuración de un servicio
- **THEN** lo que se obtiene sale de los archivos del entorno y de la configuración local vigentes
- **AND** cambiar un valor y volver a consultarlo muestra el valor nuevo

### Requirement: Ninguna explicación del repositorio remite a un artefacto de decisión

Una explicación escrita en cualquier archivo del repositorio —un comentario, un docstring, una nota de configuración o un documento— SHALL sostenerse por sí sola. SHALL NOT nombrar una spec, un change ni una decisión numerada de un diseño, ni atribuir a ninguno de ellos lo que afirma. Lo que la explicación necesita para entenderse SHALL estar en ella; lo que la justifica vive en las specs y en los artefactos de cada change, y quien lee para trabajar no tiene por qué abrirlos.

Esta regla generaliza a todo el repositorio lo que hasta ahora solo pesaba sobre el documento de entrada. El material de decisión no se pierde ni se copia: sigue donde estaba.

#### Scenario: Una explicación se entiende sin abrir nada más

- **WHEN** se lee cualquier comentario o nota del repositorio
- **THEN** lo que afirma se entiende con lo que tiene escrito y con el código que acompaña
- **AND** no remite a ningún artefacto de decisión para completarse

#### Scenario: Buscar una referencia no encuentra ninguna

- **WHEN** se busca en todo el repositorio el nombre de una spec, el nombre de un change o una decisión numerada
- **THEN** no aparece en ningún archivo fuera de los que registran decisiones
- **AND** las specs y los changes archivados siguen conservando ese detalle

### Requirement: El archivo de ejemplo de variables distingue lo que hay que configurar de lo que no

El archivo de ejemplo de variables de entorno SHALL separar, como su división principal, las variables que exigen un valor propio antes de usar el proyecto de las que se pueden dejar como vienen. Una variable SHALL quedar del lado que exige un valor cuando no tiene default, cuando su default es un secreto de desarrollo que no puede salir de una máquina de desarrollo, o cuando el valor activo de otra variable la vuelve obligatoria. Tener un default SHALL NOT bastar por sí solo para ubicarla del lado opcional.

Dentro de cada lado, las variables SHALL agruparse por el área que configuran, de modo que las que se tocan en un mismo momento queden juntas. Una variable cuyo nombre no alcance para saber qué valor admite SHALL llevar escrito cómo obtenerlo o cómo componerlo, y una que acepte un conjunto cerrado de valores SHALL enumerarlos. SHALL NOT explicarse lo que el nombre de la variable y su valor de ejemplo ya dicen.

Esta regla gobierna cómo se lee ese archivo. Que exista, que esté completo y que ninguna variable figure sin consumidor lo gobierna `local-environment`.

#### Scenario: Saber qué llenar es leer el primer bloque

- **WHEN** alguien que nunca vio el proyecto abre el archivo de ejemplo
- **THEN** el primer bloque contiene todas las variables que tiene que completar y ninguna que no
- **AND** puede dejar el resto del archivo sin tocar y levantar el proyecto

#### Scenario: Una variable con default pero con un secreto de desarrollo pide un valor

- **WHEN** se toma una variable cuyo valor de ejemplo es una credencial apta solo para desarrollo
- **THEN** está del lado de las que hay que configurar

#### Scenario: Un conjunto cerrado de valores está enumerado

- **WHEN** se toma una variable que solo admite un conjunto cerrado de valores
- **THEN** el archivo los lista
- **AND** quien la completa no necesita buscarlos en el código

#### Scenario: Las variables de un mismo servicio están juntas

- **WHEN** se busca lo que hay que configurar para un servicio concreto
- **THEN** sus variables aparecen agrupadas y no repartidas por el archivo

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
