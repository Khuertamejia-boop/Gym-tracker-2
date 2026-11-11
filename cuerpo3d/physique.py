# Athletic / aesthetic physique from the bodybuilder model: smooth spatial displacement fields per region (seam-safe:
# masks are 3D-smoothed shares of each muscle's skin, so touching skin pieces move together).
#   traps: lower;  deltoids: smaller towards the shoulder joint;  lats: in towards the body;  pecs: less forward;
#   upper back: less thick;  upper arms: slimmer around the bone.
# Applies to every shape key too.  usage: blender -b -P physique.py -- in.blend out.blend   env K_* multipliers
import bpy,sys,os
import numpy as np
from scipy.spatial import cKDTree
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices); bb=bpy.data.objects['Rig'].data.bones
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
names=[m.name for m in me.materials]
mi=np.zeros(len(me.polygons),int); me.polygons.foreach_get('material_index',mi)
lt=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_total',lt); ls=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_start',ls)
lv=np.zeros(len(me.loops),int); me.loops.foreach_get('vertex_index',lv)
pv=np.repeat(np.arange(len(me.polygons)),lt)       # polygon of each loop
def ind(mat):
    k=names.index(mat); a=np.zeros(nv,np.float32); sel=mi[pv]==k; a[lv[sel]]=1.0; return a
gi={g.index:g.name for g in hi.vertex_groups}
arm=np.zeros(nv); ua=np.zeros(nv)
for v in me.vertices:
    for g in v.groups:
        n=gi.get(g.group,'')
        if n.startswith(('upper_arm','forearm','hand','thumb','index','middle','ring','pinky')): arm[v.index]+=g.weight
        elif n.startswith('delt'): arm[v.index]+=0.5*g.weight
        if n.startswith('upper_arm'): ua[v.index]+=g.weight
roi=np.where((co[:,2]>0.95)&(co[:,2]<1.62))[0]
rng=np.random.default_rng(1); sub=rng.choice(roi,min(len(roi),150000),replace=False)
tree=cKDTree(co[sub]); SIG=E('SIG',0.025)
dd,ii=tree.query(co[roi],k=96); w=np.exp(-(dd/SIG)**2); ws=np.maximum(w.sum(1),1e-9)
def sm(a):   # 3D-smoothed share around each roi vertex
    return (w*a[sub][ii]).sum(1)/ws
P=co[roi]; D=np.zeros_like(P)
ss=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
armn=sm(arm); notarm=np.clip(1-armn*1.5,0,1); notarmL=np.clip(1-armn*E('ARMKL',1.5),0,1)
X=np.abs(P[:,0]); side=np.sign(P[:,0]); side[side==0]=1
# --- traps: lower (and a little thinner) between the neck and the shoulder
tr=np.clip(sm(ind('mus_mat_traps'))*1.6,0,1)
ft=tr*ss((X-0.035)/0.03)*ss((0.20-X)/0.05)*notarm
D[:,2]-=E('K_TRAP',1.0)*0.022*ft
D[:,1]-=E('K_TRAP',1.0)*0.006*ft*(P[:,1]>0)
# --- deltoids: smaller, towards the shoulder joint (keeps the round cap)
de=np.clip(sm(ind('mus_mat_deltoid'))*1.5,0,1)
for L,s_ in (('L',1),('R',-1)):
    j=np.array(bb['upper_arm.'+L].head_local)
    m=(side==s_)
    v=j-P[m]; dist=np.linalg.norm(v,axis=1)
    f=de[m]*ss((dist-0.04)/0.05)          # keep the joint area, act on the outer muscle
    D[m]+=v*(E('K_DELT',1.0)*0.24*f)[:,None]
# --- lats: in towards the body, mostly the outer edge under the arm
la=np.clip(sm(ind('mus_mat_lats'))*1.4,0,1)
fl=la*ss((X-0.10)/0.10)*ss(1-np.abs(P[:,2]-E('LZC',1.27))/E('LZW',0.13))*notarmL
side_dir=-np.c_[side,np.zeros(len(P)),np.zeros(len(P))]
D+=side_dir*(E('K_LAT',1.0)*0.045*fl)[:,None]
# serratus / torso side just under the armpit (front of the lats): also in
fs=ss((X-0.15)/0.07)*ss(1-np.abs(P[:,2]-E('SZC',1.27))/0.10)*ss((P[:,1]+0.14)/0.06)*notarmL*(1-la)*E('K_SER',1.0)
D+=side_dir*(E('K_LAT',1.0)*0.035*fs)[:,None]
# --- pecs: less forward (keep their shape)
pe=np.clip(sm(ind('mus_mat_pectoral'))*1.4,0,1)
fp=pe*notarm*ss((-P[:,1]-0.07)/0.05)
D[:,1]+=E('K_PEC',1.0)*0.020*fp
# --- upper back: less thick (the hump in the side view)
fb=ss((P[:,1]-0.04)/0.05)*ss(1-np.abs(P[:,2]-1.33)/0.14)*ss((0.20-X)/0.06)*notarm
D[:,1]-=E('K_BACK',1.0)*0.015*fb
# --- upper arms: slimmer around the bone (biceps/triceps), fading at the shoulder and elbow
for L,s_ in (('L',1),('R',-1)):
    a=np.array(bb['upper_arm.'+L].head_local); b=np.array(bb['upper_arm.'+L].tail_local); dv=b-a
    m=(side==s_)
    t=(P[m]-a)@dv/(dv@dv); cp=a+np.clip(t,0,1)[:,None]*dv
    fa=np.clip(ua[roi][m],0,1)*ss((t-0.25)/0.2)*ss((0.95-t)/0.15)
    D[m]+=(cp-P[m])*(E('K_ARM',1.0)*0.09*fa)[:,None]
# smooth the whole displacement field in 3D (wide, so every change fades in gently and no edge shows)
SD=E('SIGD',0.04)
sub2=rng.choice(np.arange(len(roi)),min(len(roi),60000),replace=False)
t2=cKDTree(P[sub2]); d2,i2=t2.query(P,k=int(E('KD',160)))
w2=np.exp(-(d2/SD)**2); D=(w2[:,:,None]*D[sub2][i2]).sum(1)/np.maximum(w2.sum(1),1e-9)[:,None]
mv=np.linalg.norm(D,axis=1); print('verts moved',int((mv>1e-4).sum()),'max mm %.1f  mean(moved) %.1f'%(mv.max()*1000,mv[mv>1e-4].mean()*1000))
full=np.zeros_like(co); full[roi]=D
if E('POSTN',0)>0:
    # gentle Taubin smoothing of the reshaped area only (removes small crumples left by the push)
    import scipy.sparse as sp
    ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
    A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
    dg_=np.asarray(A.sum(1)).ravel(); dg_[dg_==0]=1
    mk=np.clip(np.linalg.norm(full,axis=1)/E('POSTMM',0.006),0,1)[:,None]
    Xn=co+full
    for _ in range(int(E('POSTN',0))):
        for f_ in (0.5,-0.53): Xn=Xn+mk*f_*((A@Xn)/dg_[:,None]-Xn)
    full=Xn-co
if me.shape_keys:
    for kb in me.shape_keys.key_blocks:
        k=np.zeros(nv*3); kb.data.foreach_get('co',k); kb.data.foreach_set('co',(k.reshape(-1,3)+full).ravel())
me.vertices.foreach_set('co',(co+full).ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
