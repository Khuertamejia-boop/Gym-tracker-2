# Muñeco 3D de ejercicios: guía del proyecto

Copia de seguridad del muñeco 3D (piel gris clara, short oscuro; con rostro desde el 28-10-2026) que hace los ejercicios de la
app de iPhone en estilo «lámina de anatomía»: cuerpo casi blanco, cada músculo con su sombreado y los músculos que
trabajan en rojo. Se guardó el 23-10-2026 desde un chat que se hizo demasiado largo. Esta rama **no toca la web**
(GitHub Pages publica solo `main`).

**Para el dueño:** no tienes que hacer nada con estos archivos. Al empezar un chat nuevo, pega el mensaje del final
de esta guía y Claude seguirá desde aquí.

---

## 1. Estado (23-10-2026)

| Qué | Estado | Ejemplo |
|---|---|---|
| Estilo de dibujo **v8** (`ill/style_v8.env`) | aprobado: «bastante cerca» de la referencia; cortes grises aclarados el 23-10 | `ejemplos/espalda_cortes_antes_ahora_16x9.jpg` |
| Remo con barra | v7 (28-10-2026): estilo v12, cuerpo v2, ritmo aprobado, cuello neutro, barra sin atravesar las piernas | `ejemplos/remo_barra_v7.mp4`, `.gif` |
| Face pull en polea | hecho (v1), con torre de polea y pesas que suben | `ejemplos/facepull_v1.gif`, `ejemplos/facepull_*_16x9.jpg` |
| Jalón en polea con agarre cerrado (rojo en dos intensidades) | v3 (29-10-2026): brazos sin atravesar el cuerpo, tono suave 30 %, rojo v14 | `ejemplos/jalon_cerrado_v3.mp4`, `.gif` |
| Extensión de tríceps tras nuca en polea | v1 (29-10-2026), falta el visto bueno | `ejemplos/triceps_tras_nuca_v1.mp4`, `.gif` |
| Animación de fondo de la app: doble bíceps de espaldas (rojo Push y rojo Pull) | v5 (11-11-2026): hombro con bola, bíceps con pico, axila limpia (sección 5r; `ejemplos/v5_espalda_antes_ahora.jpg`); antes v4 (sección 5q); antes v3 (mapas v2, puños cerrados, cara con sonrisa, `ejemplos/doble_biceps_v3_cerca.jpg`); antes v2 (hombro redondo, `ejemplos/doble_biceps_hombro_antes_ahora.jpg`); falta el visto bueno: `ejemplos/doble_biceps_pull_en_la_app.mp4`, `app/doble_biceps_pull_transparente.mov`, `app/doble_biceps_pull/` | `ejemplos/doble_biceps_en_la_app.mp4`, `.jpg`; para Xcode: `app/doble_biceps_transparente.mov`, `app/doble_biceps/` |
| Animación de fondo de la app: doble bíceps **de frente** (rojo Push) | v5 (11-11-2026: hombro con bola, bíceps con pico, axila limpia, sección 5r; `ejemplos/v5_frente_antes_ahora.jpg`), falta el visto bueno | `ejemplos/doble_biceps_frente_en_la_app.mp4`, `.jpg`, `_cerca.jpg`; para Xcode: `app/doble_biceps_frente_transparente.mov`, `app/doble_biceps_frente/` |
| **Versión mujer** (cuerpo, rostro, moño, top deportivo) | v3 (28-10-2026), falta el visto bueno | `ejemplos/mujer_v3_*.jpg` |
| Peso muerto con barra (convencional) | aprobado (v2, 23-10-2026): barra sin atravesar las piernas, subida rápida y bajada lenta | `ejemplos/pesomuerto_v2.gif`, `.mp4` |
| Curl de bíceps a un brazo con mancuerna (de pie) | v2 (28-10-2026): estilo v10 y cuerpo v2; falta el visto bueno | `ejemplos/curl_un_brazo_v2.mp4`, `.gif` |
| Mapa de músculos: espalda, brazos, piernas | hecho | |
| Mapa de músculos: pecho, abdomen, oblicuos, serrato, cuello por delante (`ill/spec/front.py`) | aprobado el 23-10-2026 | `ejemplos/facepull_frente_16x9_v2.jpg` (antes: `facepull_frente_16x9.jpg`) |

**Formato final (decidido el 23-10-2026):** todo se renderiza en **1920×1080 horizontal (16:9)**, cuerpo entero con
pies y máquina en el centro. Hay que juzgar el resultado a ese tamaño, no de cerca. (Si el dueño dice que quería
vertical, cambiar `RX/RY`.)

## 2. Restaurar el proyecto (sesión nueva de Claude o laptop)

```bash
cd cuerpo3d && ./restaurar.sh ~/cuerpo3d-trabajo     # copia, crea venv (Python 3.13 + bpy 5.2.2) y genera mapas (~5 min + instalar bpy)
export GT3D=~/cuerpo3d-trabajo                      # en CADA terminal nueva
```
- Todos los programas usan la variable `GT3D` como carpeta raíz (antes era una ruta fija de la nube; si falta
  `GT3D` usan esa ruta antigua y fallarán).
- Si ya hay un `venv` con bpy, `restaurar.sh` no lo reinstala (en una sesión de Claude se puede enlazar uno).
- Blender se usa como módulo de Python, sin ventana: `$GT3D/venv/bin/python -I script.py entrada.blend salida.blend`.
- Probado el 23-10-2026: la copia restaurada da mapas idénticos (diferencia 0), la misma postura y el mismo render,
  y `ill/atlas_rebuild.sh` recompila el mapa de músculos idéntico al aprobado.
- Laptop del dueño: funciona igual si tiene Python 3.13. Solo tiene sentido para repetir renders finales en HD; crear
  ejercicios (posturas, máquinas, mapas) lo hace Claude.

## 3. Carpetas

```
cuerpo3d/
  *.py *.sh *.env   posturas y animación: facepull.py (+ facepull_geo.py máquina), barrow.py (remo),
                    pullup*.py, curl*.py, legcurl.py, legext.py, bench*.py; anim_<ejercicio>.sh = un fotograma
                    skinstack.py + corskin.py (piel), arap2.py (relaja hombros), handrig.py (dedos y agarre)
                    agarre_final.env (ajustes del agarre, se carga en todas las animaciones)
  w/                bases del cuerpo: NB_mc_row.blend (remo, face pull), NB_mc.blend (press, extensión),
                    NB_mc_hs.blend (curl femoral), NB_s.blend (dominada). Aquí se escriben los fotogramas.
  ill/              estilo ilustración
    spec/*.py       MAPA DE MÚSCULOS: contornos por músculo (lado izquierdo, el derecho se refleja)
    AUTHORING.md    cómo escribir/editar un spec (formato de puntos y contornos)  <- LEER antes de tocar spec/
    atlas.py        compila los specs -> pv/bla.npz;  bulge.py -> pv/bla_dome.npz (abombado por músculo)
    bakemaps.py     texturas (UDIM) de bordes, distancias, abombado;  linemap.py fuerza de cada borde;
    redmap.py       rojo de los músculos trabajados;  stylefields.py -> pv/bla_row2.npz (fibras)
    rendsculpt.py   EL RENDER (sombreado tipo lámina, todo en código)
    style_v8.env    estilo actual (parámetros del render);  style_v7.env el anterior
    mapas.sh        texturas de un ejercicio (~2-4 min);  atlas_rebuild.sh  recompilar el mapa tras editar spec/
    anim_fp.sh      render final del face pull en 16:9 -> out/facepull.gif;  mkgif.py GIF ida y vuelta
    rest.npz uvtri.npz relief_mc.npz curves_base.npz   datos del cuerpo en reposo (no tocar)
  referencias/      imágenes que mandó el dueño (8ccf8362 = LA referencia de estilo, remo de espalda;
                    697dfdbd cruce de poleas de frente: pecho y abdomen; 14cf49ef curl de frente; e5d5044e fondos)
  ejemplos/         últimos resultados aprobados
```

## 4. Hacer un ejercicio (ejemplo: face pull)

```bash
export GT3D=~/cuerpo3d-trabajo; cd $GT3D
# 1) músculos trabajados -> texturas (una vez por ejercicio)
ill/mapas.sh maps_fp2 "deltoid_posterior:1,trapezius:1,rhomboid_major:1,infraspinatus:1,teres_minor:1"
# 2) posturas: 11 fotogramas de 0 a 1 (P = 0,5 - 0,5·cos), 2-3 min cada uno; de 4 en 4 en paralelo
for g in "0 1 2 3" "4 5 6 7" "8 9 10"; do for f in $g; do PFX=FPd ./anim_fp.sh $f 20 & done; wait; done
# 3) render 1920x1080 estilo v8 + GIF ida y vuelta
PFX=FPd ill/anim_fp.sh
```
- Vista previa barata antes del render final: un fotograma con `RX=960 RY=540 SMP=8`. Render final `SMP=32`
  (1-2 min por fotograma en 4 núcleos).
- Cámara 16:9 del face pull (espalda, 3/4 por la izquierda): `YAW=152 PIT=10 TX=0.27 TY=-0.745 TZ=0.97 OSC=3.8 RX=1920 RY=1080`.
  Frente 3/4: `YAW=40 PIT=8 TX=-0.12 TY=-0.6 TZ=0.97 OSC=3.8`. `OSC` = ancho visible en metros. YAW 0 = de frente,
  180 = de espalda; el cuerpo mira a -Y, su izquierda es +X. `HIDEBANCO=1` oculta la máquina.
- Remo: `pose_row_v5.sh` (postura) + `ill/anim_v7.sh` (render, cambiar a style_v8 y 16:9), mapas `maps_v5`
  (lista en `restaurar.sh`).
- Nombres de músculos para el rojo: los de `ill/spec/*.py` sin `.L/.R` (`trapezius` agrupa trap_upper/middle/lower).
  Los tendones nunca van en rojo. Solo los **principales** en rojo (decisión del dueño: en el remo, sin bíceps).

## 5. Frente del torso (hecho el 23-10-2026)

`ill/spec/front.py` (lado izquierdo, prefijo `fr_`): pectoral mayor en dos porciones (clavicular y esternal, división
suave `~`, grupo `pectoralis_major`), serrato anterior (3 dientes en zigzag con el oblicuo), oblicuo externo, recto
abdominal en 4 segmentos (grupo `rectus_abdominis`) y esternocleidomastoideo. Notas:
- La línea alba es la línea del centro entre los dos rectos: como franja de tendón no cabe (la malla es de ~6 mm).
- Las 3 intersecciones del recto van como bordes **marcados**, no suaves: suaves casi no se veían a 16:9 y el abdomen
  parecía dos tiras largas (`ejemplos/abdominales_suave_vs_marcado.jpg`, izquierda suave, derecha marcado).
- Entre los pectorales queda una franja lisa de esternón (x < 1 cm), y el triángulo entre el esternocleidomastoideo y
  el trapecio queda liso (como en las láminas).
- Para el rojo: `pectoralis_major` (o `pec_clavicular` / `pec_sternal`), `rectus_abdominis`, `external_oblique`,
  `serratus_anterior`, `sternocleidomastoid`.
- Tras cambiarlo: `ill/atlas_rebuild.sh` y `ill/mapas.sh` de cada ejercicio (ya hecho para `maps_fp2`).

**Siguiente:** rehacer el GIF del face pull con el frente nuevo cuando haga falta (sección 4).

## 5b. Peso muerto (hecho el 23-10-2026, v1)

```bash
export GT3D=~/cuerpo3d-trabajo; cd $GT3D
ill/mapas.sh maps_dl "gluteus_maximus:1,biceps_femoris:1,semitendinosus:1,semimembranosus:1,erector_spinae:1"
export LEAN0=80 SPX0=22 SPX1=2 MIDF=0.07 SHDY=-0.04 NECK0=0 PFX=DLf
for g in $(seq 0 4 30); do for f in $(seq $g $((g+3))); do [ $f -le 30 ] && ./anim_dl.sh $f 60 & done; wait; done   # 31 posturas, ~15 s c/u
ill/anim_dl.sh        # render 1920x1080 estilo v8 de las 31 -> out/pesomuerto.gif (~15 min; REDO=1 rehace los PNG)
python3 ill/mkmp4.py out/pesomuerto.mp4 ill/r/dl_final/f*.png   # vídeo 16:9, mismo ritmo (más fluido en el iPhone)
```
- `deadlift.py` (hecho a partir de `barrow.py`): pies fijos, barra en línea recta sobre el centro del pie (`MIDF` 7 cm
  delante del tobillo), brazos colgando rectos. Abajo (P=0) la flexión de rodilla se calcula sola para que los discos
  (45 cm) toquen el suelo; los hombros quedan 4 cm por delante de la barra (`SHDY`). Las rodillas se estiran primero y
  la cadera empieza algo después (`KDEL`), como en la técnica real.
- `LEAN0` es la inclinación de la cadera; la extensión de espalda (`SPX0`) le resta, así que el tronco queda a ~60-65°
  de la vertical. Con `LEAN0` 55-65 salía una sentadilla (cadera a la altura de las rodillas).
- Cuello: `NECKT`/`NECK0` **positivo levanta la cabeza** y negativo la baja. 0 = cabeza en línea con la espalda y mirada
  al suelo un poco adelante (lo correcto en el peso muerto). El remo usa -40: por eso su cuello mira hacia abajo.
- Cámara: de perfil puro el disco tapa el cuerpo. Elegida: diagonal desde atrás por la izquierda
  `YAW=140 PIT=14 TX=0 TY=0 TZ=0.84 OSC=3.4` (se ve la técnica y de lleno glúteos, isquiotibiales y lumbares).
- Rojo: glúteo mayor, isquiotibiales (bíceps femoral, semitendinoso, semimembranoso) y erectores de la columna.
  Cuádriceps no (no es el principal). Los glúteos están bajo el short: `rendsculpt.py` tiene `SHRED` (0-1) para que el
  rojo se vea a través del short; el peso muerto usa `SHRED=0.7`.
- **La barra nunca entra en las piernas** (pedido del dueño, 23-10): en cada postura `deadlift.py` mide la piel de las
  piernas a la altura de la barra y, si está por delante de la línea del centro del pie, adelanta la barra hasta que
  quede a 6 mm (`GAP`). Abajo pasa a ~1,5 cm de las espinillas; arriba queda delante de los muslos/short con los brazos
  algo inclinados (como en el bloqueo real). Comprobar con `python -I barcheck.py -- w/DLf*.blend` (copia en la carpeta).
- **Velocidad** (pedido del dueño, 23-10): la subida (concéntrica) rápida y la bajada (excéntrica) lenta, con pausas.
  `ill/mkgif2.py`: 31 posturas (P = 0,5 - 0,5·cos), subida 40 ms por imagen (~1,2 s), arriba 0,4 s, bajada 80 ms por
  imagen (~2,4 s), abajo 0,6 s (`UP`, `DOWN`, `HOLDT`, `HOLDB`). Antes: 0,9 s + 0,9 s sin pausas (demasiado rápido).
- Pendiente: puntitos negros sueltos en el borde del rojo del glúteo (de cerca), y el short del lateral de la cadera
  queda negro con forma algo rara al flexionar mucho.

## 5d. Curl de bíceps a un brazo (hecho el 28-10-2026, v1)

```bash
export GT3D=~/cuerpo3d-trabajo; cd $GT3D
NONEFIX=1 ill/mapas.sh maps_curl1 "biceps_brachii.L:1,brachialis.L:1,brachioradialis.L:1"   # solo el brazo izquierdo
export PFX=CUf; for g in $(seq 0 4 30); do for f in $(seq $g $((g+3))); do [ $f -le 30 ] && ./anim_curl1.sh $f 60 & done; wait; done
cd w && ../venv/bin/python -I ../objcheck.py -- CUf*.blend; cd ..       # mancuernas: nunca dentro del cuerpo (mm > 0)
YAW=70 PIT=8 ill/render31.sh CUf maps_curl1 curl_un_brazo              # -> out/curl_un_brazo.mp4 / .gif
```
- `curl1.py` (hecho con las piezas de `barrow.py`: cálculo anatómico del brazo, agarre aprobado, piel `cor` + `arap2`):
  trabaja el brazo **izquierdo** (supino, codo pegado al costado y quieto, solo avanza un poco arriba; flexión 14° → 140°,
  muñeca algo flexionada arriba). El derecho cuelga quieto con su mancuerna (agarre neutro). De pie, cuello neutro.
- Codo como bisagra: `WPA=4` (el codo va donde se le pide), `WFV=1e9` (sin la preferencia de antebrazo vertical del remo),
  `CARRY=0` (con ángulo de carga el húmero giraba 33° al empezar). Brazos algo separados (`UAX=0.20`, `UAXR=0.24`):
  más pegados, las mancuernas se metían 2-3 cm en los muslos.
- Rojo de un solo lado: `redmap.py`/`linemap.py` aceptan `nombre.L` / `nombre.R`. Rojo como en la lámina de referencia
  del curl (`14cf49ef`): bíceps, braquial y braquiorradial.
- `NONEFIX=1` en `bakemaps.py`: en la punta del bíceps quedaba una franja en «U» marcada como piel sin músculo (la curva
  cerrada del borde confundía el lado). Solo se usa en mapas nuevos; los aprobados (remo, face pull, peso muerto) no
  se han regenerado con ella. Si se ve bien, usarla siempre.
- Cámara: de lado desde el brazo que trabaja (`YAW=70`); a 45° el antebrazo apunta a la cámara y no se entiende el
  movimiento.
- `ill/render31.sh <PFX> <mapas> <nombre>`: render estándar de las 31 posturas + GIF + MP4 para cualquier ejercicio.

## 5c. Plan para hacer los 114 ejercicios del catálogo gastando pocos créditos (23-10-2026)

Lo que gasta no es el render (es cálculo de la máquina), sino lo que Claude lee y mira: imágenes, pruebas y chats largos.

**Estándar congelado (no volver a discutirlo):** estilo v14 desde el 29-10 (antes v10, v8); cuerpo v2; 1920×1080 (16:9); 31 posturas; ritmo del peso muerto
(subida ~1,2 s, pausa 0,4 s, bajada ~2,4 s, pausa 0,6 s; `ill/mkgif2.py` y `ill/mkmp4.py`; **aprobado por el dueño**);
vídeo MP4 + GIF; rojo solo en los músculos principales (glúteos a través del short con `SHRED`); comprobación
automática de que la barra/mancuernas no atraviesan el cuerpo (`barcheck.py`).

**Paso 1 (un chat, una vez):** sistema genérico: una *ficha* corta por ejercicio (programa de movimiento, parámetros,
músculos en rojo, cámara, máquina) y un solo comando que hace todo sin supervisión: texturas, 31 posturas, comprobación de
choques, render, MP4/GIF y una hoja con 3 posturas pequeñas para revisar.

**Paso 2 (un chat por familia):** el dueño manda en un solo mensaje la lista de la familia (y una imagen de referencia
si la tiene). Claude hace las fichas, enseña UNA hoja con todos los ejercicios en pequeño, el dueño corrige todo en un
mensaje y se lanza el render final de la familia de golpe. Máximo 2 rondas de correcciones.

Familias (por "motor" y máquina compartidos; de más barata a más cara):
1. Barra de pie con bisagra o tirón (base `deadlift.py`/`barrow.py`): rumano, piernas rígidas, sumo, rack pull, buenos días,
   Pendlay, remo en T, encogimientos, curl con barra/Z, curl inverso, press militar, remo al mentón.
2. Mancuernas de pie o sentado: curls, martillo, laterales, frontales, pájaros, press de hombro, Arnold, encogimientos,
   granjero, goblet, zancadas, rumano con mancuernas, step-up, búlgara.
3. Polea (torre ya hecha en el face pull): cruces, jalones, remo sentado, curl/extensiones en polea, laterales en polea,
   pullover, crunch en polea, patada de glúteo, Pallof, leñador.
4. Banco y barra/mancuernas tumbado: press banca/inclinado/declinado/cerrado, aperturas, press francés, pullover,
   hip thrust, puente, fondos en banco, curl Scott, curl inclinado, remo con pecho apoyado.
5. Peso corporal: dominadas (hay base), fondos, flexiones, planchas, crunch, elevaciones de piernas, rueda, giros rusos,
   hiperextensiones, curl nórdico.
6. Smith (una máquina para todos): press inclinado, sentadillas, pantorrillas.
7. Sentadillas y piernas libres: sentadilla con barra, frontal.
8. Máquinas (22, cada una necesita su modelo 3D: lo más caro, al final; reutilizar asiento, respaldo y pila de pesas).

**Ahorros:** las variantes «· cuádriceps / · glúteos» (búlgara, prensa, Smith) usan las mismas posturas, solo cambia el
rojo; «Dominadas lastradas» = dominadas + disco. Chats cortos (uno por familia), empezando con el mensaje de la sección 9.

## 5e. Estilo v10 y cuerpo v2 (28-10-2026, elegido por el dueño)

El dueño ve las sombras de los músculos muy fuertes y quiere algo más natural. Tres propuestas sobre v8
(`ejemplos/sombras_opciones_v9.jpg`; misma base + cambios al final de cada archivo):
- `style_v9a.env` (A, −25 %): `BUMPK=1.05` (abombado de cada músculo), tonos oscuros más claros (`TONES` 0,48…), sombra en
  surcos `MAOP=0.35`, contraste del rojo `REDCON=1.8`.
- `style_v9b.env` (B, −45 %, recomendada): `BUMPK=0.8`, `TONES` 0,56…, `MAOP=0.25`, `GBUMP=0.5`, `REDCON=1.55`, contorno `MRC=0.38`.
- `style_v9c.env` (C, −65 %): `BUMPK=0.55`, `TONES` 0,64…, `MAOP=0.18`, `GBUMP=0.45`, `REDCON=1.3`, `MRC=0.45` (la espalda
  empieza a verse plana).
**Elegida la C** y además, a petición del dueño:
- rojo más suave: `style_v10.env` = C + `RCOLS` más claros y menos saturados (opción «Nuevo 1» de
  `ejemplos/rojo_suave_opciones.jpg`; la «Nuevo 2», `style_v10b.env`, tiraba a rosa) + fibras y líneas del rojo más claras;
- trapecio superior y pectorales algo más pequeños: `shrink.py` hunde la piel hacia dentro (trapecio 10 mm, pectorales
  8 mm, transición suave ~2 cm) -> `w/NB_mc_row2.blend` (lo crea `restaurar.sh`; `ejemplos/trapecio_pectoral_antes_despues.jpg`).
  Con 6-7 mm casi no se notaba.
**Desde ahora** `style_v10` es el estilo por defecto (`ill/render31.sh`, `ill/anim_dl.sh`, `ill/anim_fp.sh`) y
`NB_mc_row2.blend` la base por defecto (`anim_curl1.sh`, `anim_dl.sh`, `anim_fp.sh`, `anim_row.sh`). Los vídeos ya hechos
(remo, face pull, peso muerto) siguen con el estilo y el cuerpo viejos hasta rehacerlos (posturas + render).
Si se usan las otras bases (`NB_mc`, `NB_mc_hs`, `NB_s`), pasarles también `shrink.py` con el mismo `SHRINK`.

## 5f. Músculos redondeados: estilo v11 (28-10-2026, aprobado: «me gusta un poco más como está ahora»)

El dueño veía los músculos «en punta». Causa: el oscurecimiento del borde de cada músculo crecía en línea recta hasta
el centro (perfil de tejado con arista en medio; muy visible en los rojos, que tenían el borde más oscuro y más
abombado). `style_v11.env` = v10 + :
- `EROUND=1` (nuevo en `rendsculpt.py`): perfil de cúpula `1-(1-e)²`: se aclara rápido junto al borde y deja un centro
  amplio y suave; `EWF=1.0 EWFR=1.0 EGP=0.8`, rojo menos oscuro en el borde `ERMIN=0.4`;
- abombado: `RBUMP=0.5` (nuevo: abombado de los músculos rojos, antes siempre 1) y `GBUMP=0.7` (grises algo más
  redondos que en v10), perfil de cúpula más plano `DRP=0.45 PFLAT=0.6`; borde gris `EMIN=0.87`.
Probadas (`ejemplos/redondeo_antes_despues_v11.jpg`): con `GBUMP=1.3 EMIN=0.8` los contornos vuelven a verse oscuros.
`style_v11` es ya el estilo por defecto de `ill/render31.sh`, `ill/anim_dl.sh`, `ill/anim_fp.sh`. El dueño pidió no
animar más hasta dar el visto bueno.

## 5g. Fibras del rojo visibles de lejos: estilo v12 (28-10-2026)

El dueño no veía la textura (fibras) de los músculos rojos en el 16:9 completo: eran rayas de 6-9 mm (3-5 px) y en
v10 se habían aclarado. `style_v12.env` = v11 + rayas el doble de anchas `FSTR=0.42`, más contraste `FIBR=0.85 FIBL=0.9`,
fibra oscura `FIBRC=0.40,0.12,0.08`, borde de raya más nítido `FS0=0.38 FS1=0.64` (`ejemplos/fibras_rojo_1a1.jpg`,
`fibras_rojo_lejos.jpg`: la intermedia `FSTR=0.55 FIBR=0.7 FIBL=0.75` aún no se distinguía a tamaño de móvil).
`style_v12` es el estilo por defecto (`ill/render31.sh`, `ill/anim_dl.sh`, `ill/anim_fp.sh`).

## 5h. Remo con barra v7 (28-10-2026)

```bash
export GT3D=~/cuerpo3d-trabajo; cd $GT3D
NONEFIX=1 ill/mapas.sh maps_row2 "trapezius:1,latissimus_dorsi:1,infraspinatus:1,teres_major:1,teres_minor:1,rhomboid_major:1,deltoid_posterior:1,deltoid_lateral:1"
PFX=BRh ./pose_row_v6.sh                                   # 31 posturas
cd w && ../venv/bin/python -I ../barcheck.py -- BRh*.blend; cd ..   # barra fuera de las piernas (mm > 0)
YAW=135 PIT=20 TX=0 TY=0 TZ=0.68 OSC=3.0 ill/render31.sh BRh maps_row2 remo_barra
```
- La comprobación encontró que el remo aprobado (v6) tenía la barra 1-1,4 cm dentro de las rodillas abajo y de los
  muslos arriba (tocaba el cuerpo a la altura del ombligo, `TOUCHZ=1.02`, entre la barriga y los muslos).
  Ahora `barrow.py` adelanta la barra si choca con la pierna (`LEGPUSH=1`, 6 mm de holgura) y toca un poco más arriba
  (`TOUCHZ=1.05`; con 1.10 no hay choque pero los antebrazos se inclinan 43° en vez de ~35°).
- Cuello neutro `NECKT=0` (en línea con la espalda). En `barrow.py`/`deadlift.py` NECKT positivo levanta la cabeza.

## 5i. Borde del rojo suave y rostro (28-10-2026)

