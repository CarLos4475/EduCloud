# ADR 0005 · H2: trabajos y archivos privados durante desarrollo

Estado: adoptada para piloto local, 3 de noviembre de 2026.

H2 necesita persistencia independiente del navegador antes del despliegue. Firestore conserva trabajos, outbox, leases, versiones, conversaciones y consumo; el worker es un proceso separado. En local consulta trabajos pendientes; Cloud Tasks y el worker HTTP con identidad OIDC quedan como adaptadores para H6. Los servicios síncronos se ejecutan en endpoints de threadpool; upload y SSE delegan su I/O bloqueante al threadpool.

Las cargas usan un ticket firmado de diez minutos y cabecera `X-Upload-Token`, además del bearer Firebase. La API limita bytes y valida el objeto antes de finalizarlo; el estudiante no recibe una URL de Storage ni puede elegir una clave. Esto sustituye la carga directa firmada de GCS del diseño inicial y evita publicar tickets en URLs de acceso.

Sin bucket/facturación activados, `.data/objects` es el almacén privado local. Ambos orígenes Vite deniegan esa carpeta, y Cloud Run rechaza el arranque sin GCS configurado. El adaptador GCS usa generaciones inmutables y exige prevención de acceso público y acceso uniforme. No se afirma que ese adaptador haya pasado una prueba real con bucket.

Cada versión conserva texto e índice léxico JSON comprimido. Los checkpoints son por página. Una corrección publica versión nueva y reconstrucción de índice; las citas históricas permanecen resolubles. Los fallos de página se muestran como cobertura parcial. En el piloto se transcriben con IA hasta cuatro páginas escaneadas por archivo; el resto requiere completar/revisar texto.

DeepSeek transmite JSON al worker; sus fragmentos no se muestran como respuesta académica hasta validar formato y citas. SSE entrega estados y texto final persistido, no una animación que simule tokens. El cliente recupera el turno tras desconexión. No se promete replay de cada token ni facturación exactamente una vez. Los timeouts conservan reserva y requieren consentimiento para un posible consumo adicional al reintentar.

El índice de grupo `jobs.status` se declaró y habilitó en Firebase. Texto, preguntas, resúmenes y payload de trabajos no necesitan indexación automática. La verificación real de Firestore utiliza un UID sintético único y elimina exclusivamente sus documentos; las cuentas reales del usuario no se modifican.
