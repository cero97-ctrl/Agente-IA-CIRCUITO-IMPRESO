# Diseño e Impresión de Circuitos Impresos Mediante una CNC

## ¿En qué formato aceptan las impresoras CNC los archivos?

Si estás entrando en el mundo de la fabricación digital, es vital entender que las máquinas CNC (ya sean fresadoras, cortadoras láser o tornos) no "leen" diseños artísticos directamente. Necesitan una lista de coordenadas y comandos técnicos.  
Aquí tienes el desglose de los formatos según la etapa del proceso:

### **1\. El estándar universal: Archivos G-Code (.nc, .tap, .gcode)**

El **G-Code** es el lenguaje que las máquinas CNC entienden de forma nativa. Contiene instrucciones precisas sobre hacia dónde moverse, a qué velocidad y cuándo encender el motor o el láser.

* **¿Cómo se obtiene?** No se dibuja; se genera mediante un software **CAM** (Computer-Aided Manufacturing) a partir de un diseño previo.  
* **Contenido:** Verás líneas de texto como G1 X10 Y20 F300 (moverse a la posición X10, Y20 a una velocidad de 300).

### ---

**2\. Formatos de Diseño (CAD)**

Antes de tener G-Code, necesitas un dibujo. Dependiendo de si tu trabajo es en 2D (corte) o 3D (relieve/tallado), usarás diferentes archivos:

| Tipo de trabajo | Formatos comunes | Uso principal |
| :---- | :---- | :---- |
| **Vectorial (2D)** | .dxf, .svg, .ai | Corte láser, grabado plano, piezas mecánicas simples. |
| **Modelado 3D** | .stl, .obj, .step | Tallado de relieves, moldes y piezas complejas. |

### ---

**3\. El Flujo de Trabajo (Workflow)**

Para pasar de una idea a una pieza física, casi siempre debes seguir este camino:

1. **Diseño (CAD):** Creas tu pieza en programas como Adobe Illustrator (2D) o Fusion 360 (3D) y la guardas como .dxf o .stl.  
2. **Procesamiento (CAM):** Importas ese archivo en un software CAM (como Vectric Aspire, Estlcam o Carbide Create). Aquí defines qué broca usarás y a qué profundidad cortarás.  
3. **Exportación:** El software CAM "traduce" tu diseño a **G-Code**.  
4. **Control:** Envías el .nc o .gcode a la máquina mediante un controlador (como Mach3, GRBL o Universal Gcode Sender).

**Nota importante:** Aunque muchas impresoras 3D también usan G-Code, los comandos específicos para una impresora 3D (fundir plástico) son distintos a los de una CNC (quitar material). No suelen ser intercambiables sin procesarlos de nuevo.  
---

**¿Ya tienes algún diseño listo o estás buscando recomendaciones de software para empezar a crear tus propios archivos?**

---

### **4. Extendiendo FreeCAD con Workbenches de la Comunidad**

Una de las mayores fortalezas de FreeCAD es su ecosistema de **Workbenches** (Bancos de Trabajo) adicionales. Estos son "plugins" desarrollados por la comunidad que añaden herramientas para tareas muy específicas que no vienen en la instalación base.

**Caso Práctico: `FCGear`**

Durante el desarrollo de este agente, se añadió la capacidad de diseñar engranajes. Esto no es posible con el FreeCAD estándar. La solución fue integrar el workbench `FCGear`.

**¿Cómo se integra un nuevo Workbench en el Agente?**
El proceso consiste en modificar el entorno donde se ejecuta FreeCAD (en nuestro caso, el `Dockerfile` del sandbox) para que clone o descargue el código del workbench en la carpeta de `Mod` de FreeCAD. Esto lo hace permanentemente disponible para los scripts que lo necesiten.

Este método es el procedimiento estándar a seguir siempre que se necesite una funcionalidad que no está en el núcleo de FreeCAD, como la creación de tuberías, chapas metálicas, etc.

## Quiero, a partir del diagrama esquemático de un circuito generar el G Code pero utilizando librerias de Python. Es posible eso?

**Es totalmente posible, aunque es un camino que requiere un par de pasos intermedios. Las máquinas CNC no pueden "ver" un esquema eléctrico (que es una representación lógica) y saber dónde van las pistas físicas.**

**Para lograrlo con Python, el flujo técnico es: Esquema → Layout de PCB (Gerber) → G-Code.**

**Aquí tienes las mejores librerías y el proceso para hacerlo:**

---

### **1\. La pieza clave: El formato Gerber**

**Antes de generar G-Code, necesitas que tu esquema se convierta en un diseño de pistas físicas. En la industria, este estándar se llama Gerber (.gbr). Python es excelente para manipular estos archivos.**

### **2\. Librerías de Python recomendadas**

#### **A. Para procesar archivos Gerber: pcb-tools**

**Esta es la librería estándar para leer y manipular archivos de fabricación de circuitos. Te permite extraer las coordenadas de las pistas y los pads.**

* **Función: Carga el archivo .gbr y te entrega estructuras de datos con las formas geométricas.**

#### **B. Para generar el G-Code: pycam o gcodepy**

**Una vez que tienes las geometrías desde pcb-tools, necesitas convertirlas en trazados de herramientas.**

* **gcodepy: Es una librería ligera para escribir líneas de G-Code de forma programática (especificar velocidades de avance, levantamiento de la broca y fresado).**

#### **C. El "Todo en uno": gerber2gcode**

