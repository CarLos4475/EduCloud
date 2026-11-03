# Base local de la plataforma de estudio

Esta es una base técnica; aún no implementa funcionalidades de producto, autenticación, almacenamiento, renderer seguro ni integración cloud.

## Requisitos e instalación

Node 24.15 o superior de la serie 24, pnpm 11.0.8, Python 3.12 o 3.13 y uv 0.11.8. En PowerShell, desde la raíz:

```powershell
pnpm install --frozen-lockfile
uv sync --project backend --locked
pnpm dev
```

Web: http://127.0.0.1:5173; renderer: http://127.0.0.1:5174; API: http://127.0.0.1:8000/health. Ctrl+C termina los procesos. El puerto de cada servicio es estricto. `uv sync` crea `backend/.venv`, necesario antes de `pnpm dev`. No se necesitan credenciales para estas pruebas.

`.env.example` documenta valores previstos, pero T01 aún no carga configuración de este archivo. No copiar secretos al repositorio. No se requieren contenedores ni emuladores para T01; los emuladores de Firebase/Firestore/Storage se decidirán y documentarán en tareas posteriores. No se han creado imágenes ni Dockerfiles.

## Verificación

```powershell
pnpm check
pnpm test:unit
pnpm --filter @campus/web build
pnpm --filter @campus/renderer build
```

Los comandos de integración, e2e, seguridad, contratos, evaluación de IA, cloud y demo existen como nombres reservados y fallan explícitamente hasta que se implementen. `pnpm check` cubre tipos y Ruff; la validación de contratos está pendiente de T02. Los tests actuales no prueban funciones de producto. Este entorno de desarrollo no es una configuración de producción.
