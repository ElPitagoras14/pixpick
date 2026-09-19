## MODIFIED Requirements

### Requirement: Cuando un archivo no termina bien, el motivo se lee completo

Cuando un archivo no llegue a subirse, SHALL mostrarse el motivo, con el espacio que necesite aunque ocupe más de un renglón, y SHALL NOT reemplazarse por un estado genérico ni recortarse hasta volverlo inútil. Si el motivo incluye un dato que permite corregir la situación —cuánto espacio queda, cuánto lugar tiene el álbum—, ese dato SHALL formar parte de lo que se muestra.

Cuando el motivo sea uno que quien lo recibe no puede resolver, porque lo que falta no está bajo su control, SHALL decirse como tal. SHALL NOT indicársele una acción que no va a cambiar el resultado —eliminar fotos propias cuando el espacio que falta es el de la instancia y el suyo le sobra—. Un motivo que manda a hacer algo inútil es peor que uno escueto: cuesta tiempo y deja creyendo que el problema es propio cuando no lo es.

Cuando el motivo admita reintentar, SHALL ofrecerse reintentar ese archivo y solo ese.

#### Scenario: Un archivo que no entra explica por qué y cuánto falta

- **WHEN** un archivo no recibe permiso porque no hay espacio disponible
- **THEN** su bloque dice que no hay espacio
- **AND** dice cuánto espacio queda

#### Scenario: Un motivo que no depende de quien sube no le pide que actúe

- **WHEN** un archivo no recibe permiso porque no hay espacio en la instancia y la cuenta de quien sube tiene lugar de sobra
- **THEN** su bloque dice que el espacio que falta no es el suyo
- **AND** no le indica eliminar fotos propias

#### Scenario: Un fallo de transferencia se puede reintentar solo

- **WHEN** un archivo falla al transferirse y otros del mismo lote van bien
- **THEN** se ofrece reintentar ese archivo
- **AND** reintentarlo no vuelve a subir los que ya terminaron
