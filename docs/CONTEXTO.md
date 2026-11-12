# EduCloud · Contexto para retomar

Actualizado: 11 de noviembre de 2026. Este archivo resume acuerdos y estado; no sustituye los registros de pruebas ni autoriza ejecutar los pendientes.

## Propósito y experiencia

Proyecto de Cómputo en la Nube de la UNAM, FES Acatlán, Licenciatura en Matemáticas Aplicadas y Computación. Busca ayudar a universitarios de ciencias físico-matemáticas e ingeniería a organizar su estudio y aprender a partir de sus propios materiales. La diferenciación prevista combina tutor con fuentes, recursos interactivos, organización académica y progreso en un mismo espacio personalizado; los recursos integrados y el progreso completo siguen pendientes.

El alumno construye libremente sus materias con ilustraciones genéricas seleccionables. Entra a su organizador y abre el tutor cuando lo necesita. La personalidad del tutor y el modo de ayuda se eligen por separado. El material aportado tiene prioridad; ampliar con conocimiento general requiere consentimiento. La dirección visual es Block & Bold con azul y oro. El pasaporte con estampillas y comparación entre amigos está planeado; su catálogo definitivo no está decidido.

## Estado comprobado

| Hito | Estado y alcance |
|---|---|
| H0 · Base y riesgos | Cerrado: contratos iniciales y pruebas de viabilidad de extracción, recuperación y laboratorio aislado |
| H1 · Espacio académico | Cerrado: identidad, perfil, materias, periodos, temas, agenda y horario |
| H2 · Materiales y tutor | Cerrado: biblioteca privada, revisión/versiones, trabajos persistentes, recuperación, tutor con citas e historial |
| H3 · Recursos con IA | Entregado en local (11 nov 2026): resumen, conceptos, tarjetas, cuestionario y experimento interactivo con versiones, citas verificadas, esqueletos de espera, fórmulas con KaTeX, altura automática, avance guardado del experimento (T15 local) y creación desde el chat del tutor |
| H4 · Práctica y progreso | Entregado en local: intentos de cuestionario calificados en el servidor, repaso de tarjetas, progreso por materia con recomendaciones y pasaporte mínimo de 8 estampillas calculadas con actividad real. Amigos, comparación y retos quedan como trabajo futuro |
| T24 · Borrado | Entregado: eliminar materia en cascada y "borrar todo" con cierre de cuenta; retención = los datos viven mientras exista la cuenta |
| T30 · Evaluación | Entregada una evaluación propia del tutor y los recursos (`pnpm eval:ai:h3`, 16 casos sintéticos; ver [cierre H3/H4](evidence/cierre-h3-h4.md)) y la [guía de demo](DEMO.md) |
| Posteriores | Pendientes: infraestructura y despliegue en la nube (T25 a T28) y la entrega final verificable en nube (T27, T32) |

El laboratorio H0 es una prueba independiente; no equivale a generación de recursos integrada en el chat. H2 cuenta con 60 pruebas registradas, comprobaciones de tipos/build y verificaciones reales acotadas de DeepSeek y Firestore. Son resultados del cierre del 3 de noviembre, no pruebas repetidas en esta actualización. Ver [evidencia H2](evidence/cierre-h2.md).

## Arquitectura y servicios

- Monorepo: `apps/web` (React/Vite), `apps/renderer` (origen aislado), `backend` (FastAPI/API y worker), paquetes compartidos e `infra`.
- Firebase Auth y Firestore reales: proyecto `educloud-1d5de`; Firestore Native `(default)` en `us-central1`, reglas cliente deny-all y acceso mediante backend.
- Proyecto previsto para cómputo y archivos: `educloud-513604`. No hay bucket ni despliegue web confirmado. GCS y Cloud Tasks tienen adaptadores, pero no pruebas contra infraestructura real.
- Los archivos siguen en `.data/objects`, privado e ignorado. La clave DeepSeek ya está en `.env`; nunca sobrescribirlo ni mostrar su contenido. Las credenciales temporales de desarrollo no son identidad válida para un despliegue.
- Acceso real limitado al dominio exacto `pcpuma.acatlan.unam.mx`, correo verificado y lista de piloto del backend.

