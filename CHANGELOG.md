# Registro de cambios

Cada actualización de la app, de la más nueva a la más antigua.

## 2026-10-08
- Se guarda en el repo la parte de Supabase de **límites y borrar cuenta** (`supabase/limites-y-cuenta.sql`): una revisión cada hora del espacio usado, un freno automático (al 85 % se pausan las cuentas y las historias nuevas; se apaga al bajar del 75 %) y las funciones para que la app de iPhone borre la cuenta de una persona con todos sus datos. La web no cambia.
- Se guarda en el repo la parte de Supabase de los **Crews** de la app de iPhone (`supabase/crews.sql`): crear un grupo, entrar con un código, ranking de la semana y entrenos de los miembros. La web no cambia.
- `moderar.html` ahora tiene la pestaña **Historias** (entre Fotos y Otros): las historias de 24 h reportadas salen borrosas hasta tocarlas, con el nombre, cuántas personas las reportaron, los motivos y cuánto falta para que se borren solas. «Quitar historia» le suma un strike al usuario (con 2 ya no puede publicar) y borra la foto del almacén; «Está bien» la deja. Si las historias fallan, Fotos y Otros siguen funcionando. La pestaña «Otros reportes» pasó a llamarse **Otros** para que quepan las tres.
- Se guardan en el repo el programa de las historias para Cloudflare (`worker/historias.js`) y la parte de Supabase (`supabase/historias-parte1.sql` y `historias-parte2.sql`), como respaldo.
- Nueva página para moderar desde el celular: `moderar.html` (solo para el administrador, con su correo y contraseña). Pestaña **Fotos**: las fotos de perfil reportadas salen borrosas hasta tocarlas; «Eliminar foto» la borra y suma un strike, «Está bien» la aprueba. Pestaña **Otros reportes**: reportes de usuarios y entrenos, con «Descartar» y «Revisado». Se puede añadir a la pantalla de inicio del iPhone.
- La app web no cambia; solo se actualizó la caché para que no guarde la página nueva (así siempre se ve la versión publicada).

## 2026-10-03
- Enlaces cortos para las rutinas de entrenador: programa para Cloudflare en `worker/rutinas.js` (gratis). El enlace pasa de ~750 caracteres a uno como `…/r/k7Qx2pA`, y el entrenador puede corregir la rutina sin mandar otro enlace.
- Nueva página para las rutinas de entrenador (`/r/`): al abrir el enlace que manda un entrenador se ve la rutina (días, ejercicios, series, nota), con «Copiar código», el botón del App Store («Muy pronto» por ahora) y «Ya tengo la app: abrir la rutina».
- Especificación del **Modo entrenador** para la app de iPhone en `docs/app-ios/MODO-ENTRENADOR.md` (rutinas guardadas, renombrar, duplicar, compartir; «Tengo una rutina» para el alumno).
- La app web no cambia; solo se actualizó la caché para que no guarde la página nueva.

## 2026-09-27
- «Respaldo de datos» se ve también con la sesión iniciada (para pasar tu historial a la app del iPhone).
- Arreglo: en la lista de ejercicios del resumen final, el trofeo de récord salía como texto.
- La web queda terminada («congelada»): a partir de ahora solo arreglos. Plan de la app del iPhone en `docs/app-ios/PLAN.md`.

## 2026-09-26
- Editar la rutina, fácil y en cualquier momento:
  - Al elegir una rutina (también la recomendada) aparece el paso «Tu rutina»: los ejercicios de cada día con su miniatura. Arrastras ≡ para ordenarlos y abajo pulsas «Empezar con esta rutina».
  - Al tocar un ejercicio se abre una hoja con series (− / +), repeticiones, «Cambiar por otro ejercicio» (primero los del mismo músculo), «Pasar a otro día» y «Quitar de la rutina».
  - En Entrenar, «Editar» junto a los ejercicios del día abre la misma pantalla; en Mi plan, el «Editar» de la rutina también. Nombre, semana y días quedan en «Más opciones».
- Progreso con colores que significan algo: verde = vas bien o mejoras, ámbar = te quedas corto.
  - Arriba, 3 fichas (entrenos, duración, volumen) con el cambio frente al periodo anterior («↑ 18 %» en verde).
  - «Músculos» pasa a «Series por semana»: media semanal por grupo con la zona 10–20 dibujada; verde dentro, ámbar y «BAJO» si se queda corto.
  - Ejercicios: la línea va en verde si subes y en gris si estás estancado, con la mejora al lado («+7,5 kg»).
