import bpy,sys,numpy as np, scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)),(ed[:,0],ed[:,1])),shape=(nv,nv))
n,lab=connected_components(A,directed=False)
print('components',n,[int((lab==k).sum()) for k in range(n)][:10])
# boundary edges
import bmesh
bm=bmesh.new(); bm.from_mesh(me)
be=[e for e in bm.edges if e.is_boundary]
print('boundary edges',len(be))
P=np.array([[(e.verts[0].co+e.verts[1].co)/2] for e in be]).reshape(-1,3)
if len(P): print('boundary z range',P[:,2].min(),P[:,2].max(), 'x',P[:,0].min(),P[:,0].max())
rig=bpy.data.objects['Rig']; hb=rig.data.bones['head']; c=np.array(hb.head_local)*0.6+np.array(hb.tail_local)*0.4
print('head c',c)
# normals pointing inward in head region
bm.verts.ensure_lookup_table()
nr=np.array([v.normal[:] for v in bm.verts])
h=co[:,2]>1.47
inw=h&(((co-c)*nr).sum(1)<-0.0)
print('head verts',h.sum(),'inward normal verts',inw.sum(),'z',co[inw,2].min() if inw.any() else None, co[inw,2].max() if inw.any() else None)
r=np.linalg.norm(co-c,axis=1)
print('inward y range',co[inw,1].min(),co[inw,1].max())
