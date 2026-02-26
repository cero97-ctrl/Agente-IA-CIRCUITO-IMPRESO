# Hito 1.0: Generación Automatizada de PCBs (Backend)

**Estado:** Estable
**Versión:** 1.0

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

## Cambios Técnicos Clave
*   **Entorno Docker:** Se migró de `python:slim` a `ubuntu:22.04` para resolver dependencias de `pcbnew`.
*   **Compatibilidad API:** Se actualizó el código para soportar la API moderna de KiCad 6/7/8 (ej. `pcbnew.BOARD()`, `wxPoint`).
*   **Gestión de Archivos:** Implementación de montaje de volúmenes (`/mnt/out`) para intercambio de archivos entre el Agente (Host) y las herramientas CAD (Container).

## Siguientes Pasos (Rama Experimental)
*   Desarrollo de algoritmos de Auto-enrutado (Pathfinding A*).
*   Optimización de la ubicación de componentes (Placement).
*   Integración de reglas de diseño (DRC).