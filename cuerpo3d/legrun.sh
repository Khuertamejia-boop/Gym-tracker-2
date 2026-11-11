#!/bin/bash
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; W=$S/w; T=$1; cd $W; eval "$XENV"
$S/venv/bin/python -I scripts/leghf.py $W/F_f9.blend $W/L_$T.blend 2>&1 | grep -i "leg verts\|Trace" -A3
ROLL=-20 $S/venv/bin/python -I $S/posearm.py $W/L_$T.blend $W/PL_$T.blend 2>&1 | grep -i "Trace" -A3
for Y in -25 80 180; do GG=1.0 GP=1.0 AOD=0.06 AOP=3.5 LK=0.5 AMB=0.06 YAW=$Y RES=700 SMP=14 VIEWS=full REDIDS=-5 $S/venv/bin/python -I $S/rendarm.py $W/PL_$T.blend $W/r/PL_${T}_$Y 2>&1 | grep Traceback; done
cd r; python3 - "$T" <<'PY'
import sys
from PIL import Image
T=sys.argv[1]
def onwhite(f):
    im=Image.open(f).convert('RGBA'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); return bg.convert('RGB')
ref=Image.open(__import__('os').environ.get('GT3D','.')+'/referencias/30349b8e-image.jpg').convert('RGB')
ims=[onwhite(f'PL_{T}_{y}_full.png') for y in (-25,80,180)]
H=ims[0].height; ref=ref.resize((int(ref.width*H/ref.height),H)); ims=[ref]+ims
c=Image.new('RGB',(sum(i.width for i in ims)+30,H),'white'); x=0
for i in ims: c.paste(i,(x,0)); x+=i.width+10
c.save(f'PL_{T}.jpg',quality=85)
PY
