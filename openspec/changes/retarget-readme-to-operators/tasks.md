## 1. Reordenar el esqueleto

- [ ] 1.1 Reordenar las secciones de `README.md` según el mapa de D2, moviendo el contenido existente sin reescribirlo, y verificar que la lista de títulos de nivel `##` coincide exactamente con ese mapa y en ese orden
- [ ] 1.2 Agrupar todo el material de desarrollo bajo `Work on the code`, con las cuatro subsecciones de D1, y verificar que ninguna instrucción que suponga un clon del repositorio o herramientas de desarrollo instaladas queda fuera de ese bloque
- [ ] 1.3 Mover el hostname del storage y el límite de peticiones frente a una CDN a `Put it on a server`, según D5, y verificar que ninguno de los dos quedó bajo la sección de estructura

## 2. Invertir el camino principal

- [ ] 2.1 Reescribir `Start it` para que encabece con el comando que consume las imágenes publicadas, y verificar que el primer comando del documento ya no construye desde el código
- [ ] 2.2 Reducir `What you need` al runtime de contenedores, moviendo `uv` y `pnpm` al bloque de desarrollo, y verificar que la sección no pide nada que quien solo despliega no vaya a usar
- [ ] 2.3 Escribir en `Put it on a server` qué espera el stack del entorno —un punto de entrada único, dos hostnames públicos y TLS terminado afuera—, y verificar que no se nombra ninguna plataforma, proxy ni forma concreta de terminar TLS, según D5

## 3. Repartir la configuración con `.env.example`

- [ ] 3.1 Crear `Get the values you need` con las cuatro subsecciones de D3, trasladando los pasos de Google, R2, ImageKit y el hostname del storage, y verificar que las cuatro remisiones que `.env.example` hace al README encuentran ahí el procedimiento que prometen
- [ ] 3.2 Eliminar los cuatro pasajes que duplican `.env.example` según D4, y verificar que ninguna sección del README enumera los valores que admite una variable ni explica qué controla
- [ ] 3.3 Hacer que cada sección que necesita un valor nombre su variable y remita a `.env.example`, y verificar que quien sigue el documento sabe en todos los casos qué archivo abrir para completarla

## 4. Escribir lo que le falta a quien opera

- [ ] 4.1 Escribir en `Keep it running` qué volúmenes respaldar y qué se pierde sin cada uno, según D7, y verificar que dice que `nginx-cache` no hace falta y que la mención al borrado con `-v` quedó junto a esa explicación
- [ ] 4.2 Escribir cómo pasar la instancia a una versión nueva, y verificar que los pasos se ejecutan sin un clon del repositorio
- [ ] 4.3 Reemplazar los comandos de mantenimiento por su forma contra el contenedor, según D6, incluido el `--against r2` del runbook de migración, y verificar ejecutando `docker compose exec reconciler python -m src.maintenance.reconcile` con el entorno levantado
- [ ] 4.4 Resolver las dos duplicaciones internas de D8, dejando el límite de peticiones completo en el troubleshooting y una sola aparición del comando que consulta la configuración efectiva, y verificar que ninguno de los dos se explica dos veces

## 5. Corregir los datos desactualizados

- [ ] 5.1 Corregir la enumeración de servicios que lista siete cuando el entorno declara ocho, y verificar que la lista y la tabla de servicios nombran los mismos ocho
- [ ] 5.2 Explicar o unificar la diferencia entre los dos comandos que levantan un subconjunto de servicios, y verificar que un lector puede saber por qué uno incluye `migrate` y el otro no

## 6. Verificar el documento completo

- [ ] 6.1 Recorrer los cinco escenarios del requirement modificado y los tres del requirement agregado, confirmando cada uno contra el documento resultante
- [ ] 6.2 Leer el documento entero de principio a fin en el papel de quien solo va a levantar el proyecto, y verificar que llega a levantarlo, configurarlo y mantenerlo sin cruzar material de desarrollo
- [ ] 6.3 Ejecutar `uv run pytest tests/test_documentation_conventions.py` desde `backend/` y verificar que el documento no nombra ninguna spec, change ni decisión numerada
- [ ] 6.4 Ejecutar `openspec validate retarget-readme-to-operators --strict` y verificar que pasa
