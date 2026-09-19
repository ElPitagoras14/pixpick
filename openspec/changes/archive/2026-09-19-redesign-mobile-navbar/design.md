## Context

`_app/route.tsx` renderiza un único `<header>` con tres bloques en una fila (`nav` con Home/Albums, avatar+nombre, botón de logout), igual en cualquier viewport. No hay ningún breakpoint aplicado a la navegación hoy: el único uso de un breakpoint en todo el frontend es puntual en `components/ui/dialog.tsx`, sin relación con layout de página. Tampoco hay un hook de detección de viewport en JS (`matchMedia` o similar) en el código; los pocos casos responsive existentes son Tailwind puro. El patrón para saber qué subvista está activa ya existe en `routes/_app/albums/$albumId/route.tsx`, que usa `useMatchRoute()` de `@tanstack/react-router` para distinguir la vista de upload de las demás. `lucide-react` ya es dependencia del proyecto y es la librería de íconos usada en el resto de la interfaz (`gallery/PhotoViewer.tsx`, `photos/UploadItemCard.tsx`, etc.).

## Goals / Non-Goals

**Goals:**
- Definir el mecanismo responsive (breakpoint, qué contenido vive arriba y qué vive abajo) sin ambigüedad para quien lo implemente.
- Especificar cómo el footer nav sabe qué pestaña está activa y cómo sabe que tiene que ocultarse en el swipe deck.
- Resolver la composición visual del botón central (FAB) y su relación con el resto de la barra y con el contenido que queda debajo.

**Non-Goals:**
- No rediseña la navegación de desktop, que queda igual a como está hoy.
- No cambia la ruta `/albums/new` ni su formulario.
- No introduce navegación por gestos entre pestañas ni animaciones de transición.
- No resuelve accesibilidad de teclado más allá de lo que ya heredan `Button` y `Link` del design system actual.

## Decisions

**Mecanismo responsive: CSS con Tailwind (`md:`), sin JS.** El `<nav>` con Home/Albums del header actual pasa a `hidden md:flex`; el footer nav nuevo pasa a `flex md:hidden`. Sin media query en JS, sin flash de contenido incorrecto en la carga inicial, y consistente con que el único responsive existente en el proyecto ya es CSS puro. Alternativa descartada: un hook `useMediaQuery` en React — agrega un re-render extra y un estado que no hace falta cuando Tailwind resuelve lo mismo en CSS.

**El header superior no se duplica, se reduce.** El mismo `<header>` de `AppLayout` se mantiene como un único árbol: el bloque `<nav>` (Home/Albums) queda oculto por debajo de `md` vía la clase de Tailwind, y lo que sobrevive en mobile (avatar+nombre, botón de logout) es exactamente el resto del header actual, sin duplicar ese markup en un componente aparte. Alternativa descartada: dos headers distintos (uno mobile, uno desktop) montados condicionalmente — duplicaría el bloque de avatar/logout y su lógica (`useLogout`) sin necesidad, cuando ocultar un bloque con CSS alcanza.

**Footer nav como componente nuevo en `features/navigation/`.** Se crea `frontend/src/features/navigation/BottomNav.tsx`, siguiendo el mismo patrón de organización por dominio que ya usan `features/viewer`, `features/swipe`, `features/shares`. Se importa desde `_app/route.tsx`. Alternativas descartadas: agregarlo a `components/ui` (esa carpeta son primitivos de shadcn, no piezas de layout de la app) o dejarlo inline en `route.tsx` (el archivo ya mezcla layout y lógica de logout; sumarle el estado de pestaña activa y los íconos lo sobrecarga sin necesidad).

**Detección de pestaña activa: `useMatchRoute()`.** Mismo hook y mismo patrón que `isUploadView` en `$albumId/route.tsx`. Home se marca activo con `useMatchRoute({ to: "/home" })`, Albums con `useMatchRoute({ to: "/albums", fuzzy: true })` (cualquier ruta bajo `/albums`, incluida `/albums/new` y el detalle de un álbum, salvo el caso siguiente).

