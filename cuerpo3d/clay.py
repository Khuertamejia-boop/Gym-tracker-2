import bpy,sys,math,os
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Cuerpo': o.hide_render=True
m=bpy.data.materials.new('clay'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(0.6,0.6,0.6,1); b.inputs['Roughness'].default_value=0.6
ob=bpy.data.objects['Cuerpo']
for i in range(len(ob.data.materials)): ob.data.materials[i]=m
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='SINGLE'; sh.single_color=(0.75,0.75,0.75); sh.show_cavity=False
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
V={'front':((0,-6.5,0.95),(90,0,0),2.1),'back':((0,6.5,0.95),(90,0,180),2.1),'side':((6.5,0,0.95),(90,0,90),2.1),
   'legsf':((0,-6.5,0.5),(90,0,0),1.0),'legsb':((0,6.5,0.5),(90,0,180),1.0),'armf':((0.35,-6.5,1.25),(90,0,0),0.7),'armb':((0.35,6.5,1.25),(90,0,180),0.7),'torsob':((0,6.5,1.2),(90,0,180),0.8),'torsof':((0,-6.5,1.2),(90,0,0),0.8)}
for vn in os.environ.get('VIEWS','front,back').split(','):
    loc,rot,s=V[vn]; cam.location=loc; cam.rotation_euler=[math.radians(a) for a in rot]; cam.data.type='ORTHO'; cam.data.ortho_scale=s
    sc.render.resolution_x,sc.render.resolution_y=(700,1000) if s>2 else (800,800)
    sc.render.filepath=f'{out}_{vn}.png'; bpy.ops.render.render(write_still=True)
