## 1. El total de la instancia se puede calcular

- [x] 1.1 Agregar el límite de la instancia a la configuración de fotos y a `.env.example`, junto a los dos que ya viven ahí, y bajar el límite por cuenta a 120 MiB (D6). Verificar que el backend arranca con 6 GiB por omisión cuando la variable falta, y que declararla en el entorno cambia el valor efectivo.
- [x] 1.2 Escribir en el repositorio de `quota` la suma del consumo de la instancia, reusando las constantes que ya definen qué bytes aporta cada foto, qué fotos cuentan y qué álbumes están activos (D2). Verificar con una prueba que arma fotos de dos dueños distintos y comprueba que el total incluye las de ambos.
- [x] 1.3 Verificar con una prueba que la suma de la instancia y la de la cuenta no cuentan cosas distintas: sobre un mismo conjunto de fotos de un solo dueño —con una disponible, una pendiente vigente, una pendiente vencida y una de un álbum dado de baja por retención— los dos totales coinciden.

## 2. El total de la instancia se puede consultar

- [x] 2.1 Agregar el recurso que devuelve el porcentaje ocupado de la instancia, nunca el total ni el límite en bytes (D3, revisado a pedido del usuario). Verificar que cualquier persona con sesión iniciada lo obtiene, sin requerir ser dueña de nada, y que sin sesión no se obtiene.
- [x] 2.2 Verificar que el recurso no revela el total ni el límite en bytes de la instancia, ni cuánto ocupa ninguna cuenta en particular, y que el recurso del consumo de la cuenta devuelve exactamente los mismos campos que antes.

## 3. El límite se hace valer al conceder

- [x] 3.1 Escribir primero la prueba de concurrencia que hoy no puede pasar: dos personas distintas pidiendo a la vez sendos lotes que entre los dos excederían el espacio de la instancia. Verificar que **falla** contra el código actual, porque cada una bloquea su propia fila y ninguna ve a la otra.
- [x] 3.2 Reemplazar el bloqueo de la fila de la persona por el advisory lock de clave fija, conservando sin bloqueo la comprobación de que la persona existe (D1). Verificar que la prueba de 3.1 pasa y que las pruebas de concurrencia que ya existían siguen pasando sin modificarse: son las que demuestran que la exclusión nueva cubre lo que cubría la vieja.
- [x] 3.3 Evaluar el límite de la instancia como tercera comprobación por archivo, después de la de la cuenta, descontando de su remanente a medida que se concede (D4). Verificar con una prueba donde un archivo grande queda afuera por la instancia y uno más chico que viene después sí entra.
- [x] 3.4 Agregar el motivo de rechazo por instancia llena a la respuesta del pedido de permisos. Verificar con tres pruebas: cuenta con lugar e instancia llena devuelve el motivo de instancia; cuenta llena e instancia con lugar devuelve el de cuenta; y las dos llenas devuelve el de cuenta, que es la precedencia que el spec exige.

## 4. La interfaz muestra la instancia y explica el motivo nuevo

- [x] 4.1 Generalizar el medidor que hoy muestra el consumo de la cuenta para que reciba qué nombra y qué decir cuando no queda lugar (D5). Verificar que el medidor de la cuenta sigue mostrando exactamente lo que mostraba antes.
- [x] 4.2 Mostrar el medidor de la instancia junto al de la cuenta en la primera pantalla después de iniciar sesión. Verificar que se distingue cuál es cuál sin mirar los números, y que si el pedido del consumo de la instancia falla o tarda, el resto de la pantalla se dibuja igual.
- [x] 4.3 Agregar a la cola de subida el texto del motivo nuevo, junto a los dos que ya muestra. Verificar que un archivo rechazado por instancia llena dice que el espacio que falta no es el suyo y **no** le indica eliminar fotos propias, y que uno rechazado por cuenta llena sigue diciendo cuánto espacio le queda.

## 5. Verificación final

- [x] 5.1 Recorrer el ciclo completo con dos cuentas reales: llenar la instancia desde una, comprobar desde la otra que no recibe permiso y que el motivo no la manda a borrar nada suyo, liberar espacio desde la primera, y comprobar que la segunda vuelve a poder subir.
- [x] 5.2 Verificar que la instancia llena no impide nada más: crear una cuenta nueva, iniciar sesión, ver álbumes, calificar, compartir y eliminar siguen funcionando igual para todas las cuentas.
- [x] 5.3 Verificar el caso del límite reducido en los dos alcances: bajar el límite de la instancia por debajo de lo que ya ocupa, y comprobar que ninguna cuenta pierde fotos y que lo único que se rechaza es agregar. Comprobar lo mismo para una cuenta que quedó por encima de los 120 MiB nuevos.
- [x] 5.4 Correr la suite completa del backend con `ruff format` y `ruff check`, y el linter del frontend, y verificar que todo termina limpio.
- [x] 5.5 Correr `openspec validate --changes add-instance-quota --strict` y verificar que pasa.
