import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
for o in bpy.data.objects: print(o.name,o.type,[m.type+':'+m.name for m in getattr(o,'modifiers',[])], o.hide_render)
hi=bpy.data.objects['Hi']; me=hi.data
co=np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3); print('bbox',co.min(0),co.max(0))
print([a.name for a in me.attributes if not a.name.startswith('.')])
