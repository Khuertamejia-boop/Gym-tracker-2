import sys
from PIL import Image
out=sys.argv[1]; fs=sys.argv[2:]
ims=[Image.open(f).convert('RGBA') for f in fs]; h=max(i.size[1] for i in ims)
c=Image.new('RGB',(sum(i.size[0] for i in ims),h),'white');x=0
for im in ims:
    bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); c.paste(bg.convert('RGB'),(x,0)); x+=im.size[0]
c.save(out,quality=88)