## Punto de pausa y siguiente trabajo

El usuario pidió probar remotamente y evaluar Firebase frente a Vercel. La recomendación de trabajo fue Firebase Hosting con web y renderer en orígenes separados, más API/worker en Cloud Run, GCS privado y Cloud Tasks. Es una dirección pendiente de configuración y verificación, no un despliegue ya realizado.

Después pidió detener el trabajo hasta avisar que la facturación está activa. **Esa pausa sigue vigente para implementación y despliegue; esta tarea solo actualiza Markdown.** La última comprobación registró facturación desactivada; consultar de nuevo cuando el usuario reanude. No activar pagos ni hacer recargas por su cuenta.

Al reanudar, verificar facturación y estado real, preparar configuración/identidades/secretos y completar el despliegue del piloto con pruebas de extremo a extremo. Resolver o acotar las limitaciones operativas del cierre H2 antes de exponer el servicio. Los esqueletos ya reemplazan los spinners en la carga inicial, el tutor, la lectura de fuentes y los recursos (componente `components/Skeleton.tsx`); falta revisar el resto de la interfaz antes de darlo por terminado.

Si se cambia la elección a Vercel, el usuario pidió ver el `vercel.json` final y confirmar nombres de servicios, rutas públicas/internas y bindings antes de terminar. No añadir la configuración sugerida sin reconciliar API, worker, cargas y aislamiento del renderer.

## Decisión del 11 de noviembre de 2026: local primero, nube después

La facturación de Google Cloud requiere un pago de 30 USD para activar la prueba (con crédito inicial de 300 USD) y aún no hay fecha. El usuario decidió terminar y probar toda la funcionalidad en local, con Firebase Auth/Firestore reales y DeepSeek real, y conectar la nube unos días antes de la entrega. La pausa de infraestructura y despliegue **sigue vigente**. Se permite trabajo local y preparación documental o de contenedores que no cree recursos ni gaste crédito.

Riesgo asumido: los adaptadores de GCS y Cloud Tasks no se han probado contra servicios reales; reservar días de margen para el despliegue y las pruebas de extremo a extremo. Control de costos previsto: presupuesto con alertas, Cloud Run con mínimo de instancias en cero y apagado al finalizar.

Decisiones de producto del mismo día: pasaporte social en versión mínima (estampillas personales; amigos y comparación como trabajo futuro), prioridad a recursos con IA, y capturas propias para validar el diseño. Los textos de la web son simples y sin tecnicismos ni nombres de proveedores (ver memoria de feedback).

Verificación del corte H3/H4 (11 nov 2026): 72 pruebas de backend, unitarias del front, `pnpm check` y los 15 recorridos de `tests/e2e` (incluidos recursos, práctica, borrado y accesibilidad con axe en escritorio y móvil) con DeepSeek real y emuladores de Auth/Firestore; no son pruebas cloud. La lectura de respuestas del modelo repara las barras invertidas de LaTeX, y una respuesta cortada se reintenta una vez solo si su costo es conocido.

## Cómo continuar sin rehacer trabajo

Leer [AGENTS.md](../AGENTS.md), [README](../README.md), [plan](PLAN_V1.md), [runbook H2](runbooks/desarrollo-h2.md) y [Storage pendiente](runbooks/storage-pendiente.md). Consultar decisiones en `adr/` y evidencias en `evidence/`. Trabajar directamente sin subagentes por preferencia del usuario; la antigua distribución es solo referencia histórica. Mantener actualizados este resumen y los documentos afectados cuando cambie el estado.

El informe escolar H0/H1 ya tiene nueve páginas y la portada acordada. El usuario prefiere documentación concisa; no extenderlo ni regenerar el PDF por cambios de contexto técnico. Las capturas publicables están en `evidencias/`.
