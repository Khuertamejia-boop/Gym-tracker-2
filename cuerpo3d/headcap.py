# Mannequin head: remove the detailed head (face, mouth bag, eye sockets, ears) above a tilted cut through the neck
# and build a new smooth head cap on the fitted head shape (robust smooth radius per direction), joined to the neck.
# usage: blender -b -P headcap.py -- in.blend out.blend
import bpy,bmesh,sys,os,math
import numpy as np, scipy.sparse as sp
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
ss=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; rig=bpy.data.objects['Rig']
hb=rig.data.bones['head']; c=np.array(hb.head_local)*E('CH',0.6)+np.array(hb.tail_local)*(1-E('CH',0.6))
c[1]+=E('CY',0.0)
nv0=len(me.vertices)
co=np.zeros(nv0*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
# ---- shape: robust smooth radius function of direction, from the outer head surface
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
nr=np.array([v.normal[:] for v in bm.verts])
r=np.linalg.norm(co-c,axis=1); u=(co-c)/r[:,None]
fitm=(co[:,2]>E('FZ',1.47))&((u*nr).sum(1)>0.3)
DEG=int(E('HDEG',4)); terms=[(a,b,d) for a in range(DEG+1) for b in range(DEG+1) for d in range(DEG+1) if a+b+d<=DEG]
feats=lambda U: np.column_stack([U[:,0]**a*U[:,1]**b*U[:,2]**d for a,b,d in terms])
X=feats(u[fitm]); y=r[fitm]; keep=np.ones(len(y),bool)
# symmetric: mirror the points
Xm=feats(u[fitm]*np.array([-1,1,1])); X=np.vstack([X,Xm]); y=np.r_[y,y]; keep=np.r_[keep,keep]
for it in range(5):
    coef,*_=np.linalg.lstsq(X[keep],y[keep],rcond=None)
    res=y-X@coef; keep=np.abs(res)<E('HTOL',0.006)
R=lambda U: feats(U)@coef*E('HS',1.0)
print('fit kept %.0f%%'%(keep.mean()*100))
# ---- cut: delete everything above a tilted plane through the neck (under the chin at the front)
zc=E('CZ',1.455)+E('CSL',0.32)*(co[:,1]+0.08)
dele=(co[:,2]>zc)&(np.abs(co[:,0])<0.13)
dfaces=[f for f in bm.faces if all(dele[v.index] for v in f.verts)]
mi_del=np.bincount([f.material_index for f in dfaces]).argmax()
segl=bm.faces.layers.float.get('mseg')
from collections import Counter
seg_del=Counter([round(f[segl],3) for f in dfaces]).most_common(1)[0][0]
bmesh.ops.delete(bm,geom=dfaces,context='FACES')
# remove loose parts left (inner pieces) - keep the biggest component
bm.verts.ensure_lookup_table()
loose=[v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# components
lab={}; comp=0; sizes=[]
for v in bm.verts:
    if v in lab: continue
    st=[v]; lab[v]=comp; n=0
    while st:
        x=st.pop(); n+=1
        for e in x.link_edges:
            w=e.other_vert(x)
            if w not in lab: lab[w]=comp; st.append(w)
    sizes.append(n); comp+=1
big=int(np.argmax(sizes)); print('components after cut',sizes[:6])
bmesh.ops.delete(bm,geom=[v for v in bm.verts if lab[v]!=big],context='VERTS')
bm.verts.ensure_lookup_table()
# ---- boundary loop
bverts=set(); bed=[e for e in bm.edges if e.is_boundary]
adj={}
for e in bed:
    a,b=e.verts; adj.setdefault(a,[]).append(b); adj.setdefault(b,[]).append(a)
loops=[]; seen=set()
for s in adj:
    if s in seen: continue
    L=[s]; seen.add(s); prev=None; cur=s
    while True:
        nx=[w for w in adj[cur] if w!=prev and w not in seen]
        if not nx: break
        prev,cur=cur,nx[0]; L.append(cur); seen.add(cur)
    loops.append(L)
print('boundary loops',[len(L) for L in loops])
loop=max(loops,key=len)
B=np.array([v.co[:] for v in loop])
# orientation: counter-clockwise seen from above
ang=np.arctan2(B[:,1]-c[1],B[:,0]-c[0])
if np.sum(np.diff(np.unwrap(ang)))<0: loop=loop[::-1]; B=B[::-1]
M=len(loop)
# ---- rings to the crown
pole=np.array([0,E('PY',0.15),1.0]); pole/=np.linalg.norm(pole)
ub=(B-c)/np.linalg.norm(B-c,axis=1)[:,None]
rb=np.linalg.norm(B-c,axis=1)
off=rb-R(ub)
el=np.median([e.calc_length() for e in bm.edges])*E('ELS',1.0)
angs=np.arccos(np.clip(ub@pole,-1,1))
K=int(np.ceil(angs.max()*R(pole[None])[0]/el))
print('M',M,'K',K,'edge mm %.1f'%(el*1000))
def slerp(a,b,t):
    om=np.arccos(np.clip((a*b).sum(-1),-1,1))[...,None]; so=np.sin(om); so[so<1e-6]=1e-6
    return (np.sin((1-t)*om)*a+np.sin(t*om)*b)/so
dl=bm.verts.layers.deform.active
ptl={n:bm.verts.layers.float.get(n) for n in ('mq','ln','shorts','mu','groove','mdist') if bm.verts.layers.float.get(n)}
gnames={g.name:g.index for g in hi.vertex_groups}; hid=gnames['head']
prev_ring=list(loop); prev_src=np.arange(M)
KW=E('KW',10)
newverts=[]; newfaces=[]
k=1
while k<=K:
    t=k/(K+1)
    mcur=len(prev_ring)
    # halve the ring when it gets dense
    circ=np.sin(t*angs.mean())*R(pole[None])[0]*2*math.pi
    half= (mcur%2==0) and (circ/(mcur/2)>el*0.9)==False and mcur>8 and circ/mcur<el*0.6
    src_idx=prev_src[::2] if half else prev_src
    U=slerp(ub[src_idx],np.broadcast_to(pole,(len(src_idx),3)),t)
    rr=R(U)+off[src_idx]*(1-ss(k/E('KO',12)))
    P=c+U*rr[:,None]
    ring=[]
    for j,p in enumerate(P):
        v=bm.verts.new(p); ring.append(v); newverts.append(v)
        sv=loop[src_idx[j]]; s=ss(k/KW)
        for gi_,w in sv[dl].items(): v[dl][gi_]=w*(1-s)
        v[dl][hid]=v[dl].get(hid,0)*(1) + s
        for n,l in ptl.items(): v[l]=sv[l]*(0 if n in ('ln','shorts') else 1)
    m=len(ring)
    if half:
        for j in range(m):
            a0,a1,a2=prev_ring[2*j],prev_ring[2*j+1],prev_ring[(2*j+2)%mcur]
            b0,b1=ring[j],ring[(j+1)%m]
            newfaces+= [(a0,a1,b0),(a1,a2,b1),(a1,b1,b0)]
    else:
        for j in range(m):
            newfaces.append((prev_ring[j],prev_ring[(j+1)%m],ring[(j+1)%m],ring[j]))
    prev_ring=ring; prev_src=src_idx; k+=1
top=bm.verts.new(c+pole*R(pole[None])[0]); top[dl][hid]=1.0
for n,l in ptl.items(): top[l]=prev_ring[0][l]*(0 if n in ('ln','shorts') else 1)
m=len(prev_ring)
for j in range(m): newfaces.append((prev_ring[j],prev_ring[(j+1)%m],top))
newverts.append(top)
fl=[]
for vs in newfaces:
    f=bm.faces.new(vs); f.material_index=int(mi_del); f[segl]=seg_del; f.smooth=True; fl.append(f)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.verts.index_update()
loop_idx=np.array([v.index for v in loop]); new_idx=np.array([v.index for v in newverts])
bm.to_mesh(me); bm.free(); me.update()
# ---- relax: even out the cap on the sphere of directions, then a smooth radius offset (C1 join with the neck)
from scipy.sparse.csgraph import dijkstra
nv=len(me.vertices); co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1
isnew=np.zeros(nv,bool); isnew[new_idx]=True
U=(co-c); rr=np.linalg.norm(U,axis=1); U/=rr[:,None]
for _ in range(int(E('RELAX',300))):
    Un=(A@U)/deg[:,None]; Un/=np.linalg.norm(Un,axis=1)[:,None]
    U[isnew]=Un[isnew]
# geodesic distance from the seam
w=np.linalg.norm(co[ed[:,0]]-co[ed[:,1]],axis=1)
G=sp.coo_matrix((np.r_[w,w],(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
dist=dijkstra(G,indices=loop_idx,min_only=True,limit=0.2)
NB=E('NB',0.035); CB=E('CB',0.05); KOD=E('KOD',0.06)
from scipy.spatial import cKDTree
ubn=(co[loop_idx]-c); offb=np.linalg.norm(ubn,axis=1); ubn/=offb[:,None]; offb=offb-R(ubn)
_,jn=cKDTree(ubn).query(U[isnew])
dn=np.nan_to_num(dist[isnew],nan=1.0,posinf=1.0)
co[isnew]=c+U[isnew]*(R(U[isnew])+offb[jn]*(1-ss(dn/KOD)))[:,None]
# biharmonic fairing of positions over the seam band (C1 join), everything else fixed
dd=np.nan_to_num(dist,posinf=1.0)
free=((~isnew)&(dd<NB))|(isnew&(dd<CB))
L=(sp.diags(deg)-A).tocsr(); L2=(L@sp.diags(1/deg)@L).tocsr()
fi=np.where(free)[0]; fx=np.where(~free)[0]
from scipy.sparse.linalg import factorized
solve=factorized(L2[fi][:,fi].tocsc())
# neck/head axis; fair the distance from the axis (a scalar: the neck cannot get thinner by smoothing)
sl=(np.abs(co[:,2]-E('AZ',1.42))<0.004)&(np.abs(co[:,0])<0.09)&(~isnew)
a0=np.array([0,0.5*(co[sl,1].min()+co[sl,1].max()),E('AZ',1.42)]); ax_=c-a0; ax_/=np.linalg.norm(ax_)
rel=co-a0; tt=rel@ax_; radv=rel-np.outer(tt,ax_); rho=np.linalg.norm(radv,axis=1); rdir=radv/np.maximum(rho,1e-9)[:,None]
rho[fi]=solve(-(L2[fi][:,fx]@rho[fx]))
if E('FAIRT',1)>0:
    tt[fi]=solve(-(L2[fi][:,fx]@tt[fx]))
co[fi]=a0+np.outer(tt[fi],ax_)+rdir[fi]*rho[fi][:,None]
for _ in range(int(E('HT2',10))):
    for f in (0.5,-0.53): co[fi]=co[fi]+f*((A@co)/deg[:,None]-co)[fi]
print('free band verts',len(fi))
me.vertices.foreach_set('co',co.ravel()); me.update()
for n in ('ln',):
    if n in me.attributes:
        v=np.zeros(nv,np.float32); me.attributes[n].data.foreach_get('value',v)
        v=v*(1-ss((co[:,2]-1.43)/0.03)); me.attributes[n].data.foreach_set('value',v.astype(np.float32))
print('verts',nv0,'->',nv)
bpy.ops.wm.save_as_mainfile(filepath=out)
