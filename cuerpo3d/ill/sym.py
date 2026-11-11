import bpy,sys,numpy as np
from scipy.spatial import cKDTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
me=bpy.data.objects['Hi'].data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
m=co*np.array((-1,1,1)); d,i=cKDTree(co).query(m)
print('mirror dist mm p50 p95 p99 max',np.percentile(d,[50,95,99,100])*1000, 'involution ok',np.mean(i[i]==np.arange(nv)))
rig=bpy.data.objects['Rig']
for b in rig.data.bones:
    if b.name.endswith('.L') or '.' not in b.name: print(b.name,np.round(b.head_local,3),np.round(b.tail_local,3))
np.save(sys.argv[-1].replace('.blend','_mirror.npy'),i)
