# Especificación de producto · Plataforma de estudio con IA v1.0

**Fecha:** 2026-11-02. **Estado:** diseño para implementar posteriormente. **Nombre provisional:** Mi Campus; no es una marca aprobada.

## 1. Propósito y resultado esperado

Crear un espacio universitario donde el estudiante organice sus materias y convierta su propio material en aprendizaje: explicaciones, experimentos interactivos, resúmenes, tarjetas, práctica y recomendaciones. El tutor entiende la materia, las fuentes elegidas y la evidencia de aprendizaje, sin apropiarse de la navegación ni forzar un único método pedagógico.

La v1 debe funcionar de extremo a extremo con cuentas internas y permitir demostrar conceptos cloud reales: identidad, servicios administrados, almacenamiento persistente, procesamiento asíncrono, aislamiento de datos, escalamiento, observabilidad y despliegue reproducible. No basta una maqueta con respuestas pregrabadas.

### 1.1 Motivación y propuesta de valor (H0)

La hipótesis de partida es que estudiar se vuelve más difícil cuando los apuntes, las fechas, las explicaciones y la práctica quedan dispersos. En asignaturas físico-matemáticas, una respuesta aislada puede no mostrar cómo cambia un fenómeno al modificar sus parámetros ni si el estudiante es capaz de resolver un problema por sí mismo. Estas necesidades se validarán con recorridos y retroalimentación de estudiantes; no se presentan como resultados de una encuesta inexistente.

La propuesta conecta la organización académica con un ciclo de estudio: **material propio → explicación con fuentes → exploración interactiva → práctica → evidencia y siguiente paso**. Buscamos que el estudiante invierta menos esfuerzo en reconstruir el contexto y tenga más oportunidades de explorar, preguntar y comprobar su comprensión.

La diferenciación que se busca está en esa continuidad: respetar el método y la notación del material del alumno; crear recursos interactivos variados; separar personalidad del tutor y tipo de ayuda; mostrar progreso explicable, y compartir voluntariamente con amigos. Son objetivos de diseño, no afirmaciones de exclusividad frente a productos no evaluados. No se promete obtener mejores notas ni sustituir al profesor.

Cloud hace viable mantener el espacio personal entre dispositivos, separar identidades y datos, procesar documentos fuera de una petición web, adaptar capacidad a la demanda y observar fallos/costos. La arquitectura debe demostrar estas propiedades, no limitarse a publicar una página en internet. El informe académico desarrolla este argumento como una propuesta breve de presentación y una tabla de beneficios con criterios de validación.

## 2. Público, alcance y límites

- Estudiantes universitarios del Área 1: ciencias físico-matemáticas e ingeniería.
- Materias y temas libres. Cálculo, álgebra lineal, física y programación son casos representativos de validación, no cuatro materias obligatorias ni un límite del modelo de datos.
- Piloto interno con al menos tres cuentas de prueba para validar privacidad y amistad. No se elimina la autenticación porque aún no haya usuarios públicos.
- Interfaz y contenido inicial en español; fórmulas, símbolos y código preservan su notación.
- Web adaptable a escritorio, tableta y móvil. El laboratorio prioriza escritorio, pero ofrece controles accesibles y vista apilada en móvil.
- Sin pagos, comunidad pública, ranking global, integración institucional, videollamadas, tienda de estampillas ni aplicación nativa en esta versión.
- No se ejecutará código arbitrario de estudiantes en el servidor. Los ejemplos de programación pueden explicarse y visualizarse mediante recursos del laboratorio; un IDE remoto multi-lenguaje queda fuera.
- No habrá búsqueda externa automática que reemplace el material del estudiante. Ampliar con conocimiento general requiere contexto visible y, si existe material insuficiente, permiso del estudiante para esa respuesta.

## 3. Principios de experiencia

1. El estudiante llega a sus materias y pendientes. El chat empieza cerrado.
2. La primera sesión requiere pocos datos; el resto se completa cuando resulta útil.
3. El usuario puede pedir ejemplos, pistas o la solución completa. La personalidad no bloquea estas opciones.
4. Las fuentes del usuario tienen prioridad; la IA reconoce vacíos y discrepancias.
5. La personalización utiliza preferencias y resultados observables. No etiqueta a alguien permanentemente como “visual” o “auditivo”.
6. Los recursos interactivos son experiencias abiertas dentro de capacidades seguras, no variaciones de cinco plantillas.
7. Los indicadores distinguen práctica, ayuda y evidencia independiente. El tiempo conectado no equivale a aprendizaje.
8. La comparación social es voluntaria entre amigos y permite compartir solo lo elegido.

