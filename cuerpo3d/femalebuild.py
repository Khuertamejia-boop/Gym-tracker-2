# Female mannequin from the approved male one: the Blender "Human Base Meshes" realistic male and female bodies (CC0)
# share one topology, and our male body 'Hi' keeps (almost) every vertex of the male mesh in order, so each vertex of
# 'Hi' is moved to its female position -> muscle atlas, UVs, all texture maps, skin weights and attributes stay valid.
# The rig is refitted (each joint follows the skin around it). Writes the female base .blend + a female rest .npz.
#   python -I femalebuild.py BUNDLE.blend NB_mc_row.blend OUT.blend OUT_rest.npz     env: PHYK (male physique kept, 0..1)
import bpy, sys, os, numpy as np, scipy.sparse as sp
from scipy.spatial import cKDTree
from mathutils import Vector
E=lambda k,d: float(os.environ.get(k,d))
bun,src,out,outrest=sys.argv[-4:]
G=os.environ.get('GT3D','.')
R=np.load(os.path.join(G,'ill','rest.npz'),allow_pickle=True); RD={k:R[k] for k in R.files}
hc=RD['co']; main=np.array([str(x) for x in RD['main']]); ed=RD['ed']; nv=len(hc)
# ---- 1. male and female level-2 surfaces (same vertex order)
bpy.ops.wm.open_mainfile(filepath=bun)
def l2(name):
    o=bpy.data.objects[name]; o.modifiers[0].levels=2; dg=bpy.context.evaluated_depsgraph_get(); me=o.evaluated_get(dg).to_mesh()
    co=np.array([v.co[:] for v in me.vertices]); M=np.array(o.matrix_world); co=co@M[:3,:3].T+M[:3,3]; co[:,0]-=M[0,3]
    e=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',e)
    me.calc_loop_triangles(); tri=np.zeros(len(me.loop_triangles)*3,int); me.loop_triangles.foreach_get('vertices',tri)
    o.evaluated_get(dg).to_mesh_clear(); return co,e.reshape(-1,2),tri.reshape(-1,3)
m,E2,T2=l2('GEO-body_male_realistic'); f,_,_=l2('GEO-body_female_realistic'); n2=len(m)
assert len(f)==n2
# ---- 2. vertex correspondence Hi -> level 2 (order preserved; checked against the edges)
kd=cKDTree(m); d,i=kd.query(hc)
J=np.full(nv,-1); body=main!='head'; ok=(d<0.0002)&body; J[ok]=i[ok]
A2=sp.coo_matrix((np.ones(2*len(E2)),(np.r_[E2[:,0],E2[:,1]],np.r_[E2[:,1],E2[:,0]])),shape=(n2,n2)).tocsr()
a,b=ed[:,0],ed[:,1]
A1=sp.coo_matrix((np.ones(2*len(ed)),(np.r_[a,b],np.r_[b,a])),shape=(nv,nv)).tocsr()
nb1=[A1.indices[A1.indptr[k]:A1.indptr[k+1]] for k in range(nv)]
nb2=[set(A2.indices[A2.indptr[j]:A2.indptr[j+1]].tolist()) for j in range(n2)]
used=np.zeros(n2,bool); used[J[J>=0]]=True
# propagation through the (identical) mesh graph: an unmatched vertex takes the free level-2 vertex that is adjacent to
# the images of the most of its matched neighbours (ties: nearest); vertices with more matched neighbours go first
import heapq
def score(k):
    return sum(1 for q in nb1[k] if J[q]>=0)
heap=[(-score(k),k) for k in np.where(body&(J<0))[0] if score(k)>=2]; heapq.heapify(heap)
while heap:
    sc,k=heapq.heappop(heap)
    if J[k]>=0: continue
    ms=[J[q] for q in nb1[k] if J[q]>=0]
    if len(ms)<2: continue
    if -sc!=len(ms): heapq.heappush(heap,(-len(ms),k)); continue
    cnt={}
    for j in ms:
        for c in nb2[j]:
            if not used[c]: cnt[c]=cnt.get(c,0)+1
    if not cnt: continue
    top=max(cnt.values())
    if top<2: continue
    cand=[c for c,v in cnt.items() if v==top]
    c=min(cand,key=lambda c: np.linalg.norm(m[c]-hc[k]))
    J[k]=c; used[c]=True
    for q in nb1[k]:
        if J[q]<0 and body[q]: heapq.heappush(heap,(-score(q),q))
