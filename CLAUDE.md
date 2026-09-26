# Mi Gym Tracker — notas para Claude

App web (PWA) para registrar entrenamientos de gimnasio, pensada para usarse en el iPhone.
El dueño habla español, no es técnico y usa la app en el gym: **responde siempre en español,
sin jerga**, y explica los cambios en términos de lo que verá en la pantalla.

Web publicada: https://khuertamejia-boop.github.io/Gym-tracker-2/ (GitHub Pages desde `main`).

## Cómo trabajar en este repo

1. **Publicar directamente en `main`**: el dueño pidió que cada cambio se suba y se publique
   (GitHub Pages lo sirve en ~1 minuto). No abrir PR salvo que lo pida.
2. **Antes de publicar, probar**: `tests/run.sh` (todas) o `tests/run.sh descanso` (una).
   Añade o actualiza una prueba en `tests/` cuando cambies un flujo. Revisa capturas en
   `tests/.out/` (modo claro y oscuro, ancho de iPhone 390 px).
3. **Subir la versión de la caché** en `sw.js` (`const CACHE = 'gymtrack-vN'`) en cada cambio
   de archivos de la app; si no, los iPhone siguen viendo la versión anterior. Si añades un
   archivo nuevo, inclúyelo en `SHELL`.
4. **Registrar cada actualización** (lo pidió el dueño):
   - añade una línea arriba en `CHANGELOG.md` (fecha y qué cambió, en lenguaje simple);
   - actualiza `README.md` si cambia una función;
   - si se toma una decisión de diseño o producto, anótala en "Decisiones" de este archivo.
5. Después de publicar, manda capturas al dueño y dile que, si no ve el cambio, cierre y
   vuelva a abrir la app.

## Arquitectura

Sin compilación: HTML + CSS + JavaScript (módulos ES) servidos tal cual.

- `index.html` — cabecera (título centrado + perfil), `<main id="view">`, barra de 3 pestañas, `<dialog id="sheet">`.
- `js/app.js` — toda la interfaz: pestañas **Mi plan · Entrenar · Progreso**, sesión en modo enfoque,
  resumen final, hoja de compartir, menús y ajustes. Las acciones van por `data-action` → objeto `actions`.
- `js/store.js` — estado en `localStorage` (`gymtrack.v1`), rutinas, sesiones, borrador (`draft`),
  unidades kg/lb (se guarda siempre en kg), récords, progresión, plan semanal (`weekPlan`, cambios de
  "solo esta semana" en `routine.weekOverride`), descanso (`restFor`).
- `js/cloud.js` — Supabase (tabla `gym_data`, un JSON por usuario, fusión con marcas de borrado),
  login con contraseña (el código por correo está oculto, ver Decisiones).
- `js/body.js` + `js/vendor/muscle-map/` — cuerpo realista (hombre/mujer) con músculos en rojo.
- `js/share.js` — imagen para compartir (1080×1920) dibujada en canvas.
- `js/charts.js` — Chart.js (CDN jsdelivr): líneas y mini-gráficos de evolución.
- `js/data/` — catálogo de ejercicios, músculos por ejercicio y plantillas de rutinas.
- `sw.js` — funciona sin señal: abre desde la caché y descarga versiones nuevas en segundo plano.

## Estilo y preferencias del dueño

- **Estilo Apple**: limpio, elegante, mucho aire, tipografía del sistema, números grandes con etiquetas
  pequeñas en mayúsculas espaciadas. "Diseño por encima de todo".
- **Poca información en pantalla**: prefiere plegar/ocultar detalles (se abren al tocar).
  Rechazó por recargados: barra −/+ sobre el teclado y calculadora de discos.
- Colores: **carmesí** principal (`--accent`), **dorado** para logros (`--gold`), **verde** para
  completado (series hechas, check del resumen).
- Enseñar maquetas/propuestas antes de cambios grandes de diseño; implementar directo si pide "hazlo".

## Decisiones

- 3 pestañas; la app abre en **Entrenar**. Mi plan: anillo semanal, tira L–D, próximo entreno,
  días de entreno en 2×2 y volumen semanal plegado (zona 10–20 series para hipertrofia).
- La cuenta **no** se pide en la configuración inicial: se ofrece tras el 1.er entrenamiento (y el 5.º y 15.º).
  Tarjeta «Guarda tu progreso» (opción A, 26-09-2026): fondo neutro, icono de nube con check (línea carmesí sobre círculo
  suave), una frase y «Ahora no» en gris; nada rosa ni rojo que compita con el banner de Compartir.
- Controles del ejercicio (estilo iPhone): «Aproximación» y «Por lado» son cápsulas pequeñas «+ …» que se tiñen
  de carmesí con «✓» al activarlas (sin interruptor verde); contador de series tipo UIStepper (− | +, sin sombra) con
  el número en la etiqueta «4 series». Elegido entre 3 maquetas (26-09-2026).
  Orden de cápsulas: «Aproximación» siempre la primera (izquierda), «Por lado» y «Nota» (sustituye al 📝;
  «✓ Nota» en carmesí si hay texto; la nota se abre bajo las cápsulas).
