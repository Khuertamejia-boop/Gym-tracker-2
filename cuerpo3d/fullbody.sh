#!/bin/bash
# whole body: arms -> torso -> legs -> mannequin head -> arms down ; then 3 renders
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; W=$S/w; T=$1; cd $W
(source $S/aenv.sh; eval "$AX"; $S/venv/bin/python -I scripts/armhf.py eb.blend B1_$T.blend 2>&1 | grep -i "Trace" -A5)
(source $S/fenv.sh; eval "$TX"; $S/venv/bin/python -I scripts/torsohf.py B1_$T.blend B2_$T.blend 2>&1 | grep -i "Trace" -A5)
(source $S/lenv.sh; eval "$LX"; $S/venv/bin/python -I scripts/leghf.py B2_$T.blend B3_$T.blend 2>&1 | grep -i "Trace" -A5)
(eval "$NX"; $S/venv/bin/python -I scripts/neckhf.py B3_$T.blend B35_$T.blend 2>&1 | grep -i "Trace" -A5)
(eval "$HX"; $S/venv/bin/python -I scripts/headnew.py B35_$T.blend B4_$T.blend 2>&1 | grep -i "Trace" -A5)
rm -f B35_$T.blend
ROLL=-20 $S/venv/bin/python -I $S/posearm.py B4_$T.blend PB_$T.blend 2>&1 | grep -i "Trace" -A5
rm -f B2_$T.blend
for Y in -25 80 180; do GG=${GGV:-0.6} GP=1.0 AOD=0.06 AOP=3.5 LK=0.5 AMB=0.06 YAW=$Y RES=${RES:-800} SMP=14 VIEWS=${VW:-full} REDIDS=${RED:--5} LNK=${LNK:-0.75} $S/venv/bin/python -I $S/rendarm.py PB_$T.blend r/PB_${T}_$Y 2>&1 | grep Traceback; done
cd r; python3 - "$T" "${VW:-full}" <<'PY'
import sys
from PIL import Image
T,V=sys.argv[1],sys.argv[2]
def onwhite(f):
    im=Image.open(f).convert('RGBA'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); return bg.convert('RGB')
ims=[onwhite(f'PB_{T}_{y}_{V}.png') for y in (-25,80,180)]
H=ims[0].height; ref=Image.open(__import__('os').environ.get('GT3D','.')+'/referencias/30349b8e-image.jpg').convert('RGB'); ref=ref.resize((int(ref.width*H/ref.height),H))
ims=[ref]+ims; c=Image.new('RGB',(sum(i.width for i in ims)+30,H),'white'); x=0
for i in ims: c.paste(i,(x,0)); x+=i.width+10
c.save(f'PB_{T}.jpg',quality=88)
PY