print('mapped body %d of %d'%((J[body]>=0).sum(),body.sum())); import collections; print('UNMAPPED',collections.Counter(main[body&(J<0)]).most_common(10)); np.save(os.path.join(G,'w','_J.npy'),J)
v=(J[a]>=0)&(J[b]>=0)
okE=np.zeros(len(ed),bool); okE[v]=np.asarray(A2[J[a[v]],J[b[v]]]).ravel()>0
print('edges consistent %.5f'%okE[v].mean())
bad=np.zeros(nv,bool); bad[a[~okE]]=True; bad[b[~okE]]=True
good=body&(J>=0)&~bad&(np.linalg.norm(m[np.maximum(J,0)]-hc,axis=1)<0.03)
print('good verts %d of %d'%(good.sum(),nv))
# ---- 3. female positions: exact vertices by index; every other vertex is projected on the male surface (nearest point
#         with a compatible normal) and taken to the same surface point of the female, keeping PHYK of its offset
from mathutils.bvhtree import BVHTree
bvh=BVHTree.FromPolygons([tuple(p) for p in m],[tuple(int(i) for i in t) for t in T2])
hn=RD['no']; newc=hc.copy(); exact=ok.copy()
newc[exact]=f[J[exact]]
def bary(P,t):
    A_,B_,C_=m[T2[t]]; v0=B_-A_; v1=C_-A_; v2=P-A_
    d00=v0@v0; d01=v0@v1; d11=v1@v1; d20=v2@v0; d21=v2@v1; den=max(d00*d11-d01*d01,1e-18)
    vv=(d11*d20-d01*d21)/den; ww=(d00*d21-d01*d20)/den; return np.array((1-vv-ww,vv,ww))
fail=np.zeros(nv,bool)
for k in np.where(~exact)[0]:
    loc,nrm,t,dist=bvh.find_nearest(Vector(hc[k]))
    if loc is None or (np.array(nrm)@hn[k]<E('NDOT',0.3) and dist>0.002): fail[k]=True; continue
    w=bary(np.array(loc),t); fp=w@f[T2[t]]; newc[k]=fp+E('PHYK',0.5)*(hc[k]-np.array(loc))
print('projected %d, failed %d'%((~exact).sum()-fail.sum(),fail.sum()))
disp=newc-hc
deg=np.asarray(A1.sum(1)).ravel(); W=sp.diags(1/np.maximum(deg,1))@A1
for _ in range(200):                                       # failed vertices: harmonic fill from their neighbours
    if not fail.any(): break
    disp[fail]=(W@disp)[fail]
sm=~exact
for _ in range(int(E('BLENDIT',4))): disp[sm]=0.5*disp[sm]+0.5*(W@disp)[sm]   # light smoothing of the projected ones
newc=hc+disp
# ---- 4. rig: every joint moves with the skin around it (Gaussian weights, radius from the bone length)
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; rig=bpy.data.objects['Rig']
hi.data.vertices.foreach_set('co',newc.astype(np.float32).ravel()); hi.data.update()
kdh=cKDTree(hc)
def moved(p,r):
    idx=kdh.query_ball_point(p,3*r)
    if len(idx)<8: dd,idx=kdh.query(p,k=64); idx=list(np.atleast_1d(idx))
    idx=np.array(idx); w=np.exp(-(np.linalg.norm(hc[idx]-p,axis=1)/r)**2); return p+(w[:,None]*disp[idx]).sum(0)/max(w.sum(),1e-12)
bpy.context.view_layer.objects.active=rig; bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones; heads={}; tails={}
for bn in eb:
    L=(bn.tail-bn.head).length; r=min(max(0.35*L,E('RMIN',0.012)),E('RMAX',0.08))
    heads[bn.name]=moved(np.array(bn.head),r); tails[bn.name]=moved(np.array(bn.tail),r)
for bn in eb:
    rl=bn.roll; bn.head=Vector(heads[bn.name]); bn.tail=Vector(tails[bn.name]); bn.roll=rl
for bn in eb:                                    # keep connected chains connected
    if bn.parent is not None and bn.use_connect: bn.head=bn.parent.tail
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=out)
# ---- 5. female rest data (same arrays, new positions / normals / bones)
hi=bpy.data.objects['Hi']; nn=np.zeros(nv*3); hi.data.vertices.foreach_get('normal',nn)
RD['co']=newc; RD['no']=nn.reshape(-1,3)
bn=[str(x) for x in RD['bn']]; bb=rig.data.bones
RD['bh']=np.array([np.array(bb[n].head_local) for n in bn]); RD['bt']=np.array([np.array(bb[n].tail_local) for n in bn])
np.savez(outrest,**RD)
print('female height %.3f (male %.3f)'%(newc[:,2].max(),hc[:,2].max()))
