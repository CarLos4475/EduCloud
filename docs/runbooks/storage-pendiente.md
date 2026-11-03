# Storage: paso pendiente de habilitación

El bucket aún no existe. La facturación no se habilita desde scripts del proyecto. El posible prepago lo decide y realiza el titular en Google Cloud; no compartir datos de pago ni claves en el chat.

Cuando el proyecto `educloud-513604` tenga facturación activa, el bucket autorizado debe crearse como STANDARD, privado, en `us-central1`, con acceso uniforme y prevención de acceso público. Antes de asignarlo a la aplicación, comprobar escritura/lectura/borrado de un objeto sintético por generación e IAM del backend. No cambiar acceso público ni desplegar Hosting para hacer esa prueba.

Variables de backend: `CAMPUS_STORAGE_PROJECT=educloud-513604`, `CAMPUS_STORAGE_BUCKET=<nombre>`. En ejecución desplegada se requiere `CAMPUS_UPLOAD_SIGNING_KEY` desde Secret Manager e identidad administrada. La web nunca recibe estas variables.

El servicio Firebase/Firestore permanece en `educloud-1d5de`. Crear el bucket en el proyecto de cómputo no mueve ni duplica las cuentas o los datos académicos existentes.
