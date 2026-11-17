# Remove the faceting of the original hand model: Taubin smoothing (no shrinking) of the hand/finger skin at rest.
# usage: blender -b -P smoothhand.py -- in.blend out.blend   (env N = iterations, LAM, MU)
import bpy,sys,os
import numpy as np, scipy.sparse as sp
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1
# mask: finger groups fully, the hand bone group as a ramp towards the wrist
gi={g.name:g.index for g in hi.vertex_groups}
F=['thumb','index','middle','ring','pinky']
want={gi[f'{f}{k}.{L}'] for f in F for k in (1,2,3) for L in 'LR' if f'{f}{k}.{L}' in gi}
hand={gi[f'hand.{L}'] for L in 'LR'}
m=np.zeros(nv)
for v in me.vertices:
    s=0.0
    for g in v.groups:
        if g.group in want: s+=g.weight
        elif g.group in hand: s+=g.weight*E('HANDM',1.0)
    m[v.index]=min(s,1.0)
# soften the mask edge itself so no seam appears
for _ in range(int(E('MSM',20))): m=np.maximum(m*0,(A@m)/deg*0.5+m*0.5)
m=np.clip(m,0,1)[:,None]
print('smoothed verts',int((m[:,0]>0.01).sum()))
lam,mu=E('LAM',0.5),E('MU',-0.53)
c=co.copy()
for it in range(int(E('N',80))):
    for f in (lam,mu):
        c=c+m*f*((A@c)/deg[:,None]-c)
d=np.linalg.norm(c-co,axis=1); print('moved mm: mean %.3f  p99 %.3f  max %.3f'%(d[m[:,0]>0.5].mean()*1000,np.percentile(d[m[:,0]>0.5],99)*1000,d.max()*1000))
me.vertices.foreach_set('co',c.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
