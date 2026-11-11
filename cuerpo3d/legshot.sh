#!/bin/bash
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; T=$1; cd $S/w
for Y in -25 180 80; do GG=1.0 GP=1.0 AOD=0.06 AOP=3.5 LK=0.5 AMB=0.06 YAW=$Y RES=700 SMP=14 VIEWS=full REDIDS=-5 $S/venv/bin/python -I $S/rendarm.py PL_$T.blend r/x$T 2>&1 | grep Traceback; python3 -c "
from PIL import Image
im=Image.open('r/x${T}_full.png').convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);bg.convert('RGB').crop((0,330,434,700)).save('r/leg${T}_$Y.jpg')"; done
python3 -c "
from PIL import Image
ims=[Image.open('r/leg${T}_%d.jpg'%y) for y in (-25,180,80)];c=Image.new('RGB',(434*3,370),'white')
for k,i in enumerate(ims): c.paste(i,(k*434,0))
c.save('r/legs_$T.jpg')"