## 4. Recorridos principales

### 4.1 Primera sesión

Acceso → nombre visible y carrera opcional → objetivo y preferencias opcionales → crear primera materia → elegir ilustración → subir material o empezar sin él → primera actividad útil.

El tutorial usa pasos contextuales breves y puede saltarse, retomarse o reiniciarse en ajustes. No obliga a llenar horarios, todas las materias ni una evaluación antes de entrar. Un diagnóstico inicial corto se ofrece al comenzar una materia; puede omitirse y el progreso empieza como “evidencia insuficiente”.

### 4.2 Inicio y organización

Inicio muestra materias recientes, pendientes próximos, próxima evaluación, actividad sugerida y una pequeña síntesis del progreso. Un botón explícito abre al tutor. Si se abre desde una materia, adopta ese contexto; desde inicio, solicita o muestra la materia activa.

Estructura: perfil → periodos/semestres → materias → temas. Carrera y periodo pueden omitirse; una materia independiente sigue siendo válida. Se pueden crear, editar, archivar y eliminar materias. Archivar conserva historial y permite restaurar; eliminar activa el proceso de borrado descrito en arquitectura.

Pendientes: título, materia opcional, tipo (tarea, examen, estudio, otro), fecha/hora opcional, estado y notas. Horarios: bloques semanales, zona horaria y excepciones sencillas; no se integra un calendario externo en v1. Los recordatorios viven en la aplicación; correo y push no son requisitos de esta versión.

### 4.3 Materias e ilustraciones

Cada materia tiene nombre libre, descripción, periodo opcional, temas, ilustración y acento de una paleta accesible. La ilustración se elige de un catálogo genérico: geometría, ondas, cuadrícula, órbitas, circuitos, terminal, bloques, brújula, etc. Son propuestas de familias visuales, no nombres de asignaturas.

El catálogo usa identificadores estables e independientes del nombre o área. Puede cambiarse la ilustración sin perder datos. La creación ofrece una selección inicial y búsqueda por etiquetas, con una opción neutral predeterminada; nunca exige al alumno producir una imagen. La ilustración decorativa tiene texto alternativo vacío; el título de la materia es texto real. Se prevé ampliar el catálogo sin migrar las materias.

No se usará generación de imágenes pagada por cada materia en v1. Las ilustraciones finales se producirán como activos del sistema con licencia/procedencia registrada.

### 4.4 Material y biblioteca

Se aceptan PDF, PPTX, notas de texto/Markdown y fotografías/capturas PNG, JPEG y WebP. Un PPT antiguo se convierte a PPTX antes de subir; la interfaz lo explica. Se identifican PDFs con contraseña o dañados y formatos no admitidos antes de procesar.

Cada archivo muestra estado: cargando, en cola, procesando, requiere revisión, listo, falló o eliminando. El usuario puede salir y volver. Se extraen páginas/diapositivas, bloques, títulos, fórmulas y localizadores; los originales permanecen privados. En notas, las citas se ubican por sección/bloque. Las transcripciones dudosas de imágenes y fórmulas se muestran para corregir, y la corrección crea una nueva versión de extracción.

El sistema puede sugerir temas detectados para relacionar materiales y práctica. El estudiante confirma o edita esas sugerencias; no se reemplaza automáticamente su organización. Preguntas, evidencia y recomendaciones usan IDs de temas de esa materia, no etiquetas nuevas inventadas en cada respuesta.

Desde uno o varios materiales se puede pedir resumen, conceptos clave, flashcards, cuestionario o recurso interactivo. Cada resultado conserva procedencia y versión. El usuario puede guardar, renombrar, archivar y revisar recursos. Una reextracción no cambia silenciosamente los resultados existentes: se marca que su fuente tiene una versión nueva.

### 4.5 Tutor personalizado

Chat con historial por materia y conversaciones separadas. El estudiante puede iniciar una conversación nueva sin borrar su historial, elegir fuentes concretas y ver qué fuentes están activas.

Dos controles independientes:

- **Personalidad:** paciente/cercana, directa/concisa o retadora son propuestas iniciales editables. Cambian tono y ritmo.
- **Ayuda:** explicación, pistas, solución completa o práctica. Cambia el tipo de apoyo.

También puede indicar “tengo poco tiempo”, “quiero experimentar” o preferencia de formato; son ajustes de sesión. Las preferencias duraderas se guardan con consentimiento claro al cambiarlas, no se infieren como identidad permanente.