**Borde exterior del rojo** (pedido del dueño: «que no se vea tan marcado»): `bakemaps.py` con `REDSEL` (lo pasa
`mapas.sh`) guarda la distancia al borde exterior del rojo (`redd16.*.png`); `rendsculpt.py` con `RSOFT=8` hace que el
rojo entre en 8 mm desde ese borde (`RSOFT0` = rojo en el mismo borde, 0,15). La línea entre rojo y gris es más suave:
`mapas.sh` usa `SRW=0.6` (antes 1.0). `style_v13.env` = v12 + `RSOFT=8` (por defecto). Hay que rehacer los mapas de cada
ejercicio (`maps_curl2`, `maps_row3` ya hechos). Con `RSOFT=14` el rojo se veía deslavado (`ejemplos/borde_rojo_suave.jpg`).

**Rostro** (pedido del dueño con una foto de referencia: hombre, pelo muy corto): `facebuild.py` añade a la base la cabeza
original de la malla «Human Base Meshes» de Blender (CC0; nuestro cuerpo salió de su `GEO-body_male_realistic`, mismas
medidas) como objeto `Cabeza` (multires nivel 2, ~56 mil vértices, corte recto inclinado bajo la mandíbula) + ojos
`Ojo.L/R`, con los mismos pesos de la piel (se mueve con el cuello). La cabeza lisa de `Hi` se hunde 12 mm dentro
(misma topología: el atlas y los mapas siguen valiendo) -> `w/NB_mc_row3.blend` (base por defecto).
- Atributo `tint` (oscuro): pelo corto (contorno medido de perfil en `SKIN`: frente con entradas, patilla, pegado a la
  oreja, nuca a la altura del lóbulo), cejas (arcos), iris y pupila. El render lo aplica con `TINTV`.
- 28-10: el dueño veía «pelado encima de la oreja»: la oreja se quitaba del pelo con una caja que cogía todo el lado de la
  cabeza. Ahora la oreja sale de los *face sets* 4 y 5 de la malla original (`EARFS`) y el pelo baja hasta ~5 mm de
  ella, con la sien llena (`ejemplos/rostro_v2_pelo_lados.jpg`).
- 28-10: cejas como la foto del dueño (gruesas, densas, casi rectas, arco suave en el último tercio, cola fina que baja,
  inicio más claro y difuminado): forma en `facebuild.py` (`bmask`) y trazos de pelo en el render (`bw` = coordenada
  a través de los pelos, hacia arriba al inicio y en diagonal hacia fuera; `BROWSTK`, `BRSW`, `BRJ`, `BRNB`).
  `TINTV` es lineal: 0,05 = gris oscuro en pantalla (con 0,20 lo más oscuro era un gris medio); `HAIRT=0.51` mantiene el
  tono del pelo. Ojos subdivididos (`EYESUB=3`) para un iris redondo (`ejemplos/rostro_v3_cejas.jpg`).
- `rendsculpt.py` (con `FACE=1`, por defecto): hornea la piel de la cabeza, pega la franja baja (`snapw`, 1,2 cm) a la piel
  del cuello ya posada, y le copia a la cabeza el dibujo de la piel de debajo (UV por cara desde un solo triángulo del
  cuerpo + atributos): las líneas y fibras del cuello siguen sin corte. Subdivisión `FACESUB=1`.
  Probado y descartado: transparencia en la franja (`FACEFADE=1`: la sombra de los surcos dibuja una línea oscura) y
  corte por caras enteras (borde en dientes de sierra).
- Cada ejercicio hay que volver a posarlo con la base nueva para que salga la cara.

## 5j. Versión mujer (28-10-2026, v1)

Pedido del dueño: «lo mismo de la versión hombre en cuerpo de mujer, el diseño y estilo, con sus atributos».
`./mujer.sh <bundle.blend>` crea `w/NBF_row3.blend` (base) + `ill/rest_f.npz` (datos de reposo):
1. `femalebuild.py`: las mallas realistas hombre y mujer de «Human Base Meshes» tienen la MISMA topología, y nuestro
   `Hi` conserva casi todos los vértices del hombre en orden. Cada vértice se lleva a su sitio en la mujer (exactos por
   índice; el resto, proyectados sobre la superficie del hombre y llevados al mismo punto de la mujer, con `PHYK=0.5`
   de la musculatura extra del muñeco) -> el atlas de músculos, las UV, TODOS los mapas, los pesos y atributos siguen
   valiendo sin rehacer nada. El esqueleto se reajusta (cada articulación sigue a la piel de alrededor).
   Probado y descartado: emparejar por el vértice más cercano (saltos de vértice -> rayitas blancas en la piel).
   Las «caras giradas» en pies y dedos son de la propia malla de Blender (otra postura de los dedos), no errores.
2. `facebuild.py` con `SRCBODY=GEO-body_female_realistic`, `ZOFF=-0.040` (cabeza 4 cm más baja), `HAIRSTYLE=bun`: rostro
   femenino, cejas más finas y arqueadas, pelo recogido con volumen (`HVOL=4` mm), mechones hacia un **moño**
   (objeto `Ojo.Mono`, en el hueso de la cabeza; se eligió moño y no coleta porque se ve bien en cualquier postura).
   `CAPMIN`: la cabeza lisa de debajo queda siempre >= 3 mm dentro (asomaba un pico en la coronilla).
3. `topbuild.py`: top deportivo con la misma tela que el short (atributo `shorts`): banda bajo el pecho, copas con
   escote redondo, laterales, tirantes y espalda en Y.
- Posar cualquier ejercicio con `BASEB=NBF_row3.blend` (mismos programas) y renderizar con `RESTNPZ=$GT3D/ill/rest_f.npz`
  y `ill/style_mujer.env` (= v13 + mechones `HRSW=4 HRJ=0.8 HAIRSTK=0.5`). El curl funciona (agarre bien, sin choques).
- `objcheck.py` confirma con rayos si un punto está dentro del cuerpo (las normales entre dedos cerrados engañaban).
- v2 (28-10, pedido del dueño: rostro de mujer, pelo más oscuro, más femenina, ropa sin «dientes de sierra»):
  * ropa: `topbuild.py` guarda en `shorts` una RAMPA LINEAL (`TW` 12 mm) de la distancia con signo a cada borde (líneas
    analíticas combinadas con min/max, delante/detrás mezclados por `y`, sin cortes bruscos) y el render la corta en 0,5
    -> bordes limpios dentro de los triángulos. Cintura del short redibujada igual; el bajo usa `SHLIN=1` en el render
    (rampa lineal de `SHORTZ`, también mejora el bajo del hombre).
  * rostro (`FEMFACE=1`): nariz algo más fina y pequeña, mandíbula más suave (ediciones locales suaves), labios con
    tono (`LIPT`), línea de pestañas arriba (`LASHT`, más suave abajo `LASHB`), iris algo mayor (`IRISA=33`).
  * pelo más oscuro (`HAIRT=0.80`), con volumen (`HVOL=9` mm) y **moño alto** visible de frente (`BUNR/BUNY/BUNZ`);
    mechones sutiles en `style_mujer.env` (con mucho contraste parecían un gorro de natación).
  * figura: menos musculatura heredada del hombre (`PHYK=0.25`); líneas de los músculos grises más suaves
    (mapas con `SWW=0.45`, p. ej. `maps_curl2f`) y estilo `style_mujer.env` (`EMIN=0.93 GBUMP=0.55 MAOP=0.12`).
- v3 (28-10, pedido del dueño: «dale un rostro femenino, aún se le aprecia fisonomía de hombre», «mejora la ropa
  debajo del brazo», «oscurece su cabello»):
  * rostro: `femface.py` (lo llama `facebuild.py` en modo mujer), cambios suaves y locales de la cabeza de Blender:
    mandíbula más estrecha hacia el ángulo (`JN`), mentón más estrecho (`CN`) y más corto (`CH` = 6,5 mm: la parte baja
    de la cara era larga, rasgo de hombre), mejillas más llenas (`CF`, `CA`), ceja ósea más suave (`BR`), nariz más
    pequeña con la punta algo arriba (`NOSEK`, `NOSEW`, `NT`), labios más llenos (`LP`), ojos un 6 % mayores (`ES`) con
    el párpado de arriba un poco más bajo (`LIDA`: quita la mirada «asustada»), cuello más fino (`NK`; el mismo cambio en
    el cuello del cuerpo). Todo se apaga antes de la franja que se pega al cuello (si no, sale una línea en el cuello).
    Probado y descartado: exagerar la diferencia entre las cabezas de hombre y mujer de Blender (casi toda está en el
    cráneo, y en el nivel de detalle alto los puntos no coinciden: salen manchas).
  * labios con su forma (línea de la boca medida en la malla, arco del labio de arriba, comisuras apenas más bajas
    `LIPDN`, borde de 2 mm lineal `LIPS`: con 0,8 mm salía dentado) y línea de la boca más oscura (`MLINE`); cejas algo
    más gruesas con arco suave y el inicio no bajo (`BTH`, `BDROP`: si no, parecía enfadada); pestañas de abajo algo
    más marcadas (`LASHB=0.30`).
  * pelo más oscuro (`HAIRT=0.93`) y sienes más llenas (`HREC=-0.010`).
  * ropa bajo el brazo: el top se cortaba según el hueso de cada punto (la piel del costado bajo la axila es del hueso
    del brazo) -> borde en escalera. Ahora `topbuild.py` corta con un cilindro liso alrededor del CENTRO REAL del brazo
    (medido con la superficie del brazo; el hueso está descentrado), radio `RC0..RC3` (5,6–7,2 cm): curva limpia
    delante, bajo la axila y detrás. Los lados de la copa suben algo más (`TZS=1.235`) y tapan la mancha blanca de la axila.
