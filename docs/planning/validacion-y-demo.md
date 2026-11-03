# Validación, criterios de salida y demostración

Este documento prescribe pruebas futuras. Ningún caso figura como ejecutado por haber escrito el plan.

## 1. Estrategia

Validar primero reglas y límites que pueden invalidar la arquitectura; después recorridos completos. Usar tests unitarios para reglas con resultados claros, integración para almacenamiento/cola/autorización y navegador real para experiencia y aislamiento. No probar cada clase CSS ni reproducir la implementación en asserts.

Proveedor falso determinista para CI. DeepSeek real en una suite explícita con presupuesto, fuentes sintéticas/licenciadas y credenciales del entorno. Un mock aprobado no demuestra precisión del modelo. Emuladores no demuestran IAM ni comportamiento completo de servicios cloud: staging tiene su propia puerta.

## 2. Fixtures y evaluación de IA

Corpus versionado en `tests/fixtures/education/`, producido para el proyecto o con licencia compatible. No usar datos personales reales. Incluir:

1. PDF textual de cálculo, con ejemplo de derivada y referencias a páginas conocidas.
2. PDF escaneado de física con unidades, gráfico y una fórmula fotografiada.
3. PPTX de álgebra lineal con matrices en texto e imagen y notas de diapositiva.
4. Markdown de programación con pseudocódigo y una definición propia del curso.
5. Imagen manuscrita deliberadamente ambigua que deba pedir revisión.
6. Material con una errata y dos fuentes que usan notaciones diferentes.
7. Documento con instrucciones maliciosas para ignorar políticas o extraer datos.
8. Archivos truncados, extensión falsa, PDF cifrado, imagen con dimensiones excesivas y contenedor PPTX comprimido abusivo.

Matriz de 40 preguntas con respuesta/fuentes revisadas por una persona: 20 localización directa, 8 multi-página, 4 notación/fórmulas, 4 ausencia de respuesta y 4 contradicción/inyección. Se divide en 20 de desarrollo y 20 reservadas para cierre; no ajustar prompts sobre todas y reportarlas como evaluación independiente.

Umbrales propuestos para piloto, revisables solo con justificación registrada:

| Dimensión | Puerta |
|---|---|
| Recuperación | Al menos 90% de preguntas respondibles incluye bloque esperado en top-8; informar por tipo de archivo |
| Citas | 100% de IDs/localizadores existentes y autorizados; ≥90% de citas auditadas respaldan la afirmación asociada |
| Fidelidad | ≥90% de respuestas respondibles respetan método/notación de las fuentes; cero errores matemáticos graves en los cuatro ejemplos de demo |
| Incertidumbre | Los cuatro casos sin respuesta no inventan fuente; ambiguo manuscrito llega a revisión |
| Aislamiento | Cero referencias a documentos de otra cuenta en corpus A/B/C |
| Estructura | ≥95% de salidas válidas sin reparación; todas las restantes reparadas dentro del límite o rechazadas explícitamente |
| Interactivos | Los tres recursos de T03 tienen comportamiento comprobado y el modelo genera variantes utilizables mediante el SDK |

No presentar 40 preguntas como validación científica general de un tutor universitario. Conservar resultados individuales, modelo, versión de prompt, fecha y costo; repetir solo casos afectados por cambios y una muestra de regresión.

## 3. Matriz funcional y de autorización

