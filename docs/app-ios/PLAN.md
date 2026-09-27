# Mi Gym Tracker para iPhone — plan de la app (SwiftUI)

Este documento es el punto de partida de la app nativa. Está pensado para dos lectores:

- **El dueño**, que no es técnico: el resumen de cada fase dice qué verá al terminarla.
- **Claude en Xcode**: todo lo demás son instrucciones y reglas.

**Cómo usarlo:** copia este archivo a la carpeta del proyecto de Xcode con el nombre `CLAUDE.md`, junto con la carpeta
`datos/`. Claude lo leerá solo en cada conversación.

---

## 0. Instrucciones para Claude (Xcode)

- **Idioma:** responde siempre en **español, sin jerga**. El dueño no es técnico: explica cada cambio por lo que verá
  en la pantalla del iPhone y dile qué botón pulsar en Xcode (▶ para probar, qué simulador elegir…).
- **Por tandas:** el dueño trabaja con el plan Pro, con límite de uso. Haz una fase (o media) por conversación, deja todo
  compilando al terminar y apunta lo pendiente en la sección 9. Conversaciones cortas: este archivo da el contexto.
- **Maqueta viva:** la web publicada es la referencia de diseño y comportamiento:
  <https://khuertamejia-boop.github.io/Gym-tracker-2/> (código en el repo `khuertamejia-boop/Gym-tracker-2`).
  Si hay dudas sobre cómo debe verse o comportarse algo, la web manda, salvo lo que esta guía cambie a propósito
  (sección 7). **La web está congelada:** solo se arreglan errores.
- **Nada de dependencias externas** (sin CocoaPods ni paquetes SPM de terceros) salvo que sea imprescindible;
  todo con frameworks de Apple: SwiftUI, SwiftData, CloudKit, Swift Charts, ActivityKit, UserNotifications, PhotosUI.
- **Estilo Apple** (sección 4): antes de un cambio grande de diseño, describe o enseña la propuesta; si el dueño dice
  «hazlo», impleméntalo directo.
- **Probar antes de dar algo por hecho:** que compile sin avisos nuevos, probarlo en el simulador (iPhone de 6,1″) en
  claro y oscuro, y añadir pruebas (Swift Testing) para la lógica de la sección 5.
- **Registro:** mantén un `CHANGELOG.md` (fecha y qué cambió, en lenguaje simple) y anota aquí, en la sección 8,
  cada decisión de diseño o producto nueva.

## 1. Qué es la app

App para registrar entrenamientos de gimnasio y ver el progreso, pensada para usarse **en el gym, con una mano**.

- Eliges una **rutina** (recomendada según tu experiencia y los días que entrenas) y la personalizas.
- Cada día tienes tu entreno: anotas **peso y repeticiones** por serie, con **descanso automático** entre series.
- La app te sugiere cuánto subir (doble progresión), detecta **récords** y te enseña tu **progreso**.
- Compartes el entreno como imagen para historias.

Tres pestañas: **Mi plan · Entrenar · Progreso**. La app abre en **Entrenar**.

## 2. Decisiones técnicas

| Tema | Decisión |
|---|---|
| Interfaz | **SwiftUI**, iOS **18** como mínimo, solo iPhone y vertical al principio. |
| Datos | **SwiftData**, sincronizado con **iCloud (CloudKit)**: gratis, sin cuentas ni correos; cada persona usa su iCloud. |
| Gráficos | **Swift Charts**. |
| Descanso | Notificación local al acabar el descanso + **Live Activity** (pantalla bloqueada e isla dinámica) con cuenta atrás. |
| Recordatorios | Notificaciones locales programadas los días de entreno (hora a elegir en Ajustes). |
| Vibración | `sensoryFeedback` / `UINotificationFeedbackGenerator` al marcar serie, récord y fin de descanso. |
| Compartir | Imagen 1080×1920 con `ImageRenderer`, foto con `PhotosPicker`, envío con `ShareLink`. |
| Mapa muscular | Reutilizar las ilustraciones de la web (`js/vendor/muscle-map`, licencia **MIT**: conservar el aviso). |
| Sin servidor | Nada de Supabase en la app (la web lo sigue usando mientras exista). |

**Cuenta de Apple.** Con un Apple ID gratuito se puede instalar la app en tu propio iPhone para probarla (caduca a los
7 días y hay que volver a instalarla desde Xcode). Para **iCloud (CloudKit)**, **TestFlight** y la **App Store** hace
falta el **Apple Developer Program** (de pago, anual). Confírmalo en developer.apple.com al llegar a la fase 8. Hasta
entonces, SwiftData funciona solo en el teléfono, sin iCloud.

