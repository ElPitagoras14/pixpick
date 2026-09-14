## Purpose

Gobierna qué documenta el repositorio para quien va a trabajar en él: a quién se dirige cada texto, qué preguntas responde y dónde vive cada explicación. No se solapa con las specs, que registran qué tiene que hacer el sistema y por qué se decidió así; esta capability gobierna el material de lectura, no el de decisión.

## ADDED Requirements

### Requirement: El documento de entrada se dirige a quien va a trabajar en el proyecto

El repositorio SHALL tener un documento de entrada dirigido a la persona que va a desarrollar sobre él. SHALL responder qué es el proyecto, cómo levantarlo, cómo ejecutar sus pruebas y dónde vive cada parte. SHALL NOT justificar decisiones de diseño, registrar alternativas descartadas ni referirse a changes por su nombre: eso vive en las specs y en los artefactos de cada change, y quien lee para trabajar no lo necesita.

#### Scenario: Alcanza para empezar a trabajar

- **WHEN** alguien que nunca vio el proyecto lo lee de principio a fin
- **THEN** puede levantar el entorno, ejecutar las pruebas y ubicar dónde tocar cada cosa
- **AND** no le hizo falta abrir ninguna spec

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
