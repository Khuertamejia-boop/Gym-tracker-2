import bpy,sys,math,os
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
ob=bpy.data.objects['Cuerpo3D']; rig=bpy.data.objects['Esqueleto']
POSE=os.environ.get('POSE','')
def rot(b,x=0,y=0,z=0):
    pb=rig.pose.bones[b]; pb.rotation_mode='XYZ'; pb.rotation_euler=(math.radians(x),math.radians(y),math.radians(z))
if POSE=='squat':
    for s in 'LR':
        rot('thigh.'+s,-80); rot('shin.'+s,95)
    rot('hips',0)
elif POSE=='curl':
    for s in 'LR':
        rot('upper_arm.'+s,-10); rot('forearm.'+s,-100)
bpy.context.view_layer.update()
m=bpy.data.materials.new('m'); m.use_nodes=True; nt=m.node_tree; b=nt.nodes['Principled BSDF']; b.inputs['Roughness'].default_value=0.55
at=nt.nodes.new('ShaderNodeAttribute'); at.attribute_name='Col'; nt.links.new(at.outputs['Color'],b.inputs['Base Color'])
ob.data.materials.clear(); ob.data.materials.append(m)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=12; sc.cycles.device='CPU'; sc.cycles.use_denoising=True; sc.view_settings.view_transform='Standard'
w=bpy.data.worlds.new('w'); w.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.5; sc.world=w
K=0.5; YAW=float(os.environ.get('YAW','0')); _y=math.radians(YAW)
def light(loc,e):
    l=bpy.data.lights.new('L','AREA'); l.energy=e; l.size=2.5; o=bpy.data.objects.new('L',l); o.location=loc; sc.collection.objects.link(o)
    d=Vector((0,0,1.0))-o.location; o.rotation_euler=(-d).to_track_quat('Z','Y').to_euler()
R=lambda x,y,z:(x*math.cos(_y)-y*math.sin(_y),x*math.sin(_y)+y*math.cos(_y),z)
light(R(-2.2,-3,3.2),240*K); light(R(3,-2,1.2),45*K); light(R(0.5,3,2.5),90*K)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
y=math.radians(YAW); p=math.radians(3); T=(0,-0.02,float(os.environ.get('TZ','0.88'))); d=6.0
cam.location=(T[0]+d*math.sin(y)*math.cos(p),T[1]-d*math.cos(y)*math.cos(p),T[2]+d*math.sin(p)); cam.rotation_euler=(math.radians(90-3),0,y)
cam.data.type='ORTHO'; cam.data.ortho_scale=float(os.environ.get('OSC','2.0'))
sc.render.film_transparent=True; sc.render.resolution_x=int(os.environ.get('RW','700')); sc.render.resolution_y=int(os.environ.get('RH','1100'))
sc.render.filepath=out; bpy.ops.render.render(write_still=True)
