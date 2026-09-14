## 1. La regla del backend se vuelve comprobable

- [x] 1.1 Agregar `TID` al conjunto seleccionado del linter en `backend/pyproject.toml`, con la opción que prohíbe las importaciones relativas hacia paquetes superiores (D2), y verificar que `ruff check` no reporta ninguna violación: hoy el proyecto ya cumple esa mitad, así que encenderla no debe cambiar nada.
- [x] 1.2 Escribir en la suite del backend la prueba que recorre `src/` y falla cuando una importación absoluta apunta dentro del subárbol del paquete del archivo que la escribe (D3). Verificar que **falla** listando las 17 líneas en sus 7 archivos, y que el mensaje nombra archivo y línea.
- [x] 1.3 Corregir las 17 importaciones —los cuatro archivos de la raíz de `src/` y los factories de `identity/`, `images/` y `storage/`— y verificar que la prueba de 1.2 pasa y que la suite completa sigue en verde.
- [x] 1.4 Verificar que la prueba detecta una regresión: introducir a mano una importación absoluta hacia el propio subárbol, comprobar que falla, y revertirla.
- [x] 1.5 Correr `ruff format` y `ruff check` sobre `backend/` y verificar que terminan limpios.

## 2. La regla del frontend se vuelve comprobable

- [x] 2.1 Configurar en `frontend/biome.json` la regla de importaciones restringidas con un grupo que cubra `./*` y `../*` (D4), y verificar que el linter reporta exactamente las dos líneas conocidas y ninguna más.
- [x] 2.2 Corregir `main.tsx` y `router.tsx` para que importen por el alias del proyecto, y verificar que el linter pasa y que la comprobación de tipos y el build siguen funcionando.
- [x] 2.3 Verificar que la regla detecta una regresión: introducir a mano una importación relativa, comprobar que el linter la marca, y revertirla.
- [x] 2.4 Verificar que la interfaz levanta y navega, para descartar que el alias resuelva distinto que la ruta relativa en tiempo de ejecución.

## 3. El marcado sale del código

- [x] 3.1 Crear el directorio de plantillas junto al adapter del proveedor local y mover allí el marcado actual tal cual, dejando el valor variable como marcador de la plantilla (D5). Verificar que el archivo queda con resaltado y formateo de HTML y que el formateador de Python ya no lo alcanza.
- [x] 3.2 Construir el entorno de plantillas con el escape automático activado, resolviendo el directorio desde la ubicación del propio módulo y no desde el directorio de trabajo (D5, D6). Verificar que la función conserva su firma y su tipo de retorno.
- [x] 3.3 Reemplazar el f-string por el renderizado de la plantilla, y verificar comparando la respuesta anterior con la nueva, ignorando espacios en blanco: mismos campos, mismo destino y mismo método en el formulario.
- [x] 3.4 Agregar la prueba de que un valor con caracteres con significado en el marcado, recibido en la dirección, aparece en la página como texto y no agrega ni cierra ningún elemento (D6). Verificar que falla contra la versión con f-string y pasa contra la plantilla.
- [x] 3.5 Verificar el ciclo completo de ingreso local de punta a punta: pedir la pantalla, enviar el formulario, y llegar autenticado a la aplicación.
- [x] 3.6 Construir la imagen del backend y verificar dentro del contenedor que la pantalla se sirve, para confirmar que la plantilla viaja con el código.

## 4. Verificación final

- [x] 4.1 Correr la suite completa del backend junto con `ruff format` y `ruff check`, y verificar que todo termina limpio.
- [x] 4.2 Correr el linter y el formateador del frontend sobre todo el proyecto y verificar que no reportan nada.
- [x] 4.3 Verificar que cada una de las cuatro reglas del spec tiene su comprobación y que ninguna quedó dependiendo de revisión: las dos de importaciones por linter y prueba, la del marcado por la prueba de 3.4, y la de comprobación automática por el hecho de que 1.4 y 2.3 demostraron que las violaciones fallan.
- [x] 4.4 Correr `openspec validate --changes tidy-code-conventions --strict` y verificar que pasa.
