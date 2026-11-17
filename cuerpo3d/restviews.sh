#!/bin/bash
# rest pose, three views of the upper body: front, back, side.  usage: restviews.sh in.blend outprefix
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
for Y in 0 180 90; do
 ( GG=0.35 GP=1.0 AOD=0.06 AOP=2.0 LK=0.6 AMB=0.14 PIT=3 YAW=$Y RES=600 SMP=12 VIEWS=cus TX=0 TY=-0.02 TZ=1.22 OSC=0.95 REDIDS=-5 LNK=0.3 SHV=0.04 $S/venv/bin/python -I $S/rendarm.py $1 r/rv_$2_$Y > /dev/null 2>&1 ) &
done; wait
$S/venv/bin/python -I -c "
from PIL import Image
im=Image.new('RGB',(1800,600),'white')
for k,Y in enumerate(('0','180','90')):
    x=Image.open('r/rv_$2_'+Y+'_cus.png'); im.paste(x,(k*600,0),x)
im.save('r/rv_$2.jpg',quality=88)"
