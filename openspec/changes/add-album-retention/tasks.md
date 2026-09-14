## 1. El plazo y su punto de partida

- [ ] 1.1 Escribir la migración que agrega a `albums` la columna del instante desde el que corre el plazo, inicializada con el momento de aplicarla y no con la fecha de creación de cada álbum (D1, plan de migración). Regenerar `schema.sql` y verificar que el rollback deja el esquema idéntico al anterior.
- [ ] 1.2 Agregar el plazo a la configuración y a `.env.example` (D1). En su explicación, decir que bajarlo tiene efecto inmediato sobre los álbumes que ya existen: es la contracara de que el valor sea configurable de verdad, y quien lo cambie tiene que saberlo antes y no después.

## 2. La vigencia se evalúa en un solo lugar

- [ ] 2.1 Definir la condición de vigencia en un único lugar del repositorio de álbumes y hacer que todas las lecturas existentes la compongan (D2). Verificar que un álbum cuyo instante de referencia quedó más atrás que el plazo desaparece del listado y de la lectura directa, y que pedirlo responde igual que un álbum inexistente.
- [ ] 2.2 Escribir la prueba que recorre el código del backend y falla si alguna consulta lee la tabla de álbumes sin pasar por esa condición (D2). Verificar que **falla** al agregarle a propósito una consulta directa, y que pasa al quitarla.
- [ ] 2.3 Hacer que la consulta de consumo de la cuenta componga la misma condición (D5). Verificar que un álbum vencido deja de contar para el límite en el instante del vencimiento, sin que se haya borrado ningún objeto.
- [ ] 2.4 Verificar que un enlace compartido hacia un álbum vencido no otorga acceso y responde sin revelar que ese álbum existió.
- [ ] 2.5 Verificar que pedir permisos de subida para un álbum vencido responde como si el álbum no existiera.

## 3. Solo subir renueva el plazo

- [ ] 3.1 Actualizar el instante de referencia dentro de la misma transacción que deja una foto disponible (D4). Verificar con una prueba que una confirmación que se deshace tampoco mueve el plazo.
- [ ] 3.2 Escribir las pruebas de lo que **no** renueva: calificar, generar o revocar un enlace, renombrar el álbum, eliminar fotos —incluida la última subida— y un permiso de subida que venció sin completarse. Verificar que en los seis casos el vencimiento es el mismo antes y después.
- [ ] 3.3 Verificar que un álbum sin ninguna foto cuenta su plazo desde la creación, y que la primera foto que queda disponible lo corre.

## 4. Lo vencido se elimina del almacenamiento

- [ ] 4.1 Mover el comando de limpieza a un módulo de mantenimiento propio, conservando su opción de comprobación contra otro proveedor (D3). Verificar que la invocación documentada en el README sigue funcionando con la ruta nueva y que sus pruebas existentes pasan sin cambios de comportamiento.
- [ ] 4.2 Agregar al comando la eliminación de álbumes vencidos con sus fotos y sus objetos, borrando filas y confirmando antes de tocar el almacenamiento, como hace el resto de los borrados del proyecto (D3). Verificar que después de correrlo no queda ningún objeto de álbumes vencidos.
- [ ] 4.3 Verificar que la demora no tiene efecto observable: con un álbum vencido y el comando sin correr, nadie lo ve, su enlace no resuelve, y su espacio ya no cuenta para la cuenta de su dueño.
- [ ] 4.4 Actualizar el README con el comando unificado, diciendo en una línea qué descarta y por qué no correrlo solo cuesta espacio en el proveedor.

## 5. El plazo restante se ve

- [ ] 5.1 Devolver el instante de vencimiento en la respuesta del álbum y en la del listado (D6), y verificar que el cliente es quien lo convierte en texto y no el backend.
- [ ] 5.2 Mostrar cuánto le queda a cada álbum en la lista y en la vista del álbum. Verificar que también lo ve quien accede por un enlace compartido, que es quien más lo necesita para terminar de calificar a tiempo.
- [ ] 5.3 Verificar que subir una foto actualiza el plazo mostrado sin recargar la página.
- [ ] 5.4 Verificar que un álbum que vence mientras alguien lo tiene abierto se comporta como uno eliminado, reutilizando el camino que la interfaz ya recorre para ese caso.

## 6. Verificación final

- [ ] 6.1 Recorrer el vencimiento de verdad, no simulado: bajar el plazo a un par de minutos en el entorno, crear un álbum con fotos, esperar a que venza, y comprobar en ese orden que desaparece del listado, que su enlace deja de resolver, que su espacio se liberó, y que recién después el comando borra sus objetos.
- [ ] 6.2 Verificar la interacción con el límite de la cuenta: con una cuenta en su límite, dejar vencer un álbum y comprobar que se puede volver a subir por el espacio que liberó, antes de correr ninguna limpieza.
- [ ] 6.3 Verificar que bajar el plazo por debajo de la antigüedad de álbumes existentes los vence a todos de inmediato, que es el comportamiento que el spec exige, y devolver el valor al original.
- [ ] 6.4 Correr la suite completa del backend con `ruff format` y `ruff check`, y el linter del frontend, y verificar que todo termina limpio.
- [ ] 6.5 Correr `openspec validate --changes add-album-retention --strict` y verificar que pasa.
