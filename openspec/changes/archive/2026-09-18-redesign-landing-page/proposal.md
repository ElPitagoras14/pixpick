## Why

La raíz pública (`/`) es hoy un título, un párrafo y un botón. Cumple lo mínimo que pide el spec `app-entry`, pero no da a alguien que nunca usó pixpick ninguna razón para entender por qué le conviene entrar: no explica cómo se usa ni qué gana un grupo de amigos o familia al compartir un álbum en vez de mandarse fotos sueltas por chat.

## What Changes

- Reemplaza el hero mínimo actual por una landing de varias secciones, en la misma ruta pública (`/`), sin tocar la lógica de sesión existente (mismo botón condicionado a `session`).
- Agrega una sección "cómo funciona" con los pasos del flujo real: crear el álbum, compartir el link, cada persona swipea sus fotos, el dueño ve qué quedó.
- Agrega una sección de características con las capacidades ya existentes en el producto (unirse con solo el link sin invitación ni aprobación manual, progreso de subida en vivo, resultados agregados para el dueño, zoom al detalle de cada foto).
- Agrega un mock visual del gesto de swipe en el hero, construido con CSS/`motion` (ya presente en el proyecto), en lugar de fotos reales o de stock.
- Agrega un CTA final que repite el mismo acceso del hero.
- Tono y ejemplos orientados al escenario de viajes y eventos entre amigos y familia.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

(ninguna — el requirement de `app-entry` que gobierna esta pantalla ya exige decir qué es el producto y ofrecer un acceso, sin prescribir estructura visual; este change cambia el "cómo se ve", no el "qué debe cumplir")

## Impact

- `frontend/src/routes/index.tsx`: reemplazo del componente `Landing` por una composición de varias secciones.
- Componentes nuevos bajo `frontend/src/features/landing/` para el navbar, las secciones de la landing (hero, cómo funciona, características, CTA) y el mock de swipe.
- Sin cambios de API, backend, ni de esquema de datos.
