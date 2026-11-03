# Reporte de elaboración del informe

## Adaptación de estilo solicitada

Se adoptaron la portada y el formato del LaTeX proporcionado por el usuario, conservando el contenido de EduCloud: carta, 12 puntos, Times, interlineado de 1.5, sangría de 1.25 cm, márgenes laterales de 3 cm y superior/inferior de 2.5 cm. Portada sin decoraciones, institución y título centrados, datos a la derecha; pie con línea, identificación institucional y número de página. El cuerpo usa escala de grises e hipervínculos sin color visible. No se incorporaron el tema de investigación, nombres, profesor ni fecha del documento ajeno. Los campos académicos siguen editables.

Esta adaptación reemplaza visualmente la versión A4 de ocho páginas descrita en los registros históricos inferiores. El texto del cuerpo se conservó; `compacto.tex` y `14-fuentes.tex` no cambiaron, y en arquitectura solo se ajustó la sangría de un párrafo. La salida vigente tiene nueve páginas carta, incluida la portada sin numerar.

Se compilaron dos pasadas finales sin advertencias de desbordamiento o referencias indefinidas y se inspeccionaron las nueve páginas renderizadas, con detalle de portada y arquitectura. El usuario indicó los tres alumnos y al profesor Diego Romero Mora, y pidió omitir grupo; esos datos sustituyen los campos de portada correspondientes. Los nombres del documento de referencia no se utilizaron como fuente de identidad.

El usuario confirmó también la Universidad Nacional Autónoma de México, la Facultad de Estudios Superiores Acatlán y la Licenciatura en Matemáticas Aplicadas y Computación. La portada se completó con esa identificación académica y el lugar de la referencia, Naucalpan de Juárez, Estado de México.

## Corte anterior: cierre H0/H1

El PDF vigente tiene **8 páginas A4** y presenta la motivación, el pitch, la arquitectura cloud y los resultados de H0/H1. Se recompiló dos veces con pdfLaTeX después de actualizar el estado real; `pdfinfo` confirmó ocho páginas y el log no contiene desbordamientos ni referencias indefinidas. Se inspeccionó la página 7 renderizada, que documenta Firebase/Firestore y DeepSeek reales, la restricción institucional y los límites de la evaluación sintética. La revisión visual completa de la versión resumida se conserva en el registro inferior.

La evidencia de software vigente está en [cierre H0/H1](../../evidence/cierre-h0-h1.md). Los campos de integrantes, profesor y grupo siguen editables en `datos-portada.tex`. Los apartados siguientes son el historial de autoría anterior, incluida la primera versión extensa; no describen el estado actual del software.

Fecha: 2 de noviembre de 2026. Alcance de edición: solo `docs/academico/fases-1-2/`. No se modificó código de aplicación, infraestructura, documentos de planeación ni instalación global de TeX. No se creó ningún commit.

## Entrega

- `informe-fases-1-2.pdf`: **19 páginas A4**, fuente de 11 puntos y márgenes de 2.25 cm.
- `informe-fases-1-2.tex`, `datos-portada.tex` y `secciones/`: fuente modular editable.
- `README.md`: compilación, edición y revisión.
- `.gitignore`: excluye únicamente intermediarios y material regenerable de revisión de esta carpeta.

Se incluyeron portada con identidad académica editable, resumen, problema, objetivos, delimitación de H0/H1, metodología, requisitos, modelo de servicio, arquitectura, identidad/IAM, distinción Firestore/objetos, contenedores, escalamiento, asincronía, observabilidad, costo sin trial, desarrollo por tarea, criterios de cierre, riesgos, conclusiones, fuentes oficiales y trazabilidad. La motivación de H0 contiene una presentación de 60–90 segundos y una tabla de problema, aporte e hipótesis de validación. No se hacen comparaciones competitivas sin estudio ni promesas de mejores notas.

La paleta utiliza azul `#122245`, oro `#B59957`, marfil y arena. Los diagramas son TikZ vectorial. No se incluyeron mockups gigantes, datos reales, nombres inventados ni escudos institucionales.

## Comprobaciones realizadas

