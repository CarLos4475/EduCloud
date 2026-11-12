# Coordinación de subagentes y control de ejecución

**Actualización de ejecución:** el usuario prefirió continuar con un solo agente por el costo de la orquestación. Desde T02 se trabaja directamente, con pruebas focalizadas y registro breve de avance. La distribución siguiente queda como referencia opcional para el futuro, no como requisito de nuevas delegaciones.

Este documento conserva la organización original como referencia histórica; no activa delegaciones ni describe la petición actual. H0–H2 están cerrados y la ejecución actual es con un solo agente. Consultar [el contexto vigente](../CONTEXTO.md) antes de retomar. Leer el plan no autoriza ejecutar hitos futuros ni levantar la pausa de despliegue.

## 1. Responsabilidades

El agente principal es integrador: conserva requisitos, ordena dependencias, resuelve contratos y verifica cada entrega. Con cuatro espacios disponibles, usar como máximo tres subagentes simultáneos; una revisión ocupa uno de esos espacios. No crear chats del usuario para subtareas.

| Perfil | Tareas típicas | Propiedad principal |
|---|---|---|
| Integración/contratos | T01–T02, integración final, T31–T32 | Config raíz, lockfiles, modelos compartidos, router global, cliente generado |
| Runtime | T03, T15 | `apps/renderer/`, `packages/resource-sdk/` |
| Materiales/recuperación | T04, T10–T11 | extracción, indexado, fuentes y revisión de materiales |
| Académico/frontend | T05, T07–T08, T20 | tokens, shell, materias, agenda, onboarding |
| Identidad/jobs/cloud | T06, T09, T25–T27 | auth, autorización, cola, Storage, infraestructura/operación |
| Tutor/recursos | T12–T14, T16 | proveedor, prompts, turnos, generación, biblioteca/laboratorio |
| Aprendizaje | T17–T19 | evaluación, práctica, sesiones, evidencia y recomendaciones |
| Social | T21–T23 | logros, relaciones, shares, retos y pasaporte |
| Privacidad/revisión | T24, T28–T30 | borrado y revisiones acotadas de seguridad, calidad IA y experiencia |

Los perfiles son funciones reutilizables, no nueve agentes simultáneos. Un agente puede llevar tareas sucesivas del mismo módulo. Si pierde contexto, recibe un nuevo paquete acotado; no asumir que recuerda acuerdos antiguos.

## 2. Propiedad de archivos y contratos

Antes de cada delegación, asignar una lista explícita de rutas y declarar archivos solo de lectura. Ningún archivo tiene dos escritores simultáneos. Shared state incluye esquemas, índices, dependencias y rutas, no solo componentes visibles.

- `backend/src/campus/domain/`, `ports/`, `backend/openapi.json`, `packages/api-client/`: integrador de contratos. Agentes de módulo proponen cambios con motivo/consumidores; el integrador aplica y regenera.
- `packages/resource-sdk/`: runtime, sujeto a coordinación con contratos; consumidores no editan protocolo a escondidas.
- `packages/design-tokens/`, componentes compartidos: propietario frontend durante la ola; otros módulos consumen o solicitan cambios.
- Config raíz, CI, lockfiles, main/router global: integrador. Un agente puede crear un módulo/ruta local y entregar el punto de registro para integración.
- `infra/`, reglas y service accounts: cloud; cambios de contrato de almacenamiento requieren revisión de integrador/backend.
- Tests por módulo pueden crearlos sus propietarios. Fixtures compartidos los mantiene el integrador o dueño designado del corpus.

Una dependencia nueva se solicita antes de tocar lockfiles compartidos. El integrador elige versión/licencia, instala una sola vez y comunica el contrato. Si se usan worktrees durante la implementación, seguir la skill aplicable y revisar merge; no crearlos en esta etapa de planeación. Un checkout compartido es viable con propiedad estricta; los agentes no revierten archivos ajenos.

## 3. Agenda de ejecución orientativa

No es calendario ni estimación de días. La tabla expresa simultaneidad segura tras satisfacer dependencias; el integrador puede serializar cuando falten slots o aparezcan problemas.

