## MODIFIED Requirements

### Requirement: La variante se produce al pedirla y queda cacheada

Una variante SHALL producirse la primera vez que se la pide, y las peticiones siguientes por la misma variante SHALL servirse de lo ya producido sin volver a transformar.

SHALL NOT existir un mecanismo que produzca derivados por su cuenta y los almacene como objetos propios: el único camino por el que una variante se produce es una petición por la vía normal de entrega. Pedir una variante anticipadamente, para que quede cacheada antes de que la mire una persona, SHALL considerarse una petición como cualquier otra y no una excepción a esta regla — quien la pide obtiene exactamente lo mismo que obtendría cualquier visitante, y lo único que cambia es el momento.

La distinción importa porque las dos cosas se parecen y tienen consecuencias opuestas: pre-generar y almacenar derivados agrega una copia que hay que mantener sincronizada con la original y regenerar cuando cambia una variante, mientras que anticipar una petición no agrega estado alguno y lo ya cacheado se invalida por el mismo mecanismo que todo lo demás.

#### Scenario: La primera petición la produce

- **WHEN** se pide una variante que nunca se pidió
- **THEN** se produce y se entrega

#### Scenario: La segunda petición no vuelve a producirla

- **WHEN** se pide otra vez la misma variante
- **THEN** se entrega sin volver a transformar

#### Scenario: Anticipar la petición deja la variante lista

- **WHEN** el sistema pide una variante antes de que ninguna persona la haya mirado
- **THEN** la variante queda producida y cacheada
- **AND** la primera persona que la mira la recibe sin esperar a que se produzca

#### Scenario: No hay derivados almacenados como objetos propios

- **WHEN** se inspecciona qué objetos existen en el almacenamiento
- **THEN** solo están las imágenes originales
- **AND** ninguna variante figura como un objeto almacenado