- Tanda de arreglos y limpieza del entreno:
  - Los avisos salen arriba, como una notificación del iPhone, y ya no tapan el descanso.
  - El iPhone ya no hace zoom al escribir la nota, el RIR/RPE o la fecha.
  - Decimales con coma en todas partes: se escribe y se ve «77,5» (también vale «77.5»). Igual en peso corporal y medidas.
  - Si publicas una versión nueva, la app espera a que termines el entreno (y cierres el resumen) para actualizarse.
  - Un solo «⋯» arriba en el entreno: reúne lo del ejercicio (unidad kg/lb, músculos, mover, quitar) y lo del entrenamiento (añadir, terminar, descartar). Se quitó el botón «Terminar» de arriba y el selector kg | lb de cada ejercicio.
  - Aviso de fin de descanso sin emoji.
  - Mi plan: ya no felicita en verde cuando faltan entrenos. Muestra «Semana: 1 de 4» en neutro o, si hoy está libre, «Mover Pierna A a hoy».
  - Los ejercicios propios se pueden editar y borrar desde su ficha.
  - En Progreso y en la ficha del ejercicio, tocar un punto del gráfico abre ese entreno para corregir un valor mal puesto.
  - Recuperar contraseña: una hoja de la app (con repetición y sin mostrarla) en lugar de la ventana gris del navegador.
- Entreno: los ejercicios ya hechos se ven igual de suaves que los pendientes (con su check verde nítido); solo el actual va en color pleno.
- Peso y repeticiones con límites: se quitan los ceros de delante (025 → 25), el peso tiene que ser mayor que 0 (salvo lastre en ejercicios de peso corporal), las repeticiones al menos 1 y hay un máximo por ejercicio basado en los récords mundiales (p. ej. peso muerto 510 kg, press de banca 360 kg, mancuernas 120 kg cada una).
- Resumen final: el botón «Listo» ahora es carmesí y el de «Comparte tu entrenamiento» pasa a una tarjeta blanca más discreta (sin brillo animado).
- Compartir: nuevo botón «Fondo» para compartir solo los datos, sin foto: transparente → oscuro → claro. El sticker ahora firma «GYM TRACKER APP» (con el punto rojo).
- Entreno: la fila de ejercicios de arriba es más ligera. Tarjetas pequeñas y en color (antes grises), solo la del ejercicio actual es grande con borde carmesí; las terminadas llevan un check verde pequeño en la esquina.
- Miniaturas de pierna (sentadilla búlgara, extensión de cuádriceps, curl femoral, pantorrillas…): se ven las dos piernas, centradas.
- Miniaturas de los ejercicios con zoom al músculo principal: primer plano del pecho, un hombro, un bíceps, la espalda, un cuádriceps, los glúteos… así cada fila se ve distinta.
- Adiós a los emojis: los récords llevan un trofeo dorado de línea fina; Progreso vacío, una flecha de tendencia en carmesí; notas con «Nota:»; los avisos van solo con texto.
- Mi plan: «Volumen semanal» ya no lleva el emoji 📊.
- Logo nuevo: pesa blanca de formas redondeadas sobre fondo carmesí en degradado (icono del iPhone, pestaña del navegador y pantalla de bienvenida).
- Resumen final: la tarjeta «Guarda tu progreso» ya no tiene el disquete ni fondo rosa. Ahora es blanca (como «Ejercicios»), con un icono de nube con check, una frase corta y «Ahora no» en gris, para que Compartir sea el protagonista.
- Mejores recomendaciones de rutina: con 5 días (intermedio/avanzado) se recomienda la nueva «Torso / Pierna + PPL», que entrena cada músculo 2 veces; con 6-7 días, Push/Pull/Legs (principiante e intermedio) o Arnold Split (avanzado). Con 7 días se sugiere dejar uno de descanso.
- Elegir rutina, rediseñada. Principiante: una sola pantalla con la rutina recomendada en grande, sus cifras (días, ejercicios, minutos), tu semana y un botón «Empezar con esta rutina»; sin la estrella. Intermedio y avanzado: lista de rutinas estilo Ajustes; la elegida se abre con días, ejercicios por día, series por semana y minutos.
- Limpieza: se quitan estilos y código de diseños anteriores que ya no se usaban (la app se ve igual, pero es más ligera).
- Entrenar: el botón de nota 📝 se sustituye por una cápsula «+ Nota» junto a Aproximación y Por lado. Al tocarla se abre la nota justo debajo; si el ejercicio ya tiene nota se ve en carmesí como «✓ Nota».
- Entrenar: «Aproximación» va siempre primero, a la izquierda, y «Por lado» después (antes cambiaba de sitio según el ejercicio).
- Entrenar: botones más pequeños y al estilo iPhone. «Aproximación» y «Por lado» son cápsulas grises («+ Aproximación») que se tiñen de carmesí al activarlas («✓ Aproximación»). El contador de series es una pastilla fina − | + con el número en la etiqueta («4 series»). El botón de nota, más pequeño.
- Compartir: nuevo botón «Color» para poner el texto en blanco o en negro. Al usar tu foto, el color se elige solo (negro si la zona detrás del texto es clara, blanco si es oscura) hasta que toques el botón. La app recuerda el color de la última vez.
- Imagen para compartir: se quita la sombra (ni halo ni el degradado oscuro de abajo); la foto queda limpia.
- Imagen para compartir: la línea de músculos bajo el volumen muestra como máximo 3 (los que más series tuvieron), para que ocupe menos.
- Compartir: se quita el botón redondo de alineación; ahora cada toque en la imagen cambia la alineación (izquierda → centro → derecha) y se ve un momento el icono. El bloque de datos también se gira con dos dedos (con imán a la posición recta). Texto de ayuda: «Toca para alinear · arrastra, pellizca o gira».
- Cerrar sesión deja el iPhone vacío (vuelve a la pantalla de bienvenida): así se puede cambiar de cuenta sin mezclar entrenos. Antes de cerrar se guarda todo en la nube, y al volver a entrar los datos regresan.
- Iniciar sesión: se quita el botón «Entrar con un código por correo» (Supabase ya no deja poner el código en el correo sin un servicio de correo propio). Se entra con correo y contraseña.
- Días de la semana: el miércoles se muestra como «M» (antes «X»).
- Botón de compartir: el subtítulo ahora dice «Crea una imagen para tus historias».
- Compartir: el bloque de datos se arrastra con el dedo y se pellizca para cambiar el tamaño (con imán al centro), un botón en la esquina cambia la alineación; «¡NUEVO PR!» sin emoji, en blanco con cápsula de cristal. Se quitan los botones de tamaño y posición.
- Imagen para compartir: línea con los músculos trabajados (p. ej. Cuádriceps · Glúteos) bajo el volumen, cápsula dorada «¡NUEVO PR!» / «¡2 NUEVOS PR!» y tamaños de texto más contenidos (la grande es la antigua mediana, y hay una nueva más pequeña).
- Pruebas automáticas guardadas en `tests/`, notas del proyecto en `CLAUDE.md` y este registro de cambios.
- Compartir: solo la plantilla sobre foto, con alineación, tamaño de texto y posición ajustables
- Resumen más limpio: chips de mejora y récords, botón de compartir con miniatura de la historia y ejercicios plegables
- Compartir estilo Strava: hoja con plantillas Tarjeta, Sobre foto (PNG transparente o tu foto) y Récord; botón protagonista en el resumen
- Quitar la barra −/+ sobre el teclado y la calculadora de discos
- Fase 3: barra −/+ sobre el teclado, calculadora de discos, compartir resumen; el descanso se detiene tras la última serie
- Mi plan rediseñado (anillo, tira semanal, próximo entreno, días en cuadrícula y volumen plegable) y títulos centrados

