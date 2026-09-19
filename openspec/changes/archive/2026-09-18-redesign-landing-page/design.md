## Context

La ruta `/` (`frontend/src/routes/index.tsx`) renderiza hoy un único componente `Landing` con título, párrafo y botón. El resto de la interfaz organiza el código por feature (`frontend/src/features/<nombre>/`), no en un `components/` genérico — ese directorio queda reservado para primitivas de shadcn (`components/ui/`). El gesto de swipe real vive en `features/swipe/SwipeCard.tsx`: usa `@use-gesture/react` para el drag y `motion/mini` (`animate()` sobre el DOM, sin componentes declarativos) para la salida de la tarjeta. Ver `proposal.md` para la motivación del cambio.

## Goals / Non-Goals

**Goals:**
- Definir dónde vive el código nuevo y cómo se compone con la ruta existente.
- Definir cómo se construye el mock visual del swipe sin fotos reales ni reutilizar el motor de gestos real.
- Dejar trazada la fuente de la copy (qué specs respaldan cada característica mencionada).

**Non-Goals:**
- No define el copy final palabra por palabra — eso es implementación, no diseño.
- No introduce ningún mecanismo de swipe funcional en la landing: el mock es decorativo, nadie califica nada ahí.
- No toca la lógica de sesión ni el botón condicional existente (`session ? ... : ...`).

## Decisions

**Organización del código: `frontend/src/features/landing/`, no `components/`.**
Sigue la convención ya establecida (`features/swipe`, `features/gallery`, `features/quota`, etc.), donde `components/` queda solo para primitivas shadcn. Cada sección de la landing (`Hero`, `HowItWorks`, `Features`, `Cta`) es un componente propio en esa carpeta, y `routes/index.tsx` los compone. Alternativa descartada: meter todo el contenido dentro del propio `index.tsx` como un solo archivo largo — dificulta editar cada sección por separado y rompe con cómo está organizado el resto del frontend.

**Mock del swipe: CSS `@keyframes` puro, no `motion`/`@use-gesture`.**
El mock es decorativo y se reproduce solo, en loop; no necesita responder al dedo ni al mouse. Reusar el mecanismo real (`useDrag` + `motion/mini`) implicaría manejar un loop propio en JS para simular arrastres automáticos, solo para lograr un efecto que una animación CSS declarativa ya cubre. Una animación CSS también respeta `prefers-reduced-motion` con una sola media query, sin lógica adicional. Alternativa descartada: reusar `SwipeCard` con un drag simulado — más código para el mismo resultado visual, y arriesga que alguien confunda el mock con un control real.

**Placeholders visuales en vez de fotos reales o de stock.**
El proyecto no tiene banco de imágenes (`frontend/public` solo tiene `config.js`). Tanto el mock del hero como los íconos de la sección de características usan formas planas (rectángulos redondeados con color de fondo del tema) y iconografía de `lucide-react`, ya dependencia del proyecto. Evita prometer visualmente una foto real que no existe y evita agregar un pipeline de assets para este change.

**Copy de "cómo funciona" y "características": tomada de los specs ya revisados, sin inventar capacidades.**
Los 4 pasos de "cómo funciona" (crear álbum, compartir link, swipear, ver resultado) provienen de `album-management`, `album-sharing`, `photo-rating`/`rating-gallery` y `album-stats`. Las características destacadas (unirse con solo el link, progreso de subida en vivo, resultados agregados, zoom al detalle) provienen de `album-sharing`, `upload-feedback`, `album-stats` y `photo-viewer` respectivamente. No se menciona el plazo de retención (`album-retention`) como característica de venta: es una limitación operativa, no un motivo para entrar.

**Corrección durante la implementación: el link de compartir no evita iniciar sesión.** El primer borrador de esta decisión y de la copy (`Features.tsx`, `HowItWorks.tsx`) decía "entrar a calificar sin cuenta vía link" / "no account needed to open it". Es falso: `frontend/src/routes/a.$token.tsx` redirige a `/login` si no hay sesión (`beforeLoad`), y el requirement "El link funciona sin sesión previa y devuelve a la persona al álbum" de `album-sharing` dice explícitamente que abrir el link sin sesión "SHALL conducir a autenticarse". Lo que el link realmente evita es el paso de invitación/aprobación manual, no el login: cualquiera con el link puede iniciar sesión (con su propia cuenta) y queda adentro, sin que el dueño tenga que agregarlo a mano. La copy se corrigió a esa afirmación ("join with just a link" / sin invitación ni aprobación), detectado por el usuario al revisar el resultado, no en la revisión de specs previa a este change.

**Sin dependencias nuevas.**
`motion`, `lucide-react`, Tailwind v4 y los primitivos de shadcn ya usados alcanzan. No se agrega ningún paquete al `package.json`.

**Navbar y Hero de dos columnas en desktop (agregado durante la implementación).**
Se agrega `frontend/src/features/landing/Navbar.tsx`: nombre de la app a la izquierda, links de texto a `#how-it-works`/`#features` (ocultos en mobile, visibles desde `sm`) y el mismo `LandingAccessButton` a la derecha, con color en vez de `outline` (mismo componente que usan `Hero` y `Cta`, sin repetir el ternario `session ? ... : ...` una tercera vez). El `Hero` pasa de una sola columna centrada en todos los anchos a dos columnas desde `lg:` (texto con el CTA debajo a la izquierda, `SwipeMock` a la derecha); en mobile se mantiene una sola columna centrada. Motivo: en desktop la columna centrada dejaba ambos lados de la pantalla vacíos. La sección del Hero (y las grillas de `HowItWorks`/`Features`) usan `grid-cols-1` explícito en la base en vez de depender de la columna implícita "auto" de CSS Grid, que no se achica al ancho del viewport y desborda cualquier hijo con `max-width` mayor a lo disponible (bug real de overflow horizontal encontrado y corregido durante la verificación en mobile, no solo el ajuste de layout de escritorio).

## Risks / Trade-offs

- [Alguien intenta arrastrar el mock del hero esperando que "haga algo"] → Mitigación: el mock no registra ningún listener de puntero (`pointer-events-none` en la tarjeta decorativa) y se anima solo, sin esperar interacción, para no sugerir que responde al toque.
- [La copy describe capacidades reales; si esas capacidades cambian de comportamiento en el futuro, la landing queda desactualizada] → Mitigación: la copy se mantiene a nivel de qué se puede hacer, no de detalles específicos (números, límites) que cambien seguido.
- [Secciones nuevas alargan la página pública, que debe seguir siendo liviana] → Mitigación: sin imágenes reales ni dependencias nuevas, el peso adicional es solo markup y CSS.

## Migration Plan

Cambio de contenido de una sola ruta pública, sin estado persistido ni flag. Se despliega como cualquier otro cambio de frontend; el rollback es revertir el commit, sin pasos de datos.

## Open Questions

Ninguna: el alcance, el tono, la estructura de secciones y el enfoque visual ya se resolvieron con el usuario durante la exploración previa (`/opsx:explore`), y las decisiones técnicas de esta sección no dependen de ningún dato todavía desconocido.

**Resueltas durante la redacción:**
- Dónde vive el código nuevo (`features/landing/` vs `components/`) — resuelto leyendo la organización real del resto del frontend (`features/swipe`, `features/gallery`, etc.).
- Cómo animar el mock sin reusar el motor de gestos real — resuelto comparando los requisitos del mock (decorativo, en loop, sin input) contra lo que `SwipeCard.tsx` necesita para el swipe funcional.
- Qué characteristics mencionar y de qué spec sale cada una — resuelto releyendo el propósito de cada spec de producto durante la exploración previa.
