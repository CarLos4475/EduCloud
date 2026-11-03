# ADR 0002: Contratos como frontera de módulos

**Estado:** aceptada para T02, 2026-11-02.

Pydantic es la fuente de los DTO públicos del backend. Los nombres serializados usan camelCase, se rechazan campos no declarados y los campos que pertenecen al servidor —como propietario, permisos, resultados o roles— no aparecen en las entradas de mutación. `backend/scripts/generate_contracts.py` genera `backend/openapi.json` y `packages/api-client/src/generated.ts`; `pnpm contracts:check` evita que ambos se alejen de los modelos.

Los puertos de infraestructura reciben actor/scope para evitar un `get_by_id` abierto. Los adaptadores en memoria solo sirven a pruebas locales, no representan autenticación ni persistencia de producción. Las rutas de contrato devuelven `501` explícito hasta que un módulo implemente sus reglas de autorización.

`InteractivePackageV1` y el protocolo TypeScript describen el intercambio de mensajes, no autorizan ejecución de JavaScript generado. T03 define el renderer, la CSP, el worker y las capacidades permitidas.
