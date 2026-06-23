# ADN del Proyecto: Agente-IA-CIRCUITO-IMPRESO

Este documento extrae la lógica técnica y los componentes esenciales para replicar la automatización de diseño de PCBs y fabricación digital en nuevos proyectos de ingeniería asistida por IA.

## 1. Infraestructura y Contenedores (Docker)
- **Versión de KiCad:** KiCad 8.0.x (Migración crítica validada a 8.0.9+).
- **Entorno de Ejecución:** Imagen basada en `ubuntu:22.04` (migrada desde `python:slim`) para asegurar compatibilidad con la API de `pcbnew`.
- **Dependencias de Python Internas:**
    - `pcbnew`: Librería nativa de KiCad (acceso directo a la base de datos de la placa).
    - `kicad-cli`: Utilizado para la generación de archivos de fabricación vía terminal.
    - `pcb-tools-extension`: Para la manipulación avanzada de archivos Gerber.
    - `python-pathfinding`: Implementación del algoritmo A* para el trazado de rutas.
    - `pcb2gcode`: Conversión de Gerber a instrucciones G-Code (v1.1.4 para compatibilidad con Ubuntu 22.04).
- **Gestión de Volúmenes:** Mapeo de `/mnt/out` para persistencia de archivos entre el Host y el Sandbox de ejecución.

## 2. Capa de Ejecución (`execution/`)
- **Lógica de Ruteo y Ubicación:**
    - **Placement:** Algoritmos de atracción por afinidad de red para posicionar componentes cercanos según sus conexiones.
    - **Estrategia SoC:** Ubicación periférica de componentes para dejar el centro despejado, facilitando el trabajo de enrutadores externos (DeepPCB).
    - **Ruteo Local:** Implementación de búsqueda de caminos en rejilla (Grid-based A*) para conexiones simples.
- **Comandos de Fabricación:**
    - Generación automatizada de Gerbers y archivos de taladrado (Excellon) empaquetados en un ZIP industrial.
    - **Conversión CNC:** Scripts que integran la compensación de altura (Auto-leveling) mediante interpolación bilineal.
- **Validación Técnica:**
    - Scripts de diagnóstico para verificar versiones de herramientas (`check_tool_versions.py`).
    - Verificación geométrica básica de cortocircuitos entre pistas y pads antes de la exportación final.

## 3. Arquitectura de Automatización (`directives/`)
El sistema utiliza una **Arquitectura de 3 Capas** para separar la lógica probabilística del LLM de la ejecución determinista:
1. **Directivas (SOPs):** Archivos YAML (ej. `generate_kicad_pcb_script.yaml`) que definen pasos exactos y validaciones.
2. **Orquestador (Layer 2):** El LLM actúa como puente, seleccionando herramientas y gestionando estados en `.tmp/run_state.json`.
3. **Ejecución (Layer 3):** Scripts Python puros que fallan ruidosamente ante errores, sin intentar "adivinar".

## 4. Memoria y Logs de Aprendizaje (Base de Datos de Errores)
Para evitar fallos recurrentes en "DATA_LOGER", se deben tener en cuenta estos aprendizajes registrados en ChromaDB:
- **Cambio de API KiCad 8:** Se reemplazó el uso de `wxPoint`/`wxSize` por `VECTOR2I` para todas las coordenadas.
- **Depreciación de Funciones:** La función `SetExcludeEdgeLayer()` fue eliminada en KiCad 8; se debe omitir en scripts de generación de Gerbers.
- **Resiliencia de Footprints:** Si una librería no carga, el script debe generar pads THT genéricos para permitir que el proceso de diseño continúe sin bloquearse.
- **Fabricación CNC:** La profundidad de corte en cobre (0.035mm) requiere obligatoriamente una sonda Z (Z-Probe) para evitar la pérdida de pistas por irregularidades en la placa.
- **Optimización de Recursos:** En equipos con poca RAM, el uso de **ZRAM** con algoritmo `zstd` es vital para ejecutar modelos como Ollama junto con KiCad.

---
*Este resumen permite replicar la capacidad de pasar de un esquema visual a un archivo de fabricación industrial en minutos.*