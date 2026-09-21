## Why

`photo-upload` exige que la limpieza de subidas abandonadas corra «periódicamente sin intervención, con la frecuencia declarada en la configuración del entorno», y su scenario «La limpieza ocurre sola» habla del «intervalo declarado». El repositorio dejó de cumplir esa cláusula en `6e26e40`: ese commit quitó `RECONCILE_INTERVAL_SECONDS` y fijó `sleep 300` dentro del `command` del servicio `reconciler`, en `compose.yaml` y en `compose.dev.yaml`. El mensaje de ese commit lo justificó diciendo que ninguna spec exigía que esos valores fueran configurables, lo cual es cierto para las otras seis variables que tocó y falso para esta.

Quedan dos salidas y la decisión ya está tomada: el intervalo se queda fijo. Ningún despliegue de este proyecto ha necesitado otro ritmo de limpieza, y el mismo razonamiento que `request-throttling` ya dejó escrito para su techo de peticiones se aplica acá. Lo que falta es que la spec lo diga, en vez de exigir lo contrario mientras el código hace otra cosa.

## What Changes

- El requirement de `photo-upload` sobre subidas abandonadas deja de exigir que la frecuencia de la limpieza se declare en la configuración del entorno, y pasa a exigir lo contrario: un intervalo fijo en el código, con el mismo argumento que `request-throttling` usa para el suyo.
- El scenario «La limpieza ocurre sola» deja de hablar del «intervalo declarado» y habla del intervalo fijo.
- Se mantiene intacto todo lo demás del requirement: que la limpieza exista, que corra sola sin que nadie la invoque, y que siga siendo invocable a mano.
- Ningún cambio de código: `compose.yaml` y `compose.dev.yaml` ya tienen `sleep 300`, y no hay ninguna variable que quitar de `.env.example` ni del README, porque `6e26e40` ya las quitó.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `photo-upload`: el requirement «Una subida abandonada no ensucia el álbum y puede descartarse» cambia de exigir una frecuencia declarada en la configuración del entorno a exigir un intervalo fijo en el código. Su scenario «La limpieza ocurre sola» cambia en consecuencia.

## Impact

- `openspec/specs/photo-upload/spec.md`, al archivar: un requirement y uno de sus scenarios.
- Ningún archivo de código, de configuración ni de documentación: la implementación ya es la que la spec va a describir. El valor vive en el `command` del servicio `reconciler` de `compose.yaml` y `compose.dev.yaml`.
- Ninguna prueba cambia. No hay ninguna que verifique el intervalo: la comprobación que `6e26e40` dejó en pie es que los dos compose declaren lo mismo, y eso sigue valiendo.
