# 🎓 Guía de Diseño de PCBs para Estudiantes

Bienvenido al flujo de trabajo de diseño electrónico asistido por IA. Esta guía te enseñará cómo pasar de una idea dibujada en papel a un circuito profesional listo para fabricar en CNC o industria.

## El Flujo de Trabajo (Workflow)

Para diseñar circuitos complejos (como los basados en SoCs), dividimos el proceso en pasos especializados:

### Paso 1: Interpretación del Esquema (`/disenar`)
Envía una foto de tu diagrama dibujado a mano. El bot utilizará **IA Vision** para identificar los componentes y crear una lista de conexiones (Netlist).

### Paso 2: Ubicación de Componentes (`/pcb`)
El bot colocará los componentes en la placa. 
*   **Consejo:** Esta fase usa algoritmos de atracción para poner cerca los componentes que comparten muchas conexiones. 
*   El bot dejará el **centro de la placa despejado** para facilitar el trabajo de los enrutadores de IA.

### Paso 3: Exportación para IA Externa (`/deeppcb`)
Como los circuitos modernos son densos, usamos **DeepPCB.ai**.
1.  Ejecuta `/deeppcb` para obtener el archivo `.dsn`.
2.  Sube ese archivo a la plataforma DeepPCB.
3.  Deja que su red neuronal trace las pistas.
4.  Descarga el archivo de sesión resultante (`.ses`).

### Paso 4: Finalización en KiCad (Manual/Local)
1.  Abre el archivo `.kicad_pcb` que te envió el bot.
2.  Ve a `Archivo -> Importar -> Specctra Session` y elige el archivo de DeepPCB.
3.  ¡Tus pistas aparecerán mágicamente!

### Paso 5: Generación de Archivos de Fabricación (`/fabricar`)
Una vez tengas las pistas, el bot generará los **Gerbers** (el estándar industrial) en un archivo ZIP.

### Paso 6: Preparación para CNC (`/gcode`)
Si vas a fabricar la placa tú mismo con una fresadora:
1.  Usa el comando `/gcode`.
2.  El bot convertirá los Gerbers en instrucciones de movimiento para la CNC.

---

## 🛠️ Parámetros de Fresado CNC para Estudiantes

Cuando generes tu G-Code con `/gcode`, el sistema utiliza valores estándar. Sin embargo, es vital que entiendas qué significan para ajustar tu máquina:

| Parámetro | Valor Sugerido | Descripción |
| :--- | :--- | :--- |
| **Profundidad de Corte (Z)** | -0.05mm a -0.1mm | Lo justo para remover el cobre (0.035mm) sin enterrar la fresa en la baquelita. |
| **Velocidad de Avance (Feed)** | 100 - 300 mm/min | Qué tan rápido se mueve la fresa lateralmente. Empieza lento (100) para evitar roturas. |
| **Velocidad de Husillo (Spindle)** | 10,000+ RPM | Las PCBs requieren velocidades altas para un corte limpio. |
| **Ancho de Aislamiento** | 0.2mm | El espacio que la fresa "limpia" alrededor de tu pista. |

### 💡 Consejos Pro para el Taller:
1. **Nivelación (Auto-leveling):** Las placas nunca son 100% planas. Usa un sistema de sonda (Z-Probe) antes de fresar o tus pistas desaparecerán en las zonas bajas.
2. **El "V-Bit" (Fresa en V):** Recuerda que estas fresas tienen forma de cono. Si profundizas demasiado en Z, la pista se volverá más delgada de lo diseñado (porque la parte ancha de la fresa "se come" el cobre).
3. **Limpieza:** Después de fresar, usa una lija muy fina (grano 600+) para quitar las rebabas de cobre antes de soldar.

---
**Nota Técnica:** Estamos usando KiCad 8.0.9. Asegúrate de tener esta versión instalada en tu PC para abrir los archivos que genera el bot.

*Dudas o soporte: Contacta con el administrador del Agente IA.*