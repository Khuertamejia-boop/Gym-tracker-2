import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
me=bpy.data.objects['Hi'].data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
q=np.zeros(nv,np.float32); me.attributes['mq'].data.foreach_get('value',q)
for p in [(0.10,-0.03,1.47),(0.14,-0.02,1.46),(0.12,0.02,1.48),(0.08,-0.06,1.44),(0.12,-0.10,1.38)]:
    d=np.linalg.norm(co-np.array(p),axis=1); i=np.argsort(d)[:30]
    print(p, 'nearest',co[i[0]].round(3),'mq mean',q[i].mean().round(2),'min',q[i].min().round(2))
