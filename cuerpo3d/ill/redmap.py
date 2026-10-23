# per-exercise red map from the baked labels:  python -I redmap.py ATLAS.npz MAPDIR "trapezius:1,latissimus_dorsi:1,..."
#   writes MAPDIR/red.<tile>.png (R = intensity 0..255).  Names = muscle without side, or its group.
import sys, os, glob, numpy as np
from PIL import Image
atl=np.load(sys.argv[1],allow_pickle=True); d=sys.argv[2]; sel=sys.argv[3]
names=[str(n) for n in atl['names']]; base=[n.rsplit('.',1)[0] for n in names]; groups=['none']+[str(g) for g in atl['groups']]
lut=np.zeros(256)
kinds=['none']+[str(k) for k in atl['kinds']]
for it in [x for x in sel.split(',') if x.strip()]:
    key,v=it.strip().rsplit(':',1); hit=[i for i in range(1,len(names)) if base[i]==key or groups[i]==key]
    if not hit: print('WARNING no muscle or group',key)
    for i in hit:
        if kinds[i]!='tendon': lut[i]=max(lut[i],float(v))
for f in glob.glob(os.path.join(d,'lab.*.png')):
    li=np.asarray(Image.open(f)); Image.fromarray((lut[li]*255).astype(np.uint8)).save(f.replace('lab.','red.'))
print('red muscles',sorted(set(base[i] for i in range(1,len(names)) if lut[i]>0)))
