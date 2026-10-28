# Muñeco 3D de ejercicios: guía del proyecto

Copia de seguridad del muñeco 3D (maniquí sin cara, piel gris clara, short oscuro) que hace los ejercicios de la
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
| Remo con barra | aprobado (v6, estilo v7) | `ejemplos/remo_barra_v6.gif` |
| Face pull en polea | hecho (v1), con torre de polea y pesas que suben | `ejemplos/facepull_v1.gif`, `ejemplos/facepull_*_16x9.jpg` |
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

**Estándar congelado (no volver a discutirlo):** estilo v10 (antes v8); cuerpo v2; 1920×1080 (16:9); 31 posturas; ritmo del peso muerto
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

## 6. Decisiones de estilo del dueño (no deshacer)

- Lo que importa es cómo se ve **renderizado a distancia normal/lejana**, no de cerca.
- Cada músculo: más oscuro/intenso en el borde y más claro hacia el centro (degradado tipo lápiz), sin cortes
  oscuros duros («robotizado» = mal). Centros no blancos puros. Cortes grises suaves (aclarados otra vez el 23-10).
- Músculos más **redondeados** (por sombreado, no por tamaño). Espalda como grandes zonas, franja clara en la columna.
- Rojo **con degradado, nunca naranja**; más profundo solo en la parte baja/sombra del músculo.
- Short tan corto como en la referencia; cabeza sin cara; sin suelo ni sombra (fondo blanco/transparente).
- Máquinas como en las referencias: estructura gris clara, pila de pesas y patas negras.
- Remo: espalda plana y bisagra marcada. Face pull: pulgares junto a los topes de la cuerda, codos altos.

## 7. Problemas conocidos

- Face pull: de cerca, al final del movimiento, el borde del rojo en el hombro se ve irregular (la piel se estira);
  a distancia no se nota.
- Remo: el cuello aún mira algo hacia abajo.
- Contraste general algo menor que la referencia.

## 8. Cómo trabajar con el dueño

Español, sin jerga, explicando lo que se verá en la imagen. Enseñar vistas previas pequeñas y renderizar en HD solo
lo aprobado. Mandar imágenes en 16:9. Chats cortos: uno por tarea grande (los largos gastan muchos créditos).

## 9. Mensaje para empezar un chat nuevo

> Vamos a seguir con el muñeco 3D de ejercicios. Trae la rama `claude/youthful-maxwell-ns8lt5` de mi repositorio
> Gym-tracker-2, lee `cuerpo3d/GUIA.md` y restaura el proyecto con `cuerpo3d/restaurar.sh`. Luego haz el mapa de
> músculos del pecho y el abdomen (sección 5) y enséñame el face pull de frente con los brazos extendidos, en 16:9.
>
> (Ya hecho el 23-10-2026: para el siguiente chat, cambiar la última frase por la tarea nueva.)
