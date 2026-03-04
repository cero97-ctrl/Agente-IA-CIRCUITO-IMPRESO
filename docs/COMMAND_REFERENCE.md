# Referencia de Comandos del Bot

Esta es una lista completa de los comandos disponibles para el Agente de IA a través de Telegram.

## Diseño y Fabricación

| Comando | Descripción |
| --- | --- |
| `/freecad [descripción]` | Crea un modelo 3D (caja, cono, engranaje, etc). |
| `/diseñar` (con foto) | Analiza un dibujo de circuito a mano alzada. |
| `/kicad` | Genera el esquemático KiCad desde un diseño activo. |
| `/pcb` | Genera el layout PCB desde un diseño activo. |
| `/fabricar` | Crea el paquete de Gerbers (.zip) para manufactura. |
| `/gcode` | Genera el G-Code (.nc) para fresado CNC desde los Gerbers. |
| `/send_cnc [puerto] [archivo]` | Envía un archivo G-Code a la máquina CNC. |
| `/ayuda_cnc` | Envía la documentación sobre el flujo de trabajo CNC. |

## Utilidades Generales

| Comando | Descripción |
| --- | --- |
| `/investigar [tema]` | Busca en internet sobre un tema y genera un resumen. |
| `/reporte [tema]` | Genera un informe técnico detallado en la carpeta `docs/`. |
| `/resumir [url]` | Lee el contenido de una página web y lo resume. |
| `/resumir_archivo [nombre]` | Lee un archivo de la carpeta `docs/` y lo resume. |
| `/traducir [texto/archivo]` | Traduce un texto o un archivo de `docs/` o `.tmp/` al español. |

## Memoria y Recordatorios

| Comando | Descripción |
| --- | --- |
| `/recordar [dato]` | Guarda una nota en la memoria a largo plazo del agente. |
| `/memorias` | Lista los últimos recuerdos guardados en la memoria. |
| `/olvidar [ID]` | Borra un recuerdo específico de la memoria usando su ID. |
| `/ingestar [archivo]` | Agrega el contenido de un archivo de `docs/` a la memoria RAG. |
| `/recordatorio [HH:MM] [msg]` | Configura una alarma diaria recurrente. |
| `/mis_recordatorios` | Muestra todas tus alarmas activas y sus IDs. |
| `/borrar_recordatorio [ID]` | Elimina una alarma específica usando su ID. |

## Administración y Estado

| Comando | Descripción |
| --- | --- |
| `/status` | Muestra el estado actual del servidor (CPU, RAM, Disco). |
| `/limpiar` | Elimina archivos temporales, cachés y logs del proyecto. |
| `/reiniciar` | Borra el historial de conversación y restablece la personalidad. |
| `/modo [tipo]` | Cambia la personalidad del agente (ej: `serio`, `sarcastico`). |
| `/idioma [es/en]` | Cambia el idioma de reconocimiento de voz. |
| `/usuarios` | Muestra los últimos 5 IDs de usuario registrados. |
| `/broadcast [msg]` | (Admin) Envía un mensaje a todos los usuarios registrados. |
| `/ayuda` | Muestra el menú de ayuda rápida en el chat. |

## Ejecución Avanzada

| Comando | Descripción |
| --- | --- |
| `/py [código/script]` | Ejecuta código Python o un script del proyecto dentro del Sandbox de Docker. |