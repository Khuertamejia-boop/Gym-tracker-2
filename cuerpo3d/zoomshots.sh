#!/bin/bash
# usage: zoomshots.sh blend tag -> r/zs_<tag>.jpg : neck front-3/4 | side | back | shoulder-back close
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w; B=$1; T=$2
for V in "a -35 1.50 0.46" "b 90 1.50 0.46" "c 180 1.45 0.62" "d 150 1.35 0.80"; do set -- $V
 (GG=0.6 GP=1.0 AOD=0.06 AOP=3.0 LK=0.6 AMB=0.14 PIT=6 YAW=$2 RES=700 SMP=12 VIEWS=cus TZ=$3 OSC=$4 REDIDS=-5 LNK=0.85 $S/venv/bin/python -I $S/rendarm.py $B r/zs${T}_$1 2>&1 | grep Traceback) &
done; wait
python3 -I -c "
from PIL import Image
c=Image.new('RGB',(2800,700),'white')
for k,v in enumerate('abcd'):
  im=Image.open(f'r/zs${T}_{v}_cus.png').convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);c.paste(bg.convert('RGB'),(k*700,0))
c.save('r/zs_${T}.jpg',quality=88)"