**Ocultar el footer nav en el swipe deck: el mismo hook, una condición más en `AppLayout`.** `AppLayout` calcula `useMatchRoute({ to: "/albums/$albumId/swipe" })` y, si matchea, no renderiza `BottomNav`. No hace falta un mecanismo nuevo (contexto, meta de ruta, layout separado): es la misma herramienta que ya resuelve el caso de `isUploadView` a un nivel más arriba en el árbol de rutas.

**Ícono de Albums: `Images` de lucide-react.** Representa una colección de fotos mejor que un ícono de carpeta genérico (`FolderOpen`), que no comunica "álbum de fotos" tan directo. Home usa `Home`, Create Album usa `Plus` — los tres ya vienen con `lucide-react`, no hace falta un ícono nuevo ni un set adicional.

**FAB elevado: `Plus` en un botón circular, `translate-y` negativo para sobresalir de la barra.** El botón central usa el color `primary` del design system (mismo token que `Button` variant default), diámetro mayor al de los otros dos ítems, y se posiciona con un margen negativo que lo hace sobresalir por arriba del borde superior de la barra — el patrón visual de "FAB en tab bar" habitual en apps mobile. Alternativa descartada: un `Button` con `position: fixed` totalmente independiente de la barra — separar su posicionamiento del resto de la barra complica mantener alineados los tres ítems en distintos anchos de pantalla, contra ponerlo dentro del mismo contenedor flex y solo elevarlo visualmente.

**Espacio reservado para la barra fija.** El contenedor que envuelve `<main>` en `AppLayout` suma `padding-bottom` (alto de la barra + `env(safe-area-inset-bottom)`) solo por debajo de `md`, para que el footer nav fijo no tape el final del contenido. Se aplica con una clase Tailwind arbitraria (`pb-[calc(...+env(safe-area-inset-bottom))]`) condicionada al mismo breakpoint que el resto del mecanismo.

## Risks / Trade-offs

- [Barra fija reduce el área visible de contenido en viewports muy bajos] → Mitigado por mantener la barra compacta (un alto fijo chico) y por ocultarla en el swipe deck, la pantalla donde el espacio vertical importa más.
- [El estado de "pestaña activa" se calcula en dos lugares (header reducido no lo necesita, pero el footer nav sí) si en el futuro se agrega una cuarta sección] → Mitigado por dejar `useMatchRoute()` centralizado en `AppLayout` y pasarlo como dato a `BottomNav`, en vez de que el componente recalcule sus propios matches.
- [`env(safe-area-inset-bottom)` no tiene efecto visible en un navegador de escritorio ni en la mayoría de los emuladores] → No mitigable en desarrollo; se verifica en un dispositivo iOS real o con el emulador de Safari antes de dar el cambio por probado en ese punto.

## Migration Plan

Cambio puramente de frontend, sin build adicional ni feature flag: se despliega como cualquier otro cambio de UI, cubierto por el mecanismo de cacheo con revalidación que ya describe `frontend-delivery`. Rollback es un revert normal del commit, sin pasos manuales ni de datos.

## Open Questions

Ninguna — las decisiones con impacto en el enfoque (breakpoint, qué queda arriba vs abajo, cuándo se oculta la barra, tratamiento visual del FAB) ya se resolvieron durante la exploración previa a este change.

### Resueltas durante la redacción

- **Mecanismo de breakpoint (CSS vs. JS):** resuelto verificando el código — no existe ningún hook de viewport en el proyecto, y el único responsive existente ya es Tailwind puro (`dialog.tsx`), así que se sigue ese mismo patrón.
- **Cómo detectar la ruta del swipe deck para ocultar la barra:** resuelto reusando `useMatchRoute()`, el mismo hook que ya resuelve un caso equivalente (`isUploadView`) en `$albumId/route.tsx`.
- **Ícono de Albums:** resuelto eligiendo `Images` de `lucide-react` (ya es dependencia del proyecto) por ser más específico que un ícono de carpeta genérico para representar un álbum de fotos.
- **Dónde vive el componente nuevo:** resuelto siguiendo el patrón de carpetas ya establecido (`features/<dominio>/`), descartando `components/ui` (reservada a primitivos de shadcn) y descartando dejarlo inline en `route.tsx`.
