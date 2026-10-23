# Make the lats smaller on the rest model. The muscles are separate skin pieces stitched at seams, so the push is a
# SPATIAL field (same value for touching vertices of different pieces): amount = smoothed (in 3D) share of lat skin
# nearby, direction = horizontally towards the body axis. More push on the outer edge where the V flares.
# usage: blender -b -P shrinklats.py -- in.blend out.blend   env DL (m), SIG (smoothing radius, m)
import bpy,sys,os
import numpy as np
from scipy.spatial import cKDTree
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
lk=[k for k,m in enumerate(me.materials) if m and m.name=='mus_mat_lats'][0]
ind=np.zeros(nv,np.float32)
for p in me.polygons:
    if p.material_index==lk: ind[list(p.vertices)]=1.0
arm=np.zeros(nv)
for v in me.vertices:
    for g in v.groups:
        if hi.vertex_groups[g.group].name.startswith(('upper_arm','forearm','hand','delt')): arm[v.index]+=g.weight
roi=np.where((co[:,2]>0.85)&(co[:,2]<1.6)&(np.abs(co[:,0])<0.40))[0]
rng=np.random.default_rng(0); sub=rng.choice(roi,min(len(roi),120000),replace=False)
tree=cKDTree(co[sub]); SIG=E('SIG',0.025)
dd,ii=tree.query(co[roi],k=96)
w=np.exp(-(dd/SIG)**2)
lat=(w*ind[sub][ii]).sum(1)/np.maximum(w.sum(1),1e-9)
armn=(w*arm[sub][ii]).sum(1)/np.maximum(w.sum(1),1e-9)
m=np.clip(lat*1.4,0,1); m=m*m*(3-2*m)
m=m*np.clip(1-armn*E('ARMK',2.0),0,1)            # never on the arm
ax=np.abs(co[roi,0]); r=np.clip((ax-E('X0',0.06))/(E('X1',0.19)-E('X0',0.06)),0,1); r=r*r*(3-2*r)
amp=E('DL',0.018)*m*(E('BASE',0.3)+(1-E('BASE',0.3))*r)
yc=E('YC',0.0)
dvec=-np.c_[co[roi,0],co[roi,1]-yc,np.zeros(len(roi))]; dvec/=np.maximum(np.linalg.norm(dvec,axis=1,keepdims=True),1e-9)
new=co.copy(); new[roi]+=dvec*amp[:,None]
print('verts pushed',int((amp>1e-4).sum()),'max push mm %.1f'%(amp.max()*1000))
me.vertices.foreach_set('co',new.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
