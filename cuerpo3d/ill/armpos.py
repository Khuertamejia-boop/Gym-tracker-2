import os
import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
me=bpy.data.objects['Hi'].data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
r=np.load(os.environ.get('GT3D','/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad')+'/ill/rest.npz',allow_pickle=True); main=r['main']
for g in (('upper_arm.L','delt.L'),('forearm.L','fa_tw1.L','fa_tw2.L','fa_tw3.L'),('clavicle.L',)):
    m=np.array([str(x) in g for x in main]); print(g[0],'centre',np.round(co[m].mean(0),3),'min',np.round(co[m].min(0),3),'max',np.round(co[m].max(0),3))
