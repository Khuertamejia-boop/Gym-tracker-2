# New body finishing: clean shorts (smooth waistband and hem), smoothed transferred style values (mq, ln),
# majority-filtered muscle ids (no stair steps), faceless smooth mannequin head.
# usage: blender -b -P finishstyle.py -- in.blend out.blend
import bpy,sys,os
import numpy as np, scipy.sparse as sp
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices); rig=bpy.data.objects['Rig']
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1
gi={g.index:g.name for g in hi.vertex_groups}
W=lambda pref: np.array([sum(g.weight for g in v.groups if gi[g.group].startswith(pref)) for v in me.vertices])
arm=W(('upper_arm','forearm','hand','thumb','index','middle','ring','pinky'))
head=W('head')
ss=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
# ---- shorts: waistband a bit higher at the back, hem at mid thigh
zw=E('ZW',0.925)+E('ZWB',0.02)*ss((co[:,1]+0.02)/0.10)
zh=E('ZH',0.60)
band=E('BAND',0.003)
sh=ss((zw-co[:,2])/band+0.5)*ss((co[:,2]-zh)/band+0.5)*(arm<0.05)
a=me.attributes.get('shorts') or me.attributes.new('shorts','FLOAT','POINT'); a.data.foreach_set('value',sh.astype(np.float32))
# ---- smooth the transferred style values
for n in ('mq','ln'):
    if n in me.attributes:
        v=np.zeros(nv,np.float32); me.attributes[n].data.foreach_get('value',v)
        for _ in range(int(E('SMV',25))): v=(A@v)/deg*0.5+v*0.5
        me.attributes[n].data.foreach_set('value',v.astype(np.float32))
# ---- muscle ids per face: majority over face neighbours (removes the stair steps)
lt=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_total',lt); ls=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_start',ls)
lv=np.zeros(len(me.loops),int); me.loops.foreach_get('vertex_index',lv)
nf=len(me.polygons); fv=np.repeat(np.arange(nf),lt)
VF=sp.coo_matrix((np.ones(len(lv)),(lv,fv)),shape=(nv,nf)).tocsr()
mseg=np.zeros(nf,np.float32); me.attributes['mseg'].data.foreach_get('value',mseg)
mi=np.zeros(nf,int); me.polygons.foreach_get('material_index',mi)
FF=(VF.T@VF).tocsr()
for arr in (mseg,mi):
    vals=np.unique(arr)
    for it in range(int(E('MAJ',6))):
        # score of each value per face = share among faces sharing a vertex with it
        best=arr.copy(); bestsc=np.zeros(nf)
        for val in vals:
            sc=FF@(arr==val).astype(float)
            m=sc>bestsc; best[m]=val; bestsc[m]=sc[m]
        arr[:]=best
me.attributes['mseg'].data.foreach_set('value',mseg); me.polygons.foreach_set('material_index',mi)
# ---- mannequin head: radius from the head centre smoothed over the surface (face and ears melt into an egg shape)
hb=rig.data.bones['head']; c=np.array(hb.head_local)*0.6+np.array(hb.tail_local)*0.4
mk=ss((co[:,2]-E('HZ0',1.50))/E('HZW',0.06))*E('HEADON',1.0)
mk=(mk>0.5).astype(float)
for _ in range(int(E('HMS',150))): mk=(A@mk)/deg*0.5+mk*0.5
mk=ss((mk-0.15)/0.7)
if 'ln' in me.attributes:
    lnv=np.zeros(nv,np.float32); me.attributes['ln'].data.foreach_get('value',lnv); me.attributes['ln'].data.foreach_set('value',(lnv*(1-ss((co[:,2]-1.44)/0.04))).astype(np.float32))
r=np.linalg.norm(co-c,axis=1); u=(co-c)/r[:,None]
hv=np.where(mk>0.01)[0]
# smooth radius function of the direction: polynomial in (ux,uy,uz) up to degree DEG, robust fit (ears, eye sockets out)
from itertools import product
DEG=int(E('HDEG',4)); terms=[(a_,b_,c_) for a_ in range(DEG+1) for b_ in range(DEG+1) for c_ in range(DEG+1) if a_+b_+c_<=DEG]
def feats(U): return np.column_stack([U[:,0]**a_*U[:,1]**b_*U[:,2]**c_ for a_,b_,c_ in terms])
X=feats(u[hv]); y=r[hv]; keep=np.ones(len(hv),bool)
for it in range(4):
    coef,*_=np.linalg.lstsq(X[keep],y[keep],rcond=None)
    res=y-X@coef; keep=np.abs(res)<E('HTOL',0.008)
rs=r.copy(); rs[hv]=X@coef
print('head fit: kept %.0f%% of points'%(keep.mean()*100))
new=co+mk[:,None]*((c+u*rs[:,None])-co)
# final light Taubin on the head to even it out
for _ in range(int(E('HT',30))):
    for f in (0.5,-0.53): new=new+mk[:,None]*f*((A@new)/deg[:,None]-new)
me.vertices.foreach_set('co',new.ravel()); me.update()
print('shorts verts',int((sh>0.5).sum()),'head verts',int((mk>0.5).sum()))
bpy.ops.wm.save_as_mainfile(filepath=out)