- Pendiente (de cerca): algunas zonas lisas del mapa de músculos del hombre (clavícula, cuello) se ven como manchas
  blancas de borde irregular en la mujer; contorno del pelo detrás de la oreja.

## 5k. Jalón en polea con agarre cerrado (29-10-2026, v3) y rojo en dos intensidades

Pedido del dueño con una lámina de referencia (`referencias/ce0f1b38-jalon.jpg`): mismo ejercicio, y «un color más intenso
los músculos que trabajan más y un color más tenue los que menos».
```bash
export GT3D=~/cuerpo3d-trabajo; cd $GT3D
NONEFIX=1 ill/mapas.sh maps_pd3 "latissimus_dorsi:1,teres_major:1,rhomboid_major:0.30,trap_middle:0.30,trap_lower:0.30,deltoid_posterior:0.30,biceps_brachii:0.30,brachialis:0.30,brachioradialis:0.30"
export PFX=PDf; for g in $(seq 0 3 30); do for f in $(seq $g $((g+2))); do [ $f -le 30 ] && ./anim_pd.sh $f 60 & done; wait; done
grep handle-to-head w/r/log_PDf*.txt          # el agarre nunca toca la cara (mínimo ~4 cm a mitad de recorrido)
cd w && ../venv/bin/python -I ../armcheck.py -- PDf*.blend && ../venv/bin/python -I ../fistcheck.py -- PDf*.blend; cd ..
YAW=208 PIT=10 TX=0 TY=0 TZ=1.15 OSC=4.3 ill/render31.sh PDf maps_pd3 jalon_cerrado
```
- **Dos intensidades de rojo**: `mapas.sh` ya acepta `músculo:intensidad`. Principales a 1 (dorsal ancho, redondo mayor),
  secundarios a **0,30** (romboides, trapecio medio e inferior, deltoides posterior, bíceps, braquial, braquiorradial;
  elegido por el dueño: «me gusta el tono intermedio»; la v1 usó 0,35).
  Probado (`ejemplos/jalon_rojo_intensidades.jpg`): con 0,5 el secundario se ve casi igual de rojo que el principal
  (el sombreado del rojo satura pronto); con 0,2 casi desaparece.
- `pulldown.py` (piezas de `facepull.py`: brazo anatómico, agarre aprobado, piel `cor` + `arap2`): sentado en banco
  plano, muslos bajo el rodillo, pies en el suelo; torso inclinado atrás 8° arriba -> 17° abajo con el pecho arriba
  (`LEAN0/1`, `SPX1`); escápulas arriba en el estiramiento y abajo y juntas al final (`CLV0/1`, `CLR0/1`); agarre neutro
  (palmas enfrentadas, pulgares hacia atrás) en un triángulo; codos de fuera-arriba a abajo-atrás pegados al costado.
  El agarre baja en línea recta por el cable desde arriba (brazos casi estirados, `FLEX0`, `REACHK`) hasta la parte alta
  del pecho (`GY1` 17 cm delante y `GZ1` 7 cm bajo los hombros).
- `pulldown_geo.py`: banco bajo los glúteos (la piel se hunde 6 mm), rodillo sobre los muslos junto a las rodillas,
  torre con pila de pesas (suben con el recorrido), columna y brazo con la polea alta EN la línea del cable, cable a la
  polea de arriba y a las pesas, triángulo con dos agarres dentro de los puños. Marco casi blanco como en la lámina
  (`0.97`; con `0.74` salía gris oscuro).
- Cámara: de espaldas en diagonal desde la derecha (la máquina queda a la derecha, como en la lámina).
- v2 (29-10, dueño: «los brazos se pegan bastante al cuerpo y no se ve natural, revisa que los músculos no se
  atraviesen»): `armcheck.py` mide, en cada fotograma, cuánta piel del brazo queda DENTRO del torso (rayos sobre la
  malla cerrada desde 1,5 mm por fuera de la piel del brazo; lejos de la axila) y el hueco brazo-torso. En la v1, de la
  mitad hacia abajo ~600-700 puntos por brazo: los antebrazos y muñecas se hundían en el pecho y el abdomen y la parte
  alta del brazo en el dorsal (codos pegados a la cintura). Cambiar la preferencia del codo no bastaba (manda el giro
  del húmero): ahora el codo de abajo tiene un objetivo en el marco del torso, `EOX`=13 cm por fuera del hombro y `EOY`=6 cm
  adelante, con peso fuerte al final (`WPA1=8`), y el agarre queda más delante del pecho (`GY1`=24 cm, `GZ1`=8 cm).
  Resultado: ~10 puntos (pliegue de la axila al apretar), hueco ~4 mm. Probado: `EOX` 7 cm -> 265 puntos, 10 cm -> 80.

## 5l. Rojo más rojo: estilo v14 (29-10-2026)

Dueño: «me gusta el degradado pero está como que naranja, dame un color más rojizo». El rojo del v10-v13 era salmón:
sus 9 tonos (`RCOLS`) y los colores de fibras y surcos (`REDC`, `REDG`, `REDL`, `FIBRC`, `LINERC`) llevaban más verde que
azul. Tres opciones con la misma claridad (`ejemplos/jalon_rojo_tonos.jpg`): A rojo suave (`style_v14a`), B carmesí, tira
a rosa (`style_v14b`), **C rojo intenso** (`style_v14c` = `style_v14`, elegida por defecto: verde = azul en todos los
tonos y un poco más saturado). Si se cambia `REDC` hay que poner `REDINV` = 1/`REDC` (el patrón de fibras se divide por él).
`style_v14` es ya el estilo por defecto (`ill/render31.sh`, `ill/anim_dl.sh`, `ill/anim_fp.sh`) y `style_mujer.env`
lleva los mismos colores. El degradado de dos intensidades (principales 1, secundarios 0,30) no cambia.

## 5m. Extensión de tríceps tras nuca en polea (29-10-2026, v1)

```bash
export GT3D=~/cuerpo3d-trabajo; cd $GT3D
NONEFIX=1 ill/mapas.sh maps_tri "triceps:1,anconeus:0.30"
export PFX=TOf; for g in $(seq 0 3 30); do for f in $(seq $g $((g+2))); do [ $f -le 30 ] && ./anim_tri.sh $f 60 & done; wait; done
cd w && ../venv/bin/python -I ../headcheck.py -- TOf*.blend && ../venv/bin/python -I ../armcheck.py -- TOf*.blend; cd ..
YAW=65 PIT=10 TX=0 TY=0.30 TZ=1.12 OSC=4.4 ill/render31.sh TOf maps_tri triceps_tras_nuca
```
- `tricepsoh.py`: de espaldas a una polea alta, con cuerda. Pie izquierdo delante (apoyado) y derecho detrás sobre la
  punta (`FFWD`, `FBK`, `HEELUP`; piernas por cinemática de dos huesos hasta los pies, la más larga casi estirada
  `REARK`), torso inclinado adelante 24° (`TOLEAN`), cabeza en línea y algo arriba (`HEADUP`), escápulas arriba (`TOCLV`).
  Brazos quietos junto a la cabeza (`UDX`, `UDY`: arriba y algo adelante); solo se mueve el codo, bisagra pura de 140°
  (manos tras la nuca) a 8° (`FLEX0/1`); agarre neutro. El codo va donde se pide (`WPA=6`).
- OJO: `agarre_final.env` ya usa `LEAN`, `CLV` y `CLR` (dominadas): aquí `TOLEAN`, `TOCLV`, `TOCLR`.
- `headcheck.py` (nuevo): distancia de brazo, antebrazo y mano a la cabeza (negativo = dentro). Con las manos muy juntas
  tras la nuca (`FIN0=0.30`) los antebrazos entraban 1 cm en la cabeza; con `FIN0=0.15` y `UDY=0.30` quedan a ~1 cm.
- `tricepsoh_geo.py`: la torre y la cuerda del face pull, detrás del atleta (polea alta `PULY`, `PULZ`); las pesas suben.
- Rojo: tríceps (las tres cabezas) a 1, ancóneo a 0,30.

## 5n. Imagen fija para la app: «Hoy: Pull» de espaldas (03-11-2026)

