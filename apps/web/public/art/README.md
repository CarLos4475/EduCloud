# Ilustraciones e iconos

Aquí van las imágenes generadas. Si un archivo no existe, la app muestra un icono de respaldo, así que se pueden añadir de a poco. Los prompts están en `docs/design/prompts-imagenes.md`.

Formato: PNG con fondo transparente, sin texto dentro de la imagen. Nombres exactos:

| Carpeta | Archivos | Tamaño |
|---|---|---|
| `art/` | `tutor-avatar.png`, `tutor-empty.png`, `logo.png`, `login-hero.png`, `home-hero.png`, `empty-resources.png`, `empty-materials.png`, `empty-agenda.png` | ver tabla de prompts |
| `art/personalities/` | `patient.png`, `socratic.png`, `direct.png` | 256×256 |
| `art/kinds/` | `summary.png`, `concepts.png`, `flashcards.png`, `quiz.png`, `interactive.png` | 256×256 |
| `art/stamps/` | `first_material.png`, `first_question.png`, `first_resource.png`, `explorer.png`, `first_quiz.png`, `perfect_quiz.png`, `cards_ten.png`, `three_subjects.png` | 256×256 |
| `art/subjects/` | `grid.png`, `wave.png`, `orbit.png`, `geometry.png`, `terminal.png`, `circuit.png`, `blocks.png`, `compass.png`, `vector.png`, `graph.png`, `cube.png`, `nodes.png` | 640×520 |
| `art/icons/` | `nav-home.png`, `nav-subjects.png`, `nav-agenda.png`, `nav-schedule.png`, `nav-profile.png`, `mode-explain.png`, `mode-hints.png`, `mode-solution.png`, `mode-practice.png` | 128×128 |

Ya están conectados: `tutor-avatar`, `tutor-empty`, `personalities/*`, `kinds/*`, `stamps/*`, `subjects/*` y `icons/*`. También están conectados `logo` (menú y pestaña), `login-hero`, `home-hero` y los `empty-*`.
