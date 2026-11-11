import bpy,sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[-1])
for o in bpy.data.objects:
    if o.type=='MESH': print('MESH',o.name,len(o.data.vertices),'verts',len(o.data.polygons),'faces','groups',len(o.vertex_groups),'mods',[m.type for m in o.modifiers],'colors',[c.name for c in o.data.color_attributes])
    if o.type=='ARMATURE': print('ARM',o.name,len(o.data.bones),'bones')
