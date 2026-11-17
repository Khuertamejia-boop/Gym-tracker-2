# Flat gym bench: padded top (rounded box, dark), steel frame (central beam, two T-legs).
import bpy, bmesh
from mathutils import Vector, Matrix
def _mat(name,col,rough,metal=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
    b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(*col,1); b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
    return m
def _box(name,c,size,mat,bevel=0.0,seg=3):
    bpy.ops.mesh.primitive_cube_add(size=1,location=c); o=bpy.context.active_object; o.name=name; o.scale=size
    bpy.ops.object.transform_apply(scale=True)
    if bevel>0:
        bv=o.modifiers.new('bv','BEVEL'); bv.width=bevel; bv.segments=seg
    o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o
def make_bench(top,y0=-0.30,y1=0.95,width=0.28,thick=0.075):
    for o in [o for o in bpy.data.objects if o.name.startswith('Banco')]: bpy.data.objects.remove(o,do_unlink=True)
    pad=_mat('banco_pad',(0.035,0.035,0.04),0.55); steel=_mat('banco_steel',(0.12,0.12,0.13),0.35,0.8)
    L=y1-y0; yc=(y0+y1)/2
    _box('Banco_pad',(0,yc,top-thick/2),(width,L,thick),pad,bevel=0.025,seg=5)
    _box('Banco_base',(0,yc,top-thick-0.015),(width*0.85,L*0.96,0.03),steel,bevel=0.004)
    _box('Banco_beam',(0,yc,0.20),(0.06,L*0.78,0.06),steel,bevel=0.006)
    for yy in (y0+0.10,y1-0.10):
        _box('Banco_post',(0,yy,(top-thick)/2),(0.06,0.06,top-thick-0.03),steel,bevel=0.006)
        _box('Banco_foot',(0,yy,0.02),(0.42,0.06,0.04),steel,bevel=0.006)
