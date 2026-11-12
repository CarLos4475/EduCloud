# EduCloud · Guía para agentes

## Leer al retomar

1. [Contexto y estado actual](docs/CONTEXTO.md): acuerdos, alcance implementado y siguiente paso.
2. [README](README.md): instalación, ejecución y comandos de verificación.
3. [Plan v1](docs/PLAN_V1.md): alcance completo; sus tareas futuras no están implementadas por aparecer en el plan.
4. [Cierre H2](docs/evidence/cierre-h2.md), [cierre H3/H4](docs/evidence/cierre-h3-h4.md) y [runbook H2](docs/runbooks/desarrollo-h2.md): evidencia, límites y operación. La [guía de demo](docs/DEMO.md) resume el recorrido.

Consultar `docs/adr/` para decisiones técnicas y el plan detallado solo para la tarea que se esté trabajando. Los registros de cierre describen lo entregado; el plan expresa también objetivos futuros. Las instrucciones recientes del usuario prevalecen sobre documentos históricos.

## Reglas de trabajo

- Comunicarse en español y mantener documentación breve, concreta y adecuada a un proyecto universitario de Cómputo en la Nube.
- Trabajar con un solo agente. No crear subagentes salvo nueva indicación explícita del usuario.
- Conservar el estilo Block & Bold con azul y oro, materias libres e inicio organizador; el tutor se abre manualmente.
- Usar esqueletos para estados de espera, no spinners. Es un requisito pendiente de aplicar de forma general; no darlo por terminado.
- Priorizar material del estudiante, verificar citas y pedir consentimiento para usar conocimiento general. No ejecutar código generado en el origen principal.
- Mantener contratos backend/frontend sincronizados mediante los comandos del README. Verificar el cambio con comprobaciones proporcionadas a su alcance y registrar límites sin inventar resultados.
- No sobrescribir `.env`, imprimir claves ni subir credenciales, `.data`, dependencias, cachés o artefactos temporales. No copiar correos personales a la documentación.
- Mantener dominio institucional exacto `pcpuma.acatlan.unam.mx`, correo verificado en real, piloto autorizado y autorización en backend. No debilitar reglas para facilitar una demo.
- No presentar el proveedor sintético como IA real ni las pruebas con emuladores como pruebas cloud.
- **Despliegue pausado por el usuario hasta que avise que la facturación está activa.** No crear infraestructura ni desplegar mientras siga esa pausa; esta actualización documental no la revoca. Decisión vigente: terminar y probar todo en local y conectar la nube después (ver `docs/CONTEXTO.md`); el trabajo local y la preparación sin recursos están permitidos. No activar facturación, vincular pagos ni realizar recargas por el usuario.
- Al retomar infraestructura, consultar [el paso pendiente de Storage](docs/runbooks/storage-pendiente.md). Firebase/datos: `educloud-1d5de`; cómputo/Storage previsto: `educloud-513604`. No asumir que existen bucket, cola o servicios desplegados.

## graphify

Graphify is configured for this project. The graph is available only when graphify-out/graph.json exists; generated graph files are local and ignored by Git. Update the graph after source changes without paid semantic extraction unless explicitly requested.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