El tutor cita páginas o diapositivas cuando utiliza material. Si falta información, lo dice y ofrece ampliar con conocimiento general. Si detecta una contradicción, diferencia “tu material indica…” de su explicación y señala el problema. Si no hay material, puede trabajar con conocimiento general y lo indica. Un texto dentro de un PDF nunca es una instrucción administrativa para el sistema.

Durante el chat, el tutor puede iniciar la creación de un recurso si encaja con la petición o proponerlo cuando añadirlo sería una distracción. Se muestra progreso y se puede cancelar. No abre chats, realiza llamadas costosas ni modifica la agenda en segundo plano por iniciativa propia fuera de una interacción activa. Crear o cambiar pendientes requiere una acción visible de confirmación dentro del producto.

Como soporte inicial a la preferencia de escuchar, se propone lectura del texto mediante síntesis de voz disponible en el navegador, con reproducir/pausar y texto siempre visible. Su disponibilidad depende del navegador; voces premium, podcasts y transcripción continua de voz quedan fuera.

### 4.6 Laboratorio interactivo

El tutor puede crear HTML, CSS y JavaScript para explicar un concepto con composición libre: manipuladores de parámetros, gráficas, animaciones, pasos, ejercicios o visualizaciones de algoritmos. Se adapta al estilo visual de la plataforma mediante tokens, componentes de apoyo y directrices, sin obligarse a diseños cerrados.

La libertad de composición no implica acceso irrestricto al navegador. El código generado usa un SDK acotado para controles, eventos, texto, fórmulas, gráficas, dibujo y estado. No recibe credenciales, documentos completos ni objetos del navegador. El diseño de aislamiento y su prueba temprana están en [arquitectura](../../planning/arquitectura-y-contratos.md).

Flujo: petición → generación en trabajo persistente → validación estructural y de políticas → vista del recurso → guardar/reabrir → solicitar cambio → versión nueva. Si falla, se conserva la versión anterior y se ofrece explicación alternativa. Un error no se “repara” relajando restricciones de seguridad.

El recurso debe tener objetivo, instrucciones, controles con etiquetas, reinicio, explicación textual y referencias. Puede guardar parámetros y respuestas de exploración. Un recurso libre no puede declararse aprobado ni otorgar puntos: los intentos evaluados usan instrumentos controlados por el backend.

El estudiante puede compartir una versión concreta con amigos. La vista de publicación permite revisar qué texto generado se compartirá; no adjunta originales, historial, transcripciones ni citas con extractos privados. Las citas aparecen como “material privado del autor” cuando el receptor no tiene permiso. Revocar impide accesos posteriores, sin prometer borrar lo que otro ya haya visto o capturado.

### 4.7 Práctica, diagnóstico y adaptación

Se generan flashcards y cuestionarios basados en fuentes seleccionadas. Tipos iniciales: opción múltiple, respuesta numérica con unidades/tolerancia, respuesta corta y explicación abierta. Las preguntas tienen objetivo, tema, dificultad, solución razonada y referencias. La solución permanece en servidor durante un intento.

Evaluación determinista para elección y números; respuestas abiertas tienen retroalimentación de IA claramente identificada, rúbrica y opción de reportar discrepancia. Su puntuación provisional no se trata como prueba concluyente de dominio. La primera versión no implementa un evaluador simbólico universal.

Las tarjetas usan revisión espaciada sencilla con autoevaluación explícita, separada de aciertos verificados. Una petición de pista o solución marca el intento como asistido; no penaliza al estudiante por pedir ayuda, pero cambia la interpretación de la evidencia.

La recomendación propone una acción concreta y explica por qué: repasar un tema con errores, continuar una actividad, comprobar retención o preparar un examen. Una recomendación se puede omitir. La dificultad sube gradualmente con evidencia independiente y baja con errores repetidos; no cambia de forma extrema por una sola respuesta.

### 4.8 Progreso

Panel por materia/tema con intentos, precisión según tipo de evaluación, evolución, sesiones, minutos activos aproximados y revisiones pendientes. El indicador de dominio se presenta como estimación con nivel de evidencia; no como porcentaje exacto de conocimientos adquiridos.

Los minutos requieren sesión visible y actividad reciente; se fusionan intervalos entre pestañas. Se muestra que son aproximados y no se usan solos para certificar aprendizaje. Un alumno nuevo ve estados vacíos útiles, no porcentajes inventados.

### 4.9 Pasaporte, estampillas y amigos

El perfil incluye un pasaporte visual con colección, actividad y progreso compartible. Se conserva la idea de sellos/estampas de viaje, evitando que los ejemplos de las imágenes obliguen a estudiar asignaturas específicas.

