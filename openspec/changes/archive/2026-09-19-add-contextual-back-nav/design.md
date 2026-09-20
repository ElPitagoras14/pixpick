## Context

`_app/route.tsx` monta un `<header>` con tres bloques en una fila: el `nav` con Home y Albums (`hidden md:flex`), el bloque de identidad (avatar más nombre) y el botón de logout. Ya calcula ahí tres matches de ruta con `useMatchRoute()` —`isHome`, `isAlbums`, `isSwipeDeck`— y le pasa la pestaña activa a `BottomNav` como dato, en vez de que el componente recalcule lo suyo. `BottomNav` no se renderiza en el swipe deck.

La salida hacia atrás, en cambio, vive un nivel más abajo: `albums/$albumId/route.tsx` dibuja un `<Link>` con `text-muted-foreground text-xs` arriba del título, y elige su destino con un cuarto match, `isUploadView`. La vista de upload vuelve al álbum; las demás subvistas van a la lista de álbumes. `albums/new.tsx` no participa de ese layout y no tiene ninguna salida.

El tipo de `useMatchRoute()` devuelve `false | allParams`, no un booleano: un match contra `/albums/$albumId/upload` trae consigo el `albumId`. Los cuatro usos actuales lo descartan con `!!`. El único mecanismo de metadata de ruta que el proyecto usa hoy es ese hook: `staticData` no aparece en ninguna ruta, y tampoco hay hooks de viewport en JS — todo lo responsive es Tailwind puro. Los `size` de `Button` llegan hasta 36px (`lg`, `icon-lg`), por debajo del mínimo táctil que fija el spec de esta capability.

## Goals / Non-Goals

**Goals:**
- Definir de dónde sale el destino de la salida y dónde vive esa resolución, sin dejar la decisión repartida entre dos archivos.
- Fijar qué control se ve en cada viewport, de modo que nunca coexistan dos salidas ni quede una pantalla sin ninguna.
- Resolver cómo alcanza el mínimo táctil sin bifurcar el primitivo de `Button`.
- Resolver la composición del header en 360px, donde entra un elemento más a una fila que ya está llena.

**Non-Goals:**
- No toca `BottomNav` ni la regla que lo oculta en el swipe deck.
- No agrega acceso a la pantalla de entrada desde el swipe deck en mobile: es un hueco real, ya registrado, y de otro change.
- No introduce transiciones ni animación entre pantallas.
- No cambia el formulario de creación de álbum más allá de darle su salida.

## Decisions

**La resolución del destino sube a `AppLayout`, como un mapa explícito de match a destino.** El header es quien tiene que dibujar el control, así que es quien necesita saber a dónde apunta. `AppLayout` agrega los matches que le faltan y arma un único valor —el destino, o nada si la pantalla es un destino de la navegación principal— que consume tanto el botón del header como el link del contenido. Es el mismo patrón que el archivo ya aplica con la pestaña activa de `BottomNav`, y deja los `<Link>` escritos literales, con `to`, `params` y `search` tipados por el router.

Alternativa descartada: `staticData` por ruta, con `useMatches()` en el header. Es lo correcto cuando hay muchas pantallas, porque cada ruta nueva trae su propia salida sin tocar un archivo central, pero obliga a transportar `to`, `params` y `search` dentro de un objeto genérico y ahí se pierde el tipado que el router da sobre `Link`. Con cuatro subvistas, el costo de tipos no se paga.

Alternativa descartada: que el layout del álbum publique su salida por contexto y el header la consuma. Conserva la propiedad de que cada layout decide su propio destino, pero invierte el flujo de render —el hijo le dicta al padre qué dibujar—, mete estado donde hoy hay un cálculo puro y abre la ventana de un frame sin botón mientras la subvista todavía no montó.

**El `albumId` sale del propio match, no de `useParams`.** `matchRoute({ to: "/albums/$albumId/upload" })` devuelve los params cuando matchea, así que el mismo llamado que decide si la pantalla es esa aporta el dato para construir el destino. `AppLayout` está por encima de `$albumId` en el árbol, y la alternativa sería `useParams({ strict: false })`, que devuelve un tipo laxo y obliga a defenderse de un `undefined` que el match ya descartó.

**El orden de comprobación va de lo más específico a lo más general, y las rutas estáticas antes que las dinámicas.** `/albums/new` se evalúa antes que `/albums/$albumId` para que no exista la posibilidad de tratar `new` como el id de un álbum, y las subvistas antes que el álbum.

**El botón del header es `md:hidden`; el link del contenido pasa a `hidden md:block`.** Cada viewport ve exactamente un control, que es lo que el spec pide, y desktop conserva el tratamiento actual sin cambios visuales. La regla es de CSS, no de JS: no hay estado, no hay flash en la carga inicial, y es el mismo mecanismo que el resto del responsive del proyecto.

**El destino no se bifurca por viewport: el swipe deck vuelve al álbum también en desktop.** El link del contenido deja de distinguir "upload" de "el resto" y pasa a distinguir "subvista de un álbum" de "el álbum": upload y swipe vuelven al álbum, el álbum vuelve a la lista. Si el botón de mobile volviera al álbum y el link de desktop a la lista, la misma pantalla tendría dos jerarquías según el ancho, que es justo lo que el spec descarta al exigir que el destino dependa solo de qué pantalla se mira.

