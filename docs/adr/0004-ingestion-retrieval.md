# ADR 0004 · Extracción y recuperación de H0

Se eligieron pypdf (PDF textual), python-pptx (texto/notas de diapositiva), Pillow (validación de imágenes) y pypdfium2/PDFium para rasterizar páginas escaneadas antes de visión. Se evita introducir el parser AGPL inicialmente considerado. La [documentación de pypdfium2](https://pypdfium2.readthedocs.io/en/stable/readme.html#licensing) describe la elección de licencia Apache-2.0/BSD-3-Clause y los avisos de PDFium/terceros que deben conservarse al distribuir. Las fuentes @fontsource llevan OFL; las 12 ilustraciones son SVG propios.

Los originales de prueba no se descargan de internet: los genera el propio corpus. Se mantienen localizadores físicos desde 1 y referencias a propietario, materia, material y versión. Las diapositivas con figuras no interpretadas quedan bajo revisión. La transcripción de visión siempre es borrador, incluso si el proveedor expresa confianza.

BM25 local aplica filtros de owner/materia/material antes de ordenar. Se ejecutaron 40 consultas sintéticas (20 conceptos y dos redacciones); todas incluyeron la página esperada en top-8. El corpus es pequeño, de vocabulario directo; no es una evaluación ciega de equivalencias matemáticas ni un porcentaje de calidad general. No se contrató un proveedor de embeddings.

DeepSeek flash transcribió correctamente la imagen sintética de f(x)=x² y f'(x)=2x. Cuatro respuestas live respetaron las fórmulas y citaron bloques disponibles. Para una experiencia interactiva se rechazaron dos salidas inválidas (truncamiento y tipo incorrecto de instrucciones), y el tercer intento válido se comprobó en navegador. Nunca se relajó el esquema o el aislamiento para aceptar una salida.

H2 integrará carga y procesamiento asíncrono de materiales del alumno. Los límites de este prototipo no sustituyen el aislamiento de procesos y checkpoints de ese pipeline.
