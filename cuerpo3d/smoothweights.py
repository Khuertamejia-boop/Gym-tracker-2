# Smooth the torso/shoulder skin weights over the surface (removes the step-like weight borders that crack when the arms go up).
# usage: blender -b -P smoothweights.py -- in.blend out.blend   (env N iterations)
import bpy,sys,os
import numpy as np, scipy.sparse as sp
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
rig=bpy.data.objects['Rig']; bones={b.name for b in rig.data.bones}
groups=[g for g in hi.vertex_groups if g.name in bones]
gi={g.index:k for k,g in enumerate(groups)}; names=[g.name for g in groups]
W=np.zeros((nv,len(groups)),np.float32)
for v in me.vertices:
    for g in v.groups:
        k=gi.get(g.group)
        if k is not None: W[v.index,k]=g.weight
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2,np.float32),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1
col=lambda n: W[:,names.index(n)] if n in names else np.zeros(nv)
far=sum(col(n) for n in names if n.split('.')[0] in ('forearm','hand','thumb1','thumb2','thumb3','index1','index2','index3','middle1','middle2','middle3','ring1','ring2','ring3','pinky1','pinky2','pinky3','head','thigh','shin','foot','toe'))
m=((far<0.01)&(co[:,2]>E('ZLO',1.02))&(co[:,2]<E('ZHI',1.70))).astype(np.float32)
for _ in range(int(E('MSM',30))): m=np.minimum(m,(A@m)/deg)   # erode a little so the border stays untouched
for _ in range(int(E('MSM',30))): m=(A@m)/deg*0.5+m*0.5      # then soften it
m=m[:,None]
print('smoothing verts',int((m[:,0]>0.01).sum()),'groups',names)
W0=W.copy()
for it in range(int(E('N',300))):
    W=W+m*0.5*((A@W)/deg[:,None]-W)
W=np.clip(W,0,1); s=W.sum(1,keepdims=True); s[s==0]=1
ch=(m[:,0]>0.01)
W[ch]=W[ch]/s[ch]
print('mean weight change in region %.3f'%np.abs(W-W0)[ch].sum(1).mean())
# exact weights (rounding to 1/255 shows as ripples when the arm turns ~160 degrees)
idx=np.where(ch)[0]
for k,g in enumerate(groups):
    vals=W[idx,k]; z=idx[vals<=1e-4]
    if len(z): g.remove([int(i) for i in z])
    for i,w in zip(idx[vals>1e-4],vals[vals>1e-4]): g.add([int(i)],float(w),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=out)
