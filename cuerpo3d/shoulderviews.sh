#!/bin/bash
# close-up sheet of the left shoulder for several posed files.  usage: shoulderviews.sh out.jpg "yaws" file1 file2 ...
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
OUT=$1; YW=$2; shift 2; RS=${RS:-380}
for f in "$@"; do
  read X Y Z <<< $($S/venv/bin/python -I -c "
import bpy,sys
bpy.ops.wm.open_mainfile(filepath='$f')
p=bpy.data.objects['Rig'].pose.bones['upper_arm.L'].head
print('%.3f %.3f %.3f'%(p.x*0.6,p.y,p.z))" 2>/dev/null | tail -1)
  n=0
  for Yw in $YW; do
    NODISC=1 SHOWBAR=1 GG=0.35 GP=1.0 AOD=0.06 AOP=2.0 LK=0.6 AMB=0.14 PIT=${PIT:-3} YAW=$Yw RES=$RS SMP=${SMP:-8} VIEWS=cus TX=$X TY=$Y TZ=$Z OSC=${OSC:-0.55} REDIDS=-5 LNK=0.3 SHV=0.04 $S/venv/bin/python -I $S/rendarm.py $f r/sv_$(basename $f .blend)_$Yw >/dev/null 2>&1 &
    n=$((n+1)); if [ $((n%4)) = 0 ]; then wait; fi
  done; wait
done
$S/venv/bin/python -I - "$OUT" "$YW" "$RS" "$@" <<'PY'
import sys,os
from PIL import Image, ImageDraw
out,yw,rs=sys.argv[1],sys.argv[2].split(),int(sys.argv[3]); fs=sys.argv[4:]
im=Image.new('RGB',(rs*len(yw),rs*len(fs)),'white'); d=ImageDraw.Draw(im)
for i,f in enumerate(fs):
    b=os.path.basename(f)[:-6]
    for j,y in enumerate(yw):
        try: x=Image.open(f'r/sv_{b}_{y}_cus.png'); im.paste(x,(j*rs,i*rs),x)
        except Exception: pass
        d.text((j*rs+6,i*rs+6),f'{b} yaw{y}',fill=(200,0,0))
im.save(out,quality=85)
PY
