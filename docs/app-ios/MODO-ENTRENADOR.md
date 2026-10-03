# Modo entrenador — rutinas por enlace y código (app de iPhone)

Un entrenador arma una rutina en su iPhone y se la manda a su alumno por WhatsApp. El alumno descarga la app, pega el
mensaje y la rutina queda lista en su plan. **Sin servidor, sin cuentas y sin costo:** la rutina entera viaja dentro
del enlace.

**Para el dueño, al terminar verás:**

- en Ajustes, un interruptor **Modo entrenador**;
- al activarlo, **Mis rutinas de entrenador**: crear, editar, renombrar, duplicar, borrar y **Compartir**;
- en la app del alumno, **«Tengo una rutina»** (bienvenida y Mi plan): pega el mensaje, ve la vista previa y la agrega.

Lo que ya está hecho en el repo de la web (no hay que tocarlo desde Xcode):

- `r/index.html`: la página que abre el enlace (vista previa, «Copiar código», botón del App Store, «Abrir en la app»);
- `r/codigo.js`: el formato de referencia en JavaScript (si hay dudas, este archivo manda);
- `docs/app-ios/datos/codigo-rutina/`: un ejemplo y su código para las pruebas de Swift.

Cuando la app esté en el App Store, hay que poner su enlace en `APP_STORE_URL` dentro de `r/index.html`.

---

## 1. Flujo del entrenador

1. **Ajustes → Modo entrenador** (interruptor visible, con la frase «Crea rutinas y compártelas con tus alumnos»).
   Al desactivarlo, la sección se oculta pero **las rutinas guardadas no se borran**.
2. **Mis rutinas de entrenador** (lista estilo Ajustes, la más reciente arriba; cada fila: nombre y «4 días · 25 ejercicios»).
   - **Nueva rutina**: empieza vacía o desde una plantilla y se edita con el **mismo editor de rutina** de la app.
   - Tocar una fila la abre en el editor; los cambios se guardan solos.
   - Menú contextual / deslizar: **Renombrar**, **Duplicar** («copia» al final del nombre), **Compartir**, **Borrar**
     (con confirmación).
   - Estas rutinas **no** aparecen en Mi plan ni en Entrenar: son plantillas del entrenador.
3. **Compartir** abre una hoja corta:
   - «Tu nombre» (se pide la primera vez y se recuerda en Ajustes);
   - «Para» (alumno, opcional; se recuerda el último usado en esa rutina);
   - «Nota para el alumno» (opcional, hasta 500 caracteres);
   - botón **Compartir** → `ShareLink` con el mensaje (sección 3). Debajo, «Copiar enlace» y «Copiar código».
4. En cada ejercicio del editor, solo en rutinas de entrenador, aparece «Nota para el alumno» (hasta 200 caracteres)
   y el descanso en segundos (opcional).

Límites en el editor (los mismos del formato, sección 4): hasta 7 días, 30 ejercicios por día y 150 en total; nombre
de rutina hasta 60 caracteres y nombre de día hasta 40. Si se pasa, avisar con texto, sin bloquear de golpe.

## 2. Flujo del alumno

- **Dónde está «Tengo una rutina»:**
  - en la bienvenida, como opción secundaria («Tengo una rutina de mi entrenador»);
  - en Mi plan (junto a «Editar» de la rutina);
  - en Ajustes.
- **Pantalla «Tengo una rutina»:**
  - un `PasteButton` (no muestra el aviso de permiso del portapapeles) y un campo de texto para pegar a mano;
  - acepta el **código solo, el enlace o el mensaje de WhatsApp completo**: se busca el código dentro del texto.
- **Enlace directo:** la app registra el esquema `gymtracker` y abre `gymtracker://rutina?c=<código>` con `onOpenURL`
  (es lo que usa «Ya tengo la app: abrir la rutina» de la página web).
- **Vista previa:**
  - «RUTINA DE CARLOS RÍOS», nombre, «Para Luis», cifras DÍAS · EJERCICIOS · SERIES / SEM;
  - la nota del entrenador, los días plegados con sus ejercicios.
- **Botones:**
  - **Empezar con esta rutina**: la crea y la activa;
  - **Guardar sin activar**;
  - **Cancelar**.
- **Nunca se sobrescribe** una rutina existente. Si ya hay una con el mismo nombre, se añade « (2)».
- **Durante la configuración inicial:**
  - si el alumno importa la rutina en la bienvenida, se salta el paso «elegir rutina»;
  - siguen el paso 1 (experiencia y cuerpo) y, si el código no trae semana, el paso 2 (días).
- **Errores:** mensajes amables (sección 4.4), nunca un error técnico.

### 2.1 Cómo se guarda lo importado (modelos de PLAN.md, sección 3.2)

