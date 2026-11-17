import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
name=[o.name for o in bpy.data.objects if o.name in ('Hi',)][0]
me=bpy.data.objects[name].data; nv=len(me.vertices)
c=np.zeros(nv*3); me.vertices.foreach_get('co',c); c=c.reshape(-1,3)
out=[]
for z in np.arange(1.22,1.31,0.006):
    k=(np.abs(np.abs(c[:,0])-0.11)<0.003)&(np.abs(c[:,2]-z)<0.0025)&(c[:,1]<-0.05)
    out.append(f'{z:.3f}:{c[k,1].min()*1000:.1f}' if k.any() else f'{z:.3f}:-')
print('PROF',' '.join(out))
