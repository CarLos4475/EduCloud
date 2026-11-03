# Cierre de H0 y H1

Fecha: 2 de noviembre de 2026, horario de Ciudad de México. Ejecución directa, sin nuevas delegaciones.

## Comprobaciones del cierre

- `pnpm check`: TypeScript de cuatro paquetes, Ruff, mypy (22 archivos) y contratos generados sin diferencias.
- `pnpm test:unit`: 19 pruebas Python y 7 Vitest aprobadas.
- `pnpm test:integration`: una prueba de integración con identidades Firebase y Firestore emulados; comprueba propietario, revisiones, dominio y rechazo del acceso cliente directo.
- `pnpm test:e2e`: seis recorridos Playwright, incluida comprobación axe sin hallazgos en el inicio examinado.
- Builds de web y renderer completados. Auditoría de dependencias de producción sin vulnerabilidades conocidas en este corte.
- Informe: dos pasadas de pdfLaTeX, ocho páginas A4; sin desbordamientos ni referencias indefinidas; revisión visual de la página de cierre actualizada.
- Preflight remoto de solo lectura: no quedaron cuentas sintéticas del smoke.
- `pnpm dev:cloud`: arranque real comprobado, pantalla de acceso visible, `/health` 200 y ruta privada sin token 401; no se creó ninguna cuenta durante esta comprobación.

## Alcance entregado

| Tarea               | Evidencia de cierre                                                                                                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T01 · Base          | pnpm/uv con lockfiles; API/web/renderer; arranque y limpieza de puertos comprobados durante reinicio; scripts de emulador y modo cloud local                                             |
| T02 · Contratos     | DTOs de entrada/salida H1, Page, errores, SourceRef, paquete interactivo; OpenAPI y TypeScript generados; drift check; puertos de infraestructura y dobles aislados                      |
| T03 · Laboratorio   | Worker QuickJS/WASM, controles acotados, HTML/CSS sanitizados, aislamiento de origen; parábola, movimiento, ordenamiento y variante Ohm de DeepSeek; pruebas de red/DOM y bucle infinito |
| T04 · Materiales    | PDF textual y escaneado, PPTX/notas, texto e imágenes; localizadores físicos; transcripción bajo revisión; BM25 filtrado; corpus sintético y proveedor live                              |
| T05 · Diseño        | Azul/oro, Alfa Slab One/Archivo Narrow/DM Mono/Caveat Brush locales; 12 ilustraciones SVG genéricas propias; escritorio/móvil; axe sin hallazgos en el recorrido revisado                |
| T06 · Identidad     | Firebase Auth real/emulado; token verificado, dominio exacto institucional, correo verificado en real y lista de piloto; reglas Firestore cliente deny-all                               |
| T07 · Organización  | Periodos, materias libres, temas/prerrequisitos; edición con revisión, archivo/restauración, referencias de propietario y detección de ciclos; Firestore transaccional                   |
| T08 · Inicio/agenda | Inicio sin chat abierto, pendientes, exámenes, día completo/fecha con zona, horario semanal y excepciones por fecha; recarga persistente                                                 |

Los contratos detallados de módulos posteriores se ampliarán con sus consumidores. No se construyeron por adelantado los servicios de H2–H7. El borrado destructivo completo de materias sigue siendo T24: en H1 se archivan/restauran; el endpoint de borrado devuelve 501 explícito, como se definió en el plan.

## Servicios reales y operaciones externas

- Autorizado por el usuario: habilitar Firestore y crear `(default)` en `us-central1`, proyecto Firebase `educloud-1d5de`. La respuesta del servicio indicó `freeTier: true`; no se promete ausencia de cargos por consumo futuro.
- App web Firebase registrada como “EduCloud Web”. Reglas Firestore compiladas y publicadas: cliente sin lectura/escritura; acceso mediante API y autorización por propietario.
- Cloud Run no se desplegó. El proyecto `educloud-513604` se reserva para esa etapa posterior.
- Smoke real: Firebase ID token + API + Firestore, creación 201, lectura 200, token inválido 401, correo externo 403 y correo sin verificar 403.
- Se creó únicamente una cuenta sintética por intento y documentos bajo su UID. Un intento inicial falló por proyecto de cuota ausente y dejó un fixture; el auto-review rechazó repetir mutaciones. Se comprobó acceso de solo lectura, se identificó y eliminó ese fixture concreto, y después se autorizó repetir el smoke. El smoke final limpió sus datos y su cuenta. No se modificó la cuenta real del usuario ni se enviaron correos desde el script.

