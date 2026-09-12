# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Idioma

- Responder siempre en español en el chat, sin importar el idioma de la consulta.
- El código, comentarios en código, commits y nombres de ramas se mantienen en inglés (convención estándar del repo).

## Control de versiones

- No hacer `git commit` (ni `git push`) a menos que el usuario lo pida explícitamente en el mensaje actual. Preparar los cambios y describir qué se haría, pero esperar confirmación antes de commitear.
- Si el usuario ya está en `main`, sugerir crear una rama antes de commitear, pero no crearla por defecto: esperar confirmación explícita antes de hacerlo.
- Usar nombres de rama canónicos con el formato `<tipo>/<descripcion-corta-en-kebab-case>`, por ejemplo:
  - `feature/nombre-de-la-funcionalidad`
  - `fix/nombre-del-bug`
  - `chore/tarea-de-mantenimiento`
  - `docs/actualizacion-de-documentacion`
  - `refactor/nombre-del-refactor`

### Mensajes de commit

- Redactar el mensaje de commit en inglés.
- Seguir la regla 50/72: título (primera línea) de máximo 50 caracteres, línea en blanco, y cuerpo con líneas envueltas a máximo 72 caracteres.
- En el cuerpo, no dejar línea en blanco entre oraciones: el cuerpo va como uno o varios párrafos de prosa continua (sin una oración por línea separada por saltos).
- Nunca incluirse a sí mismo (Claude) como coautor: no agregar líneas `Co-Authored-By` que referencien a Claude o Anthropic.

## OpenSpec

- Al aplicar (`apply`) un change de OpenSpec, crear siempre una nueva rama a partir de `main` actualizada, sin configurar upstream hacia `main`.
- Al aplicar un change, cronometrar desde que arranca la tarea hasta que se devuelve el control al usuario. Si a medio camino surge una consulta (`AskUserQuestion` u otra pregunta que corte el trabajo), detener el cronómetro antes de preguntar y reanudarlo recién cuando el usuario responda: ese tiempo de espera no cuenta. Registrar el resultado en `local/tiempos.md`, en una sección nueva con el nombre del change (`## <nombre-del-change>`), con los cortes de hora (inicio, cada pausa/reanudación, fin) y el tiempo activo total ya restadas las pausas.
