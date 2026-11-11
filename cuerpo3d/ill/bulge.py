# Smooth dome per muscle ("inflation"): solve  L h = -1  inside each muscle with h = 0 on its border (cotan
# Laplacian on the rest mesh), so each muscle gets a round, crease-free bulge (no ridge along its middle line).
# Output per vertex: dome 0..1 (1 at the top of each muscle), shaped a little rounder with a square root.
#   python -I bulge.py ATLAS.npz OUT.npz
import sys, os, numpy as np, scipy.sparse as sp
from scipy.sparse.linalg import spsolve
HERE=os.path.dirname(os.path.abspath(__file__))
E=lambda k,d: float(os.environ.get(k,d))
atl=np.load(sys.argv[1],allow_pickle=True); out=sys.argv[2]
r=np.load(os.path.join(HERE,'rest.npz'),allow_pickle=True); co=r['co']; nv=len(co)
z=np.load(os.path.join(HERE,'uvtri.npz')); T=z['tv']
mid=atl['mid'].astype(int)
names=[str(n) for n in atl['names']]; groups=['none']+[str(g) for g in atl['groups']]; kinds=['none']+[str(k) for k in atl['kinds']]
# muscles split only by soft lines (one bulge): merge them
MERGE=set(os.environ.get('MERGE','trapezius,deltoid,pectoralis').split(','))
key=[None]+[(groups[i]+'.'+names[i].rsplit('.',1)[1]) if groups[i] in MERGE and kinds[i]!='tendon' else names[i] for i in range(1,len(names))]
ukey={k:j for j,k in enumerate(sorted(set(key[1:])),1)}
lab_of=np.array([0]+[ukey[k] for k in key[1:]]); tend_of=np.array([False]+[kinds[i]=='tendon' for i in range(1,len(names))])
mid_m=lab_of[mid]
# cotan laplacian
I=[];J=[];W=[]
for k in range(3):
    i,j,o=T[:,k],T[:,(k+1)%3],T[:,(k+2)%3]
    u=co[i]-co[o]; v=co[j]-co[o]; c=(u*v).sum(1)/np.maximum(np.linalg.norm(np.cross(u,v),axis=1),1e-12)
    c=np.clip(c,0,10)*0.5; I+=[i,j]; J+=[j,i]; W+=[c,c]
Wm=sp.coo_matrix((np.concatenate(W),(np.concatenate(I),np.concatenate(J))),shape=(nv,nv)).tocsr()
# vertex areas (for the right-hand side)
ar=0.5*np.linalg.norm(np.cross(co[T[:,1]]-co[T[:,0]],co[T[:,2]]-co[T[:,0]]),axis=1)
va=np.zeros(nv); np.add.at(va,T.ravel(),np.repeat(ar/3,3))
# a vertex is on a border if a neighbour has another label
adj=(Wm>0).tocsr()
dome=np.zeros(nv); damp=np.zeros(nv); domeraw=np.zeros(nv)
for lab in np.unique(mid_m):
    if lab==0: continue
    vs=np.where(mid_m==lab)[0]
    if len(vs)<8: continue
    sub=adj[vs][:,vs]; inside_deg=np.asarray(sub.sum(1)).ravel(); full_deg=np.asarray(adj[vs].sum(1)).ravel()
    interior=inside_deg==full_deg
    if interior.sum()<4: continue
    Ws=Wm[vs][:,vs].tocsr(); D=np.asarray(Ws.sum(1)).ravel(); Ls=(sp.diags(D)-Ws).tocsr()
    fi=np.where(interior)[0]
    h=np.zeros(len(vs))
    try: h[fi]=spsolve(Ls[fi][:,fi].tocsc(),va[vs][fi])
    except Exception as ex: print('solve failed',lab,ex); continue
    if h.max()<=0: continue
    hn=h/h.max()
    dome[vs]=np.sqrt(np.clip(hn,0,1))**E('DP',1.0)
    domeraw[vs]=np.clip(hn,0,1)
    area=va[vs].sum(); req=np.sqrt(area/np.pi)*1000          # equivalent radius, mm
    amp=np.clip(E('AK',0.07)*req,E('AMIN',1.2),E('AMAX',4.0))
    if tend_of[mid[vs]].mean()>0.5: amp=E('ATEND',0.4)
    damp[vs]=amp
# the crisp groove comes from the exact border-distance texture; here the dome only gives the round volume, so it
# must not drop to zero along the vertex staircase of the labels: lift its floor and smooth it across borders
dome=np.where(mid_m>0,E('DFLOOR',0.45)+(1-E('DFLOOR',0.45))*dome,E('DFLOOR',0.45))
deg=np.asarray(adj.sum(1)).ravel(); deg[deg==0]=1; Av=sp.diags(1/deg)@adj
for _ in range(int(E('DSM',12))):
    dome=0.5*dome+0.5*(Av@dome); damp=np.maximum(damp,0.5*damp+0.5*(Av@damp)) if False else 0.5*damp+0.5*(Av@damp)
# local half-width of each muscle: the largest border distance among same-muscle vertices nearby
from scipy.spatial import cKDTree
bd=atl['bd'].astype(float)
halfw=np.zeros(nv)
RW=E('RW',0.035)
for lab in np.unique(mid_m):
    if lab==0: continue
    vs=np.where(mid_m==lab)[0]
    if len(vs)<4: continue
    kd=cKDTree(co[vs]); nb=kd.query_ball_point(co[vs],RW)
    b=bd[vs]; halfw[vs]=np.array([b[n_].max() for n_ in nb])
halfw=np.maximum(halfw,E('WMIN',3.0))
for _ in range(int(E('WSM',20))): halfw=0.5*halfw+0.5*(Av@halfw)
dr=domeraw.copy()
for _ in range(int(E('RSM',2))): dr=0.5*dr+0.5*(Av@dr)
np.savez(out,dome=dome.astype(np.float32),damp=damp.astype(np.float32),halfw=halfw.astype(np.float32),domeraw=dr.astype(np.float32))
print('halfw mm p5/50/95',np.percentile(halfw[mid_m>0],[5,50,95]))
print('dome done, labelled verts',int((mid>0).sum()))
