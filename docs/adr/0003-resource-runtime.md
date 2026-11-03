# ADR 0003 · Laboratorio con capacidades limitadas

Se implementó un origen independiente (5174) con HTML sanitizado mediante DOMPurify, CSS analizado por css-tree y JavaScript interpretado por QuickJS/WASM en un Worker. No se inserta código generado en scripts del navegador. No se exponen window, document, fetch, sockets ni storage al intérprete. Solo JSON pasa por el puente.

Límites de prueba: heap VM 32 MiB, pila 512 KiB, 100 ms por evento, 1.000 operaciones por evaluación, paquetes de 300 KiB aproximados y estado 50 KiB. El padre comprueba origen, fuente, canal y secuencia; el iframe no permite navegación superior, formularios o ventanas. El CSS queda limitado al recurso y canvas a 800×600. El host mantiene watchdog para terminar el Worker.

Pruebas: parábola, movimiento uniforme, ordenamiento por burbuja y ley de Ohm generada por DeepSeek. Se verificaron resultados conocidos, controles y recuperación después de bucle infinito. Los controles quedan inactivos durante la carga. La prueba de navegador no observó solicitudes a dominios externos causadas por recursos.

La integración de biblioteca, estado persistente y versionado del estudiante pertenece a H3. La CSP de desarrollo y los orígenes deben configurarse para el despliegue en H6. Esto es evidencia sobre el corpus probado, no una certificación de sandbox frente a cualquier vulnerabilidad de navegador/WASM.