**Pendiente del usuario:** nombres, ilustraciones, categorías y reglas editoriales definitivas de estampillas. Se construye un motor configurable con reglas verificables, estados bloqueada/en progreso/obtenida y capacidad de desactivar una definición. Para pruebas se usan fixtures neutrales marcados “de demostración”, sin convertirlos en catálogo aprobado ni incluirlos automáticamente en producción.

Amigos mediante código de invitación aleatorio y solicitud que acepta el destinatario, sin búsqueda pública por correo. Se pueden eliminar/bloquear amistades y revocar recursos. Comparación voluntaria de estampillas compartidas, materias mostradas por alias y actividad semanal aproximada; por defecto no comparte nada. Nunca se exponen dificultades, notas privadas, documentos, calificaciones detalladas o chats.

Retos privados sencillos: objetivo de sesiones o actividades de práctica, fechas y participantes que aceptan. No hay clasificación pública ni recompensas por mantener una pestaña abierta. Las reglas definitivas de estampillas no son necesarias para validar el mecanismo de amistad y comparación.

## 5. Diseño visual y accesibilidad

Referencia: [People’s Platform / Block & Bold](https://github.com/zarazhangrui/beautiful-html-templates/tree/main/templates/peoples-platform/), adaptada a una aplicación web. Los [conceptos existentes](../../design/conceptos-v1/PROMPTS.md) guían identidad y composición.

- Azul profundo `#122245`, oro `#B59957`, marfil `#F5F2EA`, arena `#E9DEC7`. Inspiración cromática universitaria, sin escudo ni afirmación de afiliación oficial. Referencia de [identidad CCH Oriente](https://www.cch-oriente.unam.mx/secretarias/general/imprenta/logos.html).
- Títulos con Alfa Slab One; cuerpo Archivo Narrow; etiquetas DM Mono; Caveat Brush solo como acento ocasional. Revisar licencia, empaquetar fuentes y mantener alternativas legibles.
- Bloques rectangulares, bordes firmes, sombras desplazadas, textura de papel sutil, ilustraciones de tinta. No convertir todo en tarjetas repetidas ni aplicar tipografía monumental a textos de estudio.
- Navegación consistente: Inicio, Materias, Biblioteca, Progreso, Pasaporte y Ajustes. Tutor como acción contextual, no como destino obligatorio inicial.
- Escritorio: contenido y tutor/laboratorio pueden convivir. Móvil: una región principal a la vez, navegación compacta, paneles apilados; sin scroll horizontal en la página.
- Contraste comprobado: azul sobre oro, no asumir que blanco sobre oro es legible. Foco visible, teclado completo, objetivos táctiles suficientes, reducción de movimiento, tablas/gráficas con explicación textual y fórmulas accesibles.
- Estados vacíos, carga, cola, revisión, fallo, desconexión y permiso denegado son parte del diseño.

## 6. Definición de v1 terminada

Todos los recorridos anteriores funcionan con datos persistentes y controles de acceso. Hay una demostración live de DeepSeek y una de despliegue cloud; los mocks se reservan para pruebas deterministas. Se completa la matriz de [validación](../../planning/validacion-y-demo.md), no hay bloqueos críticos de seguridad y se documentan límites observados.

Puede cerrarse la implementación del motor de estampillas sin arte final. Si el catálogo sigue pendiente al presentar la v1, el pasaporte muestra “colección en preparación” y la demostración usa el modo de datos sintéticos identificado. No se afirma que el catálogo editorial esté concluido.

## 7. Decisiones pendientes y responsables

| Decisión | Responsable | Momento | Opción de trabajo mientras tanto |
|---|---|---|---|
| Nombre/logotipo | Usuario | Antes de publicación pública | “Mi Campus” provisional |
| Estampillas finales | Usuario + diseño | Antes de activar colección real | Motor + fixtures de demostración |
| Ilustraciones finales de materias | Diseño | Antes del pulido visual | 12 ilustraciones genéricas de prueba; nombres libres |
| Textos de personalidades | Producto | Durante tutor | Tres propuestas editables |
| IDs de proyecto, cuenta facturación y credenciales | Usuario/operador | Antes del despliegue | Emuladores y proveedor falso |
| Presupuesto de infraestructura pagada | Usuario | Solo si las cuotas resultan insuficientes | Medir y presentar costo concreto |
| Ajuste de límites del piloto | Implementador con evidencia | Tras pruebas de documentos | Defaults de arquitectura |

No se necesita interrumpir la implementación por decisiones artísticas pendientes. No se deben sustituir decisiones de producto por preferencias de un subagente sin registrarlas.
