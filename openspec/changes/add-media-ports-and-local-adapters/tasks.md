## 1. Los dos servicios en el entorno

- [ ] 1.1 Agregar el almacenamiento de objetos al compose con versión exacta y su volumen de datos; verificar que arranca y que reporta estado saludable antes de que nada dependa de él.
- [ ] 1.2 Dejar creado el espacio de trabajo del almacenamiento y **declarados los orígenes admitidos** al levantar el entorno, sin pasos manuales; verificar levantando desde cero que el espacio existe y que la declaración de orígenes ya está aplicada.
- [ ] 1.3 Agregar el transformador al compose con versión exacta y sus claves de firma, **sin declararle presets**: las variantes viven en el catálogo del proyecto y llegan ya especificadas en cada dirección (D6); verificar que arranca y que rechaza una petición sin firma.
- [ ] 1.4 Publicar al host el puerto del almacenamiento, porque el navegador escribe directo contra él (D3); verificar que el transformador no publica ningún puerto, dado que solo se lo alcanza por el edge, y que sigue cumpliéndose que ningún servicio propio del proyecto se expone.
- [ ] 1.5 Declarar en el archivo de ejemplo del entorno, **en los dos perfiles** de D10 de `add-local-environment`, el proveedor activo de cada puerto, las dos direcciones del almacenamiento, sus credenciales y las claves de firma del transformador; verificar que los nombres de variable son idénticos en los dos perfiles y que cada uno tiene consumidor.

## 2. El edge: el espacio reservado de las imágenes

- [ ] 2.1 Agregar al edge el espacio reservado de las imágenes proxeando al transformador, con la zona de cache en disco acotada al tamaño y al plazo de inactividad que fija D12; verificar que una variante se entrega y que la segunda petición por la misma no vuelve a transformar.
- [ ] 2.2 Configurar el colapso de peticiones simultáneas por la misma variante; verificar con varias peticiones concurrentes por una variante no producida que la transformación ocurre una sola vez y todas reciben el resultado.
- [ ] 2.3 Configurar la entrega de lo ya cacheado cuando el transformador no responde; verificar apagándolo que una variante ya producida se sigue entregando y que una no producida responde un error y no el documento de la interfaz.
- [ ] 2.4 Verificar que el fallback de la interfaz no alcanza al espacio de las imágenes: pedir una imagen inexistente devuelve un error y no un documento con respuesta satisfactoria.
- [ ] 2.5 Agregar el reenvío del espacio de las imágenes al servidor de desarrollo de la interfaz, para que el modo nativo se comporte igual (D10 de `add-local-environment`); verificar que en modo nativo una variante se entrega por el mismo origen desde el que se cargó la interfaz.
- [ ] 2.6 Verificar que ninguna directiva de cacheo o de cabeceras del espacio de imágenes duplica una del nginx del frontend, según la regla de reparto de D1 de `add-local-environment`.

## 3. El puerto de almacenamiento y su adapter local

- [ ] 3.1 Definir el puerto con sus tres operaciones y las formas de dato que devuelven, sin ninguna que lea contenido (D2); verificar leyendo el puerto que no existe operación de lectura de bytes.
- [ ] 3.2 Definir el esquema de nombres de objeto derivado de identificadores del dominio y prefijado por álbum; verificar que dos archivos con el mismo nombre original no colisionan, que los objetos de un álbum comparten prefijo, y que el nombre no depende de nada que el cliente controle.
- [ ] 3.3 Implementar el doble en memoria con comportamiento real y no como registrador de llamadas (D10): rechaza una concesión vencida, rechaza escribir un objeto distinto del concedido, y distingue un objeto ausente de uno de tamaño cero; verificar los tres casos.
- [ ] 3.4 Implementar el adapter del almacenamiento local: firmar la concesión contra la dirección del navegador y consultar y eliminar contra la dirección del servidor (D4), con el cliente sincrónico y apartando del bucle de eventos únicamente las dos operaciones que hacen red (D8); verificar que conceder una subida no emite ninguna petición.
- [ ] 3.5 Traducir los fallos del proveedor a errores de dominio; verificar que con el almacenamiento caído el consumidor recibe un error de dominio y que nada de lo que sale identifica al proveedor ni repite su mensaje.
- [ ] 3.6 Implementar la selección de proveedor de almacenamiento por variable, con fallo en el arranque ante un valor desconocido; verificar que el servicio no arranca y que el error nombra los valores admitidos.

