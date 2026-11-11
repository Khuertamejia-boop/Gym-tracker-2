#!/bin/bash
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; W=$S/w; T=$1; cd $W
$S/venv/bin/python -I scripts/torsohf.py $W/A_f2.blend $W/T_$T.blend 2>&1 | grep -i "torso verts\|Trace" -A3
ROLL=-20 $S/venv/bin/python -I $S/posearm.py $W/T_$T.blend $W/PT_$T.blend 2>&1 | grep -i "Trace" -A5
GG=${GGV:-0.9} GP=1.0 AOD=0.06 AOP=${AOPV:-3.5} LK=0.5 AMB=0.06 YAW=-30 RES=700 SMP=20 VIEWS=upper REDIDS=${REDF:--5} $S/venv/bin/python -I $S/rendarm.py $W/PT_$T.blend $W/r/TF_$T 2>&1 | grep Traceback
GG=${GGV:-0.9} GP=1.0 AOD=0.06 AOP=${AOPV:-3.5} LK=0.5 AMB=0.06 YAW=200 RES=700 SMP=20 VIEWS=upper REDIDS=${REDB:--5} $S/venv/bin/python -I $S/rendarm.py $W/PT_$T.blend $W/r/TB_$T 2>&1 | grep Traceback
GG=${GGV:-0.9} GP=1.0 AOD=0.06 AOP=${AOPV:-3.5} LK=0.5 AMB=0.06 YAW=75 RES=700 SMP=20 VIEWS=upper REDIDS=-5 $S/venv/bin/python -I $S/rendarm.py $W/PT_$T.blend $W/r/TS_$T 2>&1 | grep Traceback
cd r; python3 - "$T" <<'PY'
import sys
from PIL import Image
T=sys.argv[1]
def onwhite(f):
    im=Image.open(f).convert('RGBA'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); return bg.convert('RGB')
ref=Image.open(__import__('os').environ.get('GT3D','.')+'/referencias/b1af4f26-image.jpg').convert('RGB'); ref=ref.resize((int(ref.size[0]*700/ref.size[1]),700))
ims=[ref,onwhite(f'TF_{T}_upper.png'),onwhite(f'TS_{T}_upper.png'),onwhite(f'TB_{T}_upper.png')]
c=Image.new('RGB',(sum(i.size[0] for i in ims)+20,700),'white'); x=0
for i in ims: c.paste(i,(x,0)); x+=i.size[0]+10
c.save(f'ST_{T}.jpg',quality=88)
PY
