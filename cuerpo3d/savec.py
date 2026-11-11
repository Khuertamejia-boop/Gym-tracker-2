import bpy,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2])
for o in list(bpy.data.objects):
    if o.name in ('Barra','Discos'): bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1],compress=True)