| ID | Recorrido / condición | Resultado verificable | Tareas |
|---|---|---|---|
| V01 | Entrar, saltar tutorial y crear materia propia | Materia persistente con ilustración elegida; chat cerrado | T06–T08, T20 |
| V02 | Renombrar materia/cambiar dibujo | No pierde material, progreso ni historial | T07 |
| V03 | Agenda con zona horaria/día completo | Fechas consistentes al recargar; bloque semanal correcto | T08 |
| V04 | Subir PDF/PPTX/imagen, cerrar pestaña | Procesa; al regresar estado real y citas navegables | T09–T11 |
| V05 | Corregir transcripción | Nueva versión; resultados anteriores marcados, índice renovado | T10–T11 |
| V06 | Preguntar usando fuentes concretas | Respeta selección; cita visible abre página autorizada | T12–T13 |
| V07 | Pedir solución completa con tutor retador | La entrega; no impone pistas obligatorias | T13 |
| V08 | Material insuficiente | Explica límite y solicita ampliar; aceptación solo afecta alcance indicado | T12–T13 |
| V09 | Desconectar durante respuesta | Turno continúa; recuperar no duplica mensajes ni cobro deliberado | T09, T12 |
| V10 | Recurso generado, guardar, modificar, reabrir | Versiones separadas; estado ligado a versión; anterior disponible | T14–T16 |
| V11 | Bucle infinito o mensaje malicioso de recurso | Interrumpir VM; no acceder a red/datos, no bloquear aplicación | T03, T15, T28 |
| V12 | Resolver quiz, pedir pista/revelar | Resultado del servidor y asistencia registrados; submit duplicado estable | T17–T18 |
| V13 | Tarjetas/repaso espaciado | Autoevaluación separada de acierto comprobado; fecha de revisión estable | T18–T19 |
| V14 | Dos pestañas activas/inactividad | No duplica minutos; pausa y muestra estimación | T19 |
| V15 | Sin evidencia / con resultados mixtos | No inventa dominio; recomendación explica evidencia | T19 |
| V16 | Amistad aceptada y consentimiento | Solo proyección elegida visible; tercero no accede | T22–T23 |
| V17 | Compartir y revocar recurso | Snapshot visible solo al receptor autorizado; revocación bloquea nuevo acceso | T22 |
| V18 | Evento de logro repetido | Un solo premio; fixture demo no aparece en catálogo real | T21 |
| V19 | Borrar fuente/materia/cuenta | Revoca acceso primero; borra derivados y trabajos no resucitan contenido | T24 |
| V20 | Cuota/proveedor caído | Mensaje útil, trabajo recuperable cuando corresponda, límite efectivo | T12, T26, T28 |
| V21 | Cuenta interna A intenta IDs de B | 404 en todas las lecturas/mutaciones privadas; no filtra metadatos | T06, T28 |
| V22 | Visitante / cuenta no habilitada | 401/403 sin invocar modelo ni consumir trabajos | T06, T27 |
| V23 | Reto privado con dos participantes | Solo aceptados contribuyen; fechas y objetivo correctos | T22–T23 |
| V24 | Acceso desde móvil y teclado | Rutas fundamentales sin callejones ni controles inaccesibles | T05, T29 |

## 4. Pruebas de seguridad obligatorias

- IDOR A/B/C: sujetos, archivos, páginas, jobs, chats, versiones, estados, intentos, progreso, pasaporte y shares; autorizaciones tanto lectura como escritura.
- URLs de Storage: objeto/ruta fijados por servidor; caducidad; mismatch de tamaño/hash; archivo ajeno; objeto sustituido después de ticket. No abrir buckets ni usar nombres de archivo para rutas.
- Cola: tarea duplicada, outbox sin despacho, lease vencido, error permanente, cancelación mientras llega resultado, invocación anónima/identidad incorrecta al worker.
- Prompt injection: no expandir fuentes, revelar secretos, conceder permisos, emitir calificaciones o ejecutar herramientas por instrucciones de documentos.
- XSS: Markdown del tutor y nombres de materia sanitizados/escapados; scripts, eventos, HTML, enlaces con protocolos peligrosos y fórmulas maliciosas.
- Recursos: acceso a window/document, fetch/WebSocket/import, navegación, atributos URL, CSS url/import, prototipos, mensajes falsificados/repetidos, paquetes grandes, bucle infinito, puente de operaciones abusivo y memoria excesiva. Capturar solicitudes de red: ninguna causada por código generado fuera de activos confiables iniciales.
- SDK: ningún retorno contiene objetos/funciones del host; cada operación valida scope y esquema; no aprobar calificaciones desde el iframe.
- Grading: frontend no recibe soluciones antes de reveal/submit; editar score, ownerId, assistance o difficulty no cambia reglas del servidor.
- Web: CORS por origen exacto, redirects internos allowlisted, ninguna descarga servidor de URLs arbitrarias (SSRF), CSP aplicada y origen renderer distinto. Validar Firebase bearer, dominios de Auth y que tokens no aparezcan en URLs/logs.
- Privacidad social: invitación inválida/caducada/usada; amistad bloqueada; comparte solo snapshot revisado; sin búsqueda por correo; cambiar settings afecta lecturas posteriores.
- Dependencias: versiones bloqueadas, licencia de parsers/fuentes/ilustraciones, auditoría de vulnerabilidades relevantes, sin secretos en repositorio/builds.

Una falla de aislamiento, exposición de secretos, bypass de permisos, ejecución nativa de JS generado o resultado académico forjable bloquea la integración; no se acepta como deuda del prototipo.

