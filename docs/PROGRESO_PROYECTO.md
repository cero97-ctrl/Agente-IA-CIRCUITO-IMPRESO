# Documentación del Progreso: Agente IA para Fabricación de PCBs

Este documento resume los avances técnicos logrados en el desarrollo del sistema de automatización para el diseño y fabricación de circuitos impresos (PCBs) utilizando KiCad, Python y tecnología CNC.

## 1. Configuración y Hardware (ESP32-S3)

Se ha validado la cadena de comunicación con el microcontrolador que actuará como interfaz o controlador auxiliar:

*   **Conexión Serial:** Identificación exitosa del chip USB-UART (CH342/CH343) en el puerto `/dev/ttyACM0` (VID:1A86 PID:55D3).
*   **Firmware:** Instalación exitosa de **MicroPython v1.27.0** mediante el script `flash_esp32.py`.
*   **Modo Bootloader:** Implementación de la secuencia manual (BOOT + RESET) para el flasheo en adaptadores CH340/342.
*   **Validación:** Verificación del REPL de MicroPython y los logs de arranque (ESP-ROM) a través de comunicación serial a 115200 baudios.

## 2. Automatización del Diseño en KiCad

Se ha establecido un flujo de trabajo para interactuar programáticamente con los archivos de diseño de KiCad:

*   **API `pcbnew`:** Uso de la librería interna de Python de KiCad para acceder a la base de datos de la placa sin necesidad de exportaciones manuales.
*   **Mapeo de Componentes:** Desarrollo de scripts para identificar automáticamente la posición de pads, referencias (R1, U1, etc.) y redes eléctricas (Nets).
*   **Discretización (Grid):** Conversión del diseño continuo en milímetros a una rejilla lógica para el procesamiento algorítmico.

## 3. Algoritmos de Enrutado y Optimización

Para el dibujo automático de pistas, se ha integrado la siguiente lógica:

*   **Búsqueda de Caminos (A*):** Implementación del algoritmo A-Estrella para encontrar rutas óptimas entre puntos de conexión, evitando obstáculos (otros pads o pistas).
*   **Manejo de Obstáculos:** Creación de mapas de celdas donde los componentes existentes actúan como zonas prohibidas para el trazado de nuevas rutas.

## 4. Generación de G-Code y Fabricación CNC

El objetivo final es la producción física de la placa mediante fresado químico-mecánico:

*   **Conversión a G-Code:** Transformación de las rutas calculadas por el algoritmo A* en comandos `G0` (posicionamiento rápido) y `G1` (fresado).
*   **Parámetros de Maquinado:** Configuración de velocidades de avance (Feedrate), profundidades de corte para el cobre y alturas de seguridad.
*   **Auto-leveling (Compensación de Altura):** Diseño conceptual de un sistema de sondeo (Probing) que utiliza interpolación bilineal para ajustar la profundidad de la broca según la curvatura real de la placa de cobre.
*   **Comunicación con GRBL:** Script de envío de G-Code (`enviar_gcode`) para controlar máquinas CNC de hardware abierto mediante protocolos seriales.

## 5. Filosofía de Desarrollo

Este proyecto se basa enteramente en **Software Libre**, utilizando:
*   **KiCad:** Para el diseño EDA.
*   **Python:** Como lenguaje de orquestación y automatización.
*   **MicroPython:** Para la lógica embebida.
*   **GRBL:** Como firmware de control numérico.

---
*Última actualización: Marzo 2024*
*Desarrollado como parte del Agente IA - Circuito Impreso*