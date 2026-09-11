## 1. dbmate y la migración inicial

- [ ] 1.1 Crear `dbmate/Dockerfile` fijando la versión exacta de la imagen y copiando migraciones y esquema dentro de ella, con un comentario que enumere todos los lugares del repositorio donde esa versión aparece (Risks); verificar que la imagen construye y que buscar la referencia en el repositorio encuentra exactamente los lugares que el comentario enumera.
- [ ] 1.2 Escribir `dbmate/migrations/0001_create_initial_schema.sql` con su sección de aplicación y su sección de rollback, conteniendo la función que mantiene el campo de última modificación (D5) y nada de dominio; verificar aplicando la migración y luego haciendo rollback que la base queda como estaba.
- [ ] 1.3 Generar `dbmate/schema.sql` y versionarlo; verificar que refleja la función creada y que regenerarlo sobre el mismo esquema no produce diferencias.
- [ ] 1.4 Verificar que aplicar las migraciones sobre una base que ya está al día termina satisfactoriamente y no modifica el esquema.

## 2. Orquestación de las migraciones

- [ ] 2.1 Agregar el healthcheck de Postgres a `compose.yaml`; verificar que el servicio reporta estado saludable una vez listo y no antes.
- [ ] 2.2 Agregar el servicio de migraciones que se ejecuta y termina, esperando al healthcheck de Postgres, con su cadena de conexión compuesta por el compose a partir de los valores del servidor (D6, D7); verificar que el servicio termina con código cero y que la tabla de control de migraciones existe.
- [ ] 2.3 Hacer que el backend espere a que el servicio de migraciones haya terminado satisfactoriamente (D6); verificar levantando el entorno desde cero que el backend no acepta peticiones antes de que las migraciones estén aplicadas.
- [ ] 2.4 Verificar que una migración que no se puede aplicar impide que el backend quede atendiendo, y que el fallo es visible en la salida del servicio de migraciones.
- [ ] 2.5 Agregar la variable de conexión a `.env.example` (D7); verificar que ahora tiene consumidor y que copiando el archivo tal cual el entorno arranca completo.

## 3. Configuración y ciclo de vida de la conexión

- [ ] 3.1 Crear `backend/src/database/config.py` leyendo la única variable de conexión (D7); verificar que arrancar sin ella falla con un error que la nombra.
- [ ] 3.2 Crear `backend/src/database/client.py` con el motor asincrónico sobre el dialecto de psycopg3 y los límites de pool declarados de forma explícita (D2, D11); verificar leyendo el archivo que las conexiones permanentes y el techo total están escritos como valores y no heredados de un valor por defecto.
- [ ] 3.3 Implementar la verificación de conectividad en el arranque y la liberación del pool al cerrar de forma ordenada; verificar que con Postgres apagado el backend no arranca y el error es explícito.
- [ ] 3.4 Extender el healthcheck para que refleje el estado de la base; verificar que con Postgres caído la respuesta indica que el servicio no está operativo en lugar de informar un estado satisfactorio.
- [ ] 3.5 Verificar que cuando la base falla, la respuesta del healthcheck no contiene el texto de ninguna consulta ni nombres de tablas o columnas.

## 4. Las cinco funciones de acceso

- [ ] 4.1 Implementar en `client.py` las cinco funciones que ejecutan SQL —escribir, escribir en lote, leer una fila, leer todas y leer un valor—, todas recibiendo la conexión como primer parámetro (D3); verificar leyendo el archivo que ninguna abre ni cierra conexiones por su cuenta.
- [ ] 4.2 Crear `backend/src/database/utils.py` con el manejo del alcance transaccional que usarán los servicios; verificar que en el punto de llamada se puede determinar si una operación participa de una transacción observando únicamente la conexión que recibe.
- [ ] 4.3 Verificar que los valores viajan como parámetros y no dentro del texto de la consulta: una prueba que almacene un valor con comillas y punto y coma y compruebe que se guarda literal, sin alterar la consulta.

