# Desarrollo de H2

La aplicación sigue local. No ejecutar despliegue de Hosting o Cloud Run durante este corte.

## Uso normal

Con dependencias instaladas y `.env` existente, abrir `pnpm emulators` en una terminal y `pnpm dev` en otra. `DEEPSEEK_API_KEY` habilita el proveedor real; sin clave, el tutor informa que el proveedor no está configurado. Los textos PDF/PPTX y notas pueden extraerse localmente; las imágenes quedan pendientes de revisión si no hay proveedor de visión.

`pnpm dev:cloud` usa Firebase/Firestore reales con la sesión temporal del operador; los archivos siguen locales mientras no se configure bucket. Reiniciar cuando expire esa sesión. En Windows, reiniciar `pnpm dev` tras modificar Python; la recarga de Vite continúa activa.

## Pruebas reproducibles sin consumo de IA

Mantener emuladores y arrancar otra terminal así, sin sobrescribir `.env`:

```powershell
$env:CAMPUS_ENV_PRELOADED='1'
$env:CAMPUS_ENV='local'
$env:GOOGLE_CLOUD_PROJECT='demo-campus'
$env:CAMPUS_AI_PROVIDER='test'
$env:VITE_USE_EMULATORS='true'
$env:VITE_FIREBASE_PROJECT_ID='demo-campus'
pnpm dev
```

Luego ejecutar `pnpm test:e2e`. El proveedor de prueba es explícito y solo se admite en local con emuladores; nunca es fallback de DeepSeek. Las respuestas lo identifican como prueba. No ejecutar este recorrido contra Auth real.

Verificación: `pnpm check`, `pnpm test:unit`, `pnpm test:integration` y builds de web/renderer. La integración necesita emuladores. Las pruebas de navegador también necesitan los cuatro servicios de desarrollo.

## Verificaciones reales opt-in

- `pnpm eval:ai:h2`: dos llamadas DeepSeek con PDF e imagen sintéticos; guarda resultados detallados en `.superpowers`, ignorado por Git.
- `pnpm test:cloud:h2 --preflight`: solo consulta disponibilidad del índice Firestore. Código 2 significa índice todavía en construcción.
- `pnpm test:cloud:h2`: prueba Firestore con UID sintético sin cuenta Auth; valida outbox, consulta del worker, materiales y recuperación con cliente nuevo. Elimina sus documentos al terminar. Usa proveedor de prueba explícito y archivos locales; no demuestra GCS ni IA real.

## Operación y límites del piloto

El worker procesa trabajos sin depender de una pestaña abierta. Para reanudar tras reinicio basta arrancarlo con `pnpm dev`. Los leases duran cinco minutos. Un trabajo externo interrumpido no se repite automáticamente; la interfaz requiere aceptar posible consumo adicional si no hubo uso confirmado. Cancelar descarta resultados tardíos, pero no garantiza detener un cargo iniciado.

Cuando no hay trabajos, el poller local espera cinco segundos entre consultas para reducir lecturas de Firestore. Cloud Tasks sustituirá ese sondeo en el despliegue de H6.

Defaults: dos trabajos IA activos por cuenta, veinte preguntas/minuto, cien mil tokens diarios reservados/observados, dos tickets simultáneos, veinte MiB por documento, diez por imagen, doscientas páginas y quinientos MiB de originales por cuenta. El presupuesto se configura en `CAMPUS_DAILY_TOKEN_BUDGET`; una reserva se ajusta al consumo observado al terminar. No es un sistema de facturación comercial.

`needs_review` nunca entra silenciosamente a recuperación. Confirmar una página crea versión nueva; los fallos parciales pueden corregirse manualmente. Las presentaciones con imágenes/gráficas requieren revisión; no se promete reconstrucción visual completa de diapositivas. El visor ofrece texto con localizador y descarga del original; la vista PDF depende del soporte del navegador.

## Bucket e infraestructura posteriores

El usuario autorizó crear bucket, pero ambos proyectos tenían facturación desactivada. No se activó facturación ni se hizo prepago. Cuando esté disponible, crear un bucket STANDARD privado en `us-central1` del proyecto `educloud-513604`, con acceso uniforme y prevención de acceso público. Configurar `CAMPUS_STORAGE_BUCKET` y `CAMPUS_STORAGE_PROJECT`; nunca una variable VITE.

Antes de publicación pública, H6 debe aportar identidad administrada, IAM de mínimo privilegio, colas/reintentos y reconciliación programada, límites del contenedor/parsers, cuota de derivados y limpieza de objetos sin referencias. `CAMPUS_UPLOAD_SIGNING_KEY` debe ser persistente y provenir de Secret Manager; el archivo local de clave permanece ignorado. No usar la credencial temporal del operador como identidad desplegada.
