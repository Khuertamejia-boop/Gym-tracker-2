# ping-pong GIF (and a contact sheet) from transparent PNG frames:  python3 mkgif.py out.gif f0.png f1.png ... [env DUR ms, PAD px, W px, CROP=0 keeps the full frame]
import sys, os
from PIL import Image
out=sys.argv[1]; fs=sys.argv[2:]; DUR=int(os.environ.get('DUR','90')); PAD=int(os.environ.get('PAD','24')); W=int(os.environ.get('W','560'))
ims=[Image.open(f).convert('RGBA') for f in fs]
bb=None
for im in ims:
    b=im.getchannel('A').getbbox(); bb=b if bb is None else (min(bb[0],b[0]),min(bb[1],b[1]),max(bb[2],b[2]),max(bb[3],b[3]))
box=(max(bb[0]-PAD,0),max(bb[1]-PAD,0),min(bb[2]+PAD,ims[0].width),min(bb[3]+PAD,ims[0].height))
if os.environ.get('CROP','1')=='0': box=(0,0,ims[0].width,ims[0].height)      # keep the full frame (16:9)
fr=[]
for im in ims:
    bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); c=bg.convert('RGB').crop(box)
    if c.width>W: c=c.resize((W,int(c.height*W/c.width)),Image.LANCZOS)
    fr.append(c)
seq=fr+fr[-2:0:-1]
pal=[f.quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE) for f in seq]
pal[0].save(out,save_all=True,append_images=pal[1:],duration=DUR,loop=0,optimize=False,disposal=1)
if os.environ.get('SHEET'):
    k=[0,len(fr)//2,len(fr)-1]; sh=Image.new('RGB',(fr[0].width*3,fr[0].height),'white')
    for i,j in enumerate(k): sh.paste(fr[j],(i*fr[0].width,0))
    sh.save(os.environ['SHEET'],quality=92)
print('gif',out,len(seq),'frames',fr[0].size)
