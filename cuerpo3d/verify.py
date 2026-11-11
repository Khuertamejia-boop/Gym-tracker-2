import bpy,sys,math
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.usd_import(filepath=sys.argv[-2]); out=sys.argv[-1]
ms=[o for o in bpy.data.objects if o.type=='MESH']; print('meshes',[(o.name,len(o.data.vertices),len(o.data.materials)) for o in ms],'arm',[o.name for o in bpy.data.objects if o.type=='ARMATURE'])
print('mats',[(m.name,[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE']) for m in bpy.data.materials][:3])
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=12; sc.cycles.device='CPU'; sc.view_settings.view_transform='Standard'
w=bpy.data.worlds.new('w'); w.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value=1.0; sc.world=w
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=2.0; cam.location=(-4.6,4.6,0.92); cam.rotation_euler=(math.radians(90),0,math.radians(225))
sc.render.resolution_x,sc.render.resolution_y=450,600; sc.render.filepath=out; bpy.ops.render.render(write_still=True)
