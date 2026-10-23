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
| Mapa de músculos: espalda, brazos, piernas | hecho | |
| Mapa de músculos: pecho, abdomen, oblicuos, serrato, cuello por delante (`ill/spec/front.py`) | hecho el 23-10-2026, falta el visto bueno del dueño | `ejemplos/facepull_frente_16x9_v2.jpg` (antes: `facepull_frente_16x9.jpg`) |

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

**Siguiente:** según lo que diga el dueño de la imagen de frente, rehacer el GIF completo del face pull
(sección 4) o pasar a otro ejercicio.

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
