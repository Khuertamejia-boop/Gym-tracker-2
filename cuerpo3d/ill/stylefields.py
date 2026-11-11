# Per-vertex fields for the illustration renderer, from a compiled muscle atlas and the exercise's worked muscles.
#   python -I stylefields.py ATLAS.npz OUT.npz "trap_upper:1,latissimus_dorsi:1,deltoid_posterior:0.8,group:abs:0.6"
# Names match the muscle name without side (e.g. 'teres_major'), or its group (prefix 'group:' optional: a name that
# is not a muscle is tried as a group).  Output fields (rest vertex order, so they fit every posed frame):
#   sd bd sds bds fph fmask (copied), tend (1 on tendons), rsd (mm, + inside worked muscles, - outside),
#   rint (worked intensity, extended across the border), disp (nv,1 groove displacement in m), restco (nv,3)
import sys, os, numpy as np
from scipy.spatial import cKDTree
E=lambda k,d: float(os.environ.get(k,d))
HERE=os.path.dirname(os.path.abspath(__file__))
atl=np.load(sys.argv[1],allow_pickle=True); out=sys.argv[2]; sel=sys.argv[3] if len(sys.argv)>3 else ''
rest=np.load(os.environ.get('ATLAS_REST',os.path.join(HERE,'rest.npz')),allow_pickle=True)
co=rest['co']; nv=len(co)
names=[str(n) for n in atl['names']]; mid=atl['mid']
base=[n.rsplit('.',1)[0] for n in names]
groups=['none']+[str(g) for g in atl['groups']]
kinds=['none']+[str(k) for k in atl['kinds']]
inten=np.zeros(len(names))
for it in [x for x in sel.split(',') if x.strip()]:
    parts=it.strip().split(':'); v=float(parts[-1]); key=parts[-2]
    hit=[i for i in range(1,len(names)) if base[i]==key or groups[i]==key]
    if not hit: print('WARNING no muscle or group named',key)
    for i in hit: inten[i]=max(inten[i],v)
red=inten[mid]>0
bd=atl['bd'].astype(float); sd=atl['sd'].astype(float)
rsd=np.where(red,bd,-bd)
# extend the intensity a little across the border so the interpolated red edge stays put
rint=inten[mid].copy()
if red.any():
    kd=cKDTree(co[red]); d,i=kd.query(co[~red],distance_upper_bound=0.02); ok=np.isfinite(d)
    tmp=rint[~red]; tmp[ok]=inten[mid[red]][i[ok]]; rint[~red]=tmp
tend=np.array([1.0 if kinds[m]=='tendon' else 0.0 for m in mid])
# groove: a shallow rounded valley along hard borders, a fainter one along soft borders
GD=E('GD',0.0016); GW=E('GW',4.0); GS=E('GSOFT',0.35)
prof=lambda d: np.exp(-(d/GW)**2)
disp=-GD*np.maximum(prof(np.abs(sd))*(bd<10),GS*prof(np.abs(atl['sds']))*(atl['bds']<10))
disp*=1-rest['shorts']               # no grooves under the shorts fabric
np.savez(out,sd=sd.astype(np.float32),bd=bd.astype(np.float32),sds=atl['sds'],bds=atl['bds'],fph=atl['fph'],fmask=atl['fmask'],
         tend=tend.astype(np.float32),rsd=rsd.astype(np.float32),rint=rint.astype(np.float32),disp=disp[:,None].astype(np.float32),
         restco=co.astype(np.float32),hf=(rest['h_fine']*1000).astype(np.float32),hm=(rest['h_mid']*1000).astype(np.float32))
print('worked muscles:',sorted(set(base[i] for i in range(1,len(names)) if inten[i]>0)),'red verts',int(red.sum()))
