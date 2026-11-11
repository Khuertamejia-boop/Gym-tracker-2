# Extract the realistic male body from the Blender Human Base Meshes bundle (CC0), apply its sculpt detail level.
import bpy,sys,os
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src,load_ui=False)
keep=[o for o in bpy.data.objects if o.name.startswith('GEO-body_male_realistic')]
for o in list(bpy.data.objects):
    if o not in keep: bpy.data.objects.remove(o,do_unlink=True)
b=bpy.data.objects['GEO-body_male_realistic']
for m in b.modifiers:
    if m.type=='MULTIRES':
        print('multires levels',m.total_levels,'sculpt',m.sculpt_levels,'render',m.render_levels)
        m.levels=m.render_levels=m.sculpt_levels=int(os.environ.get('LV',m.total_levels))
bpy.context.view_layer.objects.active=b
for o in bpy.context.view_layer.objects: o.select_set(o==b)
for m in list(b.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
b.name='Hi'; b.data.name='Hi'
print('verts',len(b.data.vertices),'dims',tuple(round(d,3) for d in b.dimensions),'loc',tuple(b.location))
bpy.ops.wm.save_as_mainfile(filepath=out)
