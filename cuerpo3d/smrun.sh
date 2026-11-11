#!/bin/bash
# soft body: detailed -> smooth displacement -> mannequin head -> pose -> 3 renders (front / side / back)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; W=$S/w; T=$1; SRC=${SRC:-N_1.blend}; cd $W
(eval "$NX"; $S/venv/bin/python -I scripts/neckhf.py ${BASE:-B3_b5.blend} N_$T.blend 2>&1 | grep -i "Trace" -A4)
SRC=N_$T.blend
(eval "$SX"; $S/venv/bin/python -I scripts/smoothd.py $SRC SM_$T.blend 2>&1 | grep -i "Trace\|assert" -A4)
(eval "$HX"; $S/venv/bin/python -I scripts/headnew.py SM_$T.blend SMH_$T.blend 2>&1 | grep -i "Trace" -A4)
(eval "$PX"; ROLL=-20 $S/venv/bin/python -I $S/posearm.py SMH_$T.blend PSM_$T.blend 2>&1 | grep -i "Trace" -A4)
rm -f SMH_$T.blend N_$T.blend
for Y in 0 90 180; do (GG=${GGV:-0.35} GP=1.0 AOD=0.06 AOP=${AOPV:-2.0} LK=0.6 AMB=0.14 PIT=${PITV:-3} YAW=$Y RES=${RES:-800} SMP=14 VIEWS=full REDIDS=${RED:--5} LNK=${LNK:-0.3} SHV=${SHVV:-0.04} $S/venv/bin/python -I $S/rendarm.py PSM_$T.blend r/PSM_${T}_$Y 2>&1 | grep Traceback) & done; wait
for Y in 0 90 180; do (GG=${GGV:-0.35} GP=1.0 AOD=0.06 AOP=${AOPV:-2.0} LK=0.6 AMB=0.14 PIT=4 YAW=$Y RES=900 SMP=14 VIEWS=upper REDIDS=${RED:--5} LNK=${LNK:-0.3} SHV=${SHVV:-0.04} $S/venv/bin/python -I $S/rendarm.py PSM_$T.blend r/PSU_${T}_$Y 2>&1 | grep Traceback) & done; wait
python3 -I -c "
from PIL import Image
c=Image.new('RGB',(2700,900),'white')
for k,y in enumerate((0,90,180)):
  im=Image.open(f'r/PSU_${T}_{y}_upper.png').convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);c.paste(bg.convert('RGB'),(k*900,0))
c.save('r/PSU_${T}.jpg',quality=88)"
python3 -I - "$T" <<'PY'
import sys
from PIL import Image
T=sys.argv[1]
ims=[]
for y in (0,90,180):
    im=Image.open(f'r/PSM_{T}_{y}_full.png').convert('RGBA'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); ims.append(bg.convert('RGB'))
H=ims[0].height; ref=Image.open(__import__('os').environ.get('GT3D','.')+'/referencias/2e7cf147-image.png').convert('RGB'); ref=ref.crop((120,300,800,1900)); ref=ref.resize((int(ref.width*H/ref.height),H))
ims=[ref]+ims; c=Image.new('RGB',(sum(i.width for i in ims)+30,H),'white'); x=0
for i in ims: c.paste(i,(x,0)); x+=i.width+10
c.save(f"r/PSM_{T}.jpg",quality=88)
PY
