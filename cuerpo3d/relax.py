# Shoulder skin re-solve after posing (Laplacian surface editing): inside a ball around each shoulder joint the skin
# keeps its REST detail (each vertex's offset from the average of its neighbours, turned by the blended bone rotation)
# and is laid smoothly between the torso and the arm, which stay where the skinning put them. Removes folds/pinches.
# Bakes the result into the mesh (modifiers applied).  usage: blender -b -P relax.py -- posed.blend out.blend
# env RAD (ball radius, m), RIN (full-effect radius)
import bpy,sys,os,time
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
from mathutils import Quaternion
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
t0=time.time()
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; rig=bpy.data.objects['Rig']; me=hi.data; nv=len(me.vertices)
for m in hi.modifiers:
    if m.name=='CorrectiveSmooth2': m.show_viewport=False
dg=bpy.context.evaluated_depsgraph_get(); ev=hi.evaluated_get(dg)
newme=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=dg)
X=np.zeros(nv*3); newme.vertices.foreach_get('co',X); X=X.reshape(-1,3)
R0=np.zeros(nv*3); me.vertices.foreach_get('co',R0); R0=R0.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
Adj=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(Adj.sum(1)).ravel(); deg[deg==0]=1
Lap=sp.identity(nv,format='csr')-sp.diags(1/deg)@Adj
# bone rotations (object space of the mesh == armature space here)
mwi=hi.matrix_world.inverted(); quats={}
for pb in rig.pose.bones:
    M=(mwi@rig.matrix_world@pb.matrix@pb.bone.matrix_local.inverted()@rig.matrix_world.inverted()@hi.matrix_world).to_3x3()
    quats[pb.name]=np.array(M.to_quaternion().normalized())
gname={g.index:g.name for g in hi.vertex_groups}
RAD=E('RAD',0.20); RIN=E('RIN',0.13)
d=np.min([np.linalg.norm(R0-np.array(rig.data.bones['upper_arm.'+L].head_local),axis=1) for L in 'LR'],axis=0)
inside=d<RAD
print('region verts',int(inside.sum()))
idx=np.where(inside)[0]
# per-vertex blended rotation (quaternion average, sign-aligned to the chest)
ref=quats['chest']; Q=np.zeros((len(idx),4))
for n,i in enumerate(idx):
    acc=np.zeros(4)
    for g in me.vertices[int(i)].groups:
        b=gname.get(g.group)
        if b in quats and g.weight>0:
            q=quats[b]; acc+=g.weight*(q if q@ref>=0 else -q)
    nq=np.linalg.norm(acc); Q[n]=acc/nq if nq>0 else ref
def rotate(Q,v):
    w,x,y,z=Q[:,0],Q[:,1],Q[:,2],Q[:,3]
    u=np.c_[x,y,z]; t=2*np.cross(u,v); return v+w[:,None]*t+np.cross(u,t)
delta=(Lap@R0)[idx]; dR=rotate(Q,delta)
A=Lap[idx][:,idx].tocsr()
outside=np.where(~inside)[0]
B=Lap[idx][:,outside]
rhs=dR-B@X[outside]
# soft pull to the skinned position: none at the joint, strong far from it and on the neck/head
D0,D1=E('D0',0.04),E('D1',0.15)
t=np.clip((d[idx]-D0)/(D1-D0),0,1); lam=E('LAM',1e-6)*t*t*(3-2*t)+1e-10
gi={g.name:g.index for g in hi.vertex_groups}
nh=np.zeros(len(idx))
for n,i in enumerate(idx):
    for g in me.vertices[int(i)].groups:
        if gname.get(g.group) in ('neck','head'): nh[n]+=g.weight
lam=lam+E('LAMN',1e-5)*np.clip(nh*2,0,1)
M=(A.T@A+sp.diags(lam)).tocsc()
rr=A.T@rhs+lam[:,None]*X[idx]
print('solving',M.shape,'nnz',M.nnz); lu=sla.splu(M,permc_spec='COLAMD')
Xs=np.column_stack([lu.solve(rr[:,k]) for k in range(3)])
# full effect inside RIN, fading to the skinned result at RAD
s=np.clip((RAD-d[idx])/(RAD-RIN),0,1); s=s*s*(3-2*s)
Xn=X.copy(); Xn[idx]=X[idx]+s[:,None]*(Xs-X[idx])
mv=np.linalg.norm(Xn[idx]-X[idx],axis=1); print('moved mm: mean %.1f p95 %.1f max %.1f'%(mv.mean()*1000,np.percentile(mv,95)*1000,mv.max()*1000))
newme.vertices.foreach_set('co',Xn.ravel()); newme.update()
old=hi.data; hi.modifiers.clear(); hi.data=newme
bpy.ops.wm.save_as_mainfile(filepath=out); print('done in %.0fs'%(time.time()-t0))