**Reglas de SwiftData con CloudKit** (para no tener que rehacer los modelos después):

- todas las propiedades con valor por defecto u opcionales;
- relaciones opcionales;
- sin `@Attribute(.unique)`.

Los identificadores (`id: String`) se guardan como campo normal.

## 3. Datos

### 3.1 Catálogo (fijo, dentro de la app)

La carpeta `datos/` trae el catálogo **exportado de la web**. Añádela al proyecto como recursos y léela al arrancar:

- `ejercicios.json`: `exercises` (114, cada uno con `id`, `name`, `muscle` = grupo en español, `equipment`, `aliases`,
  `family`), `muscles` (los 11 grupos del buscador), `unilateral` (ejercicios que se pueden anotar «por lado»:
  `true` = por lado por defecto) y `families` (variantes de un mismo ejercicio, p. ej. prensa · cuádriceps / glúteos).
- `musculos.json`: `byExercise[exId] = [[principales], [secundarios]]` con grupos del mapa (`chest`, `lats`,
  `upper_back`, `shoulders`, `biceps`, `triceps`, `forearms`, `abs`, `obliques`, `lower_back`, `glutes`, `quads`,
  `hamstrings`, `calves`), `names` (nombre en español de cada grupo), `byCategory` (para ejercicios propios, según
  su grupo muscular), `backGroups` y `lowerGroups`.
- `plantillas.json`: las 6 rutinas (`key`, `name`, `description`, `daysPerWeek`, `days[{name, exercises[{exId, sets,
  reps}]}]`, `week` = 7 posiciones L→D con el índice del día o `null`).

### 3.2 Modelos (SwiftData)

Nombres orientativos; lo importante son los campos (son los de la web, para poder importar):

- **Profile**: `level` (`beginner` | `intermediate` | `advanced`), `days` ([0…6], 0 = lunes), `gender` (`male` |
  `female`, para el cuerpo del mapa), `simple` (modo sencillo).
- **Settings**: `unit` (`kg` | `lb`), `effort` (`RIR` | `RPE` | nada), `restTimer` (activo), `rest[exId]` (segundos),
  `units[exId]` (unidad por ejercicio), `unilateral[exId]`, `shareLayout` (alineación, color, fondo, posición).
- **Routine**: `id`, `name`, `fromTemplate`, `days[RoutineDay]`, `week[7]` (id de día o vacío), `weekOverride`
  (`weekStart` + `week`, solo esa semana), `activo`.
- **RoutineDay**: `id`, `name`, `order`, `exercises[RoutineExercise]`.
- **RoutineExercise**: `exId`, `sets`, `reps` (texto: «6-8»), `order`.
- **Session** (entreno hecho): `id`, `date` (AAAA-MM-DD), `startedAt`, `finishedAt`, `editedAt`, `routineId`,
  `dayName`, `exercises[SessionExercise]`.
- **SessionExercise**: `exId`, `target` (reps objetivo), `note`, `warmup[{kg, reps}]`, `sets[SetEntry]`, `order`.
- **SetEntry**: `kg` (**siempre en kg**), `reps`, `effort`, `side` (`L` | `R` | vacío), `pr` (`peso` | `1RM` | vacío),
  `order`.
- **BodyEntry**: `date`, `weight` (kg), `bodyfat`, `waist`, `chest`, `arm`, `thigh`, `hip` (cm).
- **CustomExercise**: `id` (`c-…`), `name`, `muscle`, `equipment`, `hidden` (borrado).
- **Draft** (entreno en curso): se guarda en disco en cada toque, para no perderlo nunca si la app se cierra.

### 3.3 Importar el historial de la web (una vez)

En la web: menú del perfil → **Respaldo de datos** → **Descargar copia (.json)**. En la app: Ajustes → **Importar
desde la web**, que abre el archivo con `fileImporter`. El JSON es el estado completo de la web:
`{ version, profile, settings, routines, activeRoutineId, sessions, body, customExercises, deletedIds, … }`,
con los mismos campos que la sección 3.2. Hay que:

- ignorar `draft` y `deletedIds`;
- no duplicar sesiones: si el `id` ya existe, se salta;
- mantener los kg tal cual.

Enseña un resumen antes de confirmar: «54 entrenos, 2 rutinas, 12 registros corporales».

## 4. Estilo

