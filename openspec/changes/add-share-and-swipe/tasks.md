## 1. Esquema: token, membresía y calificaciones

- [x] 1.1 Escribir la migración con las tres tablas: el token de compartir con su revocación, la membresía con clave compuesta de álbum y persona, y las calificaciones con unicidad por foto y persona; todas con eliminación en cascada y con su trigger de última modificación donde corresponda. Verificar aplicando la migración y haciendo rollback que el esquema queda como estaba.
- [x] 1.2 Incorporar en la misma migración como miembro al dueño de cada álbum ya existente (Migration Plan); verificar sobre una base que ya tenía álbumes que todos quedan con su dueño como miembro, porque de lo contrario la lista se comportaría distinto según cuándo se creó cada álbum.
- [x] 1.3 Regenerar el archivo del esquema; verificar que refleja las tres tablas, la unicidad de la calificación, las cascadas y los triggers.
- [x] 1.4 Verificar que la prueba de triggers de última modificación cubre las tablas nuevas que declaran ese campo.
- [x] 1.5 Agregar los constructores compartidos de token, membresía y calificación; verificar que una prueba puede armar un álbum compartido con un miembro que ya calificó, declarando lo mínimo.

## 2. Compartir un álbum

- [x] 2.1 Implementar la generación del link con un token impredecible y la dirección construida a partir de la dirección pública configurada; verificar que con la petición llegando por un esquema distinto la dirección devuelta usa igualmente el configurado.
- [x] 2.2 Implementar que un álbum tenga a lo sumo un link vigente, que regenerar revoque el anterior en la misma operación y que revocar deje al álbum sin link; verificar los tres comportamientos y que ningún token se repite entre generaciones sucesivas.
- [x] 2.3 Restringir la administración del link al dueño; verificar que un miembro que no es dueño no puede regenerar ni revocar y que el link no cambia.
- [x] 2.4 Implementar el ingreso por token **como una operación de escritura** (D4); verificar que el endpoint no responde a una lectura, dado que una navegación desde otra aplicación lleva la cookie de sesión.
- [x] 2.5 Verificar que un token inventado, uno revocado y uno bien formado que no corresponde a nada producen **respuestas idénticas**, comparándolas entre sí y no solo comprobando que las tres fallan.
- [x] 2.6 Implementar la incorporación como miembro al ingresar; verificar que ingresar dos veces con el mismo token no duplica la membresía ni altera nada.
- [x] 2.7 Verificar que revocar o regenerar el link no expulsa a los miembros existentes, que conservan el acceso y sus calificaciones, y que en cambio alguien nuevo con el token revocado no ingresa.
- [x] 2.8 Hacer que crear un álbum incorpore a su dueño como miembro; verificar que el dueño puede calificar su álbum recién creado sin pasar por el link de compartir.

## 3. Calificar

- [x] 3.1 Implementar el registro de la calificación como **una sola sentencia que resuelve el conflicto** sobre la clave única (D3); verificar que repetir la misma calificación no cambia nada, que emitir la contraria la reemplaza, y leyendo el código que no hay una lectura previa que decida entre insertar y actualizar.
- [x] 3.2 Restringir la calificación a los miembros del álbum; verificar que quien no es miembro recibe la misma respuesta que si la foto no existiera y que no queda ninguna calificación registrada.
- [x] 3.3 Implementar la consulta de pendientes **una sola vez** y usarla tanto para la secuencia como para el conteo (D2); verificar leyendo el código que las dos formas comparten implementación y no pueden divergir.
- [x] 3.4 Verificar que la comparación se hace contra la vista de fotos disponibles: una foto que todavía no se subió no aparece como pendiente de nadie, sin que este código tenga que excluirla explícitamente.
- [x] 3.5 Verificar que agregar fotos a un álbum le aumenta lo pendiente a quien ya había calificado todo, sin que ninguna operación adicional lo provoque, y que eliminar una foto lo reduce.
- [x] 3.6 Implementar la secuencia devolviendo todas las pendientes con las direcciones de sus variantes, sin paginar (D11); verificar con un álbum lleno hasta el máximo que la respuesta las trae todas.
- [x] 3.7 Verificar que interrumpir la secuencia y volver más tarde retoma con las que faltaban y no repite las ya calificadas.

## 4. La lista de álbumes con membresía y pendientes

- [x] 4.1 Reescribir la consulta de la lista como **una sola consulta sobre membresía** que resuelve portada, cantidad de fotos y pendientes de quien pregunta (D9, D10); verificar leyendo el código que no hay unión de dos consultas, y comprobando el tráfico que sigue sin haber una petición por álbum.
- [x] 4.2 Distinguir en la respuesta los álbumes propios de aquellos de los que solo se es miembro; verificar con dos cuentas que cada una ve la distinción correcta.
- [x] 4.3 Verificar que un álbum del que no se es dueño ni miembro no aparece en la lista de nadie más.

