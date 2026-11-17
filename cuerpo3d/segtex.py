import bpy,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2])
im=bpy.data.images.load(sys.argv[-3]); 
for m in bpy.data.objects['Cuerpo'].data.materials:
    if m:
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE': n.image=im
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])