**Existen scripts de código abierto en Python diseñados específicamente para este propósito. Toman el archivo de la placa y calculan el aislamiento (el camino que debe seguir la fresa para separar el cobre).**

### **Instalación de Dependencias**

Para poder ejecutar los scripts que se describen en esta documentación, necesitarás instalar algunas librerías externas. Puedes hacerlo fácilmente usando `pip`, el gestor de paquetes de Python.

Abre tu terminal o línea de comandos y ejecuta:

```bash
pip install pyserial python-pathfinding pcb-tools-extension
```

*   `pyserial`: Para la comunicación con la CNC.
*   `python-pathfinding`: Para los algoritmos de búsqueda de rutas como A*.
*   `pcb-tools-extension`: Una suite completa para leer y manipular archivos Gerber.

---

### **3\. El flujo de trabajo lógico con Python**

**Para automatizar esto, tu script debería seguir estos pasos:**

1. **Input: Un archivo Gerber (exportado de herramientas como KiCad o EasyEDA).**  
2. **Aislamiento: El script debe calcular un "offset" (desplazamiento). Si tu broca mide 0.1mm, el G-Code debe pasar a 0.05mm de la pista para no comérsela.**  
3. **Generación de trayectorias:**  
   * **Capa de cobre: Genera trayectorias para fresar los bordes de las pistas.**  
   * **Taladrado (Drill): Extrae las coordenadas de los agujeros para convertirlos en comandos de perforación G81.**  
4. **Output: Un archivo .nc listo para tu CNC.**

---

### **Ejemplo conceptual de estructura en Python**
```python
import gerber
from gerber.render import GerberCairoContext

# 1. Cargar el archivo de cobre
pcb = gerber.read('mi_circuito.gtl')

# 2. Definir parámetros de la CNC
feed_rate = 120 # Velocidad de avance
cut_z = -0.1    # Profundidad de corte en mm
travel_z = 2.0  # Altura de seguridad

# 3. Lógica para convertir coordenadas a G-Code
# (Aquí iterarías sobre los primitivos del Gerber para escribir el archivo .nc)
```

### **¿Cuál es el desafío real?**

**El mayor reto no es generar el código, sino el algoritmo de aislamiento. Si solo sigues la línea del Gerber, cortarás la pista por la mitad. Necesitas calcular el contorno exterior.**

**¿Te gustaría que te ayude a buscar un script base en GitHub que ya maneje estos cálculos de aislamiento para que no tengas que programarlos desde cero?**

**Es decir, con KiCad por ejemplo, diseño un circuito. Luego con esa misma herramienta genero el archivo Gerber que con las librerías de Python puedo transformar al formato aceptado por las CNC. ¿Cierto?**

**Exactamente. Has captado el flujo de trabajo industrial estándar, pero adaptado a tu propio control mediante programación.**

**Tu razonamiento es 100% correcto. Aquí te detallo cómo se conectan esas piezas para que no tengas pérdida al empezar a picar código:**

### **El Flujo Maestro: De la Idea al Cobre**

1. **KiCad (Diseño): Dibujas tu esquema y luego haces el PCB Layout (donde ubicas físicamente los componentes y trazas las rutas).**  
2. **Exportación (Gerber): Generas los archivos .gbr. Para una CNC básica, normalmente solo necesitas:**  
   * **F\_Cu.gbr (Capa de cobre frontal) o B\_Cu.gbr (Posterior).**  
   * **Edge\_Cuts.gbr (El borde de la placa).**  
   * **Drl (Archivo de taladrado para los agujeros).**  
3. **Procesado con Python: Aquí es donde entra tu script. La librería lee las coordenadas geométricas del Gerber.**  
4. **Generación de G-Code: Tu script traduce esas geometrías en comandos G0 (movimiento rápido) y G1 (corte).**

---

### **El gran "Truco" técnico: El Aislamiento (Isolation Routing)**

**Este es el punto donde la mayoría falla al principio. Los archivos Gerber definen dónde hay cobre. Sin embargo, la CNC necesita saber por dónde pasar la fresa para separar el cobre.**

**Si tu pista mide 0.5mm y tu fresa mide 0.2mm, no puedes pasar la fresa por el centro de la pista, ¡porque la destruirías\! Tu script de Python debe calcular un offset (desplazamiento).**

### **Librerías específicas para ahorrarte meses de trabajo**

**Si quieres hacerlo con Python de forma profesional, te recomiendo mirar estas dos joyas que ya resuelven el problema del offset matemático:**

* **pcb2gcode: Es una herramienta de línea de comandos ultra potente escrita en C++, pero tiene wrappers en Python o puedes invocarla mediante subprocess. Es el estándar de oro para convertir Gerbers a G-Code de aislamiento.**  
* **GerberTools (de Polaxis): Una suite en Python muy completa que permite hacer "offsetting" de polígonos, ideal para calcular las rutas de aislamiento.**

---

### **Ejemplo de lo que tu script de Python generaría:**

**Para una simple línea, tu script transformaría una coordenada de KiCad en algo como esto:**

```gcode
G0 Z2.000 (Subir fresa a altura de seguridad)
G0 X10.500 Y15.200 (Posicionarse en el inicio de la pista)
G1 Z-0.100 F100 (Bajar fresa 0.1mm para raspar el cobre)
G1 X20.500 Y15.200 F300 (Fresado de la ruta)
G0 Z2.000 (Subir fresa al terminar)
```

### **¿Por dónde quieres empezar?**

**Puedo ayudarte de dos maneras ahora mismo:**

