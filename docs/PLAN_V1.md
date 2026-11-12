# Plataforma de estudio con IA · Plan de la v1.0

Fecha del plan: 2 de noviembre de 2026. Actualización: 11 de noviembre de 2026. Estado: **H0–H2 cerrados; acceso remoto solicitado y trabajo pausado hasta aviso del usuario sobre facturación activa**. Consultar primero el [contexto actual](CONTEXTO.md).

Este paquete convierte la conversación y los conceptos visuales en un proyecto ejecutable. La v1 es una aplicación para piloto interno, orientada a estudiantes universitarios de ciencias físico-matemáticas e ingeniería. El usuario autorizó H0/H1 y su documentación LaTeX, y después H2 con publicación del código verificado en GitHub. Firebase Auth y Firestore reales están configurados; la web sigue local. Consultar el [avance de H0/H1](evidence/avance-fases-1-2.md) y el [cierre H2](evidence/cierre-h2.md) para distinguir implementación, pruebas reales y capacidades de despliegue pendientes.

## Lectura recomendada

1. [Especificación del producto](superpowers/specs/2026-11-02-plataforma-estudio-design.md): alcance, experiencia, decisiones y pendientes.
2. [Arquitectura y contratos](planning/arquitectura-y-contratos.md): componentes, datos, API, trabajos y ejecución de recursos interactivos.
3. [Plan de implementación](superpowers/plans/2026-11-02-plataforma-estudio.md): tareas, dependencias, archivos, pruebas y criterios de cierre.
4. [Coordinación de subagentes](planning/subagentes.md): referencia histórica de distribución; actualmente se trabaja con un solo agente por preferencia del usuario.
5. [Validación y demostración](planning/validacion-y-demo.md): pruebas funcionales, evaluación de IA, seguridad, experiencia y evidencia cloud.

## Qué es decisión y qué es propuesta

- **Acordado:** universidad/Área 1, materias libres, tutor configurable, documentos prioritarios, recursos interactivos abiertos, inicio organizador, pasaporte con amigos, Google Cloud, DeepSeek, pruebas internas y dirección visual Block & Bold con azul y oro.
- **Última corrección incorporada:** las materias tendrán un catálogo de ilustraciones genéricas seleccionables; sus nombres y su contenido son libres. Los nombres y dibujos definitivos de estampillas siguen pendientes.
- **Propuesta técnica de este plan:** React + TypeScript, FastAPI, Firebase Auth, Firestore, Cloud Storage, Cloud Run y Cloud Tasks; ejecución de JavaScript generado mediante un runtime limitado y un SDK de interacción. Es una recomendación de implementación, no una decisión previa atribuida al usuario.
- **Pendientes de producto:** nombre definitivo y catálogo artístico final de estampillas. Las personalidades y límites actuales del piloto están implementados y son ajustables. Los proyectos Firebase/GCP y la clave DeepSeek local ya están configurados; la facturación y la infraestructura de despliegue siguen pendientes de reanudación.
- **Nueva indicación de interfaz:** usar esqueletos en todas las esperas, sin spinners. La aplicación general de este requisito sigue pendiente.
- **Validaciones tempranas que sí condicionan trabajo posterior:** aislamiento y expresividad del laboratorio, extracción de fórmulas e imágenes, recuperación de fuentes y factibilidad del despliegue con las cuotas disponibles. No se ocultarán si fallan.

## Referencias visuales

Los [cuatro conceptos](design/conceptos-v1/PROMPTS.md) son referencia de lenguaje visual, no contratos funcionales. Textos, cifras, ilustraciones concretas y fórmulas de esas imágenes no se consideran datos aprobados.

- [Inicio](design/conceptos-v1/01-inicio.png)
- [Materia](design/conceptos-v1/02-materia.png)
- [Tutor y laboratorio](design/conceptos-v1/03-tutor-laboratorio.png)
- [Pasaporte](design/conceptos-v1/04-pasaporte.png)

## Regla de ejecución

Seguir el plan por dependencias y cerrar cada hito con evidencia. No implementar todos los módulos en paralelo desde el comienzo. Primero demostrar una ruta completa: crear materia → subir material → preguntar con cita → generar y guardar un recurso → practicar → reflejar progreso. Lo entregado cubre H0–H2; desde generar y guardar recursos integrados, la ruta completa sigue siendo objetivo de hitos posteriores.

El plan completo no equivale a implementación completa. H0–H2 tienen verificaciones registradas; las capacidades futuras y la infraestructura no desplegada requieren sus propias pruebas. La pausa actual no se levanta por actualizar esta documentación.
