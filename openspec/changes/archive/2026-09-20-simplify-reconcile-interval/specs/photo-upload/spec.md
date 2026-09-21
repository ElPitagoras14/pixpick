## MODIFIED Requirements

### Requirement: Una subida abandonada no ensucia el álbum y puede descartarse

Una foto que quedó no disponible porque nadie subió su objeto SHALL ser inocua: SHALL NOT aparecer en ninguna lectura y SHALL NOT poder pasar a disponible una vez que su permiso venció.

SHALL existir una forma de descartar esos registros y los objetos huérfanos, y esa limpieza SHALL ejecutarse periódicamente sin intervención, con un intervalo fijo en el código y no declarado en la configuración del entorno: ningún despliegue de este proyecto ha necesitado un ritmo de limpieza distinto del otro. No alcanza con que sea posible ejecutarla: un objeto huérfano ocupa espacio que ninguna de las tres cuotas contabiliza, porque una vez vencido su permiso deja de contar, de modo que dejar la limpieza librada a que alguien se acuerde convierte el techo de la instancia en un número que no describe lo que hay. SHALL seguir siendo invocable a mano además de periódicamente.

#### Scenario: Una subida abandonada nunca se vuelve visible

- **WHEN** se concede una subida y nadie sube el archivo
- **THEN** la foto nunca aparece en el álbum

#### Scenario: Un permiso vencido ya no permite completar la subida

- **WHEN** se intenta subir el archivo después de que el permiso venció
- **THEN** la escritura se rechaza
- **AND** la foto sigue no disponible

#### Scenario: Los restos se pueden descartar

- **WHEN** se ejecuta la operación de limpieza
- **THEN** los registros no disponibles con permiso vencido y los objetos huérfanos quedan eliminados

#### Scenario: La limpieza ocurre sola

- **WHEN** transcurre el intervalo fijo desde la última limpieza
- **THEN** la limpieza vuelve a ejecutarse
- **AND** nadie tuvo que invocarla

#### Scenario: Cambiar el ritmo de la limpieza requiere tocar el código

- **WHEN** se busca una variable de entorno que gobierne cada cuánto corre la limpieza
- **THEN** no existe
- **AND** quien necesite otro ritmo edita el valor fijo

#### Scenario: Muchos restos acumulados se limpian igual

- **WHEN** la limpieza encuentra más objetos huérfanos de los que el almacenamiento admite eliminar en una petición
- **THEN** todos quedan eliminados
