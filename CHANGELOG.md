# Registro de cambios

Cada actualización de la app, de la más nueva a la más antigua.

## 2026-09-26
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
