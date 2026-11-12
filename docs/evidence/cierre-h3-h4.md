# Cierre H3 y H4 · Recursos, práctica y progreso (solo local)

Fecha: 11 de noviembre de 2026. Todo se probó en local con DeepSeek real y emuladores de Auth/Firestore; **no hay pruebas contra la nube** (la facturación sigue pendiente).

## Alcance entregado

- **Recursos con IA (T14, T16):** resumen, conceptos, tarjetas, cuestionario y experimento interactivo. Cada recurso tiene versiones inmutables, citas literales verificadas, un reintento acotado de corrección y esqueletos de espera. Si una versión nueva falla, la última válida sigue vigente.
- **Renderer (T15 local):** fórmulas con KaTeX, altura automática y avance guardado del experimento. Mantiene el aislamiento: el servidor nunca ejecuta el código del recurso.
- **Tutor → recursos:** desde una respuesta se pueden crear tarjetas, cuestionario o resumen.
- **Práctica y progreso (T17 a T19):** los intentos de cuestionario se califican en el servidor; repaso de tarjetas (sabía / repasar); progreso por materia con recomendaciones.
- **Pasaporte mínimo (T21, T23 mínimo):** 8 estampillas calculadas con actividad real. Amigos, comparación y retos quedan fuera.
- **Borrado (T24):** eliminar materia en cascada (datos y archivos) y "borrar todo" con cierre de cuenta. Retención: los datos viven mientras exista la cuenta y se borran al momento al eliminarlos.
- **Textos:** simples y sin tecnicismos ni nombres de proveedores en la interfaz.

## Verificación

| Comprobación | Resultado |
|---|---|
| Pruebas de backend | 72 aprobadas |
| Pruebas unitarias del front y paquetes | aprobadas |
| `pnpm check` (tipos, Ruff, mypy, contratos) | sin errores |
| Recorridos e2e (`tests/e2e`) | recursos, práctica, borrado, accesibilidad (axe, escritorio y móvil), H2, académico y seguridad del renderer |
| Evaluación `pnpm eval:ai:h3` | ver abajo |

### Evaluación propia del tutor y los recursos

Corpus sintético de dos apuntes cortos (circuitos y cálculo); 16 casos en total. Resultado: el tutor respondió y citó bien las 4 preguntas con apuntes; reconoció el límite en las 2 preguntas que los apuntes no cubren, sin inventar citas; los 10 recursos (5 tipos × 2 apuntes) salieron válidos y con citas, y 1 necesitó una corrección. Es una medición pequeña de comportamiento, no una certificación académica. El informe completo se genera en `.superpowers/sdd/2026-11-02-plataforma-estudio/eval-h3/report.json` (ignorado por Git).

## Problemas reales encontrados al probar

- Barras invertidas de LaTeX en el JSON del modelo: `\frac` se corrompía en silencio y otras rompían la lectura. Ahora se reparan.
- Delimitadores `\( \)` y `\[ \]` aparecían como texto crudo; se normalizan.
- Con 7000 tokens de salida, el modelo a veces agotaba el presupuesto "pensando" y no terminaba el experimento. Se subieron los límites y una respuesta cortada se reintenta una vez, solo si su costo es conocido.
- Tickets de subida huérfanos al borrar una materia, lista de apuntes que no se refrescaba y un texto sin contraste suficiente.

## Límites

- Los adaptadores de GCS y Cloud Tasks siguen sin probarse contra servicios reales; el despliegue (T25 a T28) está pausado hasta activar facturación.
- El cuestionario muestra la respuesta correcta al cliente: es práctica libre, no un examen.
- Las estampillas y el progreso se calculan al consultarlos; no hay historial de rachas.
- La IA puede fallar o cortarse; la interfaz ofrece reintentar sin perder la versión anterior.
