# per-exercise border strength map: how dark each muscle border is drawn (1 = full, 0 = invisible)
#   python -I linemap.py ATLAS.npz MAPDIR "red list as redmap.py"     env: SRR (red|red), SWW (white|white), SRW (red|white)
#   MERGE="a+b,c+d" borders between those muscles (base names or groups) drawn with SMERGE
import sys, os, glob, numpy as np
from PIL import Image
E=lambda k,d: float(os.environ.get(k,d))
atl=np.load(sys.argv[1],allow_pickle=True); d=sys.argv[2]; sel=sys.argv[3]
names=[str(n) for n in atl['names']]; base=[n.rsplit('.',1)[0] for n in names]; groups=['none']+[str(g) for g in atl['groups']]
kinds=['none']+[str(k) for k in atl['kinds']]
red=np.zeros(len(names))
for it in [x for x in sel.split(',') if x.strip()]:
    key,v=it.strip().rsplit(':',1)
    for i in range(1,len(names)):
        if (base[i]==key or groups[i]==key) and kinds[i]!='tendon': red[i]=max(red[i],float(v))
def match(i,key): return base[i]==key or groups[i]==key
merges=[tuple(p.split('+')) for p in os.environ.get('MERGE','').split(',') if '+' in p]
cv=np.load(os.path.join(d,'curves.npz'))
lut=np.ones(int(cv['ids'].max())+2)
for k,a,b,s in zip(cv['ids'],cv['vp'],cv['vm'],cv['soft']):
    ra,rb=red[a]>0,red[b]>0
    if a==0 or b==0: st=E('SNONE',0.6)
    elif ra and rb: st=E('SRR',0.25)
    elif ra or rb: st=E('SRW',1.0)
    else: st=E('SWW',0.8)
    if a==b: st=0.0
    for x,y in merges:
        if (match(a,x) and match(b,y)) or (match(a,y) and match(b,x)): st=min(st,E('SMERGE',0.1))
    if groups[a]==groups[b] and a>0 and groups[a] not in ('none',): st=min(st,E('SGROUP',1.0))
    lut[k+1]=st
lut[0]=0.0
np.save(os.path.join(d,'lstr_lut.npy'),lut[1:])
for f in glob.glob(os.path.join(d,'cidh.*.png')):
    c=np.asarray(Image.open(f)).astype(int); s=lut[np.clip(c,0,len(lut)-1)]
    Image.fromarray((s*255).astype(np.uint8)).save(f.replace('cidh.','lstr.'))
print('border strengths: red|red %.2f red|white %.2f white|white %.2f, merges %d'%(E('SRR',0.25),E('SRW',1.0),E('SWW',0.8),len(merges)))