Pedido del dueño con una captura de su pantalla «Mi plan» (`referencias/c7eb47ab-app-pull.jpg`): el muñeco en la misma
postura (de pie, de espaldas, brazos algo separados). La postura de reposo de la base ya es esa (brazos a ~25°), así que
se renderiza la base tal cual (sin deformar nada): vertical 1200×1600, fondo transparente.
```bash
export GT3D=~/cuerpo3d-trabajo; cd $GT3D
NONEFIX=1 ill/mapas.sh maps_pull "latissimus_dorsi:1,trapezius:1,rhomboid_major:1,teres_major:1,infraspinatus:1,teres_minor:1,deltoid_posterior:0.30,biceps_brachii:0.30,brachialis:0.30,brachioradialis:0.30"
cd w && env $(cat ../ill/style_app.env) SHOWBAR=0 HIDEBANCO=1 MAPS=../ill/maps_pull \
  NPZ=../ill/pv/bla_row2.npz YAW=180 PIT=4 TX=0 TY=0 TZ=0.875 OSC=1.95 RX=1200 RY=1600 SMP=32 \
  ../venv/bin/python -I ../ill/rendsculpt.py NB_mc_row3.blend ../ill/r/pull_espalda
```
- En vertical, `OSC` es la ALTURA visible (Blender usa el lado mayor). `SHOWBAR=0`: la base trae una barra.
- De espaldas y con casi toda la espalda en rojo se veían dos defectos que en los vídeos (en diagonal) no: las fibras del
  rojo hacen escalones donde cambian de dirección (trapecio-dorsal, escápula) y el infraespinoso a 0,30 parecía una
  placa blanquecina. Arreglo para esta imagen: infraespinoso y redondo menor a 1 (toda la espalda alta, como en la
  captura) y fibras más suaves con bordes rojos algo más marcados (`FIBR=0.40 FIBL=0.35 FSTR=0.28 ERMIN=0.12 EWFR=1.4`).
  Sin fibras no hay escalones pero los músculos rojos se funden en una mancha. Pendiente: arreglar el campo de fibras.
- Resultado: `ejemplos/pull_espalda.png` (transparente, recortado) y `ejemplos/pull_en_la_app.jpg` (antes / ahora).
- 03-11, dueño: «esa es la distancia a la que se verá en mi app; necesita un poco más de sombras para que los músculos
  se visualicen mejor». A ese tamaño (~590 px de alto) el estilo de los vídeos se ve plano. Opciones comparadas a tamaño
  real de la pantalla (`ejemplos/pull_sombras_opciones.jpg`, `ill/style_app_a..e.env`): A y B poco cambio; C bien; D la más
  marcada pero el rojo saca manchas oscuras (relieve del rojo demasiado fuerte). **E = `ill/style_app.env`** (recomendada):
  sombras de los grises como D (`TONES` 0,30…, `BUMPK=1.8`, `GBUMP=1.1`, `EMIN=0.52`, `MAOP=0.5`, `CAVK=0.12`) y el
  relieve del rojo como C (`RBUMP=0.4`, `REDCON=2.0`), con las fibras suaves de la imagen fija. Solo para imágenes de la
  app; los vídeos siguen con `style_v14`.
- 03-11, dueño: «me gusta la opción C; el rojo está rosado, hazlo más oscuro, que se asemeje a la otra ilustración
  aunque no tan guinda; encuentra un equilibrio». Medido (mediana del rojo de la espalda): su ilustración (145, 62, 57),
  la C (230, 155, 157). Objetivo intermedio ~(185, 90, 85): **`ill/style_app.env` = C + `RCOLS` más oscuros en la parte
  iluminada (`style_app_c_r2.env`)**, mediana (190, 88, 84). `r1` algo más claro (198, 103, 99). Comparación:
  `ejemplos/pull_rojo_opciones.jpg`.

## 5o. Animación de fondo para la app: doble bíceps de espaldas, día «Push» (04-11-2026, v1)

Pedido del dueño: el muñeco aparece en reposo (manos junto al cuerpo, igual que la imagen fija de 5n), hace de forma
fluida el doble bíceps de espaldas, lo mantiene y vuelve a la posición inicial; rojo de los músculos de un día Push. Es
para ponerlo de fondo en la pantalla «Mi plan», como la imagen fija.
```bash
export GT3D=~/cuerpo3d-trabajo; cd $GT3D
NONEFIX=1 ill/mapas.sh maps_push "pec_clavicular:1,pec_sternal:1,deltoid_anterior:1,deltoid_lateral:1,triceps:1,anconeus:0.30"
export PFX=DBf; for g in $(seq 0 4 30); do for f in $(seq $g $((g+3))); do [ $f -le 30 ] && ./anim_db.sh $f 30 & done; wait; done
cd w && ../venv/bin/python -I ../headcheck.py -- DBf*.blend && ../venv/bin/python -I ../armcheck.py -- DBf*.blend; cd ..
ill/render_app.sh DBf maps_push doble_biceps          # 31 fotogramas 1200x1600 transparentes, ~1 min cada uno
python3 ill/app_video.py ill/r/app_doble_biceps out/doble_biceps   # vídeos + fotogramas recortados + maqueta
```
- `dblbiceps.py`: P=0 es exactamente la base en reposo (para que el vídeo empiece igual que la imagen fija). Hacia P=1:
  brazos de lado un poco por encima de los hombros (`DBUX/DBUY/DBUZ`), codos a ~104° con los antebrazos hacia arriba y
  algo hacia dentro (`DBFX`), puños cerrados a la altura de la cabeza con la muñeca doblada hacia ella (`DBWF=28`), pecho
  arriba (`DBSPX=4`), hombros algo arriba (`DBCLV=14`). Cada parte se mezcla desde el reposo: giro del brazo, rotación del
  húmero (~110°) y flexión del codo; la mano sigue al antebrazo. Los dedos se cierran en puño alrededor de un núcleo
  fino invisible (`handrig.wrap2`, `DBFR=7 mm`) entre P 0,15 y 0,85. Las piernas no se mueven.
- Ritmo: con el codo a la vez que el brazo, a mitad de camino quedaba en cruz con los brazos estirados (poco natural);
  el codo se adelanta (`DBLAG=-0.2`, se dobla del todo al 80 % de la subida). `P = F/30` lineal (el guion lo suaviza).
- Comprobado: brazos y puños a más de 8 cm de la cabeza; brazo-torso igual que en reposo (pliegue de la axila).
- Rojo Push: pectoral, deltoides anterior y lateral y tríceps a 1, ancóneo a 0,30. De espaldas solo se ven tríceps y
  hombros (el pecho queda delante).
- `ill/render_app.sh`: como `render31.sh` pero con `style_app.env`, vertical 1200×1600 y la cámara de la imagen fija.
- `ill/app_video.py`: un recorte igual para todos los fotogramas (la figura no salta); secuencia reposo 0,3 s → subida
  31 fotogramas → pose 1,2 s → bajada → reposo 0,5 s, a 25 fps (`HOLDB`, `HOLDT`, `HOLDE`, `FPS`). Saca:
  `_transparente.mov` (ProRes 4444 con transparencia: en el Mac, clic derecho → «Codificar archivos de vídeo
  seleccionados» → HEVC y marcar «Conservar transparencia» da un .mov ligero que el iPhone reproduce con fondo
  transparente), `_frames/` (los 31 fotogramas PNG transparentes recortados, 900 px de alto), `.mp4` (sobre el gris de
  la app) y `_en_la_app.mp4` (maqueta sobre la captura del dueño con «Push · Pecho · Hombros · Tríceps»; el halo claro
  del fondo se reconstruye con un modelo radial para borrar la figura vieja sin marcas).
- Entregado (04-11): `app/doble_biceps_transparente.mov` (666×900, 4,4 s, 16 MB, transparente), `app/doble_biceps/f00..f30.png`
  (los 31 fotogramas transparentes, 0 = reposo, 30 = pose; para animarlos en SwiftUI: reposo 8 fotogramas, 1→30 uno por
  fotograma a 25 fps, pose 30, 29→1, reposo 12), `ejemplos/doble_biceps_en_la_app.mp4` y `.jpg` (maqueta), `ejemplos/doble_biceps.mp4`.
- 04-11, dueño: «en esa posición el hombro debería verse más redondo y no tan plano» (con el brazo arriba el deltoides
  quedaba como una banda estirada, recta desde el trapecio). Arreglo: `deltbulge.py` después de `arap2.py` (ya en
  `anim_db.sh`): abulta la piel por encima de la punta del hombro en la pose (gaussiana centrada `DBA=4,5 cm` a lo largo
  del brazo desde la articulación, `DBY=2 cm` atrás y `DBZ=3,5 cm` arriba, `DBSIG=5 cm`), a lo largo de la normal y
  suavizado sobre la superficie (`DBSM`), proporcional a la subida (0 en reposo: el primer fotograma no cambia).
  `DBBULGE=0.032` (≈19 mm reales): probados 12, 20, 30 y 40 (40 ya parece un bulto). Abultar solo la zona del atlas del
  deltoides (`DBMODE=dome`) o su centro en reposo (`DBMODE=rest`) dejaba bordes irregulares o abultaba la parte baja.
- 04-11, dueño: «ahora realiza un pull»: la misma animación con `maps_pull` (la de la imagen fija 5n) y el texto
  original de la captura (`KEEPTEXT=1`):
  `ill/render_app.sh DBf maps_pull doble_biceps_pull` y
  `KEEPTEXT=1 python3 ill/app_video.py ill/r/app_doble_biceps_pull out/doble_biceps_pull`.
- 04-11, dueño: «ahora la misma animación de frente, mirando hacia adelante con el doble bíceps». Misma pose y cámara
  de frente (`YAW=0`), rojo Push (de frente sí se ve el pecho). Dos arreglos que de frente se notaban:
  - **Giro del hombro** (`untwist.py`, nuevo, `UT=0.4` en `anim_db.sh`): el húmero gira ~100° hacia fuera y la piel del
    brazo giraba entera con él, así que el deltoides (que nace en la clavícula y la escápula) se iba hacia atrás: de
    espaldas era la banda plana y de frente quedaba un hueco gris entre el pecho y el brazo. Cerca del hombro la piel
    vuelve a girar `UT·(1−a(s))` del giro del húmero sobre el eje del brazo (a(s) pasa de 0 a 1 entre `UTS0=-0.10` y
    `UTS1=0.55` del largo del brazo; máscara suave de la piel del brazo). Con `UT=0.7` sale un pico en el hombro.
    Con el giro corregido el abultamiento baja a `DBBULGE=0.020`.
  - **Puños cerrados** (`DBFR=0.003`, `DBDN=0.008`): antes el núcleo invisible quedaba a 16,5 mm de los nudillos y el
    puño parecía un gancho con un agujero; con `DN=0` los dedos se cruzan.
  ```bash
  export PFX=DFf UT=0.4 DBBULGE=0.020; for g in $(seq 0 4 30); do for f in $(seq $g $((g+3))); do [ $f -le 30 ] && ./anim_db.sh $f 30 & done; wait; done
  YAW=0 ill/render_app.sh DFf maps_push doble_biceps_frente
  python3 ill/app_video.py ill/r/app_doble_biceps_frente out/doble_biceps_frente
  ```
  Las versiones de espaldas v2 (ya entregadas) se hicieron sin `untwist.py` y con el puño antiguo (`DBFR=0.007
  DBDN=0.0165`, `DBBULGE=0.032`).

## 5p. Mapas v2: fibras suaves, sin rebabas, sin grietas (10-11-2026)

Revisión del muñeco con el modelo nuevo (`ejemplos/estado_09-11_*.jpg`). Tres defectos de los mapas, arreglados en el
horneado (`ill/bakemaps.py`), el render (`ill/rendsculpt.py`) y el atlas (`ill/spec/front.py`); comparación en
`ejemplos/mapas_v2_antes_ahora.jpg`, `mapas_v2_fibras.jpg`, `mapas_v2_clavicula.jpg`.
- **Fibras con escalones**: la fase de las rayas era un valor por vértice y se interpolaba triángulo a triángulo, así
  que las rayas se quebraban en cada arista (zigzag en el dorsal y el trapecio vistos de frente). Ahora `bakemaps.py`
  hornea la fase por texel (`fph16.<tile>.png`, `fmask16`) desenfocada DENTRO de cada músculo (`FBLURPX=3`), y
  `rendsculpt.py` la usa si existe (`FPHTEX=0` vuelve a la de vértices). Las rayas salen curvas y continuas.
- **Rebabas rojas** (tiras junto a la clavícula y el esternón, trocitos en la axila): en los bordes músculo|piel el
  horneado adivinaba por votos qué músculo había a cada lado de la línea y a veces elegía otro vecino (p. ej. pectoral
  en el lado de piel de la línea del esternocleidomastoideo) y pintaba una tira de ese músculo pegada a la línea.
  Ahora usa los dos lados que ya conoce el atlas aunque uno sea piel. Además un filtro de mayoría 5×5 (`LMAJ`) limpia
  los texels sueltos de las etiquetas.
- **Grietas en la cintura**: eran las dentelladas del serrato con el oblicuo, dibujadas como dos zetas duras y
  profundas. Ahora ese zigzag es borde suave (`~` en `spec/front.py`): queda una insinuación, no una grieta.
- Hace falta reconstruir el atlas (`ill/atlas_rebuild.sh`, 2 min) y volver a hornear cada carpeta de mapas con
  `ill/mapas.sh` (los `maps_*` viejos del disco no tienen `fph16`: el render sigue funcionando con ellos, pero con las
  fibras antiguas). `restaurar.sh` ya lo hace todo. Copias de los mapas viejos: `maps_push_v1`, `maps_pull_v1`.
- OJO para quien escriba comprobaciones: en `pv/bla.npz`, `names[0]` ya es `'none'` (no hay que anteponerlo);
  `deltbulge.py` lo tenía mal (solo afectaba a los modos `dome`/`rest`, no al usado).
- Con estos mapas se rehacen las tres animaciones del doble bíceps (espaldas Push/Pull y frente), ahora las tres con
  los puños cerrados y el giro del hombro corregido (`DFf`, sección 5o): `YAW=180 ill/render_app.sh DFf maps_push
  doble_biceps`, `YAW=180 ill/render_app.sh DFf maps_pull doble_biceps_pull`, `YAW=0 ill/render_app.sh DFf maps_push
  doble_biceps_frente`.

- Paso 3 (opcional, 10-11): opciones de rostro del hombre en `ejemplos/rostro_opciones_10-11.jpg`. `facebuild.py` admite
  `MANFACE=1` (labios, línea de la boca y pestañas también en el hombre; la boca del hombre está en `LIPZ=1.5073`, 4 cm
  más arriba que la de la mujer). B = `MANFACE=1 LIPZ=1.5073 LIPT=0.16 MLINE=0.45 LASHT=0.65 LASHB=0.20`;
  C = B + `LIPDN=-0.0006 BROWT=0.80 BZB=1.5897 BZT=1.5977` (comisuras un poco arriba, cejas más claras y 1 mm más
  altas). Se construyen con `venv/bin/python -I facebuild.py <bundle> w/NB_mc_row2.blend w/face_X.blend` desde la raíz
  del proyecto.
- 10-11, dueño: «C, gesto más amable pero con una ligera sonrisa». `facebuild.py` tiene ahora `SMILE` (m): las comisuras
  suben (y van un poco atrás y afuera) con caída gaussiana `SMX`×`SMZ`, y la mejilla justo encima se levanta un poco
  (`SMCH`); la línea de la boca sigue a las comisuras con `LIPDN` negativo. Probadas 2, 4,5 y 6 mm
  (`ejemplos/rostro_sonrisa_opciones.jpg`): **4,5 mm** (6 ya frunce). **Base nueva del hombre = C + sonrisa**:
  ```bash
  MANFACE=1 LIPZ=1.5073 LIPT=0.16 MLINE=0.45 LASHT=0.65 LASHB=0.20 BROWT=0.80 BZB=1.5897 BZT=1.5977 \
    SMILE=0.0045 SMX=0.013 SMZ=0.010 SMCH=0.002 LIPDN=-0.0030 venv/bin/python -I facebuild.py <bundle> w/NB_mc_row2.blend w/NB_mc_row3.blend
  ```
  (la cara anterior queda en `w/NB_mc_row3_v1.blend`). Todas las poses se rehacen con esta base.

## 5q. Hombros, axilas y codos naturales en el doble bíceps (10-11-2026, v4)

Dueño: «los hombros se ven en punta, antinatural; las axilas y la sangradura no se ven naturales; parece un plástico
mal doblado», con dos fotos de referencia (doble bíceps de espaldas y de frente). Cuatro causas, cuatro arreglos, en
este orden dentro de `anim_db.sh` (todos escalan con la pose: en el fotograma 0 no cambian nada):
1. **Pesos del brazo** (`armweights.py`, aplicado una vez a la base `w/NB_mc_row3.blend`; copia previa
   `NB_mc_row3_pre_aw.blend`): la piel de la cara trasera/interna del brazo, a 5-9 cm del hombro, tenía un 20-30 % de
   peso en el tórax (chest/spine). Con el brazo arriba y girado esa piel se quedaba atrás y hacía un pliegue agudo a lo
   largo del brazo (la «punta»). Ese peso pasa al húmero entre `S0=3,5` y `S1=8,5` cm del hombro.
2. **Reparto del giro del húmero** (`TW=1 TW0=0.3 TB=0.6`, opción que ya existía en `skinstack.py` y no se usaba): el
   hombro toma solo el 30 % del giro de ~100° y el resto se reparte hasta el 60 % del brazo, como los huesos de giro
   de los rigs de videojuego. Sustituye a `untwist.py` (`UT=0`). Quita el aspecto de brazo retorcido.
3. **Bola del hombro** (`shoulderfix.py`): esfera de 64 mm en la cabeza del húmero (2,5 cm a lo largo del brazo); la
   piel del hombro que cae dentro se empuja a la superficie y se suaviza (`K=0.8`, `LOWK=0.2` en el lado de la axila).
4. **Axila hueca** (`armpitfix.py`): la piel bajo la articulación, entre el brazo y el tórax (máscara en la pose, sin
   tocar los pliegues del pectoral y del dorsal), se recoge hacia una esfera de 45 mm en la articulación. Antes era
   una lona tensa; ahora es un hueco entre los dos pliegues, como en la foto.
