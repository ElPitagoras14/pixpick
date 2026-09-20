## ADDED Requirements

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
