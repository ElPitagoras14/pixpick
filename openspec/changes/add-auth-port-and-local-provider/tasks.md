## 1. Esquema: usuarios y sesiones

- [ ] 1.1 Escribir la migración con las dos tablas: usuarios con el par proveedor e identificador como único y **el correo sin unicidad** (D6), y sesiones con el hash como único, la referencia al usuario con eliminación en cascada y su vencimiento; ambas con su trigger de última modificación. Verificar aplicando la migración y haciendo rollback que el esquema queda como estaba.
- [ ] 1.2 Regenerar el archivo del esquema y versionarlo; verificar que refleja las dos tablas, que el correo no tiene índice único y que la eliminación en cascada está declarada en el esquema y no en la aplicación.
- [ ] 1.3 Verificar que la prueba del trigger de última modificación, que hasta ahora pasaba de forma trivial por no haber tablas, ahora cubre las dos tablas reales y fallaría si a una le faltara el trigger.
- [ ] 1.4 Escribir los constructores compartidos de usuario y sesión en las utilidades de prueba; verificar que una prueba puede crear un usuario declarando únicamente el correo y que el resto toma valores válidos por defecto.

## 2. Convenciones de respuesta de la API

- [ ] 2.1 Crear la base compartida de los modelos de respuesta con su convención de nombres de cara al cliente; verificar que un modelo cuyos campos siguen la nomenclatura del esquema se serializa con la convención del cliente.
- [ ] 2.2 Crear el envelope de respuesta para el caso satisfactorio y el de error; verificar que dos endpoints distintos devuelven la misma estructura externa y que un cliente puede distinguir éxito de error sin conocer el endpoint.
- [ ] 2.3 Extender las excepciones de dominio y su manejo con la correspondencia entre situación y código: falta de autenticación, falta de autorización, recurso no encontrado y error de validación; verificar cada una provocándola con una petición.
- [ ] 2.4 Verificar que un fallo no previsto responde con un mensaje genérico más un identificador que permite localizarlo en los registros, y que ninguna respuesta de error contiene trazas, texto de consultas ni nombres de tablas.

## 3. El puerto de identidad

- [ ] 3.1 Crear el puerto con sus dos operaciones —producir la dirección de autorización y canjear el código— y la forma de la identidad externa; verificar que el proveedor y el identificador de la persona son obligatorios y que los datos descriptivos admiten ausencia.
- [ ] 3.2 Crear la configuración y la selección de proveedor: un valor desconocido impide el arranque nombrando los valores admitidos, y **el adapter local se niega a activarse cuando el entorno no es de desarrollo** (D2); verificar los dos casos de fallo de arranque por separado.
- [ ] 3.3 Implementar el adapter local completo: dirección de autorización, pantalla de desarrollo servida por el propio backend y canje del código (D1); verificar que el ciclo produce una identidad externa con proveedor e identificador.

## 4. Ciclo de autorización y sesión