| Del código | En la app |
|---|---|
| `n` | `Routine.name` |
| — | `Routine.fromTemplate = "coach"` |
| `c`, `m` | campos nuevos opcionales `Routine.coachName`, `Routine.coachNote` (se ven en Mi plan, plegados) |
| `d[].n` | `RoutineDay.name` (en orden) |
| `d[].e[]` `i`, `s`, `r` | `RoutineExercise.exId`, `sets`, `reps` (sin `r` → reps vacío) |
| `d[].e[].o` | campo nuevo opcional `RoutineExercise.coachNote` (texto pequeño bajo el ejercicio en Entrenar y en el entreno) |
| `d[].e[].t` | `Settings.rest[exId]` **solo si el alumno no tiene ya un descanso propio** para ese ejercicio |
| `w` | `Routine.week` (índice de día → id del día). Sin `w`: repartir los días en orden sobre `Profile.days` (como las plantillas) |
| `x` | `CustomExercise` nuevo (id `c-…` propio de la app). Si ya existe uno con el mismo nombre normalizado y músculo, se reutiliza. Los `exId` de la rutina se cambian al id nuevo. |

Ejercicio con `exId` que no está en el catálogo de esta versión de la app (y no es propio): se omite y la vista previa
avisa «1 ejercicio no está disponible en tu versión. Actualiza la app.».

## 3. El mensaje que se comparte

```
Hola Luis, te dejo tu rutina «Hipertrofia 4 días» 💪
1) Descarga GymTracker: https://khuertamejia-boop.github.io/Gym-tracker-2/r/#GT1-…
2) Ábrela, toca «Tengo una rutina» y pega este mensaje.
— Carlos
```

- El enlace lleva el código completo después del `#`. Así **el enlace es también el código**: el alumno copia el
  mensaje entero (mantener pulsado → Copiar en WhatsApp) y la app lo encuentra dentro. Es más fácil que seleccionar un
  código de 500–750 caracteres a mano.
- Sin «Hola Luis» si no hay alumno; sin «— Carlos» si no hay nombre.
- «Copiar código» (en la hoja de compartir y en la página del enlace) copia solo `GT1-…`, por si el alumno lo prefiere.
- Lo que va después de `#` nunca llega a ningún servidor (ni a GitHub).

## 4. Formato del código «GT1» (versión 1)

```
GT1-<datos>.<control>
```

| Parte | Qué es |
|---|---|
| `GT1-` | prefijo y versión del formato |
| `<datos>` | JSON en UTF-8 → comprimido con **DEFLATE crudo** (RFC 1951, sin cabecera zlib) → **base64url sin relleno** (`-` y `_` en vez de `+` y `/`, sin `=`) |
| `.` | separador (no existe en base64url) |
| `<control>` | 6 cifras hex en minúsculas: **FNV-1a de 32 bits** sobre los bytes ASCII de `<datos>`, quedándose con los 24 bits bajos (`hash & 0xFFFFFF`, `%06x`) |

FNV-1a: `h = 0x811C9DC5`; por cada byte `b`: `h = (h XOR b) × 0x01000193` (módulo 2³²).

### 4.1 El JSON

```json
{
  "v": 1,
  "n": "Hipertrofia 4 días",
  "c": "Carlos Ríos",
  "a": "Luis",
  "m": "Semana 1: deja 2 reps en reserva.",
  "w": [0, 1, null, 2, 3, null, null],
  "d": [
    { "n": "Torso A", "e": [ { "i": "press-banca", "s": 4, "r": "6-8", "t": 150, "o": "Pausa de 1 s abajo" } ] }
  ],
  "x": { "c-hip-thrust-banda": { "n": "Hip thrust con banda", "g": "Glúteos", "q": "Banda" } }
}
```

| Clave | Obligatoria | Qué es | Reglas |
|---|---|---|---|
| `v` | sí | versión | `1`. Mayor que 1 → error «actualiza la app» |
| `n` | sí | nombre de la rutina | 1–60 caracteres |
| `c` | no | nombre del entrenador | ≤ 40 |
| `a` | no | nombre del alumno | ≤ 40 |
| `m` | no | nota del entrenador | ≤ 500, admite saltos de línea |
| `w` | no | semana L→D | 7 posiciones: índice de `d` o `null` |
| `d` | sí | días | 1–7 días |
| `d[].n` | sí | nombre del día | 1–40 |
| `d[].e` | sí | ejercicios del día | 1–30 por día, 150 en total |
| `e.i` | sí | id del ejercicio | `^[a-z0-9][a-z0-9-]{0,59}$`; los del catálogo (`ejercicios.json`) o `c-…` definidos en `x` |
| `e.s` | sí | series | entero 1–20 |
| `e.r` | no | repeticiones | `"8"` o `"6-8"` (1–3 cifras, mínimo ≥ 1, máximo ≥ mínimo). Se aceptan `–`/`—` y espacios al leer, se guardan como `-` sin espacios |
| `e.t` | no | descanso en segundos | entero 0–600 (0 o ausente = el de la app) |
| `e.o` | no | nota del ejercicio | ≤ 200 |
| `x` | no | ejercicios propios | ≤ 50; clave `c-…`; `n` 1–60, `g` uno de los 11 grupos de `ejercicios.json → muscles`, `q` equipo ≤ 30 |

- Textos: se quitan los caracteres de control (salvo el salto de línea) y los espacios de los extremos. Los límites se
  cuentan en caracteres, no en bytes.
