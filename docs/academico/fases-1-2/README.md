# Informe académico de las fases 1 y 2

Informe resumido de **9 páginas** del trabajo de Cómputo en la Nube. Fase 1 = H0 (T01–T04); fase 2 = H1 (T05–T08). Conserva pitch, motivación, arquitectura cloud y validación sin repetir el plan técnico. El formato académico de referencia usa hoja carta, 12 puntos, tipografía Times, interlineado 1.5 y márgenes de 3 cm a los lados y 2.5 cm arriba/abajo; la versión anterior de ocho páginas usaba A4 y 11 puntos.

## Compilación en PowerShell

Desde esta carpeta, con pdfLaTeX y paquetes comunes de TeX Live:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error informe-fases-1-2.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error informe-fases-1-2.tex
```

También puede utilizarse `latexmk -pdf -interaction=nonstopmode -halt-on-error informe-fases-1-2.tex` si su instalación dispone de los requisitos de latexmk. No se modificó la instalación TeX global. No se necesitan BibTeX, biber, fuentes externas, acceso a red ni `shell-escape` para compilar. La bibliografía está incluida en LaTeX.

La salida es `informe-fases-1-2.pdf`. Se usan article, inputenc, fontenc, geometry, setspace, ragged2e, microtype, xcolor, array, tabularx, booktabs, longtable, TikZ e hyperref. Se carga NewTX si está instalado; en TinyTeX mínimo se usa Times mediante mathptmx. Los títulos y el pie institucional con línea horizontal se definen directamente en LaTeX. No se instalan paquetes globales para esta adaptación.

## Edición

- `datos-portada.tex`: institución, plantel, carrera, integrantes, profesor, lugar, fecha y pie institucional. El usuario confirmó UNAM, FES Acatlán, Matemáticas Aplicadas y Computación, los tres alumnos y el profesor; se omitió grupo por su petición. Los datos siguen editables para próximas entregas.
- `informe-fases-1-2.tex`: estilo e inclusión de módulos.
- `secciones/compacto.tex`: contenido y estado del informe resumido; es la sección que debe actualizarse. Los demás módulos de la versión extensa se conservan como material de trabajo y no se compilan, salvo portada, arquitectura y bibliografía.
- `secciones/14-fuentes.tex`: bibliografía oficial simple, consultada el 2 de noviembre de 2026.

Antes de marcar una tarea como verificada, registrar comando, ambiente, resultado y ruta de evidencia. El PDF no incluye secretos, identidades de cuentas reales ni escudos institucionales. Las capturas de mockups no se usan como prueba de funcionamiento.

## Revisión

Revisar log por errores, referencias indefinidas y `Overfull`; comprobar número de páginas con `pdfinfo` y renderizar con `pdftoppm`. La revisión visual y el detalle de límites se registran en `REPORTE.md`. Las compilaciones crean `.aux`, `.log`, `.out` y `.toc`, que son intermediarios regenerables.
