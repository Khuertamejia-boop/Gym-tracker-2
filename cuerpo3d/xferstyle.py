# Carry the app style from the old body to the new one: muscle materials (per face), muscle id 'mseg', centre
# gradient 'mq', fine lines 'ln', 'shorts'. Each new vertex is taken into the old body through its main bone
# (same position along the bone, same offset in the bone's frame), then the nearest old skin point gives the values.
# usage: blender -b -P xferstyle.py -- new_rigged.blend old_body.blend out.blend
import bpy,sys,os
import numpy as np
from scipy.spatial import cKDTree
from mathutils import Matrix
new,old,out=sys.argv[-3],sys.argv[-2],sys.argv[-1]
# ---- old body
bpy.ops.wm.open_mainfile(filepath=old)
oh=bpy.data.objects['Hi']; om=oh.data; orig=bpy.data.objects['Rig']
onv=len(om.vertices); oco=np.zeros(onv*3)
(om.shape_keys.key_blocks['Basis'].data if om.shape_keys else om.vertices).foreach_get('co',oco); oco=oco.reshape(-1,3)
ob={b.name:(np.array(b.matrix_local),b.length) for b in orig.data.bones}
oatt={}
for n in ('mq','ln','shorts','mu','groove','mdist'):
    if n in om.attributes:
        a=np.zeros(onv,np.float32); om.attributes[n].data.foreach_get('value',a); oatt[n]=a
omi=np.zeros(len(om.polygons),int); om.polygons.foreach_get('material_index',omi)
oseg=np.zeros(len(om.polygons),np.float32); om.attributes['mseg'].data.foreach_get('value',oseg)
olt=np.zeros(len(om.polygons),int); om.polygons.foreach_get('loop_total',olt); olv=np.zeros(len(om.loops),int); om.loops.foreach_get('vertex_index',olv)
vface=np.zeros(onv,int); vface[olv]=np.repeat(np.arange(len(om.polygons)),olt)
mats=[m.name for m in om.materials]
otree=cKDTree(oco)
print('old body loaded',onv)
# ---- new body
bpy.ops.wm.open_mainfile(filepath=new)
hi=bpy.data.objects['Hi']; me=hi.data; rig=bpy.data.objects['Rig']; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
gi={g.index:g.name for g in hi.vertex_groups}
best=np.full(nv,-1); bw=np.zeros(nv); names=[]
nm={}
for v in me.vertices:
    for g in v.groups:
        if g.weight>bw[v.index] and gi[g.group] in ob:
            bw[v.index]=g.weight; nm[v.index]=gi[g.group]
mapped=co.copy()
for bn in set(nm.values()):
    idx=np.array([i for i,n in nm.items() if n==bn])
    b=rig.data.bones[bn]; Mn=np.array(b.matrix_local); Mo,Lo=ob[bn]
    q=(np.linalg.inv(Mn)@np.c_[co[idx],np.ones(len(idx))].T).T[:,:3]
    q[:,1]*=Lo/max(b.length,1e-6)            # same fraction along the bone
    mapped[idx]=(Mo@np.c_[q,np.ones(len(idx))].T).T[:,:3]
d,j=otree.query(mapped)
print('mapping distance to old skin: median %.1f mm, p95 %.1f mm'%(np.median(d)*1000,np.percentile(d,95)*1000))
for n,a in oatt.items():
    if n in me.attributes: me.attributes.remove(me.attributes[n])
    at=me.attributes.new(n,'FLOAT','POINT'); at.data.foreach_set('value',a[j])
# faces: majority over their vertices
lt=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_total',lt); ls=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_start',ls)
lv=np.zeros(len(me.loops),int); me.loops.foreach_get('vertex_index',lv)
vf=vface[j]; vm=omi[vf]; vs=oseg[vf]
fm=np.zeros(len(me.polygons),int); fs=np.zeros(len(me.polygons),np.float32)
for k in range(len(me.polygons)):
    vv=lv[ls[k]:ls[k]+lt[k]]; vals,cnt=np.unique(vm[vv],return_counts=True); fm[k]=vals[np.argmax(cnt)]
    vals,cnt=np.unique(vs[vv],return_counts=True); fs[k]=vals[np.argmax(cnt)]
me.materials.clear()
for n in mats: me.materials.append(bpy.data.materials.get(n) or bpy.data.materials.new(n))
me.polygons.foreach_set('material_index',fm)
if 'mseg' in me.attributes: me.attributes.remove(me.attributes['mseg'])
a=me.attributes.new('mseg','FLOAT','FACE'); a.data.foreach_set('value',fs)
me.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