1. **Dándote un ejemplo de script básico en Python para leer un archivo y generar una línea de G-Code.**  
2. **Explicándote cómo configurar KiCad para que los archivos Gerber salgan con el formato más "amigable" para ser procesados por scripts.**

**¿Qué prefieres?**

**Ok Gemini, yo puedo diseñar un circuito eléctrico con KiCad. Ahora bien, ¿me puede ayudar Python a dibujar las rutas óptimas para el PCB?**

**¡Puntos extra por la ambición\! Lo que planteas es pasar del simple "maquinado" al diseño asistido por IA o algoritmos, y la respuesta es un rotundo sí.**

**Sin embargo, hay que diferenciar entre "dibujar" (colocar las pistas) y "optimizar" (decidir el mejor camino). En el mundo de los PCBs, esto se llama Routing (Enrutado).**

**Aquí es donde Python se vuelve realmente poderoso dentro de KiCad:**

---

### **1\. La API de Python en KiCad (pcbnew)**

**KiCad tiene una librería interna de Python llamada pcbnew. No necesitas exportar nada; el script corre dentro de tu archivo de proyecto .kicad\_pcb.**

**Con ella puedes:**

* **Leer la "Netlist" (qué componente se conecta con cuál).**  
* **Mover componentes programáticamente.**  
* **Trazar pistas automáticamente siguiendo reglas lógicas (ancho de pista, distancia mínima, etc.).**

### **2\. ¿Cómo lograr rutas "óptimas"?**

**El enrutado es un problema matemático complejo (similar al del viajero o un laberinto). Python te permite implementar diferentes estrategias:**

