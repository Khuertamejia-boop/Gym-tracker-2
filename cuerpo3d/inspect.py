import bpy,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
for o in bpy.data.objects:
    d=o.data
    print(o.name,o.type, len(d.vertices) if o.type=='MESH' else '', [m.type+':'+m.name for m in o.modifiers], o.parent.name if o.parent else '')
    if o.type=='MESH':
        print('  mats',[m.name if m else None for m in d.materials],'uv',[u.name for u in d.uv_layers],'vg',len(o.vertex_groups),'attrs',[a.name for a in d.attributes][:30])
        if d.shape_keys: print('  sk',[k.name for k in d.shape_keys.key_blocks][:20])
for a in bpy.data.actions: print('action',a.name,a.frame_range[:])
print('imgs',[i.name for i in bpy.data.images])
print('scene frames',bpy.context.scene.frame_start,bpy.context.scene.frame_end)
