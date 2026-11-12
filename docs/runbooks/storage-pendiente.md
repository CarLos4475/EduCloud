# Storage: paso pendiente de habilitación

Estado documental al 11 de noviembre de 2026: el usuario pidió detener implementación e infraestructura hasta avisar que la facturación está activa. No se ha vuelto a consultar cloud durante esta actualización. Una notificación del usuario permitirá retomar; la mera existencia de este runbook no lo autoriza.

El bucket aún no existe. La facturación no se habilita desde scripts del proyecto. El posible prepago lo decide y realiza el titular en Google Cloud; no compartir datos de pago ni claves en el chat.

Cuando el proyecto `educloud-513604` tenga facturación activa, el bucket autorizado debe crearse como STANDARD, privado, en `us-central1`, con acceso uniforme y prevención de acceso público. Antes de asignarlo a la aplicación, comprobar escritura/lectura/borrado de un objeto sintético por generación e IAM del backend. No cambiar acceso público ni desplegar Hosting para hacer esa prueba.

Variables de backend: `CAMPUS_STORAGE_PROJECT=educloud-513604`, `CAMPUS_STORAGE_BUCKET=<nombre>`. En ejecución desplegada se requiere `CAMPUS_UPLOAD_SIGNING_KEY` desde Secret Manager e identidad administrada. La web nunca recibe estas variables.

El servicio Firebase/Firestore permanece en `educloud-1d5de`. Crear el bucket en el proyecto de cómputo no mueve ni duplica las cuentas o los datos académicos existentes.

## Acceso remoto pendiente

La petición de probar remotamente sustituyó la preferencia anterior de no desplegar; posteriormente quedó pausada por facturación. La dirección recomendada es Firebase Hosting para web y renderer en orígenes separados, Cloud Run para API/worker y GCS privado/Cloud Tasks para archivos y trabajos. Todavía faltan configuración, identidades, secretos, límites y verificación remota. Revisar los límites del [cierre H2](../evidence/cierre-h2.md) antes de exponer el piloto.

No publicar una web que dependa de localhost ni usar el origen principal para ejecutar recursos generados. Si se elige Vercel en lugar de Firebase, presentar su configuración final y pedir la confirmación de servicios, rutas y bindings solicitada por el usuario. Ver [contexto](../CONTEXTO.md).
