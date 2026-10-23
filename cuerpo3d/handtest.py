import bpy,sys,math,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import hand_geo
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
h=hand_geo.build()
RB=float(os.environ.get('BARR',0.0145))
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=RB,depth=0.5,rotation=(0,math.pi/2,0),location=(0,0,0))
bar=bpy.context.object
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=int(os.environ.get('SMP',10)); sc.cycles.use_denoising=False
mat=bpy.data.materials.new('m'); mat.diffuse_color=(0.8,0.8,0.8,1)
mat.use_nodes=True; mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.78,0.78,0.78,1)
for ob in (h,bar): ob.data.materials.append(mat)
ld=bpy.data.lights.new('s','SUN'); ld.energy=3.0; lo=bpy.data.objects.new('s',ld); sc.collection.objects.link(lo); lo.rotation_euler=(math.radians(50),0,math.radians(30))
sc.render.resolution_x=int(os.environ.get('RES',600)); sc.render.resolution_y=int(os.environ.get('RES',600))
sc.world=bpy.data.worlds.new('w'); sc.world.use_nodes=True; sc.world.node_tree.nodes['Background'].inputs[0].default_value=(1,1,1,1); sc.world.node_tree.nodes['Background'].inputs[1].default_value=0.8
cam=bpy.data.cameras.new('c'); cam.type='ORTHO'; cam.ortho_scale=float(os.environ.get('OSC',0.2))
co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); sc.camera=co
# local frame: X bar axis, s along fingers, t palm normal  (here drawn with s=+Z up? use world: X, Y=s, Z=t)
views={'side':((-1,0,0.0),(0.0,0.0,0.0)),'front':((0,-1,0),(0,0,0)),'palm':((0,0,1),(0,0,0)),'back':((0,0,-1),(0,0,0)),'t34':((-0.7,-0.5,0.5),(0,0,0))}
outdir=sys.argv[-1]
for name,(d,_) in views.items():
    dv=Vector(d).normalized(); co.location=Vector((0.0,-0.02,0.0))-dv*1.0
    co.rotation_euler=(-dv).to_track_quat('-Z','Y').to_euler()
    co.rotation_euler=(dv).to_track_quat('-Z','Y').to_euler() if False else co.rotation_euler
    # look from -dv*? camera looks along its -Z axis: point it at the origin
    direction=Vector((0.0,-0.02,0.0))-co.location
    co.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'{outdir}/{name}.png'; bpy.ops.render.render(write_still=True)
print('verts',len(h.data.vertices))
