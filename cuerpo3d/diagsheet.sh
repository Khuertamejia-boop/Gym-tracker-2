#!/bin/bash
# diagnostic contact sheet: frames x views, upper body.  usage: diagsheet.sh PREFIX "frames" "yaws" out.jpg [RES]
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
PF=$1; PFS=${PF//\//_}; FR=$2; YW=$3; OUT=$4; RS=${5:-420}
n=0
for F in $FR; do for Y in $YW; do
  NODISC=1 SHOWBAR=1 GG=0.35 GP=1.0 AOD=0.06 AOP=2.0 LK=0.6 AMB=0.14 PIT=3 YAW=$Y RES=$RS SMP=${SMP:-6} VIEWS=cus TX=0 TY=0 TZ=${TZ:-1.78} OSC=${OSC:-1.25} REDIDS=-5 LNK=0.3 SHV=0.04 $S/venv/bin/python -I $S/rendarm.py $PF$F.blend r/dg_${PFS}_${F}_$Y >/dev/null 2>&1 &
  n=$((n+1)); if [ $((n%4)) = 0 ]; then wait; fi
done; done; wait
$S/venv/bin/python -I - "$PFS" "$FR" "$YW" "$OUT" "$RS" <<'PY'
import sys
from PIL import Image, ImageDraw
pf,fr,yw,out,rs=sys.argv[1],sys.argv[2].split(),sys.argv[3].split(),sys.argv[4],int(sys.argv[5])
im=Image.new('RGB',(rs*len(yw),rs*len(fr)),'white'); d=ImageDraw.Draw(im)
for i,f in enumerate(fr):
    for j,y in enumerate(yw):
        try:
            x=Image.open(f'r/dg_{pf}_{f}_{y}_cus.png'); im.paste(x,(j*rs,i*rs),x)
        except Exception as e: pass
        d.text((j*rs+6,i*rs+6),f'{pf}{f} yaw{y}',fill=(200,0,0))
im.save(out,quality=85)
PY
