## 1. El consumo se puede calcular

- [ ] 1.1 Agregar el límite a la configuración de fotos y a `.env.example`, junto al máximo por álbum (D1 del proposal). Verificar que el backend arranca con el valor por defecto de 150 MiB y que cambiarlo en el entorno cambia el valor efectivo.
- [ ] 1.2 Escribir en el repositorio la consulta que suma el consumo de una persona: tamaño real de las disponibles más declarado de las pendientes con permiso vigente (D2). Verificar con una prueba que arma las tres situaciones —disponible, pendiente vigente, pendiente vencida— y comprueba que la tercera no suma.
- [ ] 1.3 Escribir la consulta del consumo por álbum y la del tamaño por foto de un álbum (D3). Verificar que la suma de las fotos de un álbum coincide con el total de ese álbum, y que la suma de los álbumes de una persona coincide con su total.

## 2. El consumo se puede consultar

- [ ] 2.1 Agregar el recurso de la cuenta, que devuelve el consumo total, el límite y el desglose por álbum (D3). Verificar que responde solo sobre la propia cuenta y que no existe forma de pedir el de otra persona.
- [ ] 2.2 Agregar el recurso del álbum, que devuelve su total y el tamaño de cada una de sus fotos (D3). Verificar con una prueba que el dueño lo obtiene y que quien accede al álbum por un enlace compartido no.
- [ ] 2.3 Verificar que ninguna respuesta existente cambió de forma: la lista de álbumes, el detalle, la galería y las estadísticas devuelven exactamente los mismos campos que antes.

## 3. El límite se hace valer al conceder

- [ ] 3.1 Escribir primero la prueba de concurrencia que hoy no puede pasar: dos lotes pedidos a la vez en dos álbumes distintos de la misma persona, que entre los dos excederían su espacio. Verificar que **falla** contra el código actual, porque cada uno bloquea su propio álbum y ninguno ve al otro.
- [ ] 3.2 Reemplazar el bloqueo de la fila del álbum por el de la fila de la persona, conservando la comprobación de pertenencia como consulta aparte (D1). Verificar que la prueba de 3.1 pasa y que las pruebas de concurrencia que ya existían siguen pasando sin modificarse: son las que demuestran que el bloqueo nuevo cubre lo que cubría el viejo.
- [ ] 3.3 Evaluar los dos límites por archivo al conceder, y recorrer el lote salteando el que no entra en lugar de cortar en el primero (D5). Verificar con una prueba donde un archivo grande queda afuera y uno más chico que viene después sí entra.
- [ ] 3.4 Cambiar la respuesta del pedido de permisos a dos listas —concedidos y no concedidos—, cada entrada con el índice que el archivo tenía en el pedido, y cada rechazo con su motivo y cuánto quedaba (D4). Verificar que pedir N archivos con espacio para M devuelve M permisos y N−M rechazos, y que los índices permiten reconstruir qué archivo es cada uno.
- [ ] 3.5 Distinguir el motivo "álbum lleno" del motivo "cuenta sin espacio" en la respuesta. Verificar con dos pruebas que provocan cada caso por separado, y una tercera donde el álbum tiene lugar pero la cuenta no.
- [ ] 3.6 Actualizar las pruebas existentes que afirman el rechazo total del lote por álbum lleno: pasan a esperar concesión parcial. Verificar que ninguna quedó afirmando el comportamiento viejo, y que las del rechazo total por archivo inadmisible siguen intactas, porque ese caso no cambia.

## 4. La interfaz muestra el consumo y explica los recortes

- [ ] 4.1 Agregar a la cola de subida el estado por archivo para el que se pidió y no se concedió, con su motivo (D4). Verificar que un lote parcialmente concedido deja unos archivos subiendo y otros detenidos con su explicación, sin que ninguno quede en un estado ambiguo.
- [ ] 4.2 Mostrar en la vista de subida el espacio disponible antes de elegir archivos (D6). Verificar que el valor coincide con el del recurso de la cuenta y que se actualiza después de subir.
- [ ] 4.3 Mostrar en la home el consumo total contra el límite. Verificar que una cuenta vacía y una cuenta llena se distinguen a simple vista.
- [ ] 4.4 Mostrar en la lista de álbumes lo que ocupa cada uno. Verificar que la suma de lo mostrado coincide con el total de la home.
- [ ] 4.5 Mostrar el tamaño de cada foto en la tira que el dueño ya ve bajo la miniatura, junto a los contadores de calificaciones. Verificar que quien accede al álbum por un enlace compartido no ve ni la tira ni el tamaño.

## 5. Verificación final

- [ ] 5.1 Recorrer el ciclo completo con una cuenta real: subir hasta acercarse al límite, pedir un lote que no entre entero, comprobar que sube lo que entra y que lo demás se explica por archivo, eliminar fotos, y comprobar que el espacio liberado vuelve a habilitar la subida.
- [ ] 5.2 Verificar que estar lleno no rompe nada más: con la cuenta en el límite, ver álbumes, calificar fotos, compartir y eliminar siguen funcionando igual.
- [ ] 5.3 Verificar el caso del límite reducido: bajar el valor en el entorno por debajo de lo que una cuenta ya ocupa, y comprobar que conserva todas sus fotos y que solo se le rechaza agregar.
- [ ] 5.4 Correr la suite completa del backend con `ruff format` y `ruff check`, y el linter del frontend, y verificar que todo termina limpio.
- [ ] 5.5 Correr `openspec validate --changes add-account-quota --strict` y verificar que pasa.
