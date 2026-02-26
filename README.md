# Diseño e Impresión de Circuitos Impresos Mediante una CNC

## Estado del Proyecto: v1.0 (Estable)
Este repositorio contiene la versión estable del agente capaz de generar esquemáticos, PCBs y archivos Gerber a partir de imágenes.
Para ver el detalle de las funcionalidades implementadas, consulta [RELEASE_NOTES_v1.0.md](docs/RELEASE_NOTES_v1.0.md).

## Descripción del Proyecto

Este proyecto documenta un flujo de trabajo completo y basado en software libre para el diseño y la fabricación de Circuitos Impresos (PCBs) utilizando una máquina CNC. Desde el diseño esquemático en KiCad hasta la generación de G-Code optimizado y la compensación de altura (auto-leveling) con scripts de Python, el objetivo es proporcionar una solución integral y accesible para la creación de PCBs caseras.

Se exploran las herramientas y algoritmos necesarios para:
*   Convertir diseños de PCB (Gerber) a G-Code.
*   Implementar algoritmos de auto-enrutado (A*) para optimizar las trayectorias de las pistas.
*   Desarrollar un sistema de auto-leveling para compensar las imperfecciones de la placa.
*   Comunicarse con la CNC a través de Python.
*   **NUEVO**: Generar archivos de fabricación industrial (Gerber y Excellon) directamente desde imágenes y empaquetarlos en ZIP para servicios como PCBWay/JLCPCB.

## Requisitos

Para replicar este flujo de trabajo, necesitarás las siguientes herramientas de software:

*   **KiCad**: Para el diseño esquemático y de PCB. (Incluye la API `pcbnew` de Python).
*   **Python 3**: Lenguaje de programación principal para los scripts de automatización.
*   **Librerías de Python**:
    *   `pathfinding`: Para los algoritmos de búsqueda de rutas (A*).
    *   `pyserial`: Para la comunicación serial con la CNC.
    *   `gerber` / `pcb-tools`: Para la manipulación de archivos Gerber.
    *   `opencv-python`: Para visión artificial y detección de taladros en imágenes.
*   **Firmware CNC**: GRBL (recomendado) o similar instalado en el controlador de la máquina.

## Documentación Detallada

Para una inmersión profunda en el proceso, las herramientas y los scripts de Python involucrados, consulta el documento principal:

Documentación Completa del Proyecto