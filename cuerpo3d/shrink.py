# Make chosen muscles a little smaller on the base body: the skin moves inwards along its normal by up to N mm over
# each muscle (atlas labels), with a smooth falloff into the neighbours (no step at the borders). Both sides.
#   SHRINK="trap_upper:7,pec_clavicular:6,pec_sternal:6" SMIT=25 python -I shrink.py in.blend out.blend
import bpy, sys, os, numpy as np, scipy.sparse as sp
E=lambda k,d: float(os.environ.get(k,d))
src,out=sys.argv[-2],sys.argv[-1]
G=os.environ.get('GT3D',os.path.dirname(os.path.abspath(__file__)))
atl=np.load(os.path.join(G,'ill','pv','bla.npz'),allow_pickle=True); names=[str(n) for n in atl['names']]; mid=atl['mid'].astype(int)
base=np.array([n.rsplit('.',1)[0] for n in names]); groups=np.array(['none']+[str(g) for g in atl['groups']])
bpy.ops.wm.open_mainfile(filepath=src); hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
assert nv==len(mid), 'mesh and atlas differ'
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
no=np.zeros(nv*3); me.vertices.foreach_get('normal',no); no=no.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(2*len(ed)),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); Wm=sp.diags(1/np.maximum(deg,1))@A
d=np.zeros(nv)
for it in [x for x in os.environ.get('SHRINK','').split(',') if x.strip()]:
    key,mm=it.rsplit(':',1); ids=[i for i in range(1,len(names)) if base[i]==key or groups[i]==key]
    if not ids: print('WARNING unknown muscle',key); continue
    ind=np.isin(mid,ids).astype(float)
    for _ in range(int(E('SMIT',25))): ind=0.5*ind+0.5*(Wm@ind)        # smooth falloff (~2 cm)
    d=np.maximum(d,float(mm)*ind)
    print('%-16s up to %.1f mm, %d verts'%(key,float(mm),int((ind>0.5).sum())))
co-=no*(d[:,None]/1000.0)
me.vertices.foreach_set('co',co.ravel()); me.update()
print('moved verts',int((d>0.05).sum()),'max %.1f mm'%d.max())
bpy.ops.wm.save_as_mainfile(filepath=out)