- **Estilo Apple**: limpio, mucho aire, tipografía del sistema (SF), **números grandes con etiquetas pequeñas en
  MAYÚSCULAS espaciadas** («4 / DÍAS»). «Diseño por encima de todo».
- **Poca información en pantalla**: plegar u ocultar detalles, que se abren al tocar. Nada recargado.
- **Sin emojis decorativos.** Iconos de línea (SF Symbols). Para logros, trofeo dorado de línea (`trophy`).
  El ✓ sí se usa.
- **Colores** (claro / oscuro), definidos como colores del catálogo de recursos:

| Nombre | Claro | Oscuro | Uso |
|---|---|---|---|
| accent (carmesí) | `#C8102E` | `#D9233A` | botones principales, selección, marca |
| accentSoft | `#FBE1E4` | `#361519` | fondos suaves de iconos |
| good (verde) | `#0C8A0C` | `#0CA30C` | completado, series hechas, «vas bien / mejoras» |
| goodSoft | `#DFF2DF` | `#15321A` | fondo de filas hechas, cápsulas «↑» |
| warn (ámbar) | `#EDA100` | `#E7A92E` | «te quedas corto» (siempre con texto «BAJO») |
| gold | `#B8861B` | `#E0B04A` | récords y logros |
| bg | `#F4F4F2` | `#101112` | fondo |
| surface | `#FCFCFB` | `#1A1A19` | tarjetas |
| surface2 | `#EFEEEB` | `#242423` | campos, cápsulas |
| border | `#E0DFDB` | `#2F2F2D` | separadores |
| text / text2 / text3 | `#0B0B0B` / `#52514E` / `#7A7974` | `#FFFFFF` / `#C3C2B7` / `#8F8E86` | textos |

- **Logo:** pesa blanca redondeada sobre degradado carmesí (`#E8354B` → `#A50D24`). Parte de `icons/icon.svg` de la
  web y exporta un PNG de 1024×1024 **cuadrado, sin esquinas redondeadas** (iOS las recorta solo).
- Controles al estilo iPhone: cápsulas «+ Aproximación» y «+ Nota» que se tiñen de carmesí con «✓» al activarse;
  contador tipo `Stepper` (− | +) para el número de series; listas agrupadas como en Ajustes.

## 5. Reglas de la app (portar tal cual y cubrir con pruebas)

- **Recomendación de rutina** (`recommendTemplate`):
  - 1–3 días → Full Body;
  - 4 → Torso/Pierna;
  - 5 → Torso/Pierna (principiante) o «Torso / Pierna + PPL» (resto);
  - 6–7 → PPL (principiante e intermedio) o Arnold (avanzado).

  La semana es fija: los días de la plantilla se reparten en orden sobre los días elegidos. Con 7 días, avisar de dejar
  uno de descanso.
- **Doble progresión** (`progressionHint`): se mira la última vez que hiciste el ejercicio y el rango de repeticiones
  (el objetivo del día, p. ej. «8-10»).
  - Si todas las series al peso máximo llegaron al tope del rango, toca **subir**: +2,5 kg (+1 kg si pesa menos de 20 kg).
    En libras, +5 lb (+2,5 lb por debajo de 45 lb).
  - Si alguna quedó por debajo del mínimo, se **mantiene** el peso hasta llegar al mínimo.
  - Si no, **mismo peso y más repeticiones**.
  - Al subir, la sesión muestra «↑ +2,5 kg · la última vez completaste todas las reps».
- **Récords** (`prType`): no cuentan la primera vez que haces un ejercicio. Una serie es récord de **peso** si supera tu
  máximo; si no, lo es de **1RM** si supera tu mejor 1RM estimado (fórmula de Epley:
  `kg × (1 + reps/30)`, o el mismo kg con 1 rep). También cuentan las series ya hechas en el entreno en curso.
- **Volumen** = kg × reps de las series hechas. En ejercicios «por lado», cada par I/D cuenta como una serie en los
  recuentos de series.
- **Series por semana** (Mi plan y Progreso): un músculo principal suma 1 serie y uno secundario ½.
  - Zona recomendada: **10–20 series por semana**.
  - En Progreso se muestra la media semanal del periodo (1M · 3M · 1A · Todo), por grupo (media de sus músculos):
    Pecho, Espalda (dorsales + espalda alta), Hombros, Brazos (bíceps + tríceps), Piernas (cuádriceps + femorales +
    glúteos) y Core.
