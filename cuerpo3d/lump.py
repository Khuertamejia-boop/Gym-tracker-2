import bpy,sys,numpy as np,scipy.sparse as sp0
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
c=np.zeros(nv*3); me.vertices.foreach_get('co',c); c=c.reshape(-1,3)
nr=np.zeros(nv*3); me.vertices.foreach_get('normal',nr); nr=nr.reshape(-1,3)
Ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',Ed); Ed=Ed.reshape(-1,2)
A=sp0.coo_matrix((np.ones(2*len(Ed)),(np.r_[Ed[:,0],Ed[:,1]],np.r_[Ed[:,1],Ed[:,0]])),shape=(nv,nv)).tocsr()
Av=(sp0.diags(1/np.maximum(np.asarray(A.sum(1)).ravel(),1))@A).tocsr()
s=c.copy()
for _ in range(80): s=0.5*s+0.5*(Av@s)
off=np.sum((c-s)*nr,1)
m=(c[:,0]>0.085)&(c[:,0]<0.20)&(c[:,2]>1.15)&(c[:,2]<1.36)&(c[:,1]<-0.04)
idx=np.where(m)[0]; o=idx[np.argsort(-off[idx])][:8]
for i in o: print('LUMP',np.round(c[i],3),round(float(off[i])*1000,2),'mm')
ms=me.attributes['mseg']; 
