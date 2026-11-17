import bpy,sys,math,os
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!=os.environ.get('OBJ','Cuerpo'): o.hide_render=True
ob=bpy.data.objects[os.environ.get('OBJ','Cuerpo')]
if os.environ.get('CLAY'):
    m=bpy.data.materials.new('clay'); b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(0.55,0.55,0.55,1); b.inputs['Roughness'].default_value=0.55
    for i in range(len(ob.data.materials)): ob.data.materials[i]=m
if os.environ.get('SEGVIZ'):
    m=bpy.data.materials.new('seg'); nt=m.node_tree; b=nt.nodes['Principled BSDF']
    at=nt.nodes.new('ShaderNodeAttribute'); at.attribute_name='mseg'; at.attribute_type='GEOMETRY'
    mu=nt.nodes.new('ShaderNodeMath'); mu.operation='MULTIPLY'; mu.inputs[1].default_value=0.6180339
    fr=nt.nodes.new('ShaderNodeMath'); fr.operation='FRACT'
    hs=nt.nodes.new('ShaderNodeCombineColor'); hs.mode='HSV'; hs.inputs[1].default_value=0.55; hs.inputs[2].default_value=0.85
    nt.links.new(at.outputs['Fac'],mu.inputs[0]); nt.links.new(mu.outputs[0],fr.inputs[0]); nt.links.new(fr.outputs[0],hs.inputs[0]); nt.links.new(hs.outputs[0],b.inputs['Base Color'])
    for i in range(len(ob.data.materials)): ob.data.materials[i]=m
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=int(os.environ.get('SMP','24')); sc.cycles.device='CPU'; sc.view_settings.view_transform='Standard'
try: sc.cycles.use_denoising=True; sc.cycles.denoiser='OPENIMAGEDENOISE'
except Exception as e: print(e)
w=bpy.data.worlds.new('w2'); w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.10,0.10,0.11,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.6; sc.world=w
def light(n,loc,rot,e,sz=3):
    l=bpy.data.lights.new(n,'AREA'); l.energy=e*float(os.environ.get('LS','0.4')); l.size=sz; o=bpy.data.objects.new(n,l); o.location=loc; o.rotation_euler=[math.radians(a) for a in rot]; sc.collection.objects.link(o)
light('k',(1.8,-3,3.2),(55,0,28),380); light('f',(-3,-2,1.0),(85,0,-55),120); light('b',(-2.5,3,2.6),(120,0,-35),220); light('r',(2.5,3,1.5),(100,0,35),140)
light('k2',(-1.8,3,3.2),(-55,0,28),380*float(os.environ.get('BK','0.6')))
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
V={'front':((0,-6.5,0.95),(90,0,0),2.1),'back':((0,6.5,0.95),(90,0,180),2.1),'side':((6.5,0,0.95),(90,0,90),2.1),
   'legsf':((0,-6.5,0.5),(90,0,0),1.0),'legsb':((0,6.5,0.5),(90,0,180),1.0),'armf':((0.38,-6.5,1.2),(90,0,0),0.6),'armb':((0.38,6.5,1.2),(90,0,180),0.6),
   'torsob':((0,6.5,1.2),(90,0,180),0.75),'torsof':((0,-6.5,1.2),(90,0,0),0.75),'legss':((6.5,0,0.5),(90,0,90),1.0),'face':((0,-6.5,1.6),(90,0,0),0.35),
   'q':((4.6,-4.6,0.95),(90,0,45),2.1),'chest3':((-2.2,-6.0,1.33),(90,0,-20),0.5),'shld':((0.15,-6.5,1.40),(90,0,0),0.35),'armb2':((0.38,6.5,1.2),(90,0,180),0.6),'armq':((3.0,-4.0,1.25),(90,0,37),0.6),'armu':((0.40,-0.6,6.0),(0,0,0),0.6),'knee':((0.16,-6.5,0.53),(90,0,0),0.18),'kneeb':((0.16,6.5,0.53),(90,0,180),0.18)}
for vn in os.environ.get('VIEWS','front,back').split(','):
    loc,rot,s=V[vn]; cam.location=loc; cam.rotation_euler=[math.radians(a) for a in rot]; cam.data.type='ORTHO'; cam.data.ortho_scale=s
    r=int(os.environ.get('RES','800')); sc.render.resolution_x,sc.render.resolution_y=(int(r*0.7),r) if s>2 else (r,r)
    sc.render.filepath=f'{out}_{vn}.png'; bpy.ops.render.render(write_still=True)
