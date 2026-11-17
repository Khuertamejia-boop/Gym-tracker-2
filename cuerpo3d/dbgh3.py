import bpy,numpy as np
bpy.ops.wm.open_mainfile(filepath='NH_1.blend')
ob=bpy.data.objects['Hi']; me=ob.data; nv=len(me.vertices)
print('attrs',[ (a.name,a.domain) for a in me.attributes if not a.name.startswith('.')])
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
nr=np.zeros(nv*3); me.vertices.foreach_get('normal',nr); nr=nr.reshape(-1,3)
C=np.array([0,-0.02,1.63]); m=(np.abs(co[:,2]-1.63)<0.05)&(np.abs(co[:,0])<0.12)&(co[:,1]>-0.01)
v=co[m]-C; vn=nr[m]; dev=np.degrees(np.arccos(np.clip(np.sum(vn*v/np.linalg.norm(v,axis=1,keepdims=True),1),-1,1)))
z=co[m,2]
for h in np.arange(1.58,1.68,0.005):
    k=(np.abs(z-h)<0.0025)
    if k.any(): print(round(h,3),round(float(dev[k].mean()),2),end=' | ')
print()
for n in ('mq','ln','shorts','mu','groove'):
    a=me.attributes.get(n)
    if a: 
        x=np.zeros(len(a.data),np.float32); a.data.foreach_get('value',x); print(n,'head-zone mean by z:',[round(float(x[m][np.abs(z-h)<0.0025].mean()),3) for h in (1.60,1.62,1.63,1.64,1.66) if (np.abs(z-h)<0.0025).any()])
