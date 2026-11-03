# Avance de las fases 1 y 2

Registro actualizado por el integrador; no sustituye resultados de prueba.

**Correspondencia:** fase 1 = H0 (T01–T04), fase 2 = H1 (T05–T08).

## Estado

| Entrega | Estado | Evidencia / pendiente |
|---|---|---|
| Justificación, motivación y propuesta de valor H0 | Completada | Especificación §1.1 e informe resumido con pitch |
| Informe escolar LaTeX/PDF | Versión resumida verificada | 8 páginas, compilación y revisión visual; reemplaza versión de 19 páginas |
| T01 Base local | Implementada y revisada | Smoke de tres servicios y revisión; Ctrl+C interactivo aún no verificado |
| T02 Contratos | Completada para H0/H1 | Entradas/salidas H1, OpenAPI/TS, puertos y protocolo. Contratos futuros se amplían con sus módulos |
| T03 Laboratorio aislado | Completada como viabilidad H0 | Tres familias y variante DeepSeek; límites, DOM/red y recuperación |
| T04 Extracción/recuperación | Completada como viabilidad H0 | PDF/PPTX/notas/imágenes, PDF escaneado, BM25 y evaluación sintética/live |
| T05 Sistema visual | Completada | Ilustraciones libres, escritorio/móvil y axe en recorrido principal |
| T06 Identidad | Completada | Firebase real/emulado; dominio, verificación y piloto; reglas deny-all |
| T07 Materias | Completada | Periodos, temas, edición/revisión, archivo y restauración; datos aislados |
| T08 Inicio/agenda | Completada | Inicio sin chat, pendientes, exámenes, horarios y fechas excluidas; persistencia |

## Recursos externos

Se usó la clave DeepSeek con material sintético y sin imprimirla. Con autorización expresa se creó Firestore `(default)` en `us-central1` dentro de `educloud-1d5de` y se aplicaron reglas cliente restrictivas. Auth y Firestore reales pasaron el smoke con una cuenta sintética eliminada después. Cloud Run no se desplegó. El [informe de cierre](cierre-h0-h1.md) detalla alcance, incidencias resueltas y límites.

## Criterio académico

El informe distingue diseño propuesto, ejecución local y validación en servicios reales. Los beneficios educativos son hipótesis evaluables; no se atribuyen resultados a estudiantes ni se promete mejora de calificaciones sin estudio.

## Verificación del corte actual

Se continúa con un solo agente por decisión del usuario. Hay pruebas de reglas, extracción, transacciones, Firebase/Firestore emulados, navegador y servicios reales. Se comprueban tipos, lint, contratos generados y builds. La evidencia y límites están en el informe de cierre. Asyncio necesita salir del sandbox de herramientas de Windows; fuera de él termina normalmente.

El informe se recompiló con pdfLaTeX y se revisaron sus páginas renderizadas. No quedan errores, referencias indefinidas ni desbordamientos en el log. Los módulos extensos se conservan como material editable, fuera del PDF resumido.

## Registro de seguridad del corte inicial (histórico)

Los campos siguientes describen únicamente el corte inicial de contratos, anterior al cierre. La comprobación vigente es la del [cierre H0/H1](cierre-h0-h1.md).

Security check:
- Data touched: modelos y fixtures sintéticos; no datos reales de estudiantes.
- Auth required: solo health y rutas iniciales 501; no hay operaciones privadas activas todavía.
- Authorization enforced at: aislamiento por actor en adaptador de prueba; autenticación real pendiente de T06.
- Secrets: ninguno leído, creado ni incluido en documentos o código.
- Input validation: DTOs rechazan campos extra, validan fechas y nombres públicos; protocolo verifica estructura básica.
- Output rendering: tipos y JSON; todavía no se ejecuta HTML/JavaScript generado.
- Logs/errors: errores iniciales sin cuerpos privados; trazabilidad real por request pendiente.
- DB/storage rules: no hay persistencia cloud implementada en este corte.
- Dependencies: Pydantic ya usado por FastAPI se declara directamente; lockfiles actualizados, sin instalar nuevo proveedor.
- Rate limiting / abuse controls: no se habilitan operaciones IA ni cargas públicas; controles de producción pendientes.
- Web risks: pruebas locales, sin sesiones propias ni fetch servidor de URLs del usuario; runtime y headers de producción pendientes.
- Prototype/security debt: los adaptadores en memoria son dobles de test, no auth ni persistencia de producción; H0/H1 siguen abiertos.
