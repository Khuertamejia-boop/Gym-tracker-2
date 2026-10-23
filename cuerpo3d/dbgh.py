import bpy,numpy as np
bpy.ops.wm.open_mainfile(filepath='H_ma.blend')
me=bpy.data.objects['Hi'].data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
m=(co[:,2]>1.58)&(np.abs(co[:,0])<0.003)&(co[:,1]>-0.2)&(co[:,1]<0.2)
y=co[m,1]; z=co[m,2]; o=np.argsort(z)
back=y>-0.02
for lab,sel in (('front',~back),('back',back)):
    zz=z[sel]; yy=y[sel]; oo=np.argsort(zz); zz=zz[oo]; yy=yy[oo]
    # silhouette y at heights
    for h in np.arange(1.60,1.76,0.01):
        k=np.abs(zz-h)<0.0015
        if k.any(): print(lab,round(h,3),round(float(yy[k].mean()),4),end=' | ')
    print()
