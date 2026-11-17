#!/bin/bash
# rest-pose comparison sheet: restsheet.sh out.jpg "yaws" a.blend b.blend ...   (upper body; env TZ OSC RS)
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
OUT=$1; YW=$2; shift 2; RS=${RS:-420}; n=0
for f in "$@"; do for Y in $YW; do
  GG=0.35 GP=1.0 AOD=0.06 AOP=2.0 LK=0.6 AMB=0.14 PIT=${PIT:-3} YAW=$Y RES=$RS SMP=${SMP:-8} VIEWS=cus TX=0 TY=0 TZ=${TZ:-1.18} OSC=${OSC:-1.05} REDIDS=-5 LNK=0.3 SHV=0.04 $S/venv/bin/python -I $S/rendarm.py $f r/rs_$(basename $f .blend)_$Y >/dev/null 2>&1 &
  n=$((n+1)); if [ $((n%2)) = 0 ]; then wait; fi
done; done; wait
$S/venv/bin/python -I - "$OUT" "$YW" "$RS" "$@" <<'PY'
import sys,os
from PIL import Image, ImageDraw
out,yw,rs=sys.argv[1],sys.argv[2].split(),int(sys.argv[3]); fs=sys.argv[4:]
im=Image.new('RGB',(rs*len(yw),rs*len(fs)),'white'); d=ImageDraw.Draw(im)
for i,f in enumerate(fs):
    b=os.path.basename(f)[:-6]
    for j,y in enumerate(yw):
        try: x=Image.open(f'r/rs_{b}_{y}_cus.png'); im.paste(x,(j*rs,i*rs),x)
        except Exception: pass
        d.text((j*rs+6,i*rs+6),f'{b} yaw{y}',fill=(200,0,0))
im.save(out,quality=85)
PY
