# Plataforma de estudio con IA · Plan de la v1.0

Fecha: 2 de noviembre de 2026. Estado: **arranque autorizado de H0 y H1; seguimiento en el registro de avance**.

Este paquete convierte la conversación y los conceptos visuales en un proyecto ejecutable. La v1 será una aplicación real para pruebas internas con varias cuentas, orientada a estudiantes universitarios de ciencias físico-matemáticas e ingeniería. El usuario autorizó comenzar las dos primeras etapas y documentarlas en LaTeX. Aún no se han aprovisionado ni desplegado servicios cloud. Consultar el [registro de avance](evidence/avance-fases-1-2.md) para distinguir trabajo terminado de trabajo previsto.

## Lectura recomendada

1. [Especificación del producto](superpowers/specs/2026-11-02-plataforma-estudio-design.md): alcance, experiencia, decisiones y pendientes.
2. [Arquitectura y contratos](planning/arquitectura-y-contratos.md): componentes, datos, API, trabajos y ejecución de recursos interactivos.
3. [Plan de implementación](superpowers/plans/2026-11-02-plataforma-estudio.md): tareas, dependencias, archivos, pruebas y criterios de cierre.
4. [Coordinación de subagentes](planning/subagentes.md): distribución del trabajo, propiedad de archivos, entregas y revisiones.
5. [Validación y demostración](planning/validacion-y-demo.md): pruebas funcionales, evaluación de IA, seguridad, experiencia y evidencia cloud.

## Qué es decisión y qué es propuesta

- **Acordado:** universidad/Área 1, materias libres, tutor configurable, documentos prioritarios, recursos interactivos abiertos, inicio organizador, pasaporte con amigos, Google Cloud, DeepSeek, pruebas internas y dirección visual Block & Bold con azul y oro.
- **Última corrección incorporada:** las materias tendrán un catálogo de ilustraciones genéricas seleccionables; sus nombres y su contenido son libres. Los nombres y dibujos definitivos de estampillas siguen pendientes.
- **Propuesta técnica de este plan:** React + TypeScript, FastAPI, Firebase Auth, Firestore, Cloud Storage, Cloud Run y Cloud Tasks; ejecución de JavaScript generado mediante un runtime limitado y un SDK de interacción. Es una recomendación de implementación, no una decisión previa atribuida al usuario.
- **Pendientes que no impiden construir:** nombre del producto, catálogo artístico final de estampillas, textos finales de personalidades y credenciales/datos del proyecto cloud. Los valores de capacidad del piloto son configurables.
- **Validaciones tempranas que sí condicionan trabajo posterior:** aislamiento y expresividad del laboratorio, extracción de fórmulas e imágenes, recuperación de fuentes y factibilidad del despliegue con las cuotas disponibles. No se ocultarán si fallan.

## Referencias visuales

Los [cuatro conceptos](design/conceptos-v1/PROMPTS.md) son referencia de lenguaje visual, no contratos funcionales. Textos, cifras, ilustraciones concretas y fórmulas de esas imágenes no se consideran datos aprobados.

- [Inicio](design/conceptos-v1/01-inicio.png)
- [Materia](design/conceptos-v1/02-materia.png)
- [Tutor y laboratorio](design/conceptos-v1/03-tutor-laboratorio.png)
- [Pasaporte](design/conceptos-v1/04-pasaporte.png)

## Regla de ejecución

Seguir el plan por dependencias y cerrar cada hito con evidencia. No implementar todos los módulos en paralelo desde el comienzo. Primero demostrar una ruta completa: crear materia → subir material → preguntar con cita → generar y guardar un recurso → practicar → reflejar progreso. El arranque actual cubre H0/H1; la ruta completa sigue siendo objetivo de hitos posteriores.

El cierre de esta planeación no significa que existan pruebas de software, infraestructura o seguridad aprobadas. Esas verificaciones están especificadas para la ejecución futura.
