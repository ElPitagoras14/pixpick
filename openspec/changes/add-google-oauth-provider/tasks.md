## 1. La configuración fuera del repositorio

- [ ] 1.1 Crear la aplicación en la consola del proveedor con el tipo que corresponde a una aplicación web; verificar que quedan emitidos el identificador de cliente y su secreto.
- [ ] 1.2 Declarar en la consola la dirección de retorno, derivada de la dirección pública del entorno donde se va a usar; verificar que **coincide carácter por carácter** con la que el sistema registra al arrancar (D5), comparando las dos en lugar de darlas por iguales.
- [ ] 1.3 Configurar la pantalla de consentimiento con los tres ámbitos mínimos (D2); verificar en la propia consola que los tres figuran como **no sensibles**, que es lo que confirma que no hace falta someter la aplicación a revisión (D9).
- [ ] 1.4 Mirar cómo se ve la pantalla de consentimiento desde una cuenta que no participó del proyecto; verificar que lo que declara pedir es el nombre y el correo, y nada más.

## 2. El adapter

- [ ] 2.1 Implementar la construcción de la dirección de autorización con los ámbitos mínimos, el valor de correspondencia que recibe y la dirección de retorno derivada de la configuración; verificar que la dirección resultante tiene la forma documentada y que no incluye ningún ámbito de más.
- [ ] 2.2 Implementar el canje del código como una petición directa servidor a servidor, autenticada con las credenciales de la aplicación; verificar que la identidad llega por esa petición y que lo único que atravesó el navegador fue el código.
- [ ] 2.3 Mapear lo que devuelve el proveedor a la identidad que el puerto declara, tomando el identificador estable del proveedor y **nunca el correo** (D4); verificar que la ausencia de un dato descriptivo, como la imagen, no impide completar el inicio de sesión.
- [ ] 2.4 Comprobar que la audiencia corresponde a las credenciales configuradas y que el emisor es el esperado, **como control de configuración y no de seguridad** (D1); verificar que unas credenciales cruzadas se detectan, y verificar leyendo el código que no afirma verificar firmas ni obtiene claves públicas.
- [ ] 2.5 Declarar las direcciones del proveedor en el código con un comentario que indique de dónde salieron (D8); verificar que el arranque no emite ninguna petición de red para obtenerlas.
- [ ] 2.6 Distinguir un rechazo del consentimiento de un fallo del proveedor (D7); verificar que un rechazo devuelve a la pantalla de inicio de sesión sin mensaje alarmante, y que un fallo real muestra un error accionable dejando el detalle en los registros.
- [ ] 2.7 Verificar que ni un rechazo ni un fallo crean sesión o usuario, según el requirement que `add-auth-port-and-local-provider` ya estableció.

## 3. Selección del proveedor y configuración

- [ ] 3.1 Registrar el adapter en la selección por variable de entorno; verificar que un valor desconocido sigue impidiendo el arranque nombrando los valores admitidos.
- [ ] 3.2 Validar las credenciales al construir el adapter y solo para el proveedor activo (D6); verificar los tres casos: credenciales ausentes impiden el arranque nombrando cuáles faltan, una credencial declarada pero vacía se trata igual que ausente, y con el proveedor local activo la ausencia de credenciales del externo no estorba.
- [ ] 3.3 Registrar al arrancar la dirección de retorno que el sistema va a usar (D5); verificar que aparece de forma legible y completa, lista para comparar con la declarada en la consola.
- [ ] 3.4 Agregar las credenciales al archivo de ejemplo del entorno en los dos perfiles, con valor vacío por tratarse de secretos; verificar que copiando el archivo tal cual el entorno arranca con el proveedor local.

## 4. Pruebas

- [ ] 4.1 Escribir la prueba de la dirección de autorización: que lleve los ámbitos mínimos, el valor de correspondencia y la dirección de retorno derivada de la configuración.
- [ ] 4.2 Escribir la prueba del canje contra un doble del proveedor; verificar que produce una identidad con proveedor e identificador presentes.
- [ ] 4.3 Escribir las pruebas del rechazo y del fallo, comprobando que se distinguen entre sí y que ninguno deja sesión ni usuario.
- [ ] 4.4 Escribir la prueba de que faltando credenciales el arranque falla, y de que con el proveedor local activo no se exigen.
- [ ] 4.5 Verificar que la suite completa **sigue sin requerir acceso a internet**: el doble del proveedor no sale a la red, y agregar un proveedor externo no puede romper esa garantía de `backend-testing`.

## 5. Documentación

- [ ] 5.1 Actualizar el README con cómo crear la aplicación en la consola, qué dirección de retorno declarar y cómo se deriva, por qué en desarrollo conviene seguir con el proveedor local, y la contingencia del modo de prueba si alguna vez la revisión resultara necesaria; verificar siguiendo las instrucciones tal como están escritas.

## 6. Verificación integral

- [ ] 6.1 Recorrer el ciclo completo contra el proveedor real, desde un navegador sin sesión previa, en un entorno con el proveedor externo activo.
- [ ] 6.2 Abrir un link de álbum compartido con una cuenta que nunca entró y completar el inicio de sesión con el proveedor externo; verificar que termina en el álbum y no en la portada, que es donde este change se cruza con el de compartir.
- [ ] 6.3 **Revisar el diff completo del change y confirmar que no hay cambios en la sesión, los endpoints, la interfaz ni el esquema.** Si los hay, no es una tarea pendiente sino un hallazgo sobre el diseño del puerto, y corresponde tratarlo como tal antes de dar el change por terminado.
- [ ] 6.4 Verificar que en desarrollo, con el proveedor local activo, todo sigue funcionando exactamente como antes de este change.
