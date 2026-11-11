#!/bin/bash
# usage: armrun.sh tag  (extra env passed through)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; W=$S/w; T=$1; cd $W
env MB=${MB:-1.5} MW=${MW:-1.18} MB_biceps=${MB_biceps:-1.35} MW_biceps=${MW_biceps:-1.12} MB_tri_lat=${MB_tri_lat:-1.35} MB_tri_long=${MB_tri_long:-1.35} MW_tri_lat=${MW_tri_lat:-1.12} MW_tri_long=${MW_tri_long:-1.12} MB_brach_l=${MB_brach_l:-1.2} FADEIT=300 DSM=3 CORE=0.88 KM=0.002 KM_F=0.005 PE_U=1.0 MW_ecu=${MW_ecu:-1.45} MW_fcu=${MW_fcu:-1.45} MW_ext_dig=${MW_ext_dig:-1.3} MW_flex=${MW_flex:-1.3} $S/venv/bin/python -I scripts/armhf.py $W/eb.blend $W/A_$T.blend 2>&1 | grep -i "Trace" -A5
ROLL=${ROLL:--20} $S/venv/bin/python -I $S/posearm.py $W/A_$T.blend $W/P_$T.blend 2>&1 | grep -i "Trace" -A5
for Y in 90 -30 200; do GG=1.0 GP=1.0 AOD=0.06 AOP=3.5 LK=0.5 AMB=0.06 YAW=$Y RES=700 SMP=20 VIEWS=upper REDIDS=${RED:-4} $S/venv/bin/python -I $S/rendarm.py $W/P_$T.blend $W/r/R_${T}_$Y 2>&1 | grep -i "Traceback"; done
cd r; python3 - "$T" <<'PY'
import sys
from PIL import Image
T=sys.argv[1]
def onwhite(f):
    im=Image.open(f).convert('RGBA'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); return bg.convert('RGB')
ref=Image.open(__import__('os').environ.get('GT3D','.')+'/referencias/40b48935-image.jpg').convert('RGB'); ref=ref.resize((int(ref.size[0]*700/ref.size[1]),700))
ims=[ref]+[onwhite(f'R_{T}_{y}_upper.png') for y in (90,-30,200)]
c=Image.new('RGB',(sum(i.size[0] for i in ims)+30,700),'white'); x=0
for i in ims: c.paste(i,(x,0)); x+=i.size[0]+10
c.save(f'S_{T}.jpg',quality=88)
PY
