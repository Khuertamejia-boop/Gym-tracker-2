import bpy,numpy as np
bpy.ops.wm.open_mainfile(filepath='H_1.blend')
for name in ('Hi','Cuerpo'):
    o=bpy.data.objects[name]; me=o.data; c=np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co',c); c=c.reshape(-1,3)
    print(name,len(c),'hide_render',o.hide_render, 'modifiers',[m.type for m in o.modifiers], 'mw',np.round(np.array(o.matrix_world)[:3,3],3))
    m=(c[:,2]>1.60)&(c[:,2]<1.72)&(np.abs(c[:,0])<0.06)&(c[:,1]<-0.05)
    print(' front face verts',m.sum(),'y min',c[m,1].min() if m.any() else None)