## 5. Traducción de errores de la capa de datos

- [ ] 5.1 Crear `backend/src/exceptions.py` con las excepciones de dominio que representan los fallos de la capa de datos; verificar que un fallo al obtener conexión llega al consumidor como excepción de dominio y no como la excepción original de la capa de acceso.
- [ ] 5.2 Crear `backend/src/handlers.py` registrando el manejo de esas excepciones, con el alcance mínimo que el healthcheck necesita; verificar que la respuesta que llega al cliente no revela la consulta ni el detalle del controlador de la base.

## 6. Infraestructura de la suite de pruebas

- [ ] 6.1 Agregar las dependencias de desarrollo del marco de pruebas y su soporte asincrónico a `backend/pyproject.toml`; verificar que la sincronización de dependencias las instala y que el comando de pruebas se reconoce.
- [ ] 6.2 Escribir `backend/tests/conftest.py` de modo que cree la base de pruebas si no existe y le aplique las migraciones del proyecto con la misma versión exacta de la herramienta (D10); verificar que la suite corre desde cero con un único comando y sin preparación manual.
- [ ] 6.3 Hacer que la preparación de la suite falle si el destino no es la base de pruebas esperada (Risks); verificar apuntándola a la base de desarrollo que se niega a ejecutarse.
- [ ] 6.4 Implementar la fixture que abre conexión, inicia transacción, la entrega y hace rollback al terminar, con su propio pool reducido (D9, D11); verificar que dos pruebas que escriben la misma tabla no observan los datos de la otra y que el resultado no depende del orden de ejecución.
- [ ] 6.5 Escribir `backend/tests/dbutils.py` con las utilidades de introspección del esquema que necesitan las pruebas de la capa de datos; verificar que permiten consultar qué tablas declaran un campo y qué triggers tiene una tabla.

## 7. Comportamiento verificado por la suite

- [ ] 7.1 Escribir la prueba de humo que confirma que la suite se conecta, que ve el esquema migrado y que el motor declara los límites de pool esperados; verificar que falla si las migraciones no se aplicaron.
- [ ] 7.2 Escribir la prueba que recorre las tablas que declaran el campo de última modificación y comprueba que cada una tiene su trigger (D5, Risks); verificar que hoy pasa de forma trivial al no haber tablas y que fallará en cuanto una tabla nueva omita el trigger.
- [ ] 7.3 Escribir las pruebas de la capa de acceso creando una tabla temporal dentro de la propia transacción de la prueba, dado que no hay tablas de dominio; verificar sobre ella la atomicidad de una operación de varias escrituras con fallo intermedio y que sin fallo todas quedan confirmadas.
- [ ] 7.4 Escribir la prueba de que una función de acceso valida la fila contra su modelo y falla en la frontera cuando la consulta deja de devolver un campo declarado (D4); verificar que el fallo ocurre al construir el modelo y no aguas abajo.
- [ ] 7.5 Verificar que la suite no depende de acceso a internet ejecutándola con la red externa deshabilitada.

## 8. Documentación

- [ ] 8.1 Actualizar `README.md` con cómo crear una migración, cómo aplicarla, cómo regenerar el archivo del esquema y cómo correr las pruebas; verificar siguiendo las instrucciones tal como están escritas.

## 9. Verificación integral

- [ ] 9.1 Levantar el entorno desde cero y verificar la secuencia completa: Postgres saludable, migraciones aplicadas, backend atendiendo, y el healthcheck reflejando el estado real de la base.
- [ ] 9.2 Hacer rollback de la migración inicial y volver a aplicarla; verificar que el esquema y el archivo versionado coinciden al final.
- [ ] 9.3 Ejecutar la suite dos veces seguidas sin limpiar nada entre una y otra; verificar que ambas ejecuciones producen el mismo resultado.
- [ ] 9.4 Verificar que después de correr la suite la base de desarrollo no quedó modificada.