**`albums/new.tsx` recibe su propio link de contenido, con el mismo tratamiento que el del álbum.** El botón del header la cubre en mobile, pero en desktop quedaría sin salida y el requirement no distingue viewport. Dársela con el patrón que ya existe —link arriba del título— es más barato que hacer aparecer el botón del header solo en esa ruta y solo en desktop, que sería una excepción de una sola pantalla.

**El mínimo táctil se alcanza con una clase puntual, no con una variante nueva de `Button`.** El botón se compone como `Button` con `variant="ghost"` y una clase que lo lleva a 44px, en lugar de agregar un `size` al primitivo: `components/ui/button.tsx` es el primitivo de shadcn y sumarle una variante lo aparta del upstream para un caso que hoy tiene un solo consumidor. Si aparece un segundo, la variante se justifica sola.

**El componente vive en `features/navigation/`, al lado de `BottomNav`.** Es la carpeta donde ya está la otra pieza de navegación, y sigue la organización por dominio del resto de `features/`. Recibe el destino resuelto como prop, igual que `BottomNav` recibe la pestaña activa: la lógica de rutas queda en un solo archivo.

**El nombre del usuario se oculta por debajo de `md`; el avatar se queda.** A 360px la fila pasa a tener botón de atrás, avatar, nombre y logout: sumando anchos y gaps no sobra nada, y un nombre largo rompe el layout en vez de truncarse de forma prolija. El avatar solo conserva la identidad visible, y el nombre sigue estando en desktop, donde hay lugar. Alternativa descartada: truncar el nombre con ellipsis — mantiene un elemento que a ese ancho no alcanza a comunicar nada y le cede espacio al control que sí se usa.

**El tab bar no se toca.** Convertir el ítem de Albums en un atrás contextual daría un objetivo de 64px sin escribir un componente nuevo, pero una tab bar conmuta entre destinos pares y estables, y un ítem que cambia de identidad según dónde se esté rompe esa expectativa. Además no sirve para el caso que más lo necesita: en el swipe deck la barra está oculta.

## Risks / Trade-offs

- [Cada subvista nueva tiene que acordarse de sumar su match en `AppLayout`, o nace sin salida] → Mitigado porque el spec de `app-navigation` lo vuelve un requirement verificable y no una convención tácita; si el mapa crece más allá de un puñado de entradas, la señal es migrar a metadata por ruta, que es la alternativa ya evaluada acá.
- [El destino de la salida y el del link del contenido podrían divergir si más adelante alguien toca uno solo] → Mitigado haciendo que ambos lean el mismo valor resuelto en `AppLayout`, en vez de que el layout del álbum siga calculando el suyo por separado.
- [Que `matchRoute` contra `/albums/$albumId` no discrimine `/albums/new` como se espera] → Mitigado por el orden de comprobación, y verificable en la implementación con las dos rutas abiertas; si el comportamiento no fuera el previsto, alcanza con exigir que ese match no sea fuzzy.
- [El mínimo táctil es verificable a ojo solo a medias: 44px se mide, la comodidad real no] → Se comprueba con el inspector sobre el área activable, no sobre el ícono, que es donde suele estar la diferencia.
- [Ocultar el nombre en mobile es una pérdida de información para quien tenga varias cuentas] → El avatar sigue diferenciando, y el caso de varias cuentas simultáneas no está soportado hoy de ninguna forma.

## Migration Plan

Cambio de frontend únicamente, sin migración de datos, sin feature flag y sin coordinación con el backend. Se despliega como cualquier otro cambio de interfaz, cubierto por el mecanismo de cacheo con revalidación que ya describe `frontend-delivery`. El rollback es un revert del commit: como el estado de la navegación no se persiste en ningún lado, volver atrás no deja rastros que haya que limpiar.

## Open Questions

Ninguna. Las cuatro decisiones con impacto en el enfoque —mecanismo de resolución, qué control se ve en cada viewport, destino de la salida desde el swipe deck y alcance de pantallas— se cerraron con el usuario antes de redactar, y las que aparecieron al escribir se resolvieron contra el código o contra el spec, como queda registrado abajo.

### Resueltas durante la redacción

- **Cómo llega el `albumId` hasta `AppLayout`, que está por encima de esa ruta:** resuelto leyendo la declaración de `useMatchRoute` en los tipos instalados del router, que devuelve `false | allParams` y no un booleano. El dato ya estaba disponible en los cuatro llamados existentes, descartado por el `!!`.
- **Si el swipe deck debía volver al álbum también en desktop o solo en mobile:** resuelto contra el spec de `app-navigation`, que exige que el destino dependa únicamente de qué pantalla se mira. Un destino distinto según el ancho de la ventana lo contradice.
- **Si `/albums/new` quedaba cubierta solo por el botón del header:** resuelto contra el mismo requirement, que no distingue viewport. Con solo el botón de mobile, esa pantalla quedaba sin salida en desktop, así que recibe además el link de contenido.
- **Cómo alcanzar 44px teniendo `Button` un máximo de 36px:** resuelto leyendo `components/ui/button.tsx` y comprobando que ningún `size` llega al umbral. Con un único consumidor, la clase puntual cuesta menos que apartar el primitivo del upstream.
- **Qué se cede en el header a 360px:** resuelto sumando los anchos de los cuatro elementos contra el ancho disponible; el nombre es el único que no aporta una acción y el único cuyo ancho depende de un dato variable.
