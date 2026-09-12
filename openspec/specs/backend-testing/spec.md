# backend-testing Specification

## Purpose

Gobierna cómo se verifica el backend: contra qué corren las pruebas, cómo se aísla cada una, cómo se ejecuta la suite y qué garantías ofrece en conjunto. No se solapa con `database-access`, que gobierna el comportamiento que estas pruebas verifican.

## Requirements

### Requirement: Las pruebas corren contra una base real migrada con las migraciones del proyecto

La suite SHALL ejecutarse contra el mismo motor de base de datos que usa la aplicación, con el esquema construido aplicando las migraciones del proyecto. SHALL NOT usarse un motor distinto, un esquema declarado aparte para pruebas ni una sustitución en memoria, porque cualquiera de esas opciones verifica un esquema que no es el que corre en producción.

#### Scenario: La suite construye su esquema con las migraciones del proyecto

- **WHEN** la suite prepara su base de datos
- **THEN** aplica las migraciones del proyecto
- **AND** no construye el esquema por otro medio

#### Scenario: Una migración inválida hace fallar la suite

- **WHEN** una migración no se puede aplicar
- **THEN** la suite falla al preparar su base
- **AND** el problema se detecta sin necesidad de una prueba dedicada a las migraciones

### Requirement: Cada prueba está aislada de las demás

Una prueba SHALL NOT observar datos escritos por otra ni dejar datos que otra pueda observar. El resultado de la suite SHALL ser independiente del orden en que las pruebas se ejecuten.

#### Scenario: Dos pruebas sobre la misma tabla no interfieren

- **WHEN** dos pruebas escriben en la misma tabla
- **THEN** ninguna observa los datos de la otra

#### Scenario: El orden de ejecución no altera el resultado

- **WHEN** la suite se ejecuta en un orden distinto
- **THEN** el resultado es el mismo

### Requirement: Una prueba no depende de datos preexistentes

Cada prueba SHALL crear los datos que necesita. SHALL NOT asumir la existencia de filas cargadas por otra prueba, por una migración o por una carga inicial.

#### Scenario: La prueba crea lo que necesita

- **WHEN** una prueba requiere datos para ejercitar su comportamiento
- **THEN** los crea ella misma

#### Scenario: Una base vacía es suficiente

- **WHEN** la suite corre sobre una base recién migrada y sin datos
- **THEN** todas las pruebas pasan

### Requirement: La suite corre con un solo comando y es repetible

Ejecutar la suite SHALL requerir un único comando, sin pasos manuales de preparación ni limpieza previa. Ejecutarla dos veces consecutivas SHALL producir el mismo resultado.

#### Scenario: Un comando alcanza

- **WHEN** se ejecuta el comando de pruebas
- **THEN** la suite prepara lo que necesita y se ejecuta
- **AND** no hizo falta ningún paso manual previo

#### Scenario: Dos ejecuciones seguidas dan lo mismo

- **WHEN** la suite se ejecuta dos veces sin limpiar nada entre una y otra
- **THEN** ambas ejecuciones producen el mismo resultado

### Requirement: La suite no depende de servicios de terceros ni de internet

Las pruebas SHALL depender únicamente de servicios que el entorno del proyecto provee. SHALL NOT requerir acceso a internet ni a servicios de terceros, para que un fallo de la suite signifique siempre un problema del código y nunca un problema de conectividad.

#### Scenario: Sin acceso a internet la suite pasa

- **WHEN** la suite se ejecuta en una máquina sin acceso a internet
- **THEN** todas las pruebas pasan

#### Scenario: Un fallo de la suite señala al código

- **WHEN** una prueba falla
- **THEN** la causa está en el código o en el esquema del proyecto
- **AND** no puede atribuirse a la disponibilidad de un servicio ajeno
