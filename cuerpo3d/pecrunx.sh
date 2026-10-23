#!/bin/bash
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; W=$S/w; T=$1; cd $W; source $S/penv.sh; eval "$XENV"
$S/venv/bin/python -I scripts/torsohf.py $W/A_f2.blend $W/G_$T.blend 2>&1 | grep -i "Trace" -A3
ROLL=-20 $S/venv/bin/python -I $S/posearm.py $W/G_$T.blend $W/PG_$T.blend 2>&1 | grep -i "Trace" -A3
for Y in -30 80; do GG=1.0 GP=1.0 AOD=0.06 AOP=3.5 LK=0.5 AMB=0.06 YAW=$Y RES=600 SMP=16 VIEWS=chest REDIDS=-5 $S/venv/bin/python -I $S/rendarm.py $W/PG_$T.blend $W/r/PG_${T}_$Y 2>&1 | grep Traceback; done
cd r; python3 - "$T" <<'PY'
import sys
from PIL import Image
T=sys.argv[1]
def onwhite(f):
    im=Image.open(f).convert('RGBA'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); return bg.convert('RGB')
ref=Image.open(__import__('os').environ.get('GT3D','.')+'/referencias/8f5015de-image.jpg').convert('RGB').crop((40,180,520,700)).resize((554,600))
ims=[ref]+[onwhite(f'PG_{T}_{y}_chest.png') for y in (-30,80)]
c=Image.new('RGB',(sum(i.size[0] for i in ims)+20,600),'white'); x=0
for i in ims: c.paste(i,(x,0)); x+=i.size[0]+10
c.save(f'PG_{T}.jpg',quality=85)
PY