## 4. El puerto de transformación y su adapter local

- [ ] 4.1 Definir el puerto con su única operación y el conjunto cerrado de variantes con nombre; verificar que no admite declarar medidas ni ningún otro parámetro de transformación.
- [ ] 4.2 Declarar el catálogo de variantes en el proyecto con el nombre, las medidas, la calidad, el formato y la regla de no ampliar de cada una (D6, D11); verificar que es la única declaración de esas características en el repositorio.
- [ ] 4.3 Implementar el adapter del transformador local traduciendo el catálogo a las opciones de procesamiento completas y firmando la dirección (D6); verificar que construir las direcciones de un álbum entero no emite ninguna petición y que se puede construir con el transformador caído.
- [ ] 4.4 Implementar la selección de proveedor de transformación por variable, con fallo en el arranque ante un valor desconocido; verificar el fallo de arranque.
- [ ] 4.5 Verificar que la regla de no ampliar llega efectivamente en la dirección: un original más chico que la variante se entrega con su tamaño original y no escalado.

## 5. El contrato, verificado

- [ ] 5.1 Escribir la suite de contrato del almacenamiento **una sola vez, parametrizada por implementación** (D9); verificar que se ejecuta contra el doble y contra el proveedor real con el mismo código de prueba.
- [ ] 5.2 Cubrir en esa suite todos los casos que el spec exige: concesión acotada a un único objeto, concesión vencida, límite de tamaño impuesto por el almacenamiento y no por la aplicación, objeto ausente distinguible de uno vacío, y eliminación idempotente y en lote.
- [ ] 5.3 Escribir la prueba de que cada variante del catálogo produce una dirección válida con el adapter activo, y de que **cambiar una medida en el catálogo cambia la dirección** (D6, D7); verificar que esa segunda parte falla si alguien reintrodujera presets, porque entonces la dirección no cambiaría.
- [ ] 5.4 Escribir la prueba de que las direcciones firmadas son estables para la misma entrada y de que alterar cualquier parte de una dirección invalida su firma.
- [ ] 5.5 Verificar que la suite completa corre con un solo comando, sin preparación manual y sin acceso a internet.

## 6. Documentación

- [ ] 6.1 Actualizar el README con qué variantes existen y para qué sirve cada una, dónde se declaran, por qué cambiarlas invalida el cache sola, cómo inspeccionar el almacenamiento local, y qué valores difieren entre los dos modos de trabajo; verificar siguiendo las instrucciones tal como están escritas.

## 7. Verificación integral

- [ ] 7.1 Recorrer el ciclo completo a mano usando la consola interactiva del backend, dado que este change no expone endpoints: pedir una concesión, subir un archivo con ella, consultar el objeto, y pedir sus tres variantes por el edge.
- [ ] 7.2 Verificar la subida desde el navegador **en los dos modos de trabajo**, porque la negociación de origen no la ejercita ninguna prueba del backend y es la falla más probable de este change (Risks).
- [ ] 7.3 Verificar la invalidación de punta a punta: cambiar una medida en el catálogo, volver a pedir la variante y comprobar que llega la nueva **sin tocar el cache y sin reiniciar el transformador**, que ya no participa de esa definición.
- [ ] 7.4 Verificar que el cache respeta su cota: superar el tamaño máximo y comprobar que expulsa entradas viejas en lugar de seguir creciendo.
- [ ] 7.5 Verificar que ningún byte de imagen atravesó la aplicación en todo el ciclo, ni al subir ni al entregar (D2).
