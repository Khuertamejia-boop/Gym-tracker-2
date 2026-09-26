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
- Temporizador de descanso automático al marcar serie; se detiene tras la última serie del entreno.
- Compartir: solo plantilla "Sobre foto" (PNG transparente o sobre foto). El bloque de datos es un
  sticker: se arrastra con un dedo, con dos se pellizca (tamaño, imán al centro) y se gira (imán a recto);
  un toque cambia la alineación izquierda → centro → derecha (sin botón; el icono aparece un momento).
  Nada de botones sobre la imagen. Muestra los músculos trabajados (en texto, máx. 3: los de más series) y una cápsula
  de cristal «¡NUEVO PR!» (sin emoji, texto blanco) si hubo récords. Botón protagonista en el resumen.
- Login solo con correo y contraseña (26-09-2026): Supabase no deja editar las plantillas de correo sin SMTP
  propio, así que el botón «Entrar con un código» se ocultó. Para recuperarlo: SMTP propio (p. ej. iCloud con
  contraseña de app) + `{{ .Token }}` en "Magic Link or OTP" y "Confirm signup" + volver a poner el botón.

- Cuentas del dueño: la de **iCloud** es la principal (datos reales); la de **Gmail** es solo para probar la app.
  Al cerrar sesión se sincroniza y se vacía el dispositivo (`S.clearLocal()`), para cambiar de cuenta sin mezclar datos.

## Pendientes (al 26-09-2026)

- Confirmar en un iPhone real el giro con dos dedos y el toque para alinear del sticker de Compartir.
- Ideas de fase 4 (no pedidas aún): superseries, recordatorios los días de entreno, semana de descarga.
- Ahorro: los chats muy largos consumen muchos créditos de la nube; conviene empezar chats nuevos
  (este archivo da el contexto) y agrupar cambios pequeños en un solo mensaje.