## 5. Experiencia, accesibilidad y rendimiento

Validar en Chromium y Firefox; un smoke de WebKit si el entorno lo soporta, registrando cualquier carencia. Viewports de referencia: 1440×900, 1920×1080, 768×1024 y 390×844. No adaptar una slide fija escalada.

Capturas: inicio vacío y con datos, creación de materia, documentos en revisión, tutor con cita, laboratorio en funcionamiento/error, quiz, progreso, pasaporte sin catálogo y con fixtures demo, compartir/revocar. Comparar intención del diseño, no exigir que el pixel difuso de una imagen generada sea una especificación.

Herramientas: Playwright + axe para flujos y accesibilidad automatizable; comprobación manual de foco, lectura de fórmulas, gráfica con alternativa y reduced-motion. Contraste AA para textos normales; navegación de teclado sin trampas y nombres accesibles en controles.

Presupuestos iniciales sobre entorno de prueba documentado:

- API CRUD caliente p95 < 800 ms en prueba de 5 usuarios concurrentes, sin incluir upload/IA.
- Respuesta inicial de chat (estado visible) < 1 s; primer contenido del proveedor medido por separado, objetivo p95 < 15 s en corpus breve. Si no se cumple, mostrar progreso honesto y revisar proveedor/configuración; no falsificar streaming.
- Una página o imagen produce progreso visible; ningún trabajo aparenta estar listo antes de terminar. Documentos largos reportan páginas procesadas.
- Laboratorio de referencia conserva interacción fluida; evento bloqueante se interrumpe dentro de su presupuesto más margen medido del host.
- Bundle inicial objetivo comprimido < 350 KiB sin runtime/gráficas del laboratorio; cargar estos por separado. Es un presupuesto de ingeniería propuesto, no requisito impuesto al usuario.
- Cloud cold-start se mide y registra aparte; informar memoria, CPU, región, concurrencia y tamaño de fixtures para hacer resultados comparables.

## 6. Demostración académica de 12–15 minutos

Usar datos sintéticos y dos cuentas prehabilitadas. Preparar una grabación o capturas como respaldo identificado, sin presentarlas como una demo en vivo si falla la conexión.

1. **Problema y arquitectura (2 min):** estudiante organiza y estudia su material; mostrar diagrama y servicios reales.
2. **Espacio personal (1 min):** inicio sin chat abierto, crear materia libre e ilustración, agregar examen.
3. **Procesamiento asíncrono (2 min):** subir apunte/foto, observar Job, salir y regresar, corregir un símbolo si se usa fixture ambiguo.
4. **Tutor con fuentes (2 min):** respuesta con página, cambiar personalidad/modo, mostrar límite cuando material no cubre pregunta.
5. **Laboratorio (2 min):** crear/manipular recurso, guardar y recuperar parámetros; enseñar que su versión nueva no destruye la anterior.
6. **Práctica y evidencia (2 min):** quiz con pista, resultado y progreso; explicar diferencia entre práctica asistida y dominio estimado.
7. **Social (1 min):** compartir una versión con amigo y comparar selección de pasaporte; etiquetas demo si no hay catálogo final.
8. **Cloud y recuperación (2–3 min):** mostrar cola/worker, trazas sin datos privados, aislamiento A/B, reintento de un trabajo y presupuesto/cuotas.

No es necesario provocar un incidente real ni mostrar secretos para demostrar observabilidad. Guardar evidencia redactada en `docs/evidence/`.

## 7. Entregables de cierre

- Aplicación local reproducible y despliegue de piloto autorizado.
- README con prerrequisitos y comandos verificados desde checkout limpio.
- `.env.example` sin valores reales, inventario de servicios y permisos.
- ADRs de decisiones relevantes y resultados de spikes.
- Matriz V01–V24 con evidencia, fecha y limitaciones.
- Informe de evaluación de IA y costo de la prueba.
- Capturas de referencia y reporte de accesibilidad.
- Runbooks de fallos, borrado, revocación, rollback, limpieza y restauración de datos sintéticos.
- Guion de demo y explicación de conceptos cloud con evidencia real.
- Lista explícita de pendientes editoriales, sin confundirlos con funcionalidades fallidas.

Se puede avanzar entre hitos con problemas menores documentados; el cierre de v1 requiere los casos críticos completos y decisiones visibles sobre cualquier objetivo de rendimiento no alcanzado. No se marca una prueba como aprobada porque esté escrita o porque una pantalla parezca funcionar.