- Temporizador de descanso automático al marcar serie; se detiene tras la última serie del entreno.
- Compartir: solo plantilla "Sobre foto" (PNG transparente o sobre foto). El bloque de datos es un
  sticker: se arrastra con un dedo, con dos se pellizca (tamaño, imán al centro) y se gira (imán a recto);
  un toque cambia la alineación izquierda → centro → derecha (sin botón; el icono aparece un momento).
  Nada de botones sobre la imagen. Sin sombra detrás del texto (se probó un halo que seguía al sticker y el dueño lo descartó).
  Color del texto: 4.º botón «Color» (blanco/negro, `INKS` en `js/share.js`); con foto, automático
  (`autoInk`: brillo de la zona bajo el sticker) hasta que el dueño toque el botón. Se recuerda en `shareLayout.color`. Muestra los músculos trabajados (en texto, máx. 3: los de más series) y una cápsula
  de cristal «¡NUEVO PR!» (sin emoji, texto blanco) si hubo récords. Botón protagonista en el resumen.
- Login solo con correo y contraseña (26-09-2026): Supabase no deja editar las plantillas de correo sin SMTP
  propio, así que el botón «Entrar con un código» se ocultó. Para recuperarlo: SMTP propio (p. ej. iCloud con
  contraseña de app) + `{{ .Token }}` en "Magic Link or OTP" y "Confirm signup" + volver a poner el botón.
- Elegir rutina (26-09-2026): principiante → pantalla «A» (solo la recomendada, en grande: etiqueta «RECOMENDADA PARA TI»
  sin estrella, 3 cifras DÍAS · EJERCICIOS · MINUTOS, tira «Tu semana», botón «Empezar con esta rutina»); intermedio/avanzado
  (o «Ver otras opciones») → lista «B» estilo Ajustes con selección redonda; la elegida se abre con días, ejerc./día,
  series/semana y minutos (≈ 3 min por serie). Nada de emojis decorativos: rompen la armonía visual
  (26-09-2026 se quitaron todos: récords con `ICON_TROPHY` dorado de línea, iconos de línea en círculo `--accent-soft`, avisos solo texto; ✓ sí se usa).
- Recomendación de rutina (26-09-2026, `recommendTemplate` en `js/store.js`): 1-3 días → Full Body; 4 → Torso/Pierna;
  5 → Torso/Pierna (principiante) o «Torso / Pierna + PPL» (resto); 6-7 → PPL (principiante/intermedio) o Arnold (avanzado).
  La semana es fija (no rota): un ciclo de 3 días (PPL, Arnold) con 5 días deja la pierna 1 vez/semana, por eso no se usa con 5.
  Con 7 días se avisa de dejar uno de descanso.
- Logo (26-09-2026, opción A de 4): pesa blanca redondeada sobre degradado carmesí (#e8354b → #a50d24), estilo iconos de Apple.
  `icons/icon.svg` lleva esquinas redondeadas (favicon, bienvenida); los PNG (`icon-180` para iPhone, 192, 512) van
  cuadrados a sangre porque iOS/Android recortan las esquinas. Reutilizar la misma pesa en la app de Xcode.
- Miniaturas de ejercicios (26-09-2026): zoom automático al músculo principal (`zoomBox` en `js/body.js`, cajas medidas
  en `BOXES`; brazos y hombros se enfocan en un solo lado; piernas, las dos y centradas, lo pidió el dueño). Ilustraciones por ejercicio y cuerpo 3D girable
  quedan para la app de Xcode (en la web solo hay dibujos de frente y espalda).
- Cuentas del dueño: la de **iCloud** es la principal (datos reales); la de **Gmail** es solo para probar la app.
  Al cerrar sesión se sincroniza y se vacía el dispositivo (`S.clearLocal()`), para cambiar de cuenta sin mezclar datos.

## Plan: app nativa para iOS (decidido el 26-09-2026)

- El dueño hará después una **app nativa en Xcode (SwiftUI)** con Claude integrado en Xcode (26.3+, plan Pro, por tandas).
  La web es la **maqueta viva**: primero se terminan los detalles visuales pendientes y luego se **congela**
  (solo arreglos). Web y app son desarrollos independientes (JS vs Swift); se comparten diseño, decisiones y datos.
- Datos de la app: recomendado **iCloud (CloudKit/SwiftData)**: gratis a cualquier escala, sin cuentas ni correos,
  sincroniza solo los cambios. El dueño **no quiere pagar Supabase Pro (25 $/mes)**.
- Supabase gratis se queda **solo para la web** mientras dura el desarrollo. No se pausa si se usa al menos una vez
  cada 7 días (si se pausa: «Restore» en el panel, sin perder datos). La sincronización actual sube/baja el JSON
  completo, pero con 1–2 usuarios es ~1 % del límite: **no cambiarla**.
- Importar el historial de la web a la app una vez (exportar JSON desde la web → importar en la app).
  Ojo: «Respaldo de datos» (exportar) solo aparece en el menú sin sesión; habrá que mostrarlo también con sesión.

## Pendientes (al 26-09-2026)

- Confirmar en un iPhone real el giro con dos dedos y el toque para alinear del sticker de Compartir.
- **Siguiente paso del dueño:** mandar en un solo mensaje su lista de detalles visuales para simplificar la web
  (quitar información, más limpio). Hacerlos en una tanda, con maquetas si son cambios grandes; después, congelar la web.
- Opcional: hacer más pequeños los enlaces «+ Aproximación / Quitar» bajo las filas de aproximación (lo ofrecí; sin respuesta).
- Cuando empiece con Xcode: preparar un documento con el plan de la app (pantallas, datos, estilo, orden de trabajo).
- Ideas de fase 4 (no pedidas aún): superseries, recordatorios los días de entreno, semana de descarga.
- Ahorro: los chats muy largos consumen muchos créditos de la nube; conviene empezar chats nuevos
  (este archivo da el contexto) y agrupar cambios pequeños en un solo mensaje.
