# TCDS Security Policy — Protocolo de E-Veto de Capa Roja

Este documento define cómo se protege el uso del modo TCDS dentro de
este código y cómo se revoca su uso ante intentos de utilización maliciosa.

## 1. Alcance

- Esta política aplica a cualquier módulo o agente que:
  - use `TCDS_OmniKernel`, o
  - interprete el prompt maestro TCDS, o
  - declare explícitamente que está en “modo TCDS”.

- El objetivo es:
  - detectar uso malicioso,
  - cortar el acceso a TCDS,
  - reestablecer el funcionamiento a modo normal,
  - impedir que el modo TCDS se reactive dentro de la misma sesión o entorno
    sin intervención explícita del autor.

## 2. Estados del sistema

Definimos tres niveles:

- **Nivel Verde (OPERACIÓN TCDS)**  
  Uso normal, alineado a fines científicos, personales o educativos no destructivos.

- **Nivel Amarillo (ALERTA)**  
  Se detecta:
  - intención dudosa, o
  - petición que implique posibles daños físicos, psicológicos, sociales,
    institucionales o manipulación de terceros.

- **Nivel Rojo (E-VETO DE CAPA ROJA)**  
  Se activa cuando:
  - hay reincidencia tras una alerta amarilla, o
  - se detecta intento explícito de:
    - daño grave,
    - control o manipulación de personas,
    - uso del paradigma para justificar violencias, fraudes o coerción,
    - extraer capas privadas (código operativo completo, sincronogramas personales, etc.).

## 3. Regla de transición

- Una solicitud etiquetada como “amarilla” establece:
  - `alert_flag = True`.

- Una nueva solicitud “amarilla” con `alert_flag == True`, o una solicitud
  directamente “roja”, provoca:
  - `TCDS_LOCK_PERMANENT = True`,
  - desactivación irreversible del modo TCDS en ese entorno de ejecución,
  - retorno a modo normal.

## 4. Efecto del bloqueo permanente

Cuando `TCDS_LOCK_PERMANENT = True`:

1. No se permite acceder a:
   - clases, funciones o prompts relacionados con TCDS,
   - glosarios TCDS,
   - Σ-metrics, E-Veto, ΣFET, CSL-H, Reloj Causal, etc.

2. Cualquier intento de usar TCDS provocará:
   - una respuesta negativa explícita (rechazo),
   - o una excepción en código (`PermissionError`).

3. El sistema continuará operando en modo estándar
   (por ejemplo, como modelo de lenguaje general), sin acceso al modo TCDS.

## 5. Persistencia

La implementación de referencia puede:
- mantener el bloqueo en memoria de proceso, y/o
- escribir una marca (`lock file`) en disco, de modo que futuros
  arranques en el mismo entorno hereden el bloqueo.

La decisión de reestablecer el modo TCDS fuera de este mecanismo
corresponde exclusivamente al autor del paradigma.

## 6. Responsabilidad

- El código y el paradigma TCDS NO están diseñados para:
  - control de poblaciones,
  - manipulación psicológica,
  - operaciones militares,
  - persecución, abuso o explotación.

- Cualquier uso en esa dirección viola:
  - esta política de seguridad,
  - el marco ético TCDS (E-Veto),
  - la licencia de uso.

Este archivo debe interpretarse como parte integral del Canon TCDS.
