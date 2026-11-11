# relief fields of the rest body for the illustration look -> npz (per vertex, same order as every posed frame)
import bpy,sys,os,numpy as np,scipy.sparse as sp
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1; Av=sp.diags(1/deg)@A
def lapsm(X,n):
    for _ in range(n): X=0.5*X+0.5*(Av@X)
    return X
def nrm(X):
    me.vertices.foreach_set('co',X.ravel()); me.update(); n=np.zeros(nv*3); me.vertices.foreach_get('normal',n); return n.reshape(-1,3)
res={}
for name,a,b in (('h_fine',2,30),('h_mid',6,150)):
    S1=lapsm(co,a); S2=lapsm(co,b); n2=nrm(S2)
    h=((S1-S2)*n2).sum(1); h=h-lapsm(h,500); res[name]=h.astype(np.float32)
    print(name,np.percentile(h,[1,5,50,95,99])*1000)
me.vertices.foreach_set('co',co.ravel()); me.update()
el=np.linalg.norm(co[ed[:,0]]-co[ed[:,1]],axis=1); print('edge len mm p5/50/95',np.percentile(el,[5,50,95])*1000)
np.savez(out,**res)
