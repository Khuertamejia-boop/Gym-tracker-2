import bpy
bpy.ops.wm.open_mainfile(filepath='H_t1.blend')
r=bpy.data.objects['Rig']; print('BONES',len(r.data.bones),[b.name for b in r.data.bones if b.name.endswith('.L') or '.' not in b.name])
c=bpy.data.objects['Cuerpo']; h=bpy.data.objects['Hi']
print('CUERPO verts',len(c.data.vertices),'groups',len(c.vertex_groups),'mods',[m.type for m in c.modifiers])
print('HI verts',len(h.data.vertices),'groups',len(h.vertex_groups),'mods',[m.type for m in h.modifiers])