| Ola | Trabajo listo | Coordinación / resultado |
|---|---|---|
| 0 | T01 → T02 | Un integrador fija base y contratos antes de repartir |
| 1 | T03, T04, T05 | Tres pruebas/frentes independientes; integrador resuelve solicitudes comunes |
| 2 | T06, finalizar spikes si faltan | No más funciones apoyadas en runtime/ingestión sin puerta validada |
| 3 | T07 → T08, T09 cuando T07 esté listo | Académico y jobs; autorizar propietario del módulo web de uploads |
| 4 | T10 → T11, T25 | Pipeline y preparación cloud en paralelo; frontend puede terminar agenda |
| 5 | T12, T17 tras T12, T26 tras T12 | No iniciar evaluación contra un proveedor inexistente; T27 base tras T26 |
| 6 | T13, T14, preparación de T18 tras T17/T14 | Tutor y recursos con áreas separadas; T15 inicia tras T14 |
| 7 | T15, T18 → T19 | Runtime y aprendizaje; T16 espera T13/T14/T15 |
| 8 | T16, T20, T21 | Tras T19, onboarding y motor de estampillas no comparten archivos |
| 9 | T22 → T23, T24 tras T21/T22 | Social primero; borrado integra relaciones y datos ya definidos |
| 10 | T27 completo, T28, T29, T30 | Hasta tres revisores; revisión primero, fixes se asignan por propietario |
| 11 | T31 → T32 | Demo integral, evidencia y cierre por integrador |

T27 tiene dos checkpoints: integración base temprana y smoke completo una vez incorporados los módulos. No marcar T27 finalizado tras solo probar healthcheck. T28/T30 requieren el checkpoint completo; T29 puede empezar antes sobre funcionalidades ya integradas.

No despachar frontend y backend del mismo flujo con contratos inventados por separado. Tras T02, un frontend sí puede avanzar con fixtures contractuales, pero su tarea no se cierra hasta integrarse con API real.

## 4. Paquete obligatorio para cada agente implementador

Usar esta plantilla cuando el usuario autorice ejecución:

```text
Tarea: Txx — [título exacto del plan]
Objetivo observable: [comportamiento concreto]
Leer:
- AGENTS.md y skills aplicables.
- Secciones precisas de spec, arquitectura y tarea.
- Resultado de tareas productoras [IDs + archivos/contratos].
Graphify: si existe graphify-out/graph.json, seguir AGENTS antes de
consultar relaciones del código; si no existe, no fingir que se consultó.
Puedes editar: [rutas exactas]
Solo lectura / otros propietarios: [rutas]
Interfaces que consumes: [nombre, versión, productor]
Interfaces que produces: [nombre, forma, consumidores]
Fuera de alcance: [límites concretos de esta tarea]
Pruebas y aceptación: [casos Vxx + comandos focalizados]
Restricciones: no tocar contratos/lockfiles compartidos sin coordinación;
no desplegar, publicar ni acceder a secretos fuera del alcance autorizado.
Entrega: resumen de comportamiento, archivos, pruebas reales y resultados,
fallos/limitaciones y cambios de contrato solicitados.
Si encuentras un problema de arquitectura, explica evidencia e impacto;
no improvises una alternativa incompatible para cerrar la tarea.
```

El paquete debe ser autosuficiente; no remitir a “lo que hablamos” ni mandar la conversación completa como única especificación. Compartir contexto suficiente sobre decisiones del usuario, especialmente fuentes, materias libres, ayuda configurable y estampillas pendientes.

## 5. Contratos de entrega entre frentes

| Productor | Entrega | Consumidores |
|---|---|---|
| T02 | Modelos Pydantic/OpenAPI, tipos TS y errores | Todos |
| T03 | `InteractivePackageV1`, SDK y pruebas de capacidades | T14, T15 |
| T04 | Extractores y recuperación elegidos con corpus | T10, T11, T30 |
| T05 | Tokens, shell, componentes e illustration IDs | Todas las vistas y renderer |
| T06 | Actor verificado, authorize owner/grant y repositorios | Todas las rutas/servicios |
| T09 | `Job`, cola, outbox, leases y `UploadTicket` | T10, T12, T14, T17, T24 |
| T11 | `Retriever` y `SourceRef` resueltos | T12, T14, T17 |
| T12 | `TutorProvider`, turnos, cuota y contexto | T13, T14, T17 |
| T14 | Recursos/versiones y contratos de estado | T15, T16, T18, T22 |
| T17 | Instrumentos públicos, intentos y evidencia verificada | T18, T19 |
| T19 | Progreso, sesiones y eventos idempotentes | T20, T21, T22 |
| T22 | Amistad, proyecciones, snapshots/grants y retos | T23, T24 |
| T25–T27 | Servicios/IAM y configuración de entorno | Pruebas cloud, revisiones y demo |

