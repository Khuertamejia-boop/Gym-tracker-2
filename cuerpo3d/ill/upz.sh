#!/bin/bash
# upz.sh OUT name1 [...]: upper body of full renders (bbox-relative crop) at ~1.4x the reference scale + reference crop
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; out=$1; shift
python3 -c "
import sys
from PIL import Image
ref=Image.open(__import__('os').environ.get('GT3D','.')+'/referencias/8ccf8362-image.jpg').convert('RGB')
H=674; tiles=[]
for n in sys.argv[1:]:
  im=Image.open('$S/ill/r/'+n+'.png'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im)
  a=im.getchannel('A').point(lambda v:255 if v>10 else 0); bb=a.getbbox()
  fr=bg.convert('RGB').crop((bb[0]-15,bb[1]-15,bb[2]+15,bb[3]+15)); fr=fr.resize((int(fr.width*H/fr.height),H),Image.LANCZOS)
  # upper body: around the torso (x 25..62% of the frame, top 0..48%)
  tiles.append(fr.crop((int(fr.width*0.24),0,int(fr.width*0.62),int(H*0.48))))
tiles.append(ref.crop((215,30,470,350)))
tiles=[t.resize((int(t.width*1.4),int(t.height*1.4)),Image.LANCZOS) for t in tiles]
W=sum(t.width for t in tiles)+10*len(tiles); Hh=max(t.height for t in tiles); o=Image.new('RGB',(W,Hh),'white'); x=0
for t in tiles: o.paste(t,(x,0)); x+=t.width+10
o.save('$S/ill/r/$out.png')" "$@"
