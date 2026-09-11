## Purpose

Gobierna cómo la interfaz obtiene los valores que dependen del entorno en el que corre, de modo que una misma construcción sirva en cualquier entorno. No cubre cómo se entrega la interfaz, que es asunto de `frontend-delivery`, ni qué variables declara el entorno, que es asunto de `local-environment`.

## ADDED Requirements

### Requirement: La configuración se resuelve al iniciar el servicio, no al construir

Los valores que dependen del entorno SHALL resolverse cuando el servicio que entrega la interfaz arranca. Una misma construcción SHALL poder servir en entornos distintos cambiando únicamente variables del entorno, y SHALL NOT requerir volver a construir la interfaz para cambiar uno de esos valores.

#### Scenario: La misma construcción sirve en dos entornos

- **WHEN** se arranca la misma construcción de la interfaz con valores de entorno distintos
- **THEN** la interfaz usa en cada caso los valores de su entorno
- **AND** no hubo una construcción intermedia

#### Scenario: Los valores del entorno no quedan horneados

- **WHEN** se inspeccionan los archivos producidos por la construcción
- **THEN** no contienen los valores del entorno
- **AND** contienen únicamente la referencia al lugar donde esos valores se resolverán

### Requirement: La configuración está disponible antes de que la aplicación se ejecute

La aplicación SHALL disponer de su configuración desde su primera ejecución. SHALL NOT existir un estado intermedio en el que la aplicación ya esté corriendo pero su configuración todavía no haya llegado, para que ninguna parte del código tenga que tolerar una configuración ausente.

#### Scenario: La primera renderización ya tiene los valores

- **WHEN** la aplicación se ejecuta por primera vez en el navegador
- **THEN** los valores de configuración ya están disponibles

#### Scenario: No hay estado sin configuración que manejar

- **WHEN** se lee el código que consume la configuración
- **THEN** no contempla el caso de que la configuración no haya llegado todavía

### Requirement: Faltar un valor requerido impide servir la interfaz

Si un valor requerido no está presente al arrancar, el servicio que entrega la interfaz SHALL fallar con un error que nombre el valor faltante. SHALL NOT servirse la interfaz con un valor vacío, con un valor por defecto silencioso, ni con el placeholder de sustitución sin reemplazar.

#### Scenario: Un valor ausente detiene el arranque

- **WHEN** el servicio arranca sin un valor requerido
- **THEN** el arranque falla
- **AND** el error nombra el valor que falta

#### Scenario: Nunca se sirve un placeholder sin sustituir

- **WHEN** se inspecciona la configuración que recibe el navegador
- **THEN** no contiene placeholders de sustitución
- **AND** todos sus valores están resueltos

### Requirement: Solo se expone al navegador configuración no sensible

Lo que llegue al navegador SHALL limitarse a valores públicos, entendiendo que cualquiera con acceso a la interfaz puede leerlos. Ningún secreto SHALL incluirse en la configuración entregada al cliente.

#### Scenario: La configuración entregada solo tiene valores públicos

- **WHEN** se inspecciona la configuración que recibe el navegador
- **THEN** todos sus valores son aptos para ser públicos

#### Scenario: Un secreto del backend no llega al cliente

- **WHEN** el entorno declara un secreto que consume el backend
- **THEN** ese valor no aparece en la configuración entregada al navegador