Un productor entrega ejemplos válidos/erróneos y pruebas; el consumidor no renombra un campo localmente como solución permanente. El integrador mantiene cambios de contrato juntos para evitar semanas de mocks incompatibles.

## 6. Revisión por tarea y por hito

1. **Implementador:** comprueba comportamiento y pruebas focalizadas; entrega evidencia real.
2. **Integrador:** verifica alcance y archivos, integra registros compartidos y ejecuta prueba entre productor/consumidor.
3. **Revisor fresco, cuando esté disponible:** revisión de especificación para funciones de producto y revisión técnica/seguridad para fronteras sensibles. No hacer tres rondas cosméticas si no hay riesgos nuevos.
4. **Corrección:** asignar hallazgo al propietario, añadir regresión si corresponde, repetir solo verificaciones afectadas.
5. **Cierre de hito:** demostrar ruta completa y actualizar matriz Vxx. Capturas bonitas no sustituyen persistencia/permisos.

Se requieren revisiones especialmente cuidadosas de T03/T06/T09/T12/T15/T17/T22/T24/T25. Cambios de interfaz, auth o permisos no se aprueban solamente porque compiló.

Los revisores no editan los módulos que están revisando mientras sus propietarios trabajan; reportan primero. Las correcciones cruzadas se serializan o se reparten con propiedad nueva explícita.

## 7. Regla de bloqueos y decisiones

- **Editorial no bloqueante:** nombre del producto y estampillas finales. Usar placeholders honestos y mantener catálogo demo separado.
- **Técnico resoluble:** parser, biblioteca de gráficos, disposición móvil o test flaky. El implementador propone y resuelve dentro de requisitos con evidencia.
- **Cambio de producto:** quitar visión, limitar materias a cuatro, imponer tutor socrático, ejecutar recursos sin aislamiento, publicar social por defecto. No autorizado por este plan; escalar al usuario con opciones concretas.
- **Externo:** credenciales, permisos cloud, presupuesto elegido. Continuar trabajo independiente local; no inventar disponibilidad ni saltarse autenticación.
- **Costo adicional material:** medir necesidad y presentar plan/recurso/costo revisable antes de pedir autorización. No interrumpir por hipótesis ni solicitar repetidamente una aprobación ya dada.

## 8. Revisión documental de esta entrega

Se solicitó un builder-check independiente según la skill de brainstorming. La herramienta de subagentes devolvió un límite de uso antes de realizar la revisión; no hubo informe ni aprobación independiente.

Revisión del agente principal completada el 2 de noviembre de 2026:

- [x] Enlaces relativos y archivos del paquete existentes: seis documentos, ningún enlace local roto en la comprobación automatizada.
- [x] T01–T32 únicos, dependencias existentes y sin ciclos; se incluyeron las dependencias adicionales del checkpoint cloud completo.
- [x] Requisitos del usuario relacionados con tareas y 24 casos de aceptación; materias libres, visión, tutor configurable, HTML interactivo, progreso y amigos incluidos.
- [x] Lectura cruzada de API, entidades, SDK y consumidores; se concretaron puertos, estados de revisión, localizadores, DTO de share y flujo de aceptación de amistad.
- [x] Propuestas técnicas y pendientes artísticos separados de acuerdos; las estampillas definitivas siguen abiertas.
- [x] Solo se escribieron documentos de planeación; las 178 casillas de implementación permanecen pendientes. No se ejecutaron pruebas de aplicación ni despliegues.

La comprobación documental usó PowerShell sobre el workspace: seis documentos, 32 tareas, 24 casos de aceptación, cero enlaces locales rotos y cero ciclos. El inventario superior conserva únicamente `.codex`, `docs`, `graphify-out` y `AGENTS.md`; no se crearon scaffold de aplicación ni repositorio Git. No existe grafo `graphify-out/graph.json`, por lo que no se atribuye una consulta a Graphify.

Al comenzar ejecución, repetir builder-check con contexto acotado si hay capacidad disponible. El fallo de esa herramienta no invalida la existencia del plan, pero debe conservarse como limitación de la revisión.
