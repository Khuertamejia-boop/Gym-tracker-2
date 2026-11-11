# Brief: make the SHOULDER deform beautifully in a pull-up (new 3D body)

## Goal (from the owner, a non-technical gym-app owner)
A 3D mannequin body (faceless head, light-gray skin, dark shorts) animated doing pull-ups for an iPhone gym app.
The owner's complaint: "the arm deforms completely during the exercise". Target look = the reference illustration
`/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/0d3967d4-image.png` (blue smooth body hanging from a bar:
round deltoids, smooth armpit, lats visible, no creases, no flat planes, arms never look twisted or deflated).
The owner's screenshot of the bad old version: `/root/.claude/uploads/8036e25a-39fc-507e-8939-935aaa1c5ddc/8ef31cc4-image.png`.
Priority: aesthetics + believable anatomy over muscle mass. It must look good in EVERY frame (P=0 dead hang .. P=1 top).

## What is already fixed (do not redo)
- Arm kinematics are now anatomical (`pullup5.py`): elbow is a pure hinge, elbow direction optimised, forearm
  pronation spread over forearm twist bones `fa_tw1..3` (wrist no longer pinches), girdle (clavicle bone) elevated
  in the hang and lowered at the top, straight arms in the dead hang, forearms vertical at the top.
- Hands/grip are approved: do not touch fingers, hand, bar, grip settings.

## What is still wrong (your job): the SHOULDER region skin
See `w/r/sh1.jpg` (current state, rows = P 0, 0.3, 0.6, 1; columns = yaw -20 front-ish, -70 side, -120 back-side, 180 back;
left shoulder in close-up). Problems: at P=0.3–0.6 the deltoid loses its round cap, a crease runs over the top of the
shoulder from the neck to the arm, the pec/deltoid meet the upper arm in flat planes ("doll joint"/"T-shirt sleeve"),
the posterior shoulder has a bulge + crease at P=0, the upper arm near the shoulder looks deflated. The torso far from
the shoulder, the forearm/hand and the head are fine.

## Environment and tools (all paths relative to S=/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad)
- Blender is a Python module: run scripts as `cd $S/w && $S/venv/bin/python -I $S/<script>.py in.blend out.blend`
  (scripts take the last two argv as input/output). No GUI. 4 CPU cores shared with other agents.
- Base file for you: `w/NB_t.blend` (body 'Hi' ~122k verts single closed mesh + armature 'Rig'). DO NOT overwrite any
  existing file in `w/` or `$S`. Work ONLY inside your own folder `w/exp_<yourname>/` and give every file you create a
  unique prefix (render helpers name outputs by file basename, so collisions with other agents must be avoided).
- Rig bones: hips, spine, chest, neck, head, clavicle.L/R (sternum -> shoulder joint; acts as the whole shoulder girdle /
  scapula), upper_arm.L/R, forearm.L/R, fa_tw1..3.L/R (forearm twist), hand.L/R, fingers, thigh/shin/foot, bar.
  `delt.L/R` = helper bone at the shoulder joint, child of clavicle, COPY_ROTATION of upper_arm (local space, influence
  0.5, i.e. half the arm rotation) — its vertex group exists but is EMPTY (unused so far). Bone rolls: arm bones' local Z =
  back of the hand / lateral; local X ~ forward at rest. Rest pose = A-pose, arms down ~25 deg. Units metres, body faces -Y,
  Z up, left side = +X. Left shoulder joint at rest (0.175,-0.033,1.355); clavicle head (0.025,-0.007,1.385).
- Skin weights: automatic heat weights (computed on the base mesh, transferred), hands re-weighted, forearm split into
  twist bones. Vertex groups = bone names + 'CS' (finger corrective-smooth mask). Shoulder weights were never tuned.
- Mesh attributes used by the renderer (keep them intact): POINT mq, ln, shorts, mu, groove, mdist; FACE mseg,
  material_index. The renderer shows only object 'Hi' (+ bar). Modifiers are added by the pose script.
- Pose a frame: `cd $S/w && set -a && . $S/agarre_final.env && set +a && P=0.3 $S/venv/bin/python -I $S/pullup5.py IN.blend OUT.blend`
  pullup5.py builds the modifier stack: Armature (LBS; env PV=1 would make it dual-quaternion for the whole body,
  which previously ballooned the chest/lats with the old weights), CorrectiveSmooth 'CS' (fingers),
  CorrectiveSmooth2 on group 'CS2' = delta-mush ball around each shoulder (env CS2IT=100 iterations, S2D0=0.10/S2D1=0.24
  inner/outer radius from the shoulder joint, rest_source ORCO). You may copy pullup5.py into your folder and change the
  modifier part, or post-process the posed file, or change the rig/weights in the base file — your call.
- Close-up shoulder sheet: `$S/shoulderviews.sh OUT.jpg "-20 -70 -120 180" file1.blend file2.blend ...`
  (run from anywhere; files are looked up in $S/w, so pass paths relative to $S/w e.g. exp_a/A_P0.blend; renders go to
  $S/w/r/sv_<basename>_<yaw>_cus.png; env RS (px, default 380), SMP (samples, 8), OSC (zoom, 0.55)).
  Full upper body sheet: `$S/diagsheet.sh PREFIX "suffixes" "yaws" OUT.jpg 360` renders $S/w/PREFIX<suffix>.blend
  (prefix may include a sub-folder, e.g. `exp_a/A_P` with suffixes "0 0.3 0.6 1"). For BOTH sheet scripts the OUT path is relative to $S/w (e.g. `exp_a/sheet1.jpg`), or absolute.
  View images with the Read tool. Keep RES ≤ 400 and SMP ≤ 8 while iterating; render at most 2 jobs at a time.
- Measurements: `twistdiag.py` (joint angles), `pick.py` (vertex info). Old-body scripts you may adapt (they were tuned
  for a different mesh, parameters will need re-tuning): `harmonicw.py` (smooth harmonic upper-arm weight field around
  the shoulder; also optional clavicle/scapula field CLAVF=1), `addhelper.py` (remaps weights onto the half-rotation
  `delt` helper: helper = 1-|2u-1|, arm = max(0,2u-1), torso scaled by max(0,1-2u)), `smoothweights.py`, `fair.py`
  (bi-harmonic fair strip under the arm, bakes the mesh), `arap.py` and `relax.py` (post-pose shoulder re-solves, bake).
- Evaluation protocol (use exactly this so results are comparable): P = 0, 0.3, 0.6, 1 ; shoulder sheet yaws
  "-20 -70 -120 180" ; plus one full upper-body sheet at P 0 and 0.6 with yaws "0 -35 180" to make sure nothing else
  broke (no ballooned chest, no torn skin, arms not shrunken). Compare with `w/r/sh1.jpg` (baseline) and the reference.

## Deliverable (your final answer)
1. A pipeline that is reproducible: script(s) in your folder + exact commands/env to go from `w/NB_t.blend` to posed
   frames for any P.
2. Paths of your final shoulder sheet and full-body sheet.
3. An honest assessment: what improved vs baseline, what defects remain (be specific: which P / view), runtime per frame.
