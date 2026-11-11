import bpy,numpy as np,sys
def get(f):
    bpy.ops.wm.open_mainfile(filepath=f); me=bpy.data.objects['Hi'].data
    c=np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co',c); return c.reshape(-1,3)
a=get(sys.argv[-2]); b=get(sys.argv[-1])
d=b-a
for z in (1.43,1.41,1.39,1.37):
    m=(np.abs(a[:,2]-z)<0.004)&(a[:,1]<-0.02)&(a[:,0]>0)&(a[:,0]<0.12)
    o=np.argsort(a[m,0]); X=a[m][o]; Dd=d[m][o]
    print('z',z,' '.join(f'{x*100:.1f}:{dy*1000:.0f}/{dz*1000:.0f}' for x,dy,dz in zip(X[::3,0],Dd[::3,1],Dd[::3,2]))[:900])
