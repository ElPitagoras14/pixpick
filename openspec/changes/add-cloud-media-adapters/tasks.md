## 1. El catálogo, que ya está unificado

- [ ] 1.1 Verificar que el catálogo de variantes del proyecto no necesita ningún cambio para dar soporte al proveedor nuevo, y que sigue siendo la única declaración de medidas, calidad y formato del repositorio (D1).
- [ ] 1.2 Verificar que ningún transformador tiene declaración de presets, ni el local ni el cloud: las variantes llegan especificadas en cada dirección.

## 2. El adapter de almacenamiento cloud

- [ ] 2.1 Implementar el adapter reutilizando el cliente del protocolo que ya existe (D2); verificar que lo que difiere del local es la configuración y no la lógica.
- [ ] 2.2 Configurar las dos direcciones del almacenamiento, que con este proveedor coinciden, **sin introducir una rama para ese caso** (D7); verificar que el modo local sigue usando dos valores distintos y que el código no distingue entre las dos situaciones.
- [ ] 2.3 Crear el espacio de almacenamiento en el proveedor y declarar los orígenes admitidos con la interfaz que ofrezca; verificar subiendo un archivo desde el navegador, no solo desde el backend.
- [ ] 2.4 Registrar el adapter en la selección por variable; verificar que un valor desconocido sigue impidiendo el arranque y que faltan credenciales impide el arranque cuando este proveedor es el activo.

## 3. El adapter de transformación cloud

- [ ] 3.1 Implementar la construcción de direcciones traduciendo el catálogo al vocabulario del proveedor (D1); verificar que para cada variante del catálogo produce una dirección válida.
- [ ] 3.2 Implementar la firma de las direcciones con la biblioteca estándar del lenguaje (D8); verificar que alterar cualquier parte de una dirección invalida su firma y que no se agregó ninguna dependencia.
- [ ] 3.3 Apuntar la cuenta del transformador al almacenamiento cloud como origen; verificar que una variante se entrega efectivamente desde el proveedor.
- [ ] 3.4 Verificar la equivalencia exigida por el spec: la misma variante produce imágenes con las mismas medidas y el mismo formato con el proveedor local y con el cloud, comparando los resultados y no las configuraciones.
- [ ] 3.5 Verificar que el proveedor cloud puede producir **todas** las variantes del catálogo; si alguna no fuera posible, es un hallazgo que se resuelve reduciendo el conjunto o descartando el proveedor, nunca dejando esa variante disponible solo con el otro.

## 4. El contrato y las pruebas

- [ ] 4.1 Parametrizar la suite de contrato del almacenamiento para que acepte al proveedor cloud como una implementación más; verificar que **las pruebas no se modifican**, porque si hubiera que ajustarlas lo que falló es el contrato.
- [ ] 4.2 Omitir esa ejecución de forma visible cuando no hay credenciales configuradas (D3); verificar que la suite completa pasa sin acceso a internet y que la omisión aparece en la salida, para que nadie confunda "no se probó" con "pasó".
- [ ] 4.3 Verificar que la suite de contrato pasa contra el proveedor cloud con las credenciales configuradas.
- [ ] 4.4 Escribir las pruebas de las direcciones firmadas del transformador cloud: estabilidad para la misma entrada y invalidación ante cualquier alteración.

## 5. Configuración y bases por conjunto de proveedores

- [ ] 5.1 Agregar al archivo de ejemplo del entorno los valores de los proveedores cloud y el nombre de base que corresponde a cada conjunto de proveedores (D4); verificar que los nombres de variable son idénticos en todos los casos y que solo cambian los valores.
- [ ] 5.2 Verificar que alternar de conjunto de proveedores y volver encuentra los datos anteriores intactos, sin haber reseteado ni filtrado nada.
- [ ] 5.3 Verificar que cambiar de **modo de ejecución** —todo en contenedores o backend nativo— **no** cambia de base: los mismos datos se ven en los dos, porque ese eje solo cambia el host con el que se la alcanza.
- [ ] 5.4 Verificar que al usar por primera vez la base de un conjunto de proveedores, las migraciones se aplican solas antes de que el backend atienda, sin ningún paso manual.

## 6. El cambio de proveedor en un entorno con datos

- [ ] 6.1 Extender el comando de reconciliación para que acepte contra qué proveedor comparar, con el activo por omisión (D6); verificar que no requirió más que ese parámetro.
- [ ] 6.2 Recorrer el procedimiento completo en un entorno de prueba con datos: copiar los objetos, comprobar que no falta ninguno, cambiar la variable, y comprobar que todas las imágenes resuelven.
- [ ] 6.3 Verificar el caso negativo, que es el que justifica el procedimiento: con una copia deliberadamente incompleta, la comprobación enumera qué falta **mientras el proveedor activo todavía no cambió**.

## 7. Documentación

- [ ] 7.1 Actualizar el README con la puesta en marcha de cada proveedor cloud, el procedimiento de cambio con su orden —copiar, comprobar, cambiar—, y la relación entre conjuntos de proveedores y bases de datos, distinguiéndola del modo de ejecución; verificar siguiendo las instrucciones tal como están escritas.

## 8. Verificación integral

- [ ] 8.1 Recorrer el flujo completo del producto con los proveedores cloud activos: crear un álbum, subir fotos, compartirlo, calificar con otra cuenta y ver los resultados.
- [ ] 8.2 Verificar la subida desde el navegador contra el proveedor cloud, que es donde una declaración de orígenes mal hecha falla con poca información y donde ninguna prueba del backend llega.
- [ ] 8.3 **Revisar el diff completo y confirmar que no hay cambios en el dominio, los endpoints, la interfaz ni el esquema.** Si los hay, es un hallazgo sobre el diseño de los puertos y corresponde tratarlo como tal antes de dar el change por terminado.
- [ ] 8.4 Verificar que el modo local sigue funcionando exactamente igual que antes de este change, incluido el cache de imágenes del edge.
