import bpy,bmesh,sys,numpy as np
from mathutils.kdtree import KDTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
ob=bpy.data.objects['Cuerpo']; me=ob.data
bm=bmesh.new(); bm.from_mesh(me)
be=[e for e in bm.edges if e.is_boundary]; print('boundary edges',len(be))
import collections
c=collections.Counter((round((e.verts[0].co.z)/0.05)*0.05, 'b' if e.verts[0].co.y>0 else 'f') for e in be); print(sorted(c.items()))
nm=[e for e in bm.edges if len(e.link_faces)>2]; print('nonmanifold >2',len(nm))
co=np.array([v.co[:] for v in me.vertices]); kd=KDTree(len(co))
for i,c_ in enumerate(co): kd.insert(c_,i)
kd.balance()
d=np.array([kd.find((-c_[0],c_[1],c_[2]))[2] for c_ in co])
for zr in [(0,0.5),(0.5,0.9),(0.9,1.2),(1.2,1.5),(1.5,1.8)]:
    m=(co[:,2]>zr[0])&(co[:,2]<zr[1])
    print(zr,'mirror dist mm median',round(np.median(d[m])*1000,2),'p95',round(np.percentile(d[m],95)*1000,2),'frac<0.5mm',round((d[m]<0.0005).mean(),3))
