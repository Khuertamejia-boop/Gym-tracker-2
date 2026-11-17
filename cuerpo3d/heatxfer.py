# Heat weights on the clean base-level mesh, copied to the detailed mesh (nearest surface, interpolated).
# usage: blender -b -P heatxfer.py -- rigged_detailed.blend base_level.blend out.blend
import bpy,sys,numpy as np
src,lo,out=sys.argv[-3],sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; rig=bpy.data.objects['Rig']
with bpy.data.libraries.load(lo) as (a,b): b.objects=['Hi']
L=b.objects[0]; L.name='Lo'; bpy.context.scene.collection.objects.link(L)
# same centring as the detailed mesh
co=np.zeros(len(L.data.vertices)*3); L.data.vertices.foreach_get('co',co); co=co.reshape(-1,3)
co=np.array([L.matrix_world@__import__('mathutils').Vector(c) for c in co]); co[:,0]-=0.5*(co[:,0].max()+co[:,0].min())
L.data.vertices.foreach_set('co',co.ravel()); L.matrix_world.identity()
for g in list(hi.vertex_groups): hi.vertex_groups.remove(g)
for m in list(hi.modifiers): hi.modifiers.remove(m)
dl={b.name:b.use_deform for b in rig.data.bones}
for n in ('delt.L','delt.R','bar'): rig.data.bones[n].use_deform=False
for o in bpy.context.view_layer.objects: o.select_set(o in (L,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
print('Lo groups',len(L.vertex_groups),'verts with no weight',sum(1 for v in L.data.vertices if len(v.groups)==0))
for n,v in dl.items(): rig.data.bones[n].use_deform=v
for g in L.vertex_groups: hi.vertex_groups.new(name=g.name)
dt=hi.modifiers.new('dt','DATA_TRANSFER'); dt.object=L; dt.use_vert_data=True; dt.data_types_verts={'VGROUP_WEIGHTS'}
dt.vert_mapping='POLYINTERP_NEAREST'; dt.layers_vgroup_select_src='ALL'; dt.layers_vgroup_select_dst='NAME'
bpy.context.view_layer.objects.active=hi
for o in bpy.context.view_layer.objects: o.select_set(o==hi)
bpy.ops.object.modifier_apply(modifier='dt')
for n in ('delt.L','delt.R'):
    if n not in hi.vertex_groups: hi.vertex_groups.new(name=n)
md=hi.modifiers.new('Armature','ARMATURE'); md.object=rig
bpy.data.objects.remove(L,do_unlink=True)
print('Hi groups',len(hi.vertex_groups),'unweighted',sum(1 for v in hi.data.vertices if len(v.groups)==0))
bpy.ops.wm.save_as_mainfile(filepath=out)
