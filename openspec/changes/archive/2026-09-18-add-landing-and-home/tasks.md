## 1. La landing

- [x] 1.1 Reescribir la ruta raíz con lo que dice qué es el producto y para qué sirve, y un acceso cuyo texto y destino salen del estado de sesión leído del contexto (D3). Verificar que no introduce ninguna consulta propia.
- [x] 1.2 Verificar sin sesión: la pantalla se ve completa, no redirige a ningún lado, y su acceso lleva a iniciar sesión.
- [x] 1.3 Verificar con sesión vigente: la misma pantalla se sigue viendo, y su acceso entra en la aplicación sin volver a pedir credenciales.
- [x] 1.4 Verificar la pantalla de teléfono a 360 px de ancho, sin desplazamiento horizontal, como exige la base mobile-first del proyecto.

## 2. La home como panel

- [x] 2.1 Mostrar el espacio ocupado contra el límite, en su propia consulta contra el recurso de cuenta, pedida junto al resto y nunca esperada antes de dibujar (D2).
- [x] 2.2 Mostrar los álbumes con fotos por calificar leyendo la consulta de álbumes que ya existe, con su misma clave, y filtrando en memoria (D1). Verificar con las herramientas de red del navegador que navegar entre la home y la lista de álbumes **no** dispara un segundo pedido de álbumes.
- [x] 2.3 Agregar el acceso a crear un álbum, enlazando la ruta que ya existe.
- [x] 2.4 Escribir los tres estados por separado —sin álbumes, con álbumes y nada por calificar, y con álbumes y cosas por calificar (D4)—. Verificar que los dos primeros muestran mensajes distintos y que ninguno queda como una sección en blanco.
- [x] 2.5 Verificar que si el pedido del espacio falla, la home dibuja igual lo pendiente y el acceso a crear: quedarse sin ver el espacio no puede impedir ver qué falta calificar.

## 3. La vuelta a la home

- [x] 3.1 Agregar el enlace a la home en el encabezado, junto al de álbumes y con el mismo tratamiento de estado activo (D5). Verificar que no se agrega ningún componente ni estructura de navegación por dos enlaces.
- [x] 3.2 Verificar desde dentro de un álbum que hay un acceso visible de vuelta a la home, sin escribir la dirección ni usar el botón de atrás del navegador.

## 4. Verificación final

- [x] 4.1 Verificar con dos cuentas que el número de pendientes que la home muestra junto a un álbum coincide con el que ese álbum informa al abrirlo, incluido un álbum al que se accedió por un enlace compartido y no es propio.
- [x] 4.2 Verificar que terminar de calificar todas las fotos pendientes de un álbum lo saca de la home al volver, sin recargar la página.
- [x] 4.3 Recorrer el camino completo de una cuenta nueva: entrar por la raíz sin sesión, iniciar sesión, llegar a la home vacía, crear el primer álbum desde ahí, subirle fotos, y comprobar que la home pasa a mostrar espacio ocupado y ese álbum con sus fotos por calificar —porque el dueño todavía no las calificó— en vez de quedarse en el estado inicial.
- [x] 4.4 Correr `tsc --noEmit`, el linter y el build del frontend, y verificar que terminan limpios.
- [x] 4.5 Correr `openspec validate --changes add-landing-and-home --strict` y verificar que pasa.
