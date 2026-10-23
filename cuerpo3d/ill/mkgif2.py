# GIF with different speeds up and down (and pauses), from transparent PNG frames given bottom -> top:
#   python3 mkgif2.py out.gif f00.png ... fNN.png     env: UP (ms per frame going up, 40), DOWN (ms going down, 80),
#   HOLDT (pause at the top, 400), HOLDB (pause at the bottom, 600), W (width px, 960), SHEET (contact sheet path)
import sys, os
from PIL import Image
out=sys.argv[1]; fs=sys.argv[2:]; E=lambda k,d: int(os.environ.get(k,d)); W=E('W',960)
fr=[]
for f in fs:
    im=Image.open(f).convert('RGBA'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); c=bg.convert('RGB')
    if c.width>W: c=c.resize((W,int(c.height*W/c.width)),Image.LANCZOS)
    fr.append(c)
n=len(fr)
seq=list(range(n))+list(range(n-2,0,-1))            # up (concentric) then down (eccentric)
dur=[E('UP',40)]*n+[E('DOWN',80)]*(n-2)
dur[n-1]=E('HOLDT',400); dur[0]=E('HOLDB',600)      # pauses at the top and at the bottom
pal=[fr[i].quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE) for i in seq]
pal[0].save(out,save_all=True,append_images=pal[1:],duration=dur,loop=0,optimize=False,disposal=1)
if os.environ.get('SHEET'):
    k=[0,n//2,n-1]; sh=Image.new('RGB',(fr[0].width*3,fr[0].height),'white')
    for i,j in enumerate(k): sh.paste(fr[j],(i*fr[0].width,0))
    sh.save(os.environ['SHEET'],quality=92)
print('gif',out,len(seq),'frames, %.2f s'%(sum(dur)/1000),fr[0].size)
