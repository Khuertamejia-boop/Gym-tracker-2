#!/bin/bash
# fullcmp.sh OUT name1 [name2 ...]: whole figures at the reference's height + the reference
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; out=$1; shift
python3 -c "
import sys
from PIL import Image
ref=Image.open(__import__('os').environ.get('GT3D','.')+'/referencias/8ccf8362-image.jpg').convert('RGB')
H=674; tiles=[]
for n in sys.argv[1:]:
  im=Image.open('$S/ill/r/'+n+'.png'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); bb=im.getchannel('A').getbbox()
  fr=bg.convert('RGB').crop((bb[0]-15,bb[1]-15,bb[2]+15,bb[3]+15)); tiles.append(fr.resize((int(fr.width*H/fr.height),H),Image.LANCZOS))
tiles.append(ref)
W=sum(t.width for t in tiles)+20*len(tiles); o=Image.new('RGB',(W,H),'white'); x=0
for t in tiles: o.paste(t,(x,0)); x+=t.width+20
o.save('$S/ill/r/$out.png')" "$@"
