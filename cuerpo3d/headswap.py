# Mannequin head from the old (approved) body: the old head+upper neck surface is brought into the new head's frame
# (same bone-relative position, scaled to the new head size) and the new head skin is laid onto it (nearest point),
# with a smooth blend down the neck. usage: blender -b -P headswap.py -- new.blend old.blend out.blend
import bpy,sys,os
import numpy as np, scipy.sparse as sp
from scipy.spatial import cKDTree
new,old,out=sys.argv[-3],sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=old)
om=bpy.data.objects['Hi'].data; orr=bpy.data.objects['Rig']
oco=np.zeros(len(om.vertices)*3); (om.shape_keys.key_blocks['Basis'].data if om.shape_keys else om.vertices).foreach_get('co',oco); oco=oco.reshape(-1,3)
oh=orr.data.bones['head']; oM=np.array(oh.matrix_local); oL=oh.length
on=orr.data.bones['neck']; onz=np.array(on.head_local)[2]
osel=oco[oco[:,2]>onz+E('OZ',0.04)]
bpy.ops.wm.open_mainfile(filepath=new)
hi=bpy.data.objects['Hi']; me=hi.data; rig=bpy.data.objects['Rig']; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
nh=rig.data.bones['head']; nM=np.array(nh.matrix_local); nL=nh.length
# old head points into the new head frame: head-bone local coords scaled by the length ratio (uniform)
q=(np.linalg.inv(oM)@np.c_[osel,np.ones(len(osel))].T).T[:,:3]*(nL/oL)*E('HSC',1.0)
tgt=(nM@np.c_[q,np.ones(len(q))].T).T[:,:3]
tgt[:,1]+=E('HDY',0.0); tgt[:,2]+=E('HDZ',0.0)
tr=cKDTree(tgt)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1
ss=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
mk=ss((co[:,2]-E('MZ0',1.44))/E('MZW',0.04))
for _ in range(int(E('MS',40))): mk=(A@mk)/deg*0.5+mk*0.5
d,j=tr.query(co)
newp=co+mk[:,None]*(tgt[j]-co)
for _ in range(int(E('HT',40))):
    for f in (0.5,-0.53): newp=newp+(mk[:,None]*f)*((A@newp)/deg[:,None]-newp)
me.vertices.foreach_set('co',newp.ravel())
if 'ln' in me.attributes:
    lnv=np.zeros(nv,np.float32); me.attributes['ln'].data.foreach_get('value',lnv); me.attributes['ln'].data.foreach_set('value',(lnv*(1-mk)).astype(np.float32))
me.update(); print('moved max mm %.1f'%(np.linalg.norm(newp-co,axis=1).max()*1000))
bpy.ops.wm.save_as_mainfile(filepath=out)