## Evidencia de IA y límites

`scripts/ai-eval.mjs` genera cuatro PDFs sintéticos y 40 consultas (20 conceptos, dos redacciones), calcula recuperación top-8 y ejecuta cinco llamadas live: una transcripción y cuatro respuestas con fuentes. Resultado: 40/40 consultas recuperaron la página esperada; la imagen f(x)=x², f'(x)=2x se transcribió correctamente. Las cuatro respuestas conservaron las fórmulas del material y citaron bloques existentes.

Este corpus no mide calidad académica general: es pequeño y de vocabulario directo. No se afirma evaluación humana con estudiantes, precisión en manuscritos arbitrarios ni una prueba ciega de razonamiento universitario. H7 incluye evaluación más amplia.

La generación interactiva tuvo tres intentos: se rechazaron truncamiento y un tipo incorrecto de `instructions`; la salida válida se ejecutó con el mismo aislamiento, y el navegador verificó V=2R al cambiar R. No se relajaron validadores ni se ejecutó código generado en Python o en el contexto principal del navegador.

## Decisiones y límites prácticos

- La web principal usa emuladores con `pnpm dev`; `pnpm dev:cloud` usa Firebase y Firestore reales con credenciales temporales del operador en memoria. Esas credenciales no son el mecanismo de despliegue: Cloud Run usará identidad administrada/ADC.
- Se permite únicamente `pcpuma.acatlan.unam.mx`. En real se exige verificación de correo y cuenta habilitada para piloto. El filtro protege la aplicación y los datos; no equivale a un bloqueo de creación de identidades a nivel de Identity Platform.
- Los documentos se procesan con scripts de viabilidad; la carga, los jobs y el tutor completo del alumno se integran en H2.
- Las estampillas definitivas siguen pendientes de decisión artística; no se inventó un catálogo aprobado.
- La revisión fue del autor con pruebas y verificaciones de integración; no se usó un revisor nuevo por la preferencia de costo del usuario.

## Seguridad comprobada en este alcance

Security check:

- Data touched: fixtures sintéticos y metadatos de proyecto; contenido real del estudiante no utilizado en pruebas.
- Auth required: tokens Firebase en todos los endpoints privados; sin token/forjado se rechaza con 401.
- Authorization enforced at: current_actor aplica dominio, verificación y piloto; servicios/repository scopean por UID y verifican relaciones antes de lectura/escritura.
- Secrets: DeepSeek en .env ignorado; OAuth del operador solo en memoria del proceso backend; no variables VITE ni logs. Configuración Firebase web es pública.
- Input validation: Pydantic extra-forbid; tipos, fechas, revisión optimista, pertenencia, ciclos, tamaños de documentos y mensajes.
- Output rendering: JSX para textos; DOMPurify/AST CSS en renderer; QuickJS/WASM en Worker sin objetos host expuestos; comandos por JSON y cuotas.
- Logs/errors: sin cuerpos privados, credenciales o cabeceras; errores API con requestId y campos seguros.
- DB/storage rules: Firestore cliente deny-all desplegado; Storage deny-all preparado para etapa de archivos, sin bucket nuevo creado aquí.
- Dependencies: lockfiles actualizados; gRPC transitivo corregido; auditoría de producción sin vulnerabilidades conocidas; no se habilitaron scripts de instalación ignorados.
- Rate limiting / abuse controls: piloto cerrado, límite de registros por colección, validación de tamaño y cuotas del renderer; endpoints de trabajos/IA públicos aún no están habilitados.
- Web risks: CORS por orígenes locales exactos, sin cookies propias ni proxy de URLs; iframe/CSP acotados; CSP/orígenes de producción se configurarán al desplegar.
- Prototype/security debt: emuladores solo para demo project/local; memoria solo en dobles de test. El laboratorio no es garantía absoluta frente a fallos desconocidos de navegador/WASM. No se declara la aplicación lista para publicación pública.
