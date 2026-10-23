import bpy,bmesh,numpy as np
bpy.ops.wm.open_mainfile(filepath='H_1.blend')
me=bpy.data.objects['Hi'].data; bm=bmesh.new(); bm.from_mesh(me)
be=[e for e in bm.edges if e.is_boundary]
print('boundary edges',len(be))
import collections
zs=[ (e.verts[0].co.z) for e in be]; print('z range of boundary', np.percentile(zs,[0,50,100]) if zs else None)
