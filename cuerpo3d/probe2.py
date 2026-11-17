import bpy,numpy as np
from scipy.spatial import cKDTree
bpy.ops.wm.open_mainfile(filepath='A_f2.blend')
def co(o):
    me=o.data; c=np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co',c); return c.reshape(-1,3)
h=co(bpy.data.objects['Hi']); l=co(bpy.data.objects['Cuerpo'])
d,i=cKDTree(l).query(h)
m=(h[:,1]<-0.0)&(np.abs(h[:,2]-1.27)<0.05)&(h[:,0]>0.08)&(h[:,0]<0.24)
for zb in np.arange(1.22,1.33,0.02):
    row=[]
    for xb in np.arange(0.08,0.24,0.02):
        s=m&(np.abs(h[:,2]-zb)<0.01)&(np.abs(h[:,0]-xb)<0.01)
        row.append(f"{d[s].max()*1000:5.1f}" if s.any() else "  -  ")
    print(f"z{zb:.2f}",' '.join(row))