- Claves desconocidas: **se ignoran** (así una versión futura puede añadir campos sin romper las anteriores).
- Al **crear** el código, solo se escriben las claves con valor y solo los `x` que se usan.

### 4.2 Límites de seguridad al leer

- Código completo: máximo 12 000 caracteres.
- JSON descomprimido: máximo **65 536 bytes**. Descomprimir con un búfer de salida limitado; si se llena, es error
  (protege de «bombas» de compresión).
- Los textos del código se muestran siempre como texto normal (`Text`), nunca como Markdown ni HTML.

### 4.3 Buscar el código dentro de un texto

1. Buscar `GT([0-9])-([A-Za-z0-9_-]+)\.([0-9a-fA-F]{6})` (que no siga una letra o número) en el texto tal cual.
2. Si no aparece, quitar todos los espacios y saltos de línea y buscar otra vez.
3. Si la versión no es 1 (o aparece `GT2-` … `GT9-`), error «actualiza la app».

### 4.4 Errores (mensajes para el usuario)

| Caso | Mensaje |
|---|---|
| No hay código | «No encontramos un código de rutina. Revisa que lo hayas copiado completo (empieza por «GT1-»).» |
| Versión nueva | «Este código es de una versión más nueva de la app. Actualiza GymTracker y vuelve a intentarlo.» |
| Control incorrecto (cortado) | «El código está incompleto o tiene un error. Pide a tu entrenador que te lo vuelva a enviar.» |
| No descomprime / JSON roto | «El código está dañado. Pide a tu entrenador que te lo vuelva a enviar.» |
| No cumple las reglas | «El código no contiene una rutina válida.» |
| Demasiado grande | «El código es demasiado largo.» |

### 4.5 En Swift (sin dependencias)

- `struct RoutineCode: Codable` con las claves cortas de 4.1 (`CodingKeys`) y funciones
  `encode(_:) throws -> String` y `decode(_ text: String) throws -> RoutineCode` (validación incluida), en un archivo
  aparte y sin UI, para probarlo con Swift Testing.
- Comprimir y descomprimir con el framework **Compression** y `COMPRESSION_ZLIB`, que en Apple es **DEFLATE crudo**,
  igual que `deflate-raw` del navegador:
  - `compression_encode_buffer`;
  - `compression_decode_buffer` con un búfer de 65 537 bytes: si devuelve 65 537 o más, es «demasiado grande»;
    si devuelve 0, «dañado».
- base64url: `Data.base64EncodedString()` y cambiar `+`→`-`, `/`→`_`, quitar `=`; al leer, al revés y rellenar con
  `=` hasta múltiplo de 4.
- FNV-1a con `UInt32` y `&*` (multiplicación con desbordamiento).
- `JSONEncoder` sin `.prettyPrinted`. El orden de las claves no importa.

### 4.6 Pruebas obligatorias (Swift Testing)

- **Vector de la web:**
  - `datos/codigo-rutina/ejemplo.codigo.txt` (generado en JavaScript) se decodifica e iguala a
    `datos/codigo-rutina/ejemplo.decodificado.json`;
  - comparar como objetos, no como texto.
- **Ida y vuelta:** `ejemplo.json` → `encode` → `decode` da lo mismo.
- **Compatibilidad hacia la web:** un código creado en Swift se abre en
  `https://khuertamejia-boop.github.io/Gym-tracker-2/r/#<código>` (prueba manual en Safari).
- **Errores:**
  - texto sin código → sin código;
  - código cortado y último carácter cambiado → control;
  - `GT2-` → versión;
  - rutina sin días, nombre de 61 caracteres, 99 series, reps «12-8», `c-` sin definir, semana con índice 9 y 7 × 30
    ejercicios → no válida;
  - una nota de 200 000 «a» → demasiado grande.
- **Dentro del mensaje:** el mensaje de la sección 3 completo y el código con un salto de línea en medio se leen bien.

## 5. Datos nuevos (SwiftData, con las reglas de CloudKit de PLAN.md)

- **CoachRoutine**: `id`, `name`, `days[RoutineDay]` (o una copia propia con el mismo formato), `week[7]`, `lastStudent`,
  `note`, `createdAt`, `updatedAt`. Va aparte de `Routine` para que no se mezcle con el plan del entrenador.
- **RoutineExercise**: añadir `coachNote` y `rest` opcionales (se usan en CoachRoutine; en Routine solo `coachNote`).
- **Routine**: añadir `coachName` y `coachNote` opcionales.
- **Settings**: `coachMode` (interruptor), `coachName`.

## 6. App Store

- En **Info** del proyecto: URL Types → esquema `gymtracker`.
- Notas para la revisión: «Modo entrenador (Ajustes) crea una rutina y la comparte como enlace. El alumno pega el
  mensaje en “Tengo una rutina”. Todo funciona sin cuenta ni servidor; la rutina va dentro del enlace.» Incluir un
  código de ejemplo (`ejemplo.codigo.txt`).
- Más adelante, con un dominio propio, se puede añadir *Universal Links* para que el enlace abra la app directamente
  (hoy no se puede: GitHub Pages de un proyecto no sirve `/.well-known/` en la raíz del dominio).
