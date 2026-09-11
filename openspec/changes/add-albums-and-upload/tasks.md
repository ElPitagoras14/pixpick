## 1. Esquema: álbumes, fotos y la vista de disponibles

- [ ] 1.1 Escribir la migración con las tablas de álbumes y fotos: dueño con eliminación en cascada, título obligatorio, descripción opcional, posición, estado de disponibilidad, y el trigger de última modificación en las dos; verificar aplicando la migración y haciendo rollback que el esquema queda como estaba.
- [ ] 1.2 Crear en la misma migración la vista que expone únicamente las fotos disponibles (D1); verificar que consultarla no requiere ninguna condición adicional y que una foto no disponible no aparece en ella.
- [ ] 1.3 Regenerar el archivo del esquema; verificar que refleja las dos tablas, la vista, las eliminaciones en cascada y los dos triggers.
- [ ] 1.4 Verificar que la prueba de triggers de `add-backend-data-layer` ahora cubre las cuatro tablas del proyecto y que fallaría si a alguna le faltara.
- [ ] 1.5 Agregar los constructores compartidos de álbum y de foto, con la foto disponible por defecto y una variante no disponible; verificar que una prueba puede crear un álbum con fotos declarando únicamente el título.

## 2. Álbumes

- [ ] 2.1 Implementar la creación de álbumes con la validación del título; verificar que la ausencia de título y un título compuesto solo de espacios se rechazan igual, nombrando el campo.
- [ ] 2.2 Implementar el listado resolviendo portada y conteo en una única consulta (D9, D10); verificar con varios álbumes y varias fotos que no se emite una consulta por álbum, y que un álbum vacío aparece con cero fotos y sin portada.
- [ ] 2.3 Implementar ver, renombrar y eliminar con la autorización del dueño; verificar con una segunda cuenta que las tres operaciones sobre un álbum ajeno responden igual que sobre uno inexistente y que el álbum no se modifica.
- [ ] 2.4 Implementar la eliminación como transacción de registros seguida de la eliminación de objetos, nunca dentro de la transacción (D6); verificar que los objetos se eliminan y que un fallo al eliminarlos no deja ningún registro apuntando a un objeto inexistente.
- [ ] 2.5 Verificar que renombrar un álbum no altera sus fotos, su orden ni su disponibilidad.

## 3. Subida: conceder

- [ ] 3.1 Implementar la concesión por lote con la validación de tipo y tamaño **antes** de emitir cualquier permiso (D2, D3); verificar que un archivo inadmisible rechaza el lote completo y que la respuesta nombra el archivo y el motivo.
- [ ] 3.2 Aplicar el techo del lote en cincuenta (D13); verificar que un lote mayor se rechaza antes de emitir permisos.
- [ ] 3.3 Implementar el máximo por álbum leído de la configuración, contando las fotos disponibles más las que esperan confirmación con permiso vigente (D14); verificar los cinco escenarios del spec, en particular que las esperas ocupan lugar, que las vencidas dejan de ocuparlo, y que reducir el máximo no toca los álbumes existentes.
- [ ] 3.4 Registrar las fotos como no disponibles y asignar sus posiciones dentro de la misma transacción que los inserta (D12); verificar que dos lotes concedidos a la vez sobre el mismo álbum no reclaman las mismas posiciones.
- [ ] 3.5 Agregar el máximo de fotos por álbum al archivo de ejemplo del entorno, en los dos perfiles; verificar que tiene consumidor y que los nombres coinciden entre perfiles.
- [ ] 3.6 Mapear el rechazo por máximo alcanzado como conflicto de estado y no como error de validación (delta de `api-conventions`); verificar que la respuesta indica cuánto espacio queda y que no señala ningún campo de la petición como inválido.

## 4. Subida: confirmar y calentar

