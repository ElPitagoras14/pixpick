## 0. Navbar

- [x] 0.1 Crear `frontend/src/features/landing/Navbar.tsx`: nombre de la app a la izquierda, links de texto a `#how-it-works` y `#features` (visibles desde `sm`, ocultos en mobile) y el mismo `LandingAccessButton` (con color, no `outline`) a la derecha. Agregar `id="how-it-works"` a la sección de `HowItWorks.tsx` y `id="features"` a la de `Features.tsx`. Verificar en el navegador que los links llevan a la sección correcta y que el botón muestra la opción correcta con y sin sesión.

## 1. Hero y mock del swipe

- [x] 1.1 Crear `frontend/src/features/landing/SwipeMock.tsx`: tarjeta decorativa con una animación CSS en loop (desliza hacia un lado, se resetea, repite), sin `@use-gesture` ni `motion`, sin listeners de puntero (`pointer-events-none`), y que respete `prefers-reduced-motion` quedando quieta en el estado inicial. Verificar corriendo `pnpm dev` y confirmando visualmente el loop, y que con `prefers-reduced-motion: reduce` activado en las devtools del navegador el mock no se mueve.
- [x] 1.2 Crear `frontend/src/features/landing/Hero.tsx` con el encabezado, el subtítulo orientado al escenario de viajes/eventos entre amigos y familia, el botón existente (`session ? "Enter pixpick" : "Log in"`) y el `SwipeMock`. Verificar que el archivo compila sin errores de tipos (`pnpm exec tsc --noEmit`).
- [x] 1.3 Layout de dos columnas para el Hero desde `lg:`: texto (encabezado, subtítulo, CTA debajo del texto) a la izquierda, `SwipeMock` a la derecha; en mobile se mantiene una sola columna centrada. Usar `grid grid-cols-1 lg:grid-cols-2` en la sección (no `flex` + `items-center` para el bloque de texto: ese patrón deja el ancho de la columna en "auto", sin achicarse al viewport, y el párrafo con `max-w-md` se desborda por el borde derecho en cualquier ancho menor a ~450px). Verificar en un ancho de escritorio (1280px) que el texto queda a la izquierda con el CTA debajo y el mock a la derecha, y en 375px que no hay scroll horizontal (`document.documentElement.scrollWidth === window.innerWidth`).

## 2. Cómo funciona

- [x] 2.1 Crear `frontend/src/features/landing/HowItWorks.tsx` con los 4 pasos del flujo real (crear álbum, compartir el link, cada persona swipea, el dueño ve el resultado), cada uno con su ícono de `lucide-react`. Verificar en el navegador (`pnpm dev`) que los 4 pasos aparecen en ese orden y son legibles en un viewport de ancho móvil (375px) sin scroll horizontal.

## 3. Características

- [x] 3.1 Crear `frontend/src/features/landing/Features.tsx` con las 4 características trazadas en design.md (unirse con solo el link sin invitación ni aprobación manual, progreso de subida en vivo, resultados agregados para el dueño, zoom al detalle de cada foto), sin mencionar el plazo de retención de álbumes. Verificar releyendo la sección "Decisions" de design.md que cada característica escrita corresponde a una de las cuatro listadas ahí, y que ninguna otra se agregó.

## 4. CTA final

- [x] 4.1 Crear `frontend/src/features/landing/Cta.tsx`, que repite el mismo acceso del hero (`session ? "Enter pixpick" : "Log in"`) sin duplicar la decisión: recibe `session` como prop desde donde ya se resuelve. Verificar leyendo ambos componentes (`Hero.tsx` y `Cta.tsx`) que la comparación `session ? ... : ...` aparece en un solo lugar reusado por los dos, no escrita dos veces.

## 5. Composición en la ruta pública

- [x] 5.1 Reemplazar el componente `Landing` de `frontend/src/routes/index.tsx` por la composición de `Navbar`, `Hero`, `HowItWorks`, `Features` y `Cta`, manteniendo `session` obtenido de `Route.useRouteContext()` sin cambios en cómo se resuelve. Verificar corriendo `pnpm dev` y abriendo `/` sin sesión y con sesión: en ambos casos el botón del hero y el del CTA final muestran la opción correcta.
- [x] 5.2 Revisar que todas las importaciones nuevas entre `frontend/src/features/landing/*` y hacia `routes/index.tsx` usan el alias `@/...` del proyecto, sin rutas relativas (`code-conventions` spec). Verificar con `pnpm lint` sobre `frontend/`.

## 6. Verificación final

- [x] 6.1 Correr `pnpm check` (biome) sobre `frontend/` y confirmar que no introduce errores ni warnings nuevos.
- [x] 6.2 Probar manualmente en el navegador (`pnpm dev`) el recorrido completo de `/` de arriba a abajo, en un ancho de escritorio y uno móvil, confirmando que ninguna sección corta contenido ni produce scroll horizontal.
