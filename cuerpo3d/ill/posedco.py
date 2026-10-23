import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); me=bpy.data.objects['Hi'].data
co=np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co',co); np.save(sys.argv[-1],co.reshape(-1,3))
