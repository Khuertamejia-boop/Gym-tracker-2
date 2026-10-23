import bpy,numpy as np
bpy.ops.wm.open_mainfile(filepath='NH_1.blend')
me=bpy.data.objects['Hi'].data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
C=np.array([0,-0.02,1.63]); m=(co[:,2]>1.60)&(co[:,2]<1.66)&(np.abs(co[:,0])<0.12)
v=co[m]-C; r=np.linalg.norm(v,axis=1); el=np.degrees(np.arcsin(v[:,2]/r)); az=np.degrees(np.arctan2(v[:,0],-v[:,1]))
for a0 in (0,90,180):
    s=(np.abs(((az-a0+180)%360)-180)<4)
    o=np.argsort(el[s]); e=el[s][o]; rr=r[s][o]
    print('az',a0,' '.join(f'{x:.1f}:{y*1000:.1f}' for x,y in zip(e[::max(1,len(e)//18)],rr[::max(1,len(e)//18)])))
# face normals continuity: use mesh polygons smooth flag
pf=np.zeros(len(me.polygons),bool); me.polygons.foreach_get('use_smooth',pf); print('smooth faces',pf.sum(),'of',len(pf))
