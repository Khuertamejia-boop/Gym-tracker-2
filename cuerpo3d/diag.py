import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
ob=bpy.data.objects['Cuerpo']; me=ob.data
co=np.array([v.co[:] for v in me.vertices])
E=np.array([e.vertices[:] for e in me.edges]); L=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1); mid=(co[E[:,0]]+co[E[:,1]])/2
def reg(n,m): print(n, 'edges',m.sum(),'mean len mm',round(L[m].mean()*1000,1),'p90',round(np.percentile(L[m],90)*1000,1))
ax=np.abs(mid[:,0]); z=mid[:,2]
reg('torso',(ax<0.2)&(z>0.95)&(z<1.45)); reg('thigh',(ax>0.03)&(ax<0.3)&(z>0.5)&(z<0.85)); reg('shin',(z>0.15)&(z<0.48)); reg('upperarm',(ax>0.25)&(z>1.2)&(z<1.42)); reg('forearm',(ax>0.35)&(z<1.2)&(z>1.05))
print('nverts',len(co),'bbox',co.min(0).round(3),co.max(0).round(3))
for b in ob.parent.data.bones: print(b.name, tuple(round(x,3) for x in b.head_local), tuple(round(x,3) for x in b.tail_local)) if '.' not in b.name or b.name.split('.')[0] in ('upper_arm','forearm','thigh','shin','clavicle','hand','foot') else None
# material counts
import collections
c=collections.Counter(p.material_index for p in me.polygons); print({me.materials[k].name:v for k,v in c.items()})