- **Descanso por defecto**: tope del rango ≤ 6 reps → 150 s; ≤ 10 → 120 s; resto → 90 s. Es ajustable por ejercicio
  (±15 s) y se recuerda. Arranca solo al marcar una serie y no se pone tras la última serie del entreno.
- **Límites al anotar**:
  - sin ceros delante;
  - peso mayor que 0 (0 = «sin lastre» solo en ejercicios de peso corporal);
  - reps de 1 a 100 (hasta 500 en peso corporal);
  - peso máximo por ejercicio algo por encima del récord mundial: peso muerto y sentadilla 510, banca 360, militar 230,
    prensa 1200;
  - o, si no hay récord, según el equipo: barra 360, mancuernas 120 cada una, máquina 400, Smith 500, polea 250,
    lastre 200.

  Al pasarse, se ajusta al máximo y se avisa. La tabla completa está en `maxKg` de `js/store.js` en la web.
- **Decimales con coma** («77,5»): se muestran con coma y se aceptan coma o punto. Siempre se guarda en kg, aunque el
  ejercicio se muestre en libras.

## 6. Pantallas (qué hace cada una)

1. **Bienvenida y configuración (3 pasos)**
   - Paso 1: experiencia (menos de 6 meses / de 6 meses a 2 años / más de 2 años) y cuerpo del mapa (hombre / mujer).
   - Paso 2: días que entrenas.
   - Paso 3: elegir rutina:
     - **principiante**: solo la recomendada, en grande. Etiqueta «RECOMENDADA PARA TI», tres cifras DÍAS · EJERCICIOS ·
       MINUTOS, tira «Tu semana» y botón «Empezar con esta rutina». Debajo, «Ver otras opciones»;
     - **intermedio y avanzado**: lista estilo Ajustes con selección redonda. La elegida se abre con días, ejercicios
       por día, series por semana y minutos.

   Después viene **«Tu rutina»**, el editor (punto 7), y se termina con «Empezar con esta rutina».
2. **Entrenar**
   - Texto «Sábado · hoy toca Torso A» y cápsulas con los días de la rutina.
   - Lista de ejercicios del día con miniatura del músculo, «4 series · 6-8 reps · 60 kg» y un botón **Editar**.
   - Botón «Empezar Torso A» y «+ Entrenamiento libre».
3. **Entreno en curso (modo enfoque, sin pestañas)**
   - Arriba: cronómetro y un **solo «⋯»**:
     - para el ejercicio actual: unidad kg/lb, ver músculos, mover, quitar;
     - para el entreno: añadir ejercicio, terminar, descartar.
   - Carrusel de miniaturas: la del ejercicio actual es grande con borde carmesí; las demás, pequeñas y suaves; las
     hechas llevan un check verde.
   - Nombre del ejercicio, «Serie 2 de 4 · objetivo 6-8 reps», «ÚLTIMA VEZ 75 kg × 8 · 8 · 8» y la línea de progresión.
   - Cápsulas: + Aproximación, + Por lado (si aplica), + Nota.
   - Tabla por serie con número, reps, peso, RIR (si está activo) y ✓. Una fila hecha se pone verde; un récord pone el
     trofeo en lugar del número.
   - Contador de series − | +.
   - Botón inferior que guía: «Marcar todas las series» → «Siguiente: …» → «Terminar entrenamiento».
   - Barra de descanso (−15 · tiempo · +15 · Saltar).
   - Deslizar a los lados cambia de ejercicio. Los avisos salen arriba, como una notificación.
4. **Resumen al terminar**
   - Check verde grande y «Entrenamiento completado» con el día y la fecha.
   - Fichas de tiempo, series y volumen, y cápsulas «↑ X % volumen» y «N récords» (dorado).
   - Tarjeta discreta «Comparte tu entrenamiento», ejercicios plegados, «Esta semana ●●○○ 1 de 4» y botón **Listo**
     en carmesí.
5. **Compartir**: imagen de historia con un «sticker» de datos: día y fecha, cuerpo con los músculos, volumen, los
   3 músculos con más series, tiempo, series, cápsula «¡NUEVO PR!» si hubo récords y la firma «● GYM TRACKER APP» con
   el punto rojo.
   - El sticker se arrastra, se pellizca para cambiar el tamaño (con imán al centro) y se gira (con imán a recto).
     Un toque cambia la alineación. No hay botones sobre la imagen.
   - Botones: Compartir, Guardar, Usar mi foto, **Fondo** (transparente → oscuro → claro) y **Color** (texto blanco o
     negro; con foto se elige solo según el brillo).