- [ ] 4.1 Implementar la confirmación consultando el objeto y comparando con lo declarado; verificar los tres desenlaces: objeto ausente deja la foto no disponible, objeto que no coincide se rechaza y el objeto se elimina, y objeto que coincide deja la foto disponible con su tamaño real.
- [ ] 4.2 Verificar que confirmar una foto que ya estaba disponible es inofensivo, y que confirmar una que nunca se subió no rompe nada porque la verificación es contra el objeto (D4).
- [ ] 4.3 Implementar el calentamiento como **una sola tarea diferida por lote**, con la cantidad de peticiones en curso acotada, un tiempo de espera corto, y las peticiones dirigidas **al edge y no al transformador** (D7); verificar que después de confirmar el cache del edge efectivamente contiene la variante, no solamente que la tarea no falló.
- [ ] 4.4 Verificar que un fallo de calentamiento no altera la respuesta, no altera el estado de las fotos y no produce ningún error visible para quien subió.
- [ ] 4.5 Verificar que la respuesta de la confirmación llega sin esperar a que las variantes estén producidas.

## 5. Eliminar fotos y reconciliar

- [ ] 5.1 Implementar la eliminación de una foto con su objeto, registro primero (D6); verificar que un fallo al eliminar el objeto no deja el registro y que el objeto queda identificable como huérfano.
- [ ] 5.2 Implementar el comando de reconciliación que descarta los registros no disponibles con permiso vencido y los objetos sin registro (D8); verificar que elimina ambas cosas y que no toca ninguna foto disponible.
- [ ] 5.3 Verificar que una subida abandonada nunca se vuelve visible y que intentar subir el archivo con el permiso ya vencido se rechaza.

## 6. Interfaz: álbumes

- [ ] 6.1 Implementar la feature de álbumes con su factory de opciones de consulta, la lista y el estado vacío; verificar que mostrar la lista no emite una petición por álbum.
- [ ] 6.2 Crear las rutas del álbum con el layout que lo carga una sola vez (D11); verificar que las vistas hijas leen el álbum del layout y no vuelven a pedirlo.
- [ ] 6.3 Implementar la vista de creación de álbum; verificar que el error de título se muestra en el campo y no como un error general.
- [ ] 6.4 Implementar el grid del álbum con las miniaturas, reservando la relación de aspecto de cada foto con las dimensiones declaradas; verificar que no hay salto de layout mientras las imágenes cargan.
- [ ] 6.5 Implementar la eliminación de álbum y de foto con confirmación previa; verificar que la lista y el grid reflejan el cambio sin recargar la página.

## 7. Interfaz: la cola de subida

- [ ] 7.1 Implementar el selector de archivos con la validación del cliente antes de pedir nada (D3); verificar que un archivo inadmisible se informa de inmediato sin emitir ninguna petición.
- [ ] 7.2 Implementar la cola con estado por archivo, cantidad de subidas en curso acotada y reintento individual (D5); verificar que reintentar reintenta únicamente el archivo que falló y que los demás no se vuelven a subir.
- [ ] 7.3 Partir una selección mayor al techo del lote en lotes sucesivos **enviados en orden y no en paralelo** (D13); verificar con una selección de sesenta archivos que las fotos quedan en el álbum en el orden en que se eligieron.
- [ ] 7.4 Mostrar el progreso por archivo y confirmar al final únicamente los que llegaron a subirse; verificar interrumpiendo una subida que el resto se confirma y el interrumpido queda pendiente.
- [ ] 7.5 Verificar que la comprobación de estilo y la construcción del frontend pasan sin errores.

## 8. Documentación

- [ ] 8.1 Actualizar el README con el flujo de crear un álbum y subir fotos, el significado del máximo configurable —que condiciona agregar y no invalida lo guardado— y el comando de reconciliación; verificar siguiendo las instrucciones tal como están escritas.

## 9. Verificación integral

- [ ] 9.1 Recorrer el flujo completo: crear un álbum, subir un lote de fotos y verlas en el grid con sus miniaturas.
- [ ] 9.2 Verificar que una foto no disponible no aparece en el grid, no se cuenta entre las fotos del álbum y no se usa como portada.
- [ ] 9.3 Verificar el máximo de punta a punta: llenar un álbum, comprobar que no acepta más, eliminar algunas fotos y comprobar que vuelve a aceptar.
- [ ] 9.4 Verificar que reducir el máximo por debajo de la cantidad de fotos de un álbum existente lo deja íntegro y utilizable, y que solo impide agregar.
- [ ] 9.5 Verificar la subida completa en el **modo nativo**, dado que el origen desde el que se carga la interfaz cambia y con él la negociación de origen contra el almacenamiento.