- [ ] 4.1 Implementar el endpoint de inicio de sesión: genera el valor de correspondencia, lo guarda junto al destino de retorno en una cookie httpOnly de vida corta en modo laxo (D3, D4) y redirige a la dirección del proveedor; verificar que la cookie se emite y que la redirección apunta a donde el proveedor indicó.
- [ ] 4.2 Implementar la validación del destino de retorno aceptando solo rutas del propio sitio; verificar con una prueba por cada forma de evasión conocida —doble barra inicial, esquema explícito y esquema de script— que cada una se descarta y se usa el destino por omisión (Risks).
- [ ] 4.3 Implementar el endpoint de retorno: exige que el valor de correspondencia coincida con el de la cookie y consume la cookie; verificar que un valor que no coincide, ausente o ya usado se rechaza sin establecer sesión.
- [ ] 4.4 Implementar la correspondencia entre identidad externa y usuario por el par proveedor e identificador, refrescando los datos descriptivos (D6); verificar que volver a entrar no crea un usuario nuevo, que un correo cambiado se actualiza sin duplicar, y que dos identidades de proveedores distintos con el mismo correo producen dos usuarios.
- [ ] 4.5 Implementar la creación de sesión: identificador generado con fuente aleatoria criptográfica, almacenamiento de su resumen con una función rápida (D7) y cookie con la misma vigencia que la sesión (D5); verificar que ningún valor almacenado sirve como cookie y que la cookie no sobrevive al vencimiento.
- [ ] 4.6 Eliminar las sesiones vencidas del usuario al iniciar sesión (D8); verificar que después de un segundo inicio de sesión las vencidas de ese usuario ya no están y que las vigentes de otros usuarios no se tocan.
- [ ] 4.7 Implementar la redirección final al destino de retorno validado, construida a partir de la URL pública configurada y nunca del esquema o el host del request (D9 de `add-local-environment`); verificar que con el request llegando por HTTP la redirección usa el esquema configurado.
- [ ] 4.8 Implementar la dependencia que resuelve el usuario autenticado y lo entrega como parámetro; verificar que sin sesión válida el código del endpoint no se ejecuta y que una sesión vencida se trata igual que una ausente.
- [ ] 4.9 Implementar el endpoint de identidad actual; verificar que la respuesta describe a la persona sin incluir el identificador de sesión ni su resumen, y que sin sesión indica falta de autenticación.
- [ ] 4.10 Implementar el cierre de sesión **como una escritura y no como una lectura** (D4); verificar que elimina el registro, que la cookie anterior deja de autenticar, que las demás sesiones del mismo usuario siguen activas, y que el endpoint no responde a una lectura.
- [ ] 4.11 Montar el router de autenticación bajo el prefijo de la API; verificar que sus rutas aparecen en el esquema publicado con el prefijo incluido.
- [ ] 4.12 Agregar al archivo de ejemplo del entorno el proveedor de identidad activo y la URL pública del sitio; verificar que ambas tienen consumidor y que copiando el archivo tal cual el entorno arranca.

## 5. Frontend: sesión, guard y vista de inicio

- [ ] 5.1 Configurar el cliente HTTP para que envíe credenciales y para que trate la respuesta no autorizada invalidando la sesión en caché y enviando a iniciar sesión (D9); verificar que una sesión que muere mientras se usa la aplicación termina en la vista de inicio y no en una pantalla rota.
- [ ] 5.2 Crear la factory de opciones de la consulta de sesión en la feature de autenticación; verificar que el loader raíz y el guard consumen la misma consulta y no dos.
- [ ] 5.3 Inyectar la sesión en el contexto del router; verificar que no existe una segunda copia del estado de sesión en ningún componente.
- [ ] 5.4 Implementar el guard del layout autenticado, que redirige a la vista de inicio llevando la ubicación pretendida como destino de retorno; verificar que entrar sin sesión a una ruta del layout y luego autenticarse termina exactamente en esa ruta.
- [ ] 5.5 Convertir la vista de inicio de sesión de placeholder a vista real, resolviendo los componentes necesarios del registro de shadcn; verificar en un viewport de 360px que no hay desplazamiento horizontal y que el control de inicio tiene área táctil suficiente.
- [ ] 5.6 Mostrar la identidad de la persona y el cierre de sesión en el layout autenticado, con la imagen tomada de la dirección que entrega el proveedor (D10); verificar que cerrar sesión devuelve a la vista de inicio y que volver atrás en el navegador no reingresa.
- [ ] 5.7 Verificar que la comprobación de estilo y la construcción del frontend pasan sin errores.

## 6. Documentación

- [ ] 6.1 Actualizar el README con cómo entrar usando el proveedor local, qué variable lo selecciona y por qué el servicio se niega a arrancar con ese proveedor fuera de desarrollo; verificar siguiendo las instrucciones tal como están escritas.

## 7. Verificación integral

- [ ] 7.1 Recorrer el ciclo completo desde un entorno recién levantado: sin sesión, iniciar sesión, pantalla de desarrollo, retorno, sesión establecida, identidad actual; verificar que no hizo falta ningún paso manual fuera del flujo.
- [ ] 7.2 Verificar que abrir sin sesión una ubicación que la requiere y autenticarse termina en esa ubicación, y que un destino manipulado para apuntar a otro sitio termina en el destino por omisión.
- [ ] 7.3 Verificar que declarar el proveedor local con un entorno que no es de desarrollo impide el arranque del servicio.
- [ ] 7.4 Verificar que la suite completa pasa, que corre con un solo comando y que no requiere acceso a internet.