6. **Mi plan**
   - Anillo semanal «1/4» y tira L–D. Al tocar un día libre, puedes mover un entreno solo esta semana.
   - Tarjeta del próximo entreno. El verde solo aparece con la semana completa; si no, «Semana: 1 de 4» o
     «Mover Pierna A a hoy».
   - Días de la semana en una cuadrícula 2×2 y volumen semanal plegado.
7. **Editor de rutina** (el mismo en tres sitios: tras elegir rutina, «Editar» en Entrenar y «Editar» en Mi plan)
   - Cápsulas de días y filas con miniatura y «4 × 6-8». ≡ para arrastrar y ordenar (`onMove`).
   - Al tocar una fila se abre una hoja con:
     - series (−/+) y repeticiones;
     - cambiar por otro ejercicio (buscador filtrado por el mismo músculo);
     - pasar a otro día;
     - quitar.
   - Nombre, semana y días plegados en «Más opciones».
8. **Progreso** (periodo 1M · 3M · 1A · Todo)
   - Fichas de entrenos, duración y volumen, con el cambio frente al periodo anterior (verde «↑» si sube).
   - «Series por semana» con la franja 10–20: verde dentro, ámbar con «BAJO» si te quedas corto.
   - Evolución de cada ejercicio: línea verde si mejora y gris si está estancado, con cápsula «+7,5 kg». Al tocar un
     punto se abre ese entreno para corregirlo.
   - Constancia (cuadrícula de semanas y racha), peso corporal y medidas, e historial.
9. **Ficha de ejercicio**: pestañas Acerca de (cuerpo frente y espalda, músculos, equipo, unidad, vídeo de técnica en
   YouTube, añadir a un día), Historial, Gráficos y Récords. Los ejercicios propios se pueden editar y borrar.
10. **Perfil y ajustes**: cuerpo de la guía, unidad por defecto, modo sencillo, descanso, esfuerzo (RIR/RPE), tema,
    recordatorios, importar desde la web y respaldo.

## 7. Qué cambia respecto a la web (a propósito)

- **Sin cuenta ni correo**: iCloud en lugar de Supabase. Se quitan el login y la tarjeta «Guarda tu progreso».
- **Descanso con el teléfono bloqueado**: Live Activity con cuenta atrás (`Text(timerInterval:)`) y notificación al
  terminar. Vibración al acabar.
- **Recordatorios** los días de entreno.
- Gestos nativos: deslizar para borrar, arrastrar para ordenar y menús contextuales.
- Más adelante (sin prisa): ilustraciones por ejercicio, cuerpo en 3D que se gira con el dedo, widget con la semana y
  app para el Apple Watch.

## 8. Orden de trabajo (fases)

Cada fase termina con algo que el dueño puede probar en su iPhone.

1. **Proyecto y datos**
   - Crear el proyecto «GymTracker» (SwiftUI, iOS 18), los colores, el icono y los modelos SwiftData.
   - Cargar `datos/`.
   - *Verás:* la app abre con las 3 pestañas vacías y tu logo.
2. **Configuración inicial y rutinas**
   - Bienvenida, 3 pasos, recomendación y editor de rutina.
   - *Verás:* eliges y personalizas tu rutina.
3. **Mi plan y Entrenar**
   - Semana, próximo entreno, lista del día y mover días.
4. **Entreno en curso**
   - Tabla de series, límites, coma decimal, progresión, récords, aproximación, por lado, notas, borrador a prueba de
     cierres y resumen.
   - *Verás:* puedes entrenar de verdad con la app.
5. **Descanso, vibración y Live Activity**
   - Temporizador automático, notificación, pantalla bloqueada e isla dinámica.
6. **Progreso**
   - Fichas, series por semana, gráficos de cada ejercicio, constancia, cuerpo e historial.
7. **Compartir**
   - Sticker, foto, fondo y color.
8. **iCloud e importación**
   - Activar CloudKit (necesita el programa de pago), importar el JSON de la web y los recordatorios.
9. **Pulido y TestFlight**
   - Accesibilidad (VoiceOver, Dynamic Type), revisión en claro y oscuro, y subir a TestFlight para probar como una
     app normal.

## 9. Pendientes y decisiones nuevas

*(Claude: apunta aquí lo que quede a medias y cada decisión nueva que tome el dueño.)*

- Pedidas para más adelante: **superseries** y **semana de descarga** (enseñar una maqueta antes).