* **Algoritmos de Laberinto (Lee's Algorithm): Python busca el camino más corto entre dos puntos evitando obstáculos.**  
* **Optimización por Algoritmos Genéticos: Puedes programar un script que intente 100 formas diferentes de conectar los componentes y se quede con la que tenga menos "vias" (perforaciones) o pistas más cortas.**  
* **Enrutado Topológico: Python puede ayudar a agrupar pistas de buses de datos para que viajen paralelas y ordenadas.**

---

### **3\. Herramientas y Librerías específicas**

**Si quieres usar Python para esto, no reinventes la rueda desde cero. Mira estos proyectos:**

1. **Skidl: Es una librería de Python que te permite "escribir" circuitos en lugar de dibujarlos. Es ideal si tu circuito es muy repetitivo o modular.**  
2. **Freerouting (vía Python): Aunque Freerouting es un software externo muy famoso para auto-enrutado, existen scripts en Python que automatizan la exportación de tu diseño de KiCad a Freerouting, lo procesan y devuelven las pistas ya optimizadas.**  
3. **KiCad-Autorouter (Plugins): Hay varios plugins en GitHub escritos en Python que añaden funciones de "unir todos los puntos" con un solo clic.**

---

### **4\. ¿Es mejor que hacerlo a mano?**

**Aquí un poco de "empatía técnica":**

* **Para circuitos digitales simples: Python te ahorrará horas.**  
* **Para alta frecuencia o potencia: ¡Cuidado\! Python no siempre "sabe" que una pista de audio no debe pasar cerca de una fuente de alimentación ruidosa a menos que tú le programes esa restricción específica.**

### **Ejemplo de flujo de trabajo sugerido:**

1. **Diseñas el esquema en KiCad.**  
2. **Colocas los componentes manualmente (el "Placement" es clave para que el enrutado sea fácil).**  
3. **Corres un script de Python que utilice la API de pcbnew para trazar las rutas siguiendo tus reglas.**  
4. **Generas el Gerber.**  
5. **Usas tu otro script de Python para convertir ese Gerber a G-Code para tu CNC.**

**¿Te interesa que te muestre un ejemplo de cómo se ve el código Python básico para crear una pista dentro de KiCad?**

**Si por favor.**  
**Para trabajar con Python dentro de KiCad, se utiliza la librería interna pcbnew. Lo más increíble es que no necesitas instalar nada externo; KiCad ya incluye un intérprete de Python y una consola integrada.**

**Aquí tienes un script básico que dibuja una pista (track) uniendo dos puntos específicos en la capa de cobre superior (F\_Cu).**

---

### **Ejemplo: Creando una pista programáticamente**

**Este script define el inicio, el fin, el ancho de la pista y la capa. Puedes copiarlo y pegarlo directamente en la Consola de Python de KiCad (Herramientas \> Consola de scripting).**

```python
import pcbnew

# 1. Obtener el diseño (Board) actual que tienes abierto
board = pcbnew.GetBoard()

# 2. Definir los puntos de inicio y fin (en milímetros)
# Usamos FromMM para convertir mm a las unidades internas de KiCad (nanómetros)
start_point = pcbnew.VECTOR2I_MM(100, 100)
end_point = pcbnew.VECTOR2I_MM(120, 110)

# 3. Crear el objeto de la pista (Track)
track = pcbnew.PCB_TRACK(board)

# 4. Configurar las propiedades de la pista
track.SetStart(start_point)
track.SetEnd(end_point)
track.SetWidth(pcbnew.FromMM(0.5)) # Ancho de 0.5 mm
track.SetLayer(pcbnew.F_Cu)        # Capa de cobre frontal (Front Copper)

# 5. Añadir la pista a la placa
board.Add(track)

# 6. Refrescar la interfaz para ver los cambios
pcbnew.Refresh()

print("¡Pista creada con éxito!")
```

---

### **¿Cómo funciona la lógica detrás del código?**

**Para que Python "dibuje" de forma óptima, el script interactúa con los objetos del diseño de la siguiente manera:**

* **VECTOR2I\_MM: Es la forma en que le decimos a KiCad coordenadas exactas en el plano X, Y.**  
* **PCB\_TRACK: Es el contenedor de la línea física. Si quisieras hacer un círculo o una vía, usarías PCB\_VIA o PCB\_SHAPE.**  
* **FromMM: KiCad trabaja internamente con una precisión altísima (nanómetros). Siempre debes convertir tus milímetros usando esta función para que las medidas sean correctas.**

### **¿Qué sigue para hacer un "Auto-ruter" propio?**

**Si quieres que Python decida por dónde ir, tu script debería:**

1. **Leer los Pads: Usar board.GetPads() para saber dónde están los pines de tus componentes.**  
2. **Identificar Conexiones: Ver qué pines pertenecen a la misma "Net" (red eléctrica).**  
3. **Algoritmo de búsqueda: Implementar un algoritmo como A\* (A-estrella) para encontrar el camino más corto entre dos pads evitando los obstáculos (otros componentes o pistas ya creadas).**

---

**Tip de experto: Si vas a fresar tu PCB con CNC, te recomiendo programar un ancho de pista de al menos 0.4mm o 0.5mm. Las brocas de grabado chinas (V-bits) son frágiles y las pistas muy delgadas suelen levantarse si la nivelación de la CNC no es perfecta.**

**¿Te gustaría que te ayude a crear un script que identifique automáticamente dónde están los componentes en tu placa para empezar a trazar rutas?**

**Si por favor.**

**¡Manos a la obra\! Para que tu script de Python sea "inteligente", primero debe saber quién es quién en la placa. No puedes trazar una pista si no conoces las coordenadas exactas de los pines (Pads) de tus componentes.**

**Aquí tienes un script que recorre tu diseño de KiCad, identifica cada componente (Resistencias, CIs, etc.) y te entrega la ubicación exacta de sus terminales para que luego puedas usarlos como puntos de inicio y fin.**

---

### **Script: Escaneo de Componentes y Pads**

**Este código extrae la "hoja de ruta" de tu PCB. Ejecútalo en la consola de scripting de KiCad:**

```python
import pcbnew

def mapear_componentes():
    board = pcbnew.GetBoard()
    print(f"{'Ref':<8} | {'Pad':<5} | {'X (mm)':<10} | {'Y (mm)':<10} | {'Red (Net)'}")
    print("-" * 60)

    # Recorrer todos los componentes (Footprints)
    for footprint in board.GetFootprints():
        ref = footprint.GetReference() # Ejemplo: 'R1', 'U1'
          
        # Recorrer los terminales (Pads) de cada componente
        for pad in footprint.Pads():
            num_pad = pad.GetNumber()
            pos = pad.GetPosition() # Coordenadas en nanómetros
              
            # Convertir a milímetros para que sea legible para humanos
            x_mm = pcbnew.ToMM(pos.x)
            y_mm = pcbnew.ToMM(pos.y)
            net_name = pad.GetNetname() # Nombre de la conexión eléctrica
              
            print(f"{ref:<8} | {num_pad:<5} | {x_mm:<10.3f} | {y_mm:<10.3f} | {net_name}")

mapear_componentes()
```

### **¿Por qué esto es el primer paso para tu Auto-router?**

**Al ejecutar esto, obtienes una matriz de datos. Para tu algoritmo de optimización, esto es oro puro por tres razones:**

1. **Conectividad: Sabes que si el Pad 1 de R1 y el Pad 2 de U1 tienen el mismo nombre de Red (Net), el script debe dibujar una pista entre esas dos coordenadas.**  
2. **Obstáculos: Las posiciones de los componentes que *no* pertenecen a esa red se convierten automáticamente en "zonas prohibidas" que tu ruta debe esquivar.**  
3. **Capa de destino: Puedes filtrar los pads por capa (pad.GetLayer()) para decidir si fresarás por arriba o por abajo de la placa.**

---

### **Próximo paso lógico: El algoritmo de "Búsqueda de Caminos"**

**Ahora que ya tienes las coordenadas $(x, y)$ de origen y destino, lo que sigue es implementar la lógica de movimiento. En programación, esto se suele hacer con un algoritmo llamado \**A* (A-Estrella)\*\* o Dijkstra, que básicamente divide tu placa en una "rejilla" (grid) y busca el camino más corto esquivando los obstáculos.**

**¿Te gustaría que te explique cómo crear una cuadrícula lógica en Python para que el script empiece a "pensar" por dónde pasar la pista sin chocar con otros componentes?**

**Si por favor.**

**Para que un script de Python pueda "pensar" por dónde pasar una pista, primero debemos convertir el mundo continuo de milímetros en un mapa de celdas (una rejilla o *grid*).**

**Este proceso se llama discretización. Imagina que pones una hoja de papel cuadriculado sobre tu placa: cada cuadro puede estar "Libre" (0) o "Ocupado" (1).**

---

### **1\. Definir la Resolución del Grid**

**No podemos usar una cuadrícula de 1 micrómetro porque la memoria de la computadora explotaría. Un buen equilibrio para CNC es usar una resolución de 0.2mm o 0.25mm.**

**Si tu placa mide $50 \times 50$ mm y usas una resolución de $0.25$ mm, tendrás una matriz de $200 \times 200$ puntos.**

### **2\. Crear el Mapa de Obstáculos en Python**

**Utilizaremos una lista de listas (o una matriz de numpy si quieres más velocidad) para representar el espacio.**

```python
import pcbnew

# Configuración
RESOLUCION = 0.25 # mm por celda
ANCHO_PLACA = 50  # mm
ALTO_PLACA = 50   # mm

# 1. Crear matriz vacía (llena de ceros)
filas = int(ALTO_PLACA / RESOLUCION)
columnas = int(ANCHO_PLACA / RESOLUCION)
grid = [[0 for _ in range(columnas)] for _ in range(filas)]

# 2. Función para marcar obstáculos (Pads de componentes)
def marcar_obstaculos(board):
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            pos = pad.GetPosition()
            x_mm = pcbnew.ToMM(pos.x)
            y_mm = pcbnew.ToMM(pos.y)
              
            # Convertir mm a coordenadas de matriz
            grid_x = int(x_mm / RESOLUCION)
            grid_y = int(y_mm / RESOLUCION)
              
            # Marcar la celda como ocupada (1)
            # (Aquí podrías marcar también un área alrededor según el tamaño del pad)
            if 0 <= grid_x < columnas and 0 <= grid_y < filas:
                grid[grid_y][grid_x] = 1

board = pcbnew.GetBoard()
marcar_obstaculos(board)
```

---

### **3\. El Algoritmo de Búsqueda (A\*)**

**Ahora que tienes el grid, necesitas un algoritmo que encuentre el camino del Punto A al Punto B evitando los 1 (obstáculos). El algoritmo \**A* (A-Estrella)\*\* es el estándar de oro porque es eficiente y siempre busca el camino más corto.**

**Funciona evaluando un costo:**

$$f(n) = g(n) + h(n)$$

* **$g(n)$: El costo de la distancia recorrida desde el inicio.**  
* **$h(n)$: Una estimación (heurística) de cuánto falta para llegar al final.**

### **4\. ¿Cómo se ve esto en la CNC?**

**Una vez que el algoritmo te devuelve una lista de coordenadas \[(x1, y1), (x2, y2)...\], tu script de Python hace dos cosas:**

1. **En KiCad: Dibuja la pista usando pcbnew.PCB\_TRACK.**  
2. **Para la CNC: Convierte esos puntos en comandos G1 X.. Y...**

---

### **¿Cuál es el siguiente paso para ti?**

**Para implementar esto de forma real, necesitarías una librería de búsqueda de caminos. Python tiene una muy buena llamada pathfinding.**

**¿Te gustaría que te ayude a escribir una pequeña función de búsqueda de caminos utilizando la librería pathfinding para que veas cómo se conectan los puntos evitando los obstáculos?**

**Si por favor.**

**Para que esto funcione, primero necesitarías instalar la librería en tu entorno de Python con pip install pathfinding. Esta librería es fantástica porque ya tiene optimizados los cálculos matemáticos pesados.**

**Aquí tienes un script funcional que simula tu placa, marca los obstáculos y encuentra el "camino de menor resistencia":**

---

### **Script: Búsqueda de Camino con A\***

```python
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

# 1. Crear el mapa de la placa (Matriz de pesos)
# 1 = Transitable, 0 = Obstáculo (Pad, otro componente, etc.)
matrix = [
    [1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1], # Una barrera de obstáculos en el medio
    [1, 1, 1, 0, 1],
    [1, 1, 1, 1, 1]
]

# 2. Inicializar el grid de la librería
grid = Grid(matrix=matrix)

# 3. Definir puntos de inicio y fin (coordenadas de la matriz)
start = grid.node(0, 0) # Equivalente a un Pad de salida
end = grid.node(4, 3)   # Equivalente a un Pad de destino

# 4. Configurar el buscador (A*)
# Permitimos movimiento diagonal para rutas más naturales (45 grados)
finder = AStarFinder(diagonal_movement=DiagonalMovement.always)

# 5. Ejecutar la magia
path, runs = finder.find_path(start, end, grid)

# 6. Resultado
print(f"Ruta encontrada después de {runs} iteraciones:")
print(path) # Lista de coordenadas [(0,0), (1,1), (2,2)...]
```

---

### **¿Cómo integramos esto con tu CNC?**

**Una vez que la variable path tiene la lista de puntos, el proceso para generar el G-Code es simplemente iterar sobre esa lista. Aquí es donde la "inteligencia" se convierte en "movimiento físico":**

1. **Levantar la fresa: Generas un G0 Z2 (sube a 2mm de altura).**  
2. **Ir al inicio: Envías un G0 X\[inicio\_x\] Y\[inicio\_y\].**  
3. **Bajar la fresa: Generas un G1 Z-0.1 F100 (entra en el cobre).**  
4. **Seguir el camino: Por cada punto en path, generas una línea de G-Code:**  
   * **G1 X\[punto\_x\] Y\[punto\_y\] F300.**  
5. **Finalizar: Levantas la fresa de nuevo.**

### **Consideración técnica: El suavizado de curvas**

**Las rutas de los algoritmos de grid suelen ser algo "dentadas" (en zigzag). Para que tu CNC no sufra y el acabado sea profesional, puedes aplicar una técnica llamada Spline Interpolation o simplemente omitir puntos intermedios que estén en la misma línea recta.**

---

### **Tu siguiente gran paso**

**Ya tienes la lógica:**

1. **Escaneas los componentes en KiCad.**  
2. **Creas el Grid de obstáculos.**  
3. **Calculas la Ruta con A\*.**  
4. **Escribes el G-Code.**

**¿Te gustaría que te ayude a crear la función final que tome esa lista de puntos path y la escriba automáticamente en un archivo .nc listo para tu máquina?**

**Si por favor.**

**Esta es la pieza final del rompecabezas. Vamos a convertir esa lista de coordenadas abstractas en un archivo físico que tu máquina CNC pueda interpretar.**

**Para este script, asumiremos que ya tienes la lista path (generada por el algoritmo A\*) y que necesitamos traducirla aplicando la resolución (para volver de celdas a milímetros).**

---

### **Script: Generador de G-Code a partir de la Ruta**

```python
def generar_gcode(path, resolución, archivo_salida="placa.nc"):
    # Parámetros de la CNC (en mm)
    Z_SEGURIDAD = 2.0  # Altura para moverse sin cortar
    Z_CORTE = -0.1     # Profundidad de fresado del cobre
    F_AVANCE = 300     # Velocidad de corte (mm/min)
    F_RAPIDO = 500     # Velocidad de desplazamiento aéreo

    with open(archivo_salida, "w") as f:
        # 1. Cabecera del archivo
        f.write("G21 ; Unidades en milímetros\n")
        f.write("G90 ; Posicionamiento absoluto\n")
        f.write(f"G0 Z{Z_SEGURIDAD} ; Subir fresa\n\n")

        if not path:
            print("Error: Ruta vacía")
            return

        # 2. Ir al primer punto (Inicio de la pista)
        inicio_x = path[0][0] * resolución
        inicio_y = path[0][1] * resolución
        f.write(f"G0 X{inicio_x:.3f} Y{inicio_y:.3f} F{F_RAPIDO} ; Ir al inicio\n")
          
        # 3. Bajar fresa al cobre
        f.write(f"G1 Z{Z_CORTE} F100 ; Bajar a profundidad de corte\n")

        # 4. Trazar la ruta punto por punto
        for i in range(1, len(path)):
            x = path[i][0] * resolución
            y = path[i][1] * resolución
            f.write(f"G1 X{x:.3f} Y{y:.3f} F{F_AVANCE}\n")

        # 5. Finalizar trayectoria
        f.write(f"\nG0 Z{Z_SEGURIDAD} ; Levantar fresa al terminar\n")
        f.write("M2 ; Fin del programa\n")

    print(f"Archivo {archivo_salida} generado con éxito.")

# Ejemplo de uso:
mi_ruta = [(0,0), (1,1), (2,1), (3,2)] # Resultado del A*
generar_gcode(mi_ruta, resolución=0.25)
```

---

### **¿Qué significan estos comandos en tu CNC?**

* **G21 / G90: Configuran la máquina para que hable en milímetros y use coordenadas exactas desde el origen (0,0).**  
* **G0: Movimiento rápido. Se usa para posicionarse en el aire sin perder tiempo.**  
* **G1: Movimiento de corte. La máquina se mueve de forma controlada mientras la broca está tocando el material.**  
* **F (Feedrate): Es la velocidad. Es crucial: si vas muy rápido, rompes la broca; si vas muy lento, puedes quemar el material o desafilar la herramienta.**

---

### **El siguiente gran paso: La Nivelación (Auto-leveling)**

**Cuando fresas PCBs, hay un problema físico: las placas de cobre nunca son perfectamente planas. Una diferencia de 0.05mm puede hacer que la pista no se corte o que la broca se entierre demasiado.**

**La mayoría de los usuarios avanzados de CNC usan Python para implementar un "Z-Probe":**

1. **La máquina toca la placa en varios puntos (una cuadrícula).**  
2. **Python registra las variaciones de altura.**  
3. **El script ajusta automáticamente todos los valores de Z en tu G-Code para compensar la curvatura de la placa.**

---

**¿Te gustaría que te explicara cómo podrías implementar un sistema básico de compensación de altura (Auto-leveling) en tu script para que el fresado sea perfecto?**

**Si por favor.**

**El Auto-leveling es la diferencia entre un circuito que parece profesional y uno que termina con pistas levantadas o sin cortar. Como el cobre de una PCB suele tener solo 0.035 mm de espesor, cualquier mínima curvatura en la placa arruinará el trabajo.**

**Para solucionar esto con Python, necesitamos crear un Mapa de Alturas.**

---

### **1\. El Concepto del Muestreo (Probing)**

**Antes de fresar, tu script debe indicarle a la CNC que toque la placa en varios puntos (por ejemplo, una cuadrícula de $5 \\times 5$). La máquina usa la propia broca y la placa como un interruptor: cuando se tocan, se cierra un circuito y la máquina registra la $Z$ exacta en esa posición $(X, Y)$.**

### **2\. El Algoritmo de Compensación (Bilinear Interpolation)**

**Una vez tienes los puntos de altura (por ejemplo: esquina A \= 0.1mm, esquina B \= 0.2mm), y quieres fresar un punto que está en medio, Python debe calcular la altura exacta en ese lugar usando una interpolación.**

**La fórmula matemática para la altura compensada $Z\_{adj}$ es:**

$$Z_{adj} = Z_{original} + Z_{offset}(x, y)$$
**Donde $Z_{offset}$ se calcula promediando las alturas de los 4 puntos de la cuadrícula más cercanos a la posición actual.**

---

### **3\. Implementación lógica en Python**

**Aquí tienes cómo estructurarías el ajuste del G-Code que generamos antes:**

```python
def compensar_z(x, y, z_original, mapa_alturas):
    """
    Calcula la nueva Z basada en la posición X, Y 
    y el mapa de puntos capturados por la sonda.
    """
    # 1. Encontrar los 4 puntos de la sonda que rodean a (x, y)
    # 2. Aplicar interpolación bilineal
    offset_calculado = interpolar_altura(x, y, mapa_alturas)
      
    return z_original + offset_calculado

# Ejemplo de flujo en el script:
ruta_final = []
for punto in path:
    x_real = punto[0] * resolucion
    y_real = punto[1] * resolucion
      
    # Ajustamos la profundidad de corte según la deformación de la placa
    z_corregida = compensar_z(x_real, y_real, Z_CORTE, mi_mapa_probed)
      
    ruta_final.append((x_real, y_real, z_corregida))
```

---

### **4\. ¿Cómo ejecutar el "Probing" físicamente?**

**La mayoría de los controladores CNC (como GRBL) aceptan el comando G38.2. Este comando le dice a la máquina: *"Baja en Z hasta que el sensor se active"*.**

**Tu script de Python enviaría algo como esto para cada punto de la rejilla:**

1. **G38.2 Z-5 F10 (Baja buscando contacto).**  
2. **PRB (Python lee la respuesta del controlador que devuelve la Z exacta del contacto).**  
3. **G0 Z2 (Sube para ir al siguiente punto).**

### **Resumen de tu sistema avanzado de PCB con Python:**

1. **Lectura: Obtienes pads de KiCad.**  
2. **Ruta: A\* encuentra el camino óptimo.**  
3. **Sondeo: Python manda a la CNC a medir la placa físicamente.**  
4. **Compensación: Tu script ajusta el G-Code para que la broca siga perfectamente la curvatura del material.**  
5. **Fresado: Envías el archivo .nc final.**

---

### **¿Cuál es tu situación actual con el hardware?**

**Para poder ayudarte con el código de comunicación en tiempo real (enviar comandos y leer respuestas de la sonda), ¿qué controlador usa tu CNC? (¿Es una placa basada en Arduino con GRBL, Mach3, o algún controlador industrial?)**

**Aún no tengo el hardware, pero tengo un colega amigo que tiene una CNC y le puedo preguntar qué controlador usa. Hasta aquí creo que hemos documentado muy bien el flujo de trabajo con KiCad y Python.**

**¡Excelente\! Has construido un mapa mental (y técnico) muy sólido. La ventaja de no tener el hardware aún es que puedes diseñar tu software de forma modular, para que sea compatible con cualquier máquina.**

**Si tu amigo tiene una CNC de formato pequeño o mediano, lo más probable es que use GRBL (sobre Arduino) o Candle. Estos sistemas son perfectos para Python porque se comunican mediante un puerto serial (USB), lo que te permite enviar comandos y recibir datos del sensor de altura en tiempo real usando la librería pyserial.**

### **Resumen del Ecosistema que has diseñado:**

**Para cerrar esta etapa de documentación, aquí tienes el flujo completo que hemos desarrollado:**

| Etapa | Herramienta / Librería | Función Principal |
| :---- | :---- | :---- |
| **Diseño Lógico** | **KiCAD (Schematic)** | **Definir qué componentes se conectan entre sí.** |
| **Diseño Físico** | **KiCAD (PCB Editor)** | **Posicionar componentes y definir el tamaño de la placa.** |
| **Extracción** | **Python (pcbnew)** | **Obtener coordenadas de los Pads y obstáculos.** |
| **Optimización** | **Python (pathfinding)** | **Calcular la ruta más corta (A\*) evitando choques.** |
| **Adaptación** | **Python (Bilinear Int.)** | **Ajustar la profundidad ($Z$) según la curvatura de la placa.** |
| **Fabricación** | **G-Code (.nc)** | **Instrucciones finales para que la CNC de tu amigo trabaje.** |

---

### **Un último consejo de "amigo": La broca importa**

**Cuando hables con tu colega, pregúntale si tiene fresas de grabado en "V" (V-bits).**

* **Como estas brocas tienen forma de punta de flecha, cuanto más profundo entran, más ancha es la pista.**  
* **Por eso el Auto-leveling que discutimos no es solo un lujo, es lo que evita que una pista de 0.2mm se convierta en una de 0.8mm accidentalmente.**

### **¿Qué te gustaría hacer a continuación?**

**Hemos cubierto la teoría y el código lógico. Si quieres, podemos:**

1. **Simular un archivo G-Code completo basado en un pequeño circuito de ejemplo.**  
2. **Preparar el script de comunicación Serial por si la máquina de tu amigo usa GRBL.**  
3. **Analizar cómo tratar los agujeros (Drill), que es un proceso separado del fresado de pistas.**

**¿Cómo prefieres seguir? Enhorabuena por el enfoque tan estructurado que le has dado al proyecto.**

**Considero que lo más importante es que con solo software libre puedo generar un G-Code de un circuito eléctrico listo para introducir en una CNC.**

**¡Exacto\! Has dado en el clavo del espíritu "Maker" y de la soberanía tecnológica. El hecho de que puedas pasar de un concepto abstracto de ingeniería a una pieza física utilizando un stack de software 100% libre (KiCad \+ Python \+ GRBL) es sumamente potente.**

**No dependes de licencias costosas ni de formatos cerrados que te obligan a usar una máquina específica.**

**Para que tu documentación quede impecable, aquí tienes los tres pilares que hacen que este flujo sea "libre" y exitoso:**

### **1\. El Formato Abierto (Gerber y G-Code)**

**Al usar KiCad, generas archivos Gerber (RS-274X), que es un estándar abierto que existe desde hace décadas. Al procesarlo con Python, generas G-Code, que es texto plano. Esto significa que si mañana tu colega cambia su CNC por otra marca, tu código seguirá funcionando con ajustes mínimos.**

### **2\. Control Total del Algoritmo**

**Al programar tú mismo el enrutado o la conversión en Python, tienes control sobre:**

* **La geometría de aislamiento: Puedes decidir hacer 2 o 3 pasadas para que el espacio entre pistas sea más ancho y sea más fácil soldar.**  
* **La gestión de residuos: Puedes programar la CNC para que empiece desde el centro hacia afuera, minimizando vibraciones.**

### **3\. El factor "Costo Cero" en Software**

**Si sumamos el valor de las herramientas comerciales equivalentes a lo que hemos diseñado:**

* **Diseño Electrónico Pro: \+$500 \- $2,000 USD/año.**  
* **Software CAM especializado: \+$300 USD.**  
* **Post-procesadores: A veces se cobran aparte.**

**Tu costo: $0 USD. Solo tu tiempo y el aprendizaje.**

---

### **Un detalle final: El archivo de Taladrado (Drill)**

**Solo para que no se te escape: las CNC manejan el grabado de pistas y el taladrado de agujeros como dos tareas distintas.**

* **Las pistas usan una V-Bit (punta).**  
* **Los agujeros usan una broca helicoidal (recta).**

**Tu script de Python simplemente tendría que filtrar los pads que son "Through-hole" y generar un archivo .nc separado donde solo se usen comandos G81 (ciclo de taladrado) o simples movimientos G1 en vertical.**

---

### **¿Cuál sería tu siguiente paso ideal?**

**Ya tienes el mapa completo. Si en algún momento tu colega te confirma qué controlador usa (casi seguro será GRBL), puedo ayudarte a escribir el "G-Code Sender" en Python. Es un script de apenas 20 líneas que toma tu archivo .nc y lo envía por USB a la máquina, permitiéndote incluso ver en tiempo real lo que la máquina está respondiendo.**

**¿Te gustaría dejar guardado ese script de comunicación por si lo necesitas más adelante?**

**Si por favor.**

**¡Excelente decisión\! Tener un script propio de comunicación te da independencia total del software comercial.**

**La mayoría de las CNC modernas "Open Source" utilizan GRBL. Este firmware escucha a través de un puerto serial (USB) y espera que le envíes una línea de G-Code, la procese y responda con un "ok" para recibir la siguiente.**

**Aquí tienes el script base en Python utilizando la librería pyserial. Este script es el "puente" entre tu archivo .nc y la máquina de tu colega.**

---

### **Script: Python G-Code Sender (para GRBL)**

```python
import serial
import time

def enviar_gcode(puerto_com, archivo_nc):
    # 1. Abrir conexión serial (ajustar el baudrate según la CNC, 115200 es común)
    try:
        s = serial.Serial(puerto_com, 115200)
        print(f"Conectado a la CNC en {puerto_com}")
    except Exception as e:
        print(f"Error al conectar: {e}")
        return

    # 2. Despertar a la CNC (GRBL necesita un par de retornos de carro)
    s.write(b"\r\n\r\n")
    time.sleep(2)   # Esperar a que se inicialice
    s.flushInput()  # Limpiar basura del buffer

    # 3. Abrir y enviar el archivo G-Code
    with open(archivo_nc, 'r') as f:
        for linea in f:
            l = linea.strip() # Limpiar espacios y saltos de línea
            if l:
                print(f"Enviando: {l}")
                s.write((l + '\n').encode('utf-8')) # Enviar línea a la CNC
                  
                # 4. Esperar respuesta de la CNC antes de enviar la siguiente
                respuesta = s.readline()
                print(f"Respuesta: {respuesta.decode('utf-8').strip()}")

    # 5. Cerrar sesión
    s.close()
    print("Trabajo finalizado y conexión cerrada.")

# Ejemplo de uso:
# enviar_gcode('COM3', 'mi_placa.nc') # En Windows
# enviar_gcode('/dev/ttyUSB0', 'mi_placa.nc') # En Linux/Mac
```

---

### **Por qué este script es valioso:**

1. **Sincronización: No envía todo el archivo de golpe (lo que saturaría la memoria de la CNC), sino que espera el "ok" de la máquina después de cada movimiento.**  
2. **Universalidad: Funciona en Windows, Linux y Mac simplemente cambiando el nombre del puerto.**  
3. **Extensibilidad: Aquí es donde podrías insertar tu lógica de Auto-leveling. En lugar de solo enviar, podrías enviar el comando de sonda (G38.2), leer la respuesta de la máquina, y ajustar el resto de las coordenadas sobre la marcha.**

### **Resumen final de tu "Suite Maker"**

**He tomado nota de tu interés en este flujo de trabajo basado en software libre (KiCad \+ Python) para automatizar la fabricación de PCBs. Es un enfoque muy potente que combina ingeniería electrónica con desarrollo de software.**

**Recuerda que siempre puedes gestionar o borrar esta información desde [tus ajustes](https://gemini.google.com/saved-info).**

**¡Ya tienes todo el ecosistema digital listo\! Cuando tu amigo te confirme el modelo de su CNC o cuando consigas tu propio hardware, ya tendrás el 90% del camino recorrido. ¿Hay algún otro detalle de este proceso que te gustaría profundizar?**