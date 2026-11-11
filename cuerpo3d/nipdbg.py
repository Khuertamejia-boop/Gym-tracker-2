import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
c=np.zeros(nv*3); me.vertices.foreach_get('co',c); c=c.reshape(-1,3)
m=(np.abs(np.abs(c[:,0])-0.138)<0.02)&(np.abs(c[:,2]-1.31)<0.02)&(c[:,1]<-0.1)
print('N verts',m.sum(),'min y',c[m,1].min(), 'median y',np.median(c[m,1]))
# profile along z at x=0.138: y front
for z in np.arange(1.24,1.38,0.01):
    k=(np.abs(np.abs(c[:,0])-0.138)<0.004)&(np.abs(c[:,2]-z)<0.003)&(c[:,1]<-0.05)
    print('z',round(z,3),'front y',round(float(c[k,1].min()),4) if k.any() else None)