1. Se ejecutó el hook `mark_artifact_operation_started.mjs` exactamente una vez antes de la autoría, con salida 0.
2. Se verificaron paquetes disponibles. Se evitó instalar componentes globales. La primera compilación detectó que `xcolor[table]` requería `colortbl`, ausente; se retiró esa opción innecesaria. La versión final usa `xcolor` sin dependencia de `colortbl`.
3. Se compiló con pdfLaTeX hasta resolver índice, referencias y coordenadas de portada. Las dos últimas ejecuciones terminaron con código 0:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error informe-fases-1-2.tex
```

4. El log final no contiene errores de LaTeX, referencias o citas indefinidas, avisos de nueva pasada ni cajas `Overfull`. Conserva **dos avisos `Underfull \hbox`** en finales de párrafo junto a tablas: son advertencias de justificación, sin recorte o invasión de márgenes en la revisión visual.
5. `pdfinfo` y `pypdf` confirmaron 19 páginas. Todas contienen texto; no hay páginas vacías. `pdfinfo` informa A4, sin cifrado ni JavaScript.
6. Se renderizaron las 19 páginas mediante Poppler y se inspeccionaron hojas de contacto. Se revisaron a mayor resolución portada, arquitectura (página 7), motivación y pitch (página 10) y estado (página 19). Se corrigieron una superposición inicial de portada, tres cajas de texto desbordadas y una flecha que cruzaba nodos. La marca Cloud Storage conserva su nombre sin partición.
7. La revisión del integrador también inspeccionó los contactos y detalle de arquitectura/pitch. Las páginas de interés para una revisión adicional son **7** (arquitectura), **8–9** (datos y operación/costo), **10** (pitch y tabla de valor), **13** (autorización), **18** (trazabilidad) y **19** (estado).

Los renderizados y la salida de compilación están en `revision/` como material temporal ignorado por Git. El PDF final no depende de esos archivos.

## Fuentes y precisión técnica

Se consultaron páginas oficiales de NIST, Google Cloud y Firebase, con enlaces exactos dentro de la bibliografía. La fecha de consulta aparece en el PDF. Se mantuvo la distinción entre capacidades del proveedor y decisiones del proyecto.

La documentación vigente de Cloud Billing distingue presupuestos de solo alertas y presupuestos con límite de gasto. El informe precisa que **las alertas por sí mismas no detienen el gasto**, y solicita verificar disponibilidad/cobertura de límites antes de depender de ellos. Fuente: https://docs.cloud.google.com/billing/docs/how-to/budgets . No se fijaron precios numéricos, cuotas supuestamente permanentes ni un costo observado inexistente.

El worker del diseño se describe como servicio HTTP privado de Cloud Run invocado por Tasks, para evitar confundirlo con Cloud Run worker pools y su comportamiento de escalamiento.

## Estado y límites

El apartado factual está separado en `secciones/99-estado.tex`. Al cierre de esta entrega refleja el reporte del integrador: **T01 base local implementada, revisión independiente en curso; T02 pendiente y no iniciado**. No marca H0 ni H1 terminados. T03–T08 y despliegue cloud no tienen aprobación atribuida. Ese apartado se puede actualizar con evidencia posterior sin reescribir el diseño como resultado.

Faltan los datos reales de portada. La compilación y revisión del PDF no validan software, IAM real, calidad de IA ni facturación. La evaluación de valor educativo es una propuesta de estudio, no un resultado obtenido. El PDF no es una certificación de accesibilidad y no está etiquetado como PDF/UA.

La actualización de Graphify, dado que afecta una carpeta ajena al alcance documental asignado, corresponde al integrador junto con los cambios de la aplicación. No se ejecutó desde esta subtarea para evitar tocar archivos compartidos fuera de `docs/academico/fases-1-2/`.
# Actualización: versión resumida

El usuario pidió reducir la extensión. El PDF vigente tiene 8 páginas en lugar de 19 y compila `secciones/compacto.tex` junto con portada, arquitectura y bibliografía. Se conservaron motivación, pitch, conceptos cloud y alcance H0/H1; se retiraron del PDF el índice, apéndices y explicaciones repetidas. Los módulos previos siguen disponibles como material de trabajo. Recompilación exitosa y revisión visual de páginas; sin desbordamientos ni referencias indefinidas. El registro de avance del repositorio es la referencia vigente sobre implementación.
