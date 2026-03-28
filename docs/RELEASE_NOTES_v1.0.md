# Hito 1.1: Gestión de Sesiones y Memoria Persistente

**Estado:** Estable (Actualizado)
**Versión:** 1.1

## Descripción General
El Agente IA ha alcanzado la capacidad de automatizar el ciclo completo de diseño de PCBs, desde la interpretación visual de un esquema hasta la generación de archivos de fabricación industrial, utilizando una arquitectura de contenedores para ejecutar herramientas CAD (KiCad).

## Capacidades Implementadas

### 1. Ingeniería Inversa Visual (`/diseñar`)
*   **Motor:** Gemini 1.5 Flash/Pro (Vision).
*   **Función:** Convierte imágenes de diagramas a mano alzada en una Netlist digital (JSON).
*   **Detalle:** Identifica componentes (R, C, U, D) y sus conexiones nodo a nodo.

### 2. Diseño Esquemático (`/kicad`)
*   **Motor:** Script Python nativo (`json_to_kicad_netlist.py`).
*   **Función:** Genera archivos `.kicad_sch` compatibles con KiCad 9.0.
*   **Mejoras:** Posicionamiento automático de etiquetas para evitar superposiciones.

### 3. Diseño de PCB (Layout) (`/pcb`)
*   **Motor:** Scripting de KiCad (`pcbnew`) vía Docker.
*   **Función:** Crea archivos `.kicad_pcb` físicos.
*   **Características:**
    *   Colocación automática de huellas (Footprints) en rejilla.
    *   Generación de Ratsnest (conexiones lógicas).
    *   Ejecución aislada en Sandbox (Ubuntu 22.04) para acceso a librerías de sistema.

### 4. Manufactura (`/fabricar`)
*   **Motor:** Generador de Gerbers (`generate_gerbers.py`).
*   **Función:** Exporta capas de cobre, máscara, serigrafía y corte.
*   **Salida:** Paquete ZIP estandarizado para fabricantes (JLCPCB, PCBWay) o CNC.

### 5. Generación de G-Code (`/gcode`)
*   **Motor:** `pcb2gcode` (v1.1.4 compatible) + Scripts Python.
*   **Función:** Convierte archivos Gerber en instrucciones G-Code (.nc) para fresadoras CNC.
*   **Características:**
    *   Cálculo de rutas de aislamiento (Isolation Routing).
    *   Generación de vista previa vectorial (.svg).
    *   Soporte para taladrado (Drill) y corte de contorno (Edge Cuts).
    *   Parámetros ajustados para compatibilidad con versiones legacy de `pcb2gcode`.

### 6. Gestión de Sesiones (Nueva)
*   **Motor:** SQLite + LLM Summarization.
*   **Funcionalidad:** `/resume`, `/buscar_sesion`, `/exportar_sesion`.
*   **Persistencia:** Guardado automático de contextos antes de reinicios de sistema.
*   **Documentación:** Generación de archivos .md automáticos desde el historial.

### 7. Optimización Inteligente de Contexto
*   **Gestión de Historial:** Implementación de un sistema de "ventana deslizante" que prioriza los mensajes más recientes y el contexto inicial de sistema.
*   **Compresión Dinámica:** Reducción automática de la carga de tokens al detectar hilos de conversación extensos.
*   **Protección contra Prompts Masivos:** Poda automática de archivos de entrada o logs que excedan los límites operativos seguros (30k caracteres).
*   **Ahorro de Costos/Latencia:** Optimización de la cantidad de datos enviados a la API sin perder el hilo conductor de la tarea.

## Cambios Técnicos Clave
*   **Entorno Docker:** Se migró de `python:slim` a `ubuntu:22.04` para resolver dependencias de `pcbnew`.
*   **Compatibilidad API KiCad 8:** Se migró toda la API de `wxPoint`/`wxSize` a `VECTOR2I` (requerido por KiCad 8.0.9+).
*   **Dependencias:** Se agregó `kicad-footprints` al Dockerfile para asegurar la carga de librerías estándar.
*   **Gestión de Archivos:** Implementación de montaje de volúmenes (`/mnt/out`) para intercambio de archivos entre el Agente (Host) y las herramientas CAD (Container).
*   **Correcciones Críticas:**
    *   Fix en `pathfinding` (uso de atributos `.x/.y` en GridNode).
    *   Mejora en fallback de footprints: ahora genera pads THT reales para permitir el enrutado si falla la carga de librería.
    *   Fix en `/fabricar`: Se eliminó `SetExcludeEdgeLayer()` (removido en KiCad 8) para corregir la generación de Gerbers.
    *   **Validación DRC:** Se añadió verificación geométrica de cortocircuitos (Track vs Pad) en el script de generación de PCB.
    *   **Integración CNC:** Implementación de `pcb2gcode` en el Sandbox para conversión Gerber -> G-Code.
    *   **Compatibilidad Legacy:** Ajuste de parámetros de `pcb2gcode` para soportar la versión 1.1.4 (Ubuntu 22.04).
    *   **Diagnóstico:** Nuevo comando `/versiones` y script `check_tool_versions.py` para auditar el entorno.
    *   **Memoria:** Aumento de ventana de contexto a 20 mensajes en `chat_with_llm.py`.
    *   **Consistencia:** Migración de `chat_history.py` al directorio raíz de ejecución para cumplimiento de arquitectura de 3 capas.

## Siguientes Pasos (Rama Experimental)
*   Desarrollo de algoritmos de Auto-enrutado (Pathfinding A*).
*   Optimización de la ubicación de componentes (Placement).
*   Integración de reglas de diseño (DRC).
*   Implementación de búsqueda semántica profunda en el historial de sesiones.