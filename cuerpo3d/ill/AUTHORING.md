# Muscle atlas authoring guide (3D gym-app mannequin)

## Why
A gym app (iPhone) shows a 3D mannequin doing exercises. The owner wants the body drawn like classic **exercise
anatomy plates**: near-white body, every superficial muscle outlined by a thin dark line, faint fibre striations, and
the worked muscles in coral red with fibre lines. Target style examples (view them with the Read tool):
- `/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/8ccf8362-image.jpg`  bent-over row, back view (THE main target)
- `/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/697dfdbd-image.jpg`  cable fly, front view (pecs, abs, legs front)
- `/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/e5d5044e-image.jpg`  bench dips, side view (shoulder, chest, legs)
- `/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/14cf49ef-image.jpg`  dumbbell curl, front view (arms, abs, legs)
- `/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/85b4a749-image.jpg`  lying leg curl (back of legs, back)
- `/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/1f41ce2d-image.jpg`  lat pulldown (back)
- `/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/b1af4f26-image.jpg`  leg extension (quads)
- `/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/0aec36d1-image.jpg`  pull-up, back view
- `/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/f6be1ff1-image.jpg`  labelled arm anatomy chart (Spanish)
Study how those plates divide the surface into muscles: that division is what you are drawing.

## What you produce
A spec file (plain Python) that defines the superficial muscles of your body region on the LEFT side of the body
(+x). The right side is mirrored automatically. The compiler turns it into per-vertex data (which muscle, distance to
the borders, fibre direction) that the renderer uses for lines, fibres and the red highlight.

Body: rest pose (A-pose, arms ~25 deg down, palms facing the thighs), metres, Z up, the body faces -Y (front = -y,
back = +y), left side = +x. Height ~1.70 m. The mesh is a sculpted athletic body: its muscle relief (grooves between
muscles) is visible in the previews and should guide your borders.

## Spec format
See the header of `ill/atlas.py` (full reference). In short:
```python
LM = {                                   # landmarks (surface points), LEFT side
  'sps_med': ('B', 0.078, 1.335),        # seen from the back at x=0.078, z=1.335 (first surface hit)
  'bic_top': ('limb','upper_arm.L',0.25,0),  # on the upper arm, 25% down the bone, front (0)
  ...
}
MUSCLES = {
  'infraspinatus': dict(loop=['sps_med','sps_mid','is_lat1','is_lat2','inf_ang','is_med1'],
                        seed=('B',0.11,1.28), origin=('inf_ang','sps_med'), insertion=('sps_mid','is_lat2'), sp=6),
  'triceps_tendon': dict(loop=[...], seed=..., kind='tendon'),
}
```
- Landmark spec kinds: `F`/`B` (x,z), `L`/`R` (y,z), `T`/`U` (x,y), `MX` (x0,y,z: ray going +x from a point inside
  the body; use it for the flank under the hanging arm and for inner thigh/arm), `V` (yaw,pitch,a,b oblique view),
  `limb` (bone,t,angle: 0 front, 90 outer side, 180 back, -90 inner side), `P` (x,y,z nearest), `AT` (name,dx,dy,dz).
  Bones: upper_arm.L, forearm.L, hand.L, thigh.L, shin.L, foot.L, clavicle.L, spine, chest, neck, hips.
- `loop`: the closed border in order. Neighbouring muscles MUST use the same landmarks for their common border (the
  path between two landmarks is computed once, so shared landmark pairs give one single line). Append `~` to a name
  to make the segment to the next landmark a SOFT line (division inside one muscle: e.g. deltoid heads, trapezius
  parts, pectoral clavicular/sternal heads). Append `!` to force a straight (shortest) path; by default paths follow
  the sculpted grooves a little.
- `origin`/`insertion`: (first, last) landmarks of the two arcs of the loop where the fibres start and end, in loop
  order, so that the loop reads origin-arc ... insertion-arc ... . Fibres run from one arc to the other, so pick them
  so the striations follow the real fibre direction (fan muscles converge to the insertion). `sp`: fibre line spacing
  in mm (5-8). `kind='tendon'` for aponeuroses/tendons (drawn plain, no fibres).
- `seed`: a point well inside the muscle (a spec tuple or a landmark name).
- `group` (optional): e.g. all trapezius parts can carry group 'trapezius'; default = muscle name.

## Shared landmarks (do NOT redefine or move; ask in your report if one is wrong)
`ill/spec/shared.py` defines the junction points where regions meet (midline: occ c7 t3 t7 t12 l4 sac jug xiph
pubis; clavicle: sc_l clav_mid trap_clav dp_top acr; scapular spine: sps_med sps_mid sps_lat; inf_ang; armpit:
ax_back ax_front dp_low delt_ins; flank: lat_ax lat_mid crest_side; crest_back asis) and CHAINS (borders two regions
share). Use them for every border that touches another region. Your own landmark names must be prefixed with your
region key (e.g. `bk_`, `fr_`, `ar_`, `lg_`) so the four specs never collide.

## Tools (run from `ill/`; S=/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad)
```
cd $S/ill
# compile (shared + your spec; add other regions' specs read-only if you want to check neighbours)
$S/venv/bin/python -I atlas.py pv_<key>/a.npz spec/shared.py spec/<key>.py
# where do my landmarks land? (3D + view coordinates)
$S/venv/bin/python -I atlas.py --print spec/shared.py spec/<key>.py
# preview: VIEW = KIND[:a,b,size]  (F/B: world x,z  L/R: world y,z  T: x,y  V<yaw>,<pitch>: picture-plane a,b)
THREADS=2 $S/venv/bin/python -I atlas_preview.py pv_<key>/a.npz pv_<key>/p B:0.12,1.25,0.5 L:0.0,1.2,0.6 V135,20:0,1.1,0.9
```
The preview draws muscles in pastel colours with their names, black lines on hard borders, grey on soft ones, fibre
stripes, your landmarks (pink dots, left side) and a world-coordinate grid (1 cm minor lines with `GRID=0.01`, labels
every 5 cells). Env: `RES` (px, 900), `LABELS=0` hides landmark names, `MNAMES=0` hides muscle names, `RLR` (relief
contrast, smaller = stronger, default 7). An empty spec preview shows the bare sculpted relief: start there to see
where the body's own muscle grooves are. Read the PNGs with the Read tool. Work only inside `ill/pv_<key>/` and your
spec file. Never edit atlas.py, atlas_preview.py, shared.py or another region's spec. 4 CPU cores are shared by 4
authors: keep THREADS=2, RES<=1000, and render a few views per call.

## Quality bar
- Superficial muscles only, shapes and proportions as in standard anatomy plates (Netter/Kenhub style) and the
  reference images. Every visible muscle of your region must be present; borders where the plates draw lines.
- Borders sit in the body's sculpted grooves when the groove exists; otherwise at the anatomically correct place
  relative to the bony landmarks. Smooth, natural curves: 2-5 cm between landmarks, closer on tight curves.
- No compiler PROBLEM lines (LEAK, overlaps, detours, unknown landmarks). No unintended gaps between neighbouring
  muscles (a shared border must be ONE line). Plain skin is fine only where anatomy has no muscle under the skin
  (bony points: clavicle strip, acromion, elbow, knee, spine line, iliac crest, shin bone, ankles).
- Fibre striations must follow the real fibre direction of each muscle.
- Check every muscle from at least two views (front/back/side/oblique) and zoomed in.

## Regions, owners and who depends on whom
| key | prefix | owns | shares borders with |
|---|---|---|---|
| back | `bk_` | trapezius (upper/middle/lower parts), DELTOID (anterior/lateral/posterior heads), infraspinatus, teres minor, teres major, latissimus dorsi, erector spinae and the low-back fascia, rhomboid/levator/splenius only where the plates show them | front (deltopectoral chain, lat_front chain), arm (deltoid lower border, armpit), leg (pelvis chain) |
| front | `fr_` | pectoralis major (clavicular + sternal heads), sternocleidomastoid, serratus anterior (digitations), external oblique, rectus abdominis (segments + linea alba), other visible neck-front muscles | back (deltopectoral, lat_front), arm (pec_arm chain), leg (pelvis chain) |
| arm | `ar_` | biceps, brachialis, coracobrachialis, triceps (long/lateral/medial heads + tendon), brachioradialis, wrist/finger extensors, anconeus, flexor group, pronator teres (down to the wrist; hands stay plain) | back (deltoid lower border, teres major/lats at the armpit — use the landmarks of spec/back.py), front (pec_arm chain) |
| leg | `lg_` | gluteus maximus, gluteus medius, tensor fasciae latae, iliotibial band, quadriceps (rectus femoris, vastus lateralis, vastus medialis), sartorius, adductors/gracilis, hamstrings (biceps femoris, semitendinosus, semimembranosus), gastrocnemius (2 heads), soleus, Achilles tendon, tibialis anterior, toe extensors, peroneus, patella/patellar tendon (down to the ankle; feet stay plain) | back/front (pelvis chain) |
The arm author starts after the back author has finished and must take the deltoid's lower border and the
teres major / latissimus landmarks from `spec/back.py` (read-only). The muscles under the shorts (gluteals, top of
the thigh) are still needed: some exercises show them in red through the shorts.

## Budget
Images are expensive: render at RES 700-900, crop to the area you are checking, and read only the images you need.
Prefer 2-4 views per render call. Stop iterating when the quality bar is met.