5. **Codo** (`elbowfix.py`): el bíceps y el braquial se abultan con la flexión (`BAMP=16 mm` × flexión, perfil de
   cúpula del atlas) y la piel de la cara interna del codo (65 mm alrededor, lado de la bisectriz) se relaja (20
   iteraciones) y se mantiene fuera de una esfera de 45 mm: la sangradura pasa de V a valle redondeado.
Comparaciones: `ejemplos/hombro_v4_antes_ahora.jpg` (paso 1-3). `deltbulge.py` queda sin uso (`DBBULGE=0`).
Superado por la v5 (sección 5r): los pasos 1, 3 y 4 se sustituyeron.

## 5r. Hombro con bola, bíceps con pico y axila limpia: doble bíceps v5 (11-11-2026)

Dueño, tras ver la v4: «revisa el bíceps, se ve antinatural» (con la foto de frente como objetivo). Al mirar cortes del
brazo (perpendiculares al húmero, `ejemplos/hombro_v5_cortes_diagnostico.png`: fila 1 = solo skinning, fila 2 = tras
`arap2.py`, fila 3 = tras `shoulderfix.py`, fila 4 = tras `armpitfix.py`) salieron las causas de fondo. La v4 las
tapaba con parches; la v5 las quita:
1. **El hombro se hundía por `arap2.py`.** El skinning (CoR) deja una buena cúpula de deltoides, 3 cm por encima del
   hueso. La relajación ARAP limpia la axila pero aplasta la parte de arriba: la piel quedaba 2 cm POR DEBAJO del eje
   del húmero (hombro plano, brazo fino en la raíz, bíceps como un globo aparte). `shoulderfix.py` lo empeoraba
   (empujaba hacia abajo la piel que ya estaba bajo el centro de la esfera). Arreglo: **`capkeep.py`** mezcla las dos
   mallas por la altura sobre el eje del brazo en la pose: arriba la del skinning (cúpula), abajo la relajada (axila),
   transición entre −35 y +10 mm (`Y0`/`Y1`). `shoulderfix.py` y `armpitfix.py` quedan apagados (`SFK`, `AXK` = 0).
   Ojo: los demás ejercicios con el brazo arriba (dominadas, jalón, tríceps tras nuca) usan `arap2.py` sin
   `capkeep.py`; al rehacerlos conviene añadirlo.
2. **Pesos de la axila** (**`armpitweights.py`**, sustituye a `armweights.py`; se aplica una vez a la base:
   `NB_mc_row3_pre_aw.blend` → `NB_mc_row3.blend`; la versión anterior queda en `NB_mc_row3_aw1.blend`). En reposo el
   brazo descansa contra el costado (se tocan entre z = 1,15 y 1,22) y los pesos originales se «contagiaban» por
   cercanía: el serrato y el dorsal, 10-20 cm bajo el hombro, tenían 50-80 % de brazo (el costado subía con el brazo:
   lona delante de la axila) y `armweights.py` además mandó parte del costado al 94 % (un pico que atravesaba el
   tríceps). Para distinguir brazo de costado donde se tocan se usa una coordenada armónica SOBRE la superficie
   (1 del codo en adelante, 0 en el tronco): en la zona de contacto el costado vale 0,14-0,20 y la cara interna del
   brazo 0,46-0,59. Brazo (> 0,42) = peso 1; costillas (etiquetas de serrato, oblicuo, etc. con < 0,25; pectoral a más
   de 15 cm; dorsal a más de 20 cm) = 0; la parte alta del hombro conserva sus pesos; el resto (axila, borde del
   pectoral, dorsal alto) se resuelve armónico entre ambos.
3. **Giro del húmero**: `TW0=0 TB=0.7` (antes 0,3 / 0,6): el hombro no gira con el húmero y el deltoides anterior
   queda mirando al frente, como en la foto.
4. **Bíceps con pico** (`elbowfix.py`, `BMODE=peak`, por defecto): antes se inflaba toda la etiqueta del bíceps a lo
   largo de sus normales (globo largo y plano). Ahora la piel del brazo se desplaza hacia el lado del antebrazo con una
   gaussiana a lo largo del brazo (centro `BS0=0.56`, anchos `BSA=0.13` hacia el hombro y `BSB=0.10` hacia el codo, en
   fracción del brazo), lóbulo alrededor (`BCP=2`) y `BAMP=34 mm` × flexión; el tríceps cuelga 6 mm (`TAMP`) y el
   antebrazo gana 7 mm cerca del codo (`FAMP`, centro `FS0=0.24`). Cambios de pocos mm se notan mucho en este estilo.
5. **Hoyito del tríceps y motas** (`ill/bakemaps.py`, copia previa `bakemaps_v2.py`): la línea dorsal|serrato pasa a
   3 mm de la cara interna del brazo en reposo y se «imprimía» en el tríceps. Ahora una línea solo cuenta para un
   téxel si mira hacia el mismo lado Y es borde de uno de los músculos de su triángulo (`SURFK=96`, `SURFDOT=0`); si
   no, se toma la siguiente línea válida. `ill/atlas.py` (copia `atlas_v2.py`) además reetiqueta islas sueltas de
   menos de 40 vértices (había 10 en el brazo derecho con etiqueta de dorsal/serrato). Atlas y mapas rehechos
   (`maps_push`, `maps_pull`; los anteriores en `maps_push_v2`, `maps_pull_v2`; atlas anterior en `pv/*_v2.npz`).
   Los mapas de los otros ejercicios siguen con el horneado viejo hasta que se rehagan con `ill/mapas.sh`.

Cadena actual de `anim_db.sh` (la v4 queda en `anim_db_v4.sh`): `dblbiceps.py` → `arap2.py` → `capkeep.py` →
`elbowfix.py`. Poses `w/DG00..30.blend` (`PFX=DG ./anim_db.sh F 30`, 4 en paralelo: 1,5 min las 31). El fotograma 0
difiere de la base menos de 1 mm. Comparaciones: `ejemplos/v5_frente_antes_ahora.jpg`, `v5_espalda_antes_ahora.jpg`.
Herramientas de diagnóstico que sirvieron (no están en el repo, son cortas): cortes del brazo perpendiculares al eje
coloreados por músculo, y perfil superior/inferior del brazo por tramos de x. No fiarse del ojo en montajes pequeños.

## 6. Decisiones de estilo del dueño (no deshacer)

- Lo que importa es cómo se ve **renderizado a distancia normal/lejana**, no de cerca.
- Cada músculo: más oscuro/intenso en el borde y más claro hacia el centro (degradado tipo lápiz), sin cortes
  oscuros duros («robotizado» = mal). Centros no blancos puros. Cortes grises suaves (aclarados otra vez el 23-10).
- Músculos más **redondeados** (por sombreado, no por tamaño). Espalda como grandes zonas, franja clara en la columna.
- Rojo **con degradado, nunca naranja**; más profundo solo en la parte baja/sombra del músculo.
- Short tan corto como en la referencia; cabeza CON rostro y pelo corto desde el 28-10-2026 (antes sin cara); sin suelo ni sombra (fondo blanco/transparente).
- Máquinas como en las referencias: estructura gris clara, pila de pesas y patas negras.
- Remo: espalda plana y bisagra marcada. Face pull: pulgares junto a los topes de la cuerda, codos altos.

## 7. Problemas conocidos

- Face pull: de cerca, al final del movimiento, el borde del rojo en el hombro se ve irregular (la piel se estira);
  a distancia no se nota.
- Remo: el cuello miraba hacia abajo (`NECKT=-40`); corregido en v7 con `NECKT=0`.
- Contraste general algo menor que la referencia.

## 8. Cómo trabajar con el dueño

Español, sin jerga, explicando lo que se verá en la imagen. Enseñar vistas previas pequeñas y renderizar en HD solo
lo aprobado. Mandar imágenes en 16:9. Chats cortos: uno por tarea grande (los largos gastan muchos créditos).

## 9. Mensaje para empezar un chat nuevo

> Vamos a seguir con el muñeco 3D de ejercicios. Trae la rama `claude/youthful-maxwell-ns8lt5` de mi repositorio
> Gym-tracker-2, lee `cuerpo3d/GUIA.md` y restaura el proyecto con `cuerpo3d/restaurar.sh` (crea también la versión
> mujer). Luego: <TAREA NUEVA>.

Estado al 04-11-2026: rojo de los vídeos = estilo v14 (5l); degradado de dos intensidades (principales 1, secundarios
0,30). Hechos con cara y estilo actual: jalón cerrado v3 (5k), extensión de tríceps tras nuca v1 (5m). Imagen fija de la
app «Hoy: Pull» de espaldas (5n) con `ill/style_app.env` (sombra C + rojo más oscuro, elegidos por el dueño).
Animación de fondo de la app: doble bíceps de espaldas con rojo Push (5o). Mujer v3 (5j).
Comprobaciones de choques: `armcheck.py` (brazo-torso), `headcheck.py` (brazo-cabeza), `fistcheck.py`, `objcheck.py`.
Siguiente posible: imágenes de la app para los otros días (Legs, Push…) con `style_app.env`; rehacer los vídeos viejos.
Ritmo, formato 16:9 y plan por familias: sección 5c.