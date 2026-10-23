import bpy,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
rig=bpy.data.objects['Rig']
for pb in rig.pose.bones:
    pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0); pb.scale=(1,1,1)
bpy.context.view_layer.update(); bpy.ops.wm.save_as_mainfile(filepath=out)
