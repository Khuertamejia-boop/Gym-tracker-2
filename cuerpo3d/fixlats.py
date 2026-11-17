# The torso skin followed the arm too far down (to ~28 cm below the shoulder): the lats ballooned when the arms go up.
# Cap the upper-arm weight by distance to the upper-arm bone (full near the arm, zero 13 cm away), give the rest
# back to the torso bones, then smooth the changed weights over the surface. Exact float weights.
# usage: blender -b -P fixlats.py -- in.blend out.blend   env: D0 D1 (m), N smoothing iterations
import bpy,sys,os
import numpy as np, scipy.sparse as sp
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices); rig=bpy.data.objects['Rig']; bb=rig.data.bones
bones={b.name for b in bb}
groups=[g for g in hi.vertex_groups if g.name in bones]; gi={g.index:k for k,g in enumerate(groups)}; names=[g.name for g in groups]
W=np.zeros((nv,len(groups)),np.float32)
for v in me.vertices:
    for g in v.groups:
        k=gi.get(g.group)
        if k is not None: W[v.index,k]=g.weight
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2,np.float32),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1
def segd(P,a,b):
    d=b-a; t=np.clip((P-a)@d/(d@d),0,1); return np.linalg.norm(P-(a+t[:,None]*d),axis=1)
W0=W.copy(); changed=np.zeros(nv,bool)
torso=[names.index(n) for n in ('chest','spine','clavicle.L','clavicle.R','neck','hips') if n in names]
for L in 'LR':
    k=names.index('upper_arm.'+L)
    a=np.array(bb['upper_arm.'+L].head_local); b=np.array(bb['upper_arm.'+L].tail_local)
    d=segd(co,a,b)
    t=np.clip((d-E('D0',0.07))/(E('D1',0.13)-E('D0',0.07)),0,1); cap=1-t*t*(3-2*t)
    # only skin that also belongs to the torso (the arm itself keeps its weights)
    tor=W[:,torso].sum(1)>0.02
    new=np.where(tor,np.minimum(W[:,k],W[:,k]*cap),W[:,k])
    freed=W[:,k]-new; ch=freed>1e-5; changed|=ch
    W[:,k]=new
    rest=W[:,torso].copy(); s=rest.sum(1,keepdims=True); s[s==0]=1
    W[:,torso]+= rest/s*freed[:,None]
    print(L,'verts changed',int(ch.sum()),'weight moved to the torso: mean %.3f max %.3f'%(freed[ch].mean(),freed.max()))
# smooth the changed region (and a margin) so no new border appears
m=changed.astype(np.float32)
for _ in range(int(E('GROW',40))): m=np.maximum(m,(A@m)/deg)
m=np.clip(m*2,0,1)
for _ in range(20): m=(A@m)/deg*0.5+m*0.5
m=m[:,None]
for it in range(int(E('N',150))): W=W+m*0.5*((A@W)/deg[:,None]-W)
W=np.clip(W,0,1); s=W.sum(1,keepdims=True); s[s==0]=1; W=W/s
idx=np.where((np.abs(W-W0).max(1)>1e-5))[0]; print('verts written',len(idx))
for k,g in enumerate(groups):
    vals=W[idx,k]; z=idx[vals<=1e-4]
    if len(z): g.remove([int(i) for i in z])
    for i,w in zip(idx[vals>1e-4],vals[vals>1e-4]): g.add([int(i)],float(w),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=out)
