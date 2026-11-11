#!/bin/bash
# usage: headshots.sh PSM_tag.blend tag  -> r/HD_<tag>.jpg (front | 3/4 | side | back), head + neck + shoulders
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w; B=$1; T=$2
for Y in 0 -40 90 180; do (GG=${GGV:-0.35} GP=1.0 AOD=0.06 AOP=2.0 LK=0.6 AMB=0.14 PIT=4 YAW=$Y RES=700 SMP=12 VIEWS=cus TZ=1.54 OSC=0.5 REDIDS=-5 LNK=${LNK:-0.3} $S/venv/bin/python -I $S/rendarm.py $B r/hd${T}_$Y 2>&1 | grep Traceback) & done; wait
python3 -I -c "
from PIL import Image
c=Image.new('RGB',(2800,700),'white')
for k,y in enumerate((0,-40,90,180)):
  im=Image.open(f'r/hd${T}_{y}_cus.png').convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);c.paste(bg.convert('RGB'),(k*700,0))
c.save('r/HD_${T}.jpg',quality=88)"
