#!/bin/bash
# cmp.sh OUT name1 name2 ... : side-by-side arm crops + reference
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; out=$1; shift
python3 -c "
import sys
from PIL import Image
ns=sys.argv[1:]; ims=[]
for n in ns:
  im=Image.open('$S/ill/r/'+n+'.png'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); ims.append(bg.convert('RGB').crop((200,0,700,700)))
ref=Image.open('$S/ill/ref_arm.png').convert('RGB').resize((284,700))
o=Image.new('RGB',(500*len(ims)+284,700),'white')
for i,im in enumerate(ims): o.paste(im,(500*i,0))
o.paste(ref,(500*len(ims),0)); o.save('$S/ill/r/$out.png')" "$@"
