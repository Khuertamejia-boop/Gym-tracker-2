# Arms overhead: the skin strip under each arm (lat "wing" + armpit) only has a sensible shape with the arm down.
# After posing, that strip is rebuilt as a smooth fair surface (bi-harmonic: L^2 X = 0) between the ribs below and
# the arm above, continuing smoothly into the skin around it. Bakes the mesh.
# usage: blender -b -P fair.py -- posed.blend out.blend   env XR0 ZR0 ZR1 UARM
import bpy,sys,os,time
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
t0=time.time()
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
dg=bpy.context.evaluated_depsgraph_get(); ev=hi.evaluated_get(dg)
newme=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=dg)
X=np.zeros(nv*3); newme.vertices.foreach_get('co',X); X=X.reshape(-1,3)
P=np.zeros(nv*3); me.vertices.foreach_get('co',P); P=P.reshape(-1,3)
gi={g.index:g.name for g in hi.vertex_groups}
arm=np.zeros(nv); nh=np.zeros(nv)
cand=np.where((np.abs(P[:,0])>E('XR0',0.14)-0.02)&(P[:,2]>E('ZR0',1.15)-0.02)&(P[:,2]<E('ZR1',1.36)+0.02))[0]
for i in cand:
    for g in me.vertices[int(i)].groups:
        n=gi.get(g.group,'')
        if n.startswith(('upper_arm','forearm','hand')): arm[i]+=g.weight
        elif n.startswith('delt'): arm[i]+=0.5*g.weight
        if n in ('neck','head'): nh[i]+=g.weight
R=(np.abs(P[:,0])>E('XR0',0.14))&(P[:,2]>E('ZR0',1.15))&(P[:,2]<E('ZR1',1.36))&(arm<E('UARM',0.6))&(nh<0.1)
R&=(P[:,1]>E('YR0',-0.13))&(P[:,1]<E('YR1',0.13))
idx=np.where(R)[0]; print('strip verts',len(idx))
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
# rows: verts in R and their 1-ring (their Laplacians touch R)
nb=np.zeros(nv,bool); nb[idx]=True
ek=nb[ed[:,0]]|nb[ed[:,1]]; ring=np.zeros(nv,bool); ring[ed[ek].ravel()]=True
rows=np.where(ring)[0]
ek2=ring[ed[:,0]]|ring[ed[:,1]]; e2=ed[ek2]
cols_used=np.unique(np.r_[rows,e2.ravel()])
cpos=-np.ones(nv,int); cpos[cols_used]=np.arange(len(cols_used)); rpos=-np.ones(nv,int); rpos[rows]=np.arange(len(rows))
deg=np.bincount(ed.ravel(),minlength=nv).astype(float)
# L (uniform) restricted to rows x cols_used
ra=[];ca=[];va=[]
for a_,b_ in ((e2[:,0],e2[:,1]),(e2[:,1],e2[:,0])):
    m=ring[a_]; ra.append(rpos[a_[m]]); ca.append(cpos[b_[m]]); va.append(-1.0/deg[a_[m]])
ra.append(rpos[rows]); ca.append(cpos[rows]); va.append(np.ones(len(rows)))
L=sp.coo_matrix((np.concatenate(va),(np.concatenate(ra),np.concatenate(ca))),shape=(len(rows),len(cols_used))).tocsr()
free=R[cols_used]; Lf=L[:,np.where(free)[0]]; Lx=L[:,np.where(~free)[0]]
Xfix=X[cols_used[~free]]
M=(Lf.T@Lf).tocsc(); rhs=-(Lf.T@(Lx@Xfix))
lu=sla.splu(M,permc_spec='COLAMD'); Xs=np.column_stack([lu.solve(rhs[:,k]) for k in range(3)])
fid=cols_used[free]
mv=np.linalg.norm(Xs-X[fid],axis=1); print('moved mm: mean %.1f p95 %.1f max %.1f'%(mv.mean()*1000,np.percentile(mv,95)*1000,mv.max()*1000))
X[fid]=Xs
newme.vertices.foreach_set('co',X.ravel()); newme.update()
if newme.shape_keys:
    pass
hi.shape_key_clear() if me.shape_keys else None
hi.modifiers.clear(); hi.data=newme
bpy.ops.wm.save_as_mainfile(filepath=out); print('done in %.0fs'%(time.time()-t0))
