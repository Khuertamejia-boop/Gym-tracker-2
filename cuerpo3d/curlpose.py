import bpy,sys,math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
rig=bpy.data.objects['Rig']
for L in ('L','R'):
    pb=rig.pose.bones['forearm.'+L]; pb.rotation_mode='XYZ'; pb.rotation_euler=(math.radians(-105),0,0)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
