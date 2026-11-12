# Mi Campus · H0–H2

Funcionan identidad, perfil, materias libres, temas, periodos, agenda y horario. H2 incorpora biblioteca privada, extracción y revisión de apuntes, tutor con fuentes verificables, personalidades, modos de ayuda e historial recuperable. H0 conserva el laboratorio aislado de recursos interactivos; su generación dentro del tutor corresponde a H3.

Para retomar el proyecto, leer primero [AGENTS.md](AGENTS.md) y el [contexto actualizado](docs/CONTEXTO.md). **Al 11 de noviembre de 2026, el despliegue sigue pausado hasta que el usuario avise que la facturación está activa; el desarrollo y las pruebas continúan en local y la nube se conecta después (ver contexto).** La solicitud de acceso remoto ya existe; aún no se ha desplegado la web. La dirección propuesta es Firebase Hosting en dos orígenes y Cloud Run para API/worker. También queda pendiente aplicar esqueletos a todos los estados de espera, sin spinners.

## Requisitos e instalación

Node 24 LTS, pnpm 11, Python 3.12–3.13, uv y Java 21 para los emuladores. Esta PC tiene un JRE 21 local en `.tools/java21`, detectado por el script sin modificar el Java del sistema. En PowerShell:

```powershell
pnpm install --frozen-lockfile
uv sync --project backend --locked
pnpm emulators
```

En otra terminal: `pnpm dev`. Arranca web, renderer, API y worker persistente. Copiar `.env.example` a `.env` solo la primera vez; nunca sobrescribir una clave ya configurada. En Windows, reiniciar este comando tras cambios de Python; la web mantiene HMR.

- Aplicación: http://127.0.0.1:5173
- Laboratorio H0: http://127.0.0.1:5173/h0.html
- Contratos API: http://127.0.0.1:8000/docs
- Auth/Firestore emulados: puertos 9099/8080; cuentas sintéticas con dominio institucional.

El emulador exporta datos al salir con el script; `.firebase` está ignorado. Archivar conserva relaciones. Eliminar una materia borra también sus temas, pendientes, apuntes, archivos, conversaciones, recursos y práctica; se rechaza mientras haya tareas en curso.

## Servicios reales

Firebase y datos: `educloud-1d5de`, con Firestore Native `(default)` en `us-central1`, reglas cliente deny-all y app web registrada. `educloud-513604` queda reservado para Cloud Run posterior; aún no hay despliegue de la aplicación.

Los originales, versiones e índices de H2 se guardan por ahora en `.data/objects`, fuera de las rutas servidas y excluida de Git. Los dos servidores Vite deniegan también acceso mediante `@fs`. El adaptador GCS exige acceso uniforme y prevención de acceso público. Crear el bucket requiere activar facturación; no se ha vinculado ninguna cuenta ni creado el bucket. El worker local consulta trabajos persistidos; el transporte Cloud Tasks queda preparado para H6.

`pnpm dev:cloud` conecta la web local con Firebase/Firestore reales usando las sesiones Firebase CLI/gcloud del operador. Las credenciales temporales permanecen en memoria, no en variables VITE ni archivos. Al expirar la sesión, reiniciar el comando. En Cloud Run se usará identidad de servicio/ADC; el adaptador de operador local se niega a funcionar allí. El script local de gcloud está preparado para la ruta de Windows de esta PC.

La API exige dominio exacto `pcpuma.acatlan.unam.mx`, correo verificado en real y pertenencia al piloto (`CAMPUS_PILOT_UIDS` o `CAMPUS_PILOT_EMAILS`, solo backend). Esta restricción protege acceso a datos; no bloquea la creación de identidades externas mediante la API pública de Firebase. Las cuentas externas no acceden a la aplicación. La verificación de correo se omite únicamente en el emulador.

## Verificación

```powershell
pnpm check
pnpm test:unit
pnpm test:integration # requiere emuladores
pnpm test:e2e         # usar modo de prueba del runbook H2
pnpm test:security
pnpm audit --prod
pnpm --filter @campus/web build
pnpm --filter @campus/renderer build
```

`pnpm check` comprueba tipos, Ruff, mypy y sincronización de contratos. El sandbox de herramientas de Windows puede bloquear asyncio: las pruebas se verificaron fuera de él. No se sustituyen resultados de emulador por resultados de servicios reales.

Pruebas opt-in: `pnpm eval:ai` utiliza DeepSeek con cinco solicitudes sintéticas; `node scripts/ai-eval.mjs --generate-resource` genera y valida una experiencia; `node scripts/cloud-smoke.mjs --preflight` solo lee permisos y fixtures; `pnpm test:cloud` crea una cuenta sintética, prueba Auth/Firestore y elimina únicamente sus datos. El fixture se marca verificado por Admin SDK sin enviar correos. No se modifica la cuenta real del estudiante. La clave DeepSeek se lee de `.env` y no se imprime.

H2: `pnpm eval:ai:h2` verifica visión y tutoría con dos llamadas reales y material sintético. `pnpm test:cloud:h2 --preflight` consulta el índice remoto sin escribir; sin esa opción crea un UID de fixture, prueba persistencia y elimina solo sus documentos, sin crear cuentas de Auth. El [runbook H2](docs/runbooks/desarrollo-h2.md) explica arranque, pruebas, límites y configuración futura del bucket.

## Contratos y documentación

`pnpm contracts:generate` exporta OpenAPI y DTOs TypeScript desde el backend; `pnpm contracts:check` detecta divergencias. Las rutas académicas ya ejecutan operaciones reales; `/api/v1/contracts` queda como diagnóstico 501. Los contratos detallados de futuros módulos se amplían al implementar sus consumidores.

El [informe escolar de H0/H1](docs/academico/fases-1-2/informe-fases-1-2.pdf) ocupa nueve páginas con la portada y el estilo académico indicados por el usuario. H2 se documenta en su [registro de cierre](docs/evidence/cierre-h2.md). La implementación continúa directamente con un solo agente por decisión del usuario.

El [cierre H3/H4](docs/evidence/cierre-h3-h4.md) resume recursos, práctica, pasaporte y borrado, y la [guía de demo](docs/DEMO.md) explica el recorrido. `pnpm eval:ai:h3` mide con IA real la calidad del tutor y los recursos. El [registro de evidencia](docs/evidence/avance-fases-1-2.md) detalla pruebas y límites. El laboratorio es una prueba de viabilidad QuickJS/WASM con SDK acotado, no un IDE remoto. La configuración de orígenes/CSP debe adaptarse al desplegar. La calidad de IA se evaluó con un corpus sintético pequeño, no como certificación académica general.
