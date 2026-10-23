import bpy, numpy as np, math, os
bpy.ops.wm.open_mainfile(filepath='PSM_gt5.blend')
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Barra': o.hide_render=True
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
t=(0.30,-0.03,2.135); p=math.radians(-8); d=6
cam.location=(t[0], t[1]-d*math.cos(p), t[2]+d*math.sin(p)); cam.rotation_euler=(math.radians(98),0,0)
cam.data.type='ORTHO'; cam.data.ortho_scale=0.2; sc.render.resolution_x=sc.render.resolution_y=200
sc.render.engine='CYCLES'; sc.cycles.samples=1; sc.render.film_transparent=True
if os.environ.get('NOMOD'): bpy.data.objects['Barra'].modifiers[0].show_render=False
sc.render.filepath=os.environ.get('GT3D','/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad')+'/w/r/bartest.png'; bpy.ops.render.render(write_still=True)
from PIL import Image
a=np.array(Image.open(sc.render.filepath)); ys=np.where(a[:,10,3]>128)[0]; print('ROWS',ys.min()*5,ys.max()*5)