## 5. Interfaz: ingresar por el link

- [x] 5.1 Crear la ruta del token que carga la aplicación y dispara la incorporación; verificar que abrirla sin sesión lleva a autenticarse y que después la persona termina en ese álbum y no en la portada.
- [x] 5.2 Verificar que el link abierto desde una aplicación de mensajería o un cliente de correo funciona igual que abierto desde el propio sitio, que es lo que depende del modo laxo de las cookies.
- [x] 5.3 Tras ingresar, conducir a calificar o a ver el álbum según si quedan pendientes; verificar los dos casos.
- [x] 5.4 (Agregada durante la implementación: el plan no traía ninguna tarea para exponer el link en la interfaz, solo para entrar por él.) Agregar en la página del álbum, visible solo al dueño, un control mínimo de "Compartir": obtiene/muestra el link vigente, copiar, regenerar y revocar; verificar que un miembro que no es dueño no lo ve.

## 6. Interfaz: la interacción de swipe

- [x] 6.1 Agregar las dos dependencias con versión fijada; verificar que la construcción del frontend pasa.
- [x] 6.2 Combinar sobre la misma tarjeta la referencia de la librería de gestos y el ámbito de la de animación (D7); verificar que el gesto y la animación operan sobre el mismo elemento.
- [x] 6.3 Implementar el arrastre escribiendo el transform **directamente sobre el elemento**, sin estado de React ni animación intermedia (D7); verificar que mover el dedo no produce renderizados.
- [x] 6.4 Impedir que arrastrar la tarjeta desplace la página, con el escucha no pasivo que eso requiere; verificar en un viewport de teléfono que el arrastre horizontal no scrollea.
- [x] 6.5 Implementar el umbral de D8 con sus dos vías, el piso de distancia de la vía rápida y la dominancia horizontal; verificar **cuatro** casos, dos de ellos negativos: un arrastre largo califica, un impulso corto y rápido califica, **un roce diminuto y veloz no califica**, y **un gesto vertical no califica**.
- [x] 6.6 Implementar la animación al soltar con resorte, volando hacia afuera al aceptar y regresando al centro al no alcanzar el umbral; verificar que el regreso tiene un leve sobrepaso y no un frenado lineal.
- [x] 6.7 Implementar el apilado para que la foto siguiente asome debajo y se adelante cuando la de arriba se va.
- [x] 6.8 Implementar los controles visibles de aprobar y rechazar y el manejo de las flechas del teclado; verificar que se puede completar una secuencia entera **sin usar el gesto ni el puntero**.
- [x] 6.9 Implementar la precarga acotada reutilizando exactamente las direcciones que la secuencia entregó (D5); verificar en el tráfico que las direcciones precargadas son idénticas a las que después se muestran, y que son unas pocas por delante y no el álbum entero.
- [x] 6.10 Implementar la cola de calificaciones con avance optimista, envío de a una y reintento espaciado (D6); verificar que la siguiente foto aparece sin esperar al servidor, que un fallo temporal se reintenta solo, y que un fallo persistente avisa sin perder lo que la persona ya decidió.
- [x] 6.11 Implementar el estado de secuencia terminada, con el camino a ver el álbum.
- [x] 6.12 Verificar que la comprobación de estilo y la construcción del frontend pasan.

## 7. Lo pendiente en la interfaz

- [x] 7.1 Mostrar la cantidad pendiente en la lista de álbumes y dentro del álbum; verificar que aumenta sola cuando el dueño sube fotos nuevas a un álbum que alguien ya había terminado de calificar.

## 8. Documentación

- [x] 8.1 Actualizar el README con el flujo de compartir, qué significa revocar y regenerar, y cómo se califica; verificar siguiendo las instrucciones tal como están escritas.

## 9. Verificación integral

- [x] 9.1 Recorrer el flujo completo con dos cuentas: crear un álbum, subirle fotos, compartirlo, abrir el link con la segunda cuenta desde fuera del sitio, y calificar todas las fotos.
- [x] 9.2 Verificar que el dueño califica su propio álbum sin haber pasado nunca por el link.
- [x] 9.3 Verificar que revocar el link deja afuera a quien no había ingresado y conserva intactos el acceso y las calificaciones de quien ya era miembro.
- [x] 9.4 Verificar que subir fotos nuevas le aumenta lo pendiente a quien ya había terminado, y que al calificarlas vuelve a cero sin que exista ningún estado de finalización.
- [x] 9.5 Verificar el ingreso por link y la calificación completa en el **modo nativo** de trabajo.
