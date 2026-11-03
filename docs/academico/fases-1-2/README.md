# Informe académico de las fases 1 y 2

Informe resumido de **8 páginas** del trabajo de Cómputo en la Nube, reducido desde 19 páginas. Fase 1 = H0 (T01–T04); fase 2 = H1 (T05–T08). Conserva pitch, motivación, arquitectura cloud y validación sin repetir el plan técnico.

## Compilación en PowerShell

Desde esta carpeta, con pdfLaTeX y paquetes comunes de TeX Live:

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error informe-fases-1-2.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error informe-fases-1-2.tex
```

También puede utilizarse `latexmk -pdf -interaction=nonstopmode -halt-on-error informe-fases-1-2.tex` si su instalación dispone de los requisitos de latexmk. No se modificó la instalación TeX global. No se necesitan BibTeX, biber, fuentes externas, acceso a red ni `shell-escape` para compilar. La bibliografía está incluida en LaTeX.

La salida es `informe-fases-1-2.pdf`. Se usan article, inputenc, fontenc, lmodern, geometry, microtype, xcolor, array, tabularx, booktabs, longtable, TikZ e hyperref. Se evitaron paquetes no instalados (babel español, fancyhdr, titlesec y enumitem).

## Edición

- `datos-portada.tex`: institución, plantel, integrantes, profesor, grupo y fecha. Los campos entre corchetes son intencionales.
- `informe-fases-1-2.tex`: estilo e inclusión de módulos.
- `secciones/compacto.tex`: contenido y estado del informe resumido; es la sección que debe actualizarse. Los demás módulos de la versión extensa se conservan como material de trabajo y no se compilan, salvo portada, arquitectura y bibliografía.
- `secciones/14-fuentes.tex`: bibliografía oficial simple, consultada el 2 de noviembre de 2026.

Antes de marcar una tarea como verificada, registrar comando, ambiente, resultado y ruta de evidencia. El PDF no incluye secretos, identidades de cuentas reales ni escudos institucionales. Las capturas de mockups no se usan como prueba de funcionamiento.

## Revisión

Revisar log por errores, referencias indefinidas y `Overfull`; comprobar número de páginas con `pdfinfo` y renderizar con `pdftoppm`. La revisión visual y el detalle de límites se registran en `REPORTE.md`. Las compilaciones crean `.aux`, `.log`, `.out` y `.toc`, que son intermediarios regenerables.
