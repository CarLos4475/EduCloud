# H2 · Materiales y tutor con fuentes

3 de noviembre de 2026. Fase 3, T09–T13. Implementación directa; sin nuevos subagentes ni despliegue público.

## Resultado

El alumno puede subir PDF, PPTX e imágenes o escribir notas en su materia, seguir el procesamiento y corregir una transcripción. El tutor conserva conversaciones por materia, utiliza fuentes seleccionadas, muestra citas verificadas y permite elegir personalidad y tipo de ayuda por separado. Cerrar el panel o recargar no elimina el trabajo.

| Tarea | Entrega comprobada                                                                                                                                             |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T09   | Job/outbox transaccionales, idempotencia, lease, cancelación/reintento y recuperación; ticket firmado, límite de bytes, hash/generación y almacén privado      |
| T10   | Extracción por página, checkpoints, estados de revisión/error parcial, versiones inmutables, asociación confirmada a temas y descarga autorizada del original  |
| T11   | BM25 con índice JSON comprimido por versión, caché acotada, filtros de propietario/materia/fuentes, citas históricas y reconstrucción de índice                |
| T12   | DeepSeek estructurado y streaming interno, contexto acotado, consentimiento para conocimiento general, cuotas y consumo observado/desconocido; SSE recuperable |
| T13   | Biblioteca y tutor adaptables, historial, fuentes, personalidades, ayuda completa/pistas, citas, fórmulas/Markdown seguros y lectura del navegador             |

## Evidencia

- Backend: **41 pruebas unitarias y 2 de integración** aprobadas con Auth/Firestore emulados. Incluyen formatos, corrupción, fallo parcial, citas ajenas/inventadas, cuotas al cambiar de día, doble liquidación, cancelación, stream interrumpido, JSON excesivo y rechazo del modo emulado en Cloud Run.
- Frontend: **8 pruebas Vitest** y **9 recorridos Playwright** aprobados. El recorrido del tutor pasó axe A/AA; se comprobó también revisión de imagen en móvil. Esto no constituye certificación completa de accesibilidad.
- Tipos, Ruff, mypy sobre 39 archivos y contratos generados: aprobados. Builds de web/renderer completados. El tutor y KaTeX se cargan al abrir el panel; bundle inicial web: aproximadamente 112 kB gzip.
- DeepSeek real: PDF listo, imagen en `needs_review` con los tres valores esperados y respuesta de solución completa con cita a página 1. Consumo observado: **459 tokens de visión y 844 de tutoría**. Material sintético pequeño: no demuestra precisión académica general ni manuscritos arbitrarios.
- Firestore real (`educloud-1d5de`): outbox persistido, consulta de pendientes, material listo y turno/cita recuperados con cliente nuevo. Cada smoke eliminó sus **14 documentos sintéticos**. No creó cuentas Auth ni modificó la cuenta del usuario. Este smoke usó archivos locales y proveedor de prueba explícito; la IA real se verificó por separado.
- Índice de grupo `jobs.status` habilitado y confirmado `READY`; la prueba final encontró el trabajo esperado. Campos de texto/payload excluidos de indexación automática. Reglas cliente deny-all conservadas.
- Auditoría de producción npm: sin vulnerabilidades conocidas. Se corrigió también KaTeX transitivo a 0.19.1, evitando la versión deprecada 0.18.11 y el advisory GHSA-238p-pmpm-9mq7.

Se detectó y corrigió que Vite podía servir `.data` mediante `@fs`; la prueba con un archivo sintético falló antes del ajuste y pasó en ambos orígenes después. Los renders nunca muestran HTML activo ni habilitan navegación de enlaces generados.

## Alcance y pendientes de infraestructura

Los archivos permanecen en almacenamiento local privado. GCS y Cloud Tasks están implementados como adaptadores, pero **no se probaron con bucket/cola reales**. El usuario autorizó crear bucket; la facturación desactivada y el posible prepago siguen bajo su control. No se vinculó facturación, no se creó bucket y no se desplegó la web. H6 debe aportar infraestructura, IAM, límites de contenedor, reconciliación programada y limpieza/cuotas de derivados.

El piloto transcribe con IA hasta cuatro páginas escaneadas por archivo; el resto requiere revisión/completar texto. Las figuras de presentaciones se señalan para revisión; no se afirma conversión visual completa de PPTX. La vista del PDF depende del navegador; texto y descarga del original conservan acceso autorizado. No hay garantía de exactamente un cargo del proveedor tras un timeout.

La generación de resúmenes, tarjetas, quizzes y recursos dentro del chat corresponde a H3. El laboratorio H0 sigue disponible como prueba independiente. El informe LaTeX de nueve páginas conserva su alcance H0/H1; este registro documenta H2 sin alargarlo.

## Revisión de seguridad

Security check:

- Data touched: materiales, versiones, conversaciones y consumo del propietario; pruebas con fixtures sintéticos.
- Auth required: Firebase bearer verificado en endpoints privados; worker HTTP requiere identidad Google y cuenta invocadora configurada.
- Authorization enforced at: actor del servidor y claves por UID; referencias de materia, material, tema, turno y cita verificadas antes del acceso.
- Secrets: DeepSeek y OAuth solo backend; clave de tickets local en `.data` ignorada o configuración de Secret Manager para despliegue.
- Input validation: Pydantic extra-forbid, tickets caducables, tamaño real/hash/formato, JSON acotado, generación inmutable y revisión optimista.
- Output rendering: JSX, Markdown sin HTML activo/imágenes/enlaces navegables, KaTeX actualizado con trust=false y límites de expansión.
- Logs/errors: sin documentos, prompts, tokens ni cabeceras; errores estables y requestId. Los reportes detallados de IA contienen solo fixtures y quedan ignorados.
- DB/storage rules: Firestore cliente deny-all; originales detrás de API; ambos Vite deniegan datos/secretos locales; GCS exige prevención pública y acceso uniforme.
- Dependencies: lockfiles actualizados, dependencias oficiales Google Cloud y bibliotecas de render; auditoría npm de producción y pip-audit sin vulnerabilidades conocidas. El paquete local editable se revisa como código, no mediante PyPI.
- Rate limiting / abuse controls: piloto cerrado, veinte preguntas/minuto, dos IA activas, presupuesto diario y cuotas de tickets/archivos; desconocimiento de consumo conserva reserva.
- Web risks: CORS por origen exacto, bearer fuera de URL, firma en cabecera, endpoint proveedor fijo, worker sin CORS público y fuente en diálogo con foco nativo.
- Prototype/security debt: originales limitados; contabilidad de derivados/objetos huérfanos y aislamiento fuerte de parsers pendientes de H6 antes de publicación. No se declara listo para tráfico público.
