# Prompts de ilustraciones e iconos

Para generar con ChatGPT. Cada imagen se guarda en `apps/web/public/art/` con el nombre indicado; si falta, la app muestra un icono de respaldo ([README de art](../../apps/web/public/art/README.md)).

## Cómo usarlos

1. Empieza **cada** prompt con el estilo maestro de abajo, para que todo salga coherente.
2. Pide 1024×1024 (o la proporción indicada). La app la reduce.
3. Si ChatGPT no da fondo transparente, pide "fondo liso #F5F2EA" y quítalo con una herramienta de recorte. Con ese color de fondo también funcionan en la app.
4. Guarda como PNG con el nombre exacto de la tabla.

## Estilo maestro (pegar al inicio de cada prompt)

> Ilustración vectorial plana, estilo editorial "Block & Bold": formas geométricas sólidas, contornos gruesos y limpios en azul marino #122245, acentos en oro #b59957, rellenos suaves en arena #e9dec7 y papel #f5f2ea, con una sombra desplazada dura en oro (sin degradados, sin difuminados, sin 3D realista). Esquinas ligeramente redondeadas. Sensación universitaria de matemáticas, física e ingeniería. Sin texto, sin letras legibles, sin marcas de agua. Fondo transparente. Composición centrada con 8% de margen.

## Tutor

| Archivo | Tamaño | Prompt (después del estilo maestro) |
|---|---|---|
| `tutor-avatar.png` | 512×512 | Mascota amable: una estrella de cuatro puntas dorada con ojos redondos y una sonrisa suave, con un birrete pequeño azul marino. Vista frontal, cabeza y hombros, pensada para recortarse en círculo. |
| `tutor-empty.png` | 800×600 | Una estudiante sentada con laptop y cuaderno; a su lado flota la mascota estrella dorada señalando garabatos abstractos de ecuaciones (ilegibles). Ambiente tranquilo y motivador. |
| `personalities/patient.png` | 256×256 | Una escalera de cuatro escalones con una figura pequeña subiendo con calma. Representa "paso a paso". |
| `personalities/socratic.png` | 256×256 | Una bombilla grande con un signo de interrogación dibujado como forma geométrica dentro. Representa "preguntemos". |
| `personalities/direct.png` | 256×256 | Una flecha recta que atraviesa el centro de una diana. Representa "al grano". |

## Tipos de recurso

| Archivo | Tamaño | Prompt |
|---|---|---|
| `kinds/summary.png` | 256×256 | Una hoja con líneas de texto abstractas y un marcador dorado en el borde. |
| `kinds/concepts.png` | 256×256 | Una bombilla con tres puntos conectados por líneas, como una pequeña red de ideas. |
| `kinds/flashcards.png` | 256×256 | Dos tarjetas apiladas, la de arriba a medio voltear. |
| `kinds/quiz.png` | 256×256 | Una lista con tres casillas, una con palomita dorada, y un lápiz. |
| `kinds/interactive.png` | 256×256 | Un matraz de laboratorio con ondas dentro y un control deslizante (slider) debajo. |

## Estampillas del pasaporte

Todas: estampilla postal circular con borde dentado, sello de tinta en azul marino y oro, 256×256.

| Archivo | Prompt (después del estilo maestro y la línea anterior) |
|---|---|
| `stamps/first_material.png` | Una pluma sobre una hoja. |
| `stamps/first_question.png` | Un signo de interrogación dentro de un globo de diálogo. |
| `stamps/first_resource.png` | Una estrella dorada sobre un libro abierto. |
| `stamps/explorer.png` | Un telescopio apuntando a una estrella y una brújula pequeña. |
| `stamps/first_quiz.png` | Una palomita grande sobre una lista de casillas. |
| `stamps/perfect_quiz.png` | Una diana con la flecha exactamente en el centro y destellos alrededor. |
| `stamps/cards_ten.png` | Un abanico de diez tarjetas abiertas. |
| `stamps/three_subjects.png` | Tres libros apilados: uno azul marino, uno dorado y uno arena. |

## Materias (cuadro 640×520, las 12 ilustraciones que se pueden elegir)

| Archivo | Prompt |
|---|---|
| `subjects/grid.png` | Una retícula de líneas finas con una franja diagonal dorada gruesa. |
| `subjects/wave.png` | Tres ondas senoidales superpuestas con distinta amplitud. |
| `subjects/orbit.png` | Un núcleo central con tres órbitas elípticas y pequeños satélites dorados. |
| `subjects/geometry.png` | Un triángulo con una circunferencia inscrita y un compás de dibujo. |
| `subjects/terminal.png` | Una ventana de terminal con un cursor, un prompt y llaves { }. |
| `subjects/circuit.png` | Un circuito sencillo con batería, resistencia, interruptor y un foco encendido. |
| `subjects/blocks.png` | Bloques geométricos apilados como piezas de rompecabezas. |
| `subjects/compass.png` | Una brújula grande con aguja dorada. |
| `subjects/vector.png` | Ejes cartesianos con dos vectores y su suma en oro. |
| `subjects/graph.png` | Una gráfica de funciones con un área sombreada bajo la curva. |
| `subjects/cube.png` | Un cubo isométrico en estructura de alambre con una cara rellena en oro. |
| `subjects/nodes.png` | Un grafo de nodos conectados con un nodo central dorado. |

## Iconos de la interfaz (128×128, trazo grueso, un solo motivo, sin sombra)

| Archivo | Prompt |
|---|---|
| `icons/nav-home.png` | Una casa sencilla. |
| `icons/nav-subjects.png` | Un libro cerrado con un marcador. |
| `icons/nav-agenda.png` | Un calendario con una marca. |
| `icons/nav-schedule.png` | Un reloj con dos manecillas. |
| `icons/nav-profile.png` | Una persona de pecho hacia arriba. |
| `icons/mode-explain.png` | Un libro abierto. |
| `icons/mode-hints.png` | Una brújula pequeña. |
| `icons/mode-solution.png` | Una palomita gruesa. |
| `icons/mode-practice.png` | Una diana con una flecha. |

## Escenas grandes (aún no conectadas; se conectan al tenerlas)

| Archivo | Tamaño | Prompt |
|---|---|---|
| `logo.png` | 512×512 | Un bloque cuadrado azul marino con una estrella dorada de cuatro puntas en el centro. |
| `login-hero.png` | 1200×1400 | Una torre de bloques geométricos con formas inspiradas en ∫, Σ y π (como siluetas, sin letras), estrellas doradas alrededor. Pensada sobre fondo azul marino: contornos claros #f5f2ea y oro. |
| `home-hero.png` | 600×400 | Un compás y una escuadra sobre una retícula, con una franja dorada. |
| `empty-resources.png` | 600×400 | Un cajón abierto con tarjetas y un matraz asomando, vacío y acogedor. |
| `empty-materials.png` | 600×400 | Una pila de hojas con un documento tipo PDF y una presentación, y una flecha hacia arriba. |
| `empty-agenda.png` | 600×400 | Un calendario grande con una palomita dorada y una pequeña maceta. |