## 2026-09-25
- Pedir la cuenta después del primer entrenamiento, no en la configuración inicial
- Fase 2: configuración en 3 pasos, entrar con código por correo, guía de instalación y Progreso vacío
- Fase 1: temporizador de descanso, apertura instantánea sin señal, pantalla encendida y aviso de subida de peso
- Progreso con estilo de analíticas: fichas, barras de músculos y evolución por ejercicio
- Check verde en el resumen final y ocultar comparaciones de volumen poco realistas
- Nueva paleta: carmesí como color principal y dorado para logros
- Pestaña Mi plan (mover días esta semana, volumen semanal) y nuevo resumen final
- Con sesión iniciada, ocultar el respaldo manual del menú
- Contador compacto de series y botón de nota
- Sesión más limpia: carrusel vertical, atenuado intermedio y última vez compacta
- Atenuado más marcado en el carrusel de ejercicios
- Una sola serie de aproximación y carrusel centrado en el ejercicio actual
- Renombrar elevaciones de talones a elevación de pantorrillas
- Actualizaciones fiables, buscador sobre el teclado y convertir series
- Opción por lado (unilateral) en los ejercicios que lo permiten
- Buscador arriba, variantes por enfoque y series de aproximación
- Entrenamiento en modo enfoque con progresión horizontal
- Terminar entrenamiento al final y resumen motivador
- Separar la cuenta de los ajustes con un menú de perfil
- Guía muscular con cuerpo realista y vista del plan
- Kilos o libras por ejercicio y volumen en kg en lugar de toneladas
- Evitar importar dos veces el Excel si ya se importó con la versión anterior
- Configuración inicial, dos pestañas y modo simple

## 2026-09-24
- Conectar la app con el proyecto de Supabase
- Cuenta en la nube, rutina del Excel y mejoras al entrenar
- App de seguimiento del gym: rutinas, registro de entrenamientos y progreso
