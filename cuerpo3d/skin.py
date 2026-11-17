import bpy,sys,math,numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.usd_import(filepath=sys.argv[-1])
me=[o for o in bpy.data.objects if o.type=='MESH'][0]; rig=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
print('mods',[m.type for m in me.modifiers],'vgroups',len(me.vertex_groups),'bones',len(rig.data.bones))
def ev():
    dg=bpy.context.evaluated_depsgraph_get(); e=me.evaluated_get(dg); m=e.to_mesh(); a=np.array([v.co[:] for v in m.vertices]); e.to_mesh_clear(); return a
a=ev(); pb=[p for p in rig.pose.bones if 'thigh' in p.name and 'L' in p.name][0]; pb.rotation_mode='XYZ'; pb.rotation_euler=(math.radians(-60),0,0); bpy.context.view_layer.update(); b=ev()
print('moved verts',int((np.linalg.norm(a-b,axis=1)>0.01).sum()),'bone',pb.name)
