# Guía de demo (unos 8 minutos)

## Preparación

1. `pnpm emulators` en una terminal y `pnpm dev` en otra (ver [README](../README.md)). La clave de la IA debe estar en `.env`.
2. Abrir http://127.0.0.1:5173 y crear una cuenta con un correo `@pcpuma.acatlan.unam.mx` (en local se verifica solo).
3. Tener a la mano un PDF o unos apuntes cortos.

## Recorrido

1. **Acceso y materias libres.** Entrar, crear una materia con su ilustración y agregar un tema y un pendiente. Mostrar el inicio organizador.
2. **Apuntes primero.** Subir un PDF o guardar una nota. Mostrar que queda "Listo para estudiar" y abrir el material para ver el texto y las páginas.
3. **Tutor con fuentes.** Abrir el tutor, elegir los apuntes y preguntar algo que sí está. Abrir una cita para ver la página original. Preguntar algo que no está y mostrar que pide permiso antes de usar conocimiento general.
4. **Del chat al repaso.** Con "Llévalo a tu repaso", crear tarjetas o un cuestionario desde esa respuesta.
5. **Recursos.** En la materia, crear un resumen y un experimento interactivo. Mover los controles; pedir "hazlo más sencillo" y mostrar las dos versiones.
6. **Práctica y progreso.** Contestar el cuestionario, repasar tarjetas y ver "Tu progreso" con sus recomendaciones.
7. **Pasaporte.** En "Mi perfil", mostrar las estampillas ganadas.
8. **Cierre.** Mencionar que eliminar una materia o "borrar todo" borra los datos de verdad.

## Qué decir con honestidad

- Todo corre en local con IA real; la nube (Cloud Run, Storage, Cola) está diseñada y con adaptadores, pero **no se ha desplegado** porque falta activar la facturación.
- La IA puede equivocarse o tardar; por eso hay citas verificadas, reintentos y versiones que no se pierden.
- Pasaporte social (amigos y comparación) queda como trabajo futuro.

## Si algo falla

- Sin respuesta de la IA: revisar la clave en `.env` y reintentar desde la propia pantalla.
- Cambios en Python en Windows: reiniciar `pnpm dev`.
