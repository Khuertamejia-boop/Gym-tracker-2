# white-background illustration render
import bpy,sys,math,os
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!=os.environ.get('OBJ','Cuerpo') and not os.environ.get('PROPS'): o.hide_render=True
if os.environ.get('CLAY'):
    ob=bpy.data.objects[os.environ.get('OBJ','Cuerpo')]
    m=bpy.data.materials.new('clay'); b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(0.85,0.85,0.85,1); b.inputs['Roughness'].default_value=0.55
    for i in range(len(ob.data.materials)): ob.data.materials[i]=m
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=int(os.environ.get('SMP','32')); sc.cycles.device='CPU'
sc.view_settings.view_transform='Standard'; sc.view_settings.exposure=float(os.environ.get('EXP','0'))
sc.cycles.use_denoising=True
sc.render.film_transparent=True
w=bpy.data.worlds.new('w3'); w.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value=float(os.environ.get('AMB','0.55')); sc.world=w
def light(n,loc,rot,e,sz=4):
    l=bpy.data.lights.new(n,'AREA'); l.energy=e; l.size=sz; o=bpy.data.objects.new(n,l); o.location=loc; o.rotation_euler=[math.radians(a) for a in rot]; sc.collection.objects.link(o); return o
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
V={'front':((0,-6.5,0.92),(90,0,0),2.0),'back':((0,6.5,0.92),(90,0,180),2.0),'q':((4.6,-4.6,0.92),(90,0,45),2.0),'qb':((-4.6,4.6,0.92),(90,0,225),2.0),
   'side':((6.5,0,0.92),(90,0,90),2.0),'torsof':((0,-6.5,1.22),(90,0,0),0.8),'torsob':((0,6.5,1.22),(90,0,180),0.8),'legsf':((0,-6.5,0.5),(90,0,0),1.0),'legsb':((0,6.5,0.5),(90,0,180),1.0),
   'armf':((0.36,-6.5,1.2),(90,0,0),0.6),'arma':((1.2,-3.8,1.18),(90,0,18),0.55),'armp':((1.6,3.5,1.25),(90,0,155),0.55),'face':((0,-6.5,1.6),(90,0,0),0.35),'tq':((2.3,-2.3,1.2),(90,0,45),0.9),'tqb':((-2.3,2.3,1.15),(90,0,225),0.9),'hamz':((0.15,6.5,0.62),(90,0,180),0.3)}
E=float(os.environ.get('LE','1.0'))
lights=[]
for vn in os.environ.get('VIEWS','front,back').split(','):
    loc,rot,s=V[vn]
    for l in lights: bpy.data.objects.remove(l,do_unlink=True)
    yaw=rot[2]; 
    def rl(dx,dy,dz,az,e,sz=4):
        a=math.radians(yaw); x=dx*math.cos(a)-dy*math.sin(a); y=dx*math.sin(a)+dy*math.cos(a)
        o=light('L%d'%len(lights),(x,y,dz),(0,0,0),e*E,sz); d=__import__('mathutils').Vector((0,0,1.0))-o.location
        o.rotation_euler=(-d).to_track_quat('Z','Y').to_euler(); return o
    lights=[rl(2.2,-3.2,3.4,0,420),rl(-3.0,-2.2,1.6,0,160),rl(0,3.5,2.8,0,260),rl(0,-2,-1.5,0,60)]
    cam.location=loc; cam.rotation_euler=[math.radians(a) for a in rot]; cam.data.type='ORTHO'; cam.data.ortho_scale=s
    r=int(os.environ.get('RES','900')); sc.render.resolution_x,sc.render.resolution_y=(int(r*0.75),r) if s>=2 else (r,r)
    sc.render.filepath=f'{out}_{vn}.png'; bpy.ops.render.render(write_still=True)
