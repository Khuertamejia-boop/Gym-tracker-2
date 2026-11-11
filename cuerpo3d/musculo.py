# Athletic definition + a little more muscle mass on the rest body (new body), following the body's own anatomy.
#  1) DEFINITION: the mid-size relief of the professional mesh (muscle bellies and the grooves between them, ~1-5 cm)
#     is measured as a band-pass of the surface (light smoothing minus strong smoothing, both Taubin = no shrinking,
#     taken along the normal) and amplified by KDEF.
#  2) MASS: smooth normal offsets per region (deltoids, upper arms, forearms, chest, lats, traps, upper back, legs).
#  Head/neck, hands, feet and the crotch are left as they are (smooth fade). Vertex count/order unchanged, so skin
#  weights and every other attribute stay valid.   usage: python -I musculo.py in.blend out.blend   (env K*)
import bpy,sys,os
import numpy as np, scipy.sparse as sp
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
ss=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices); bb=bpy.data.objects['Rig'].data.bones
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1
Av=sp.diags(1/deg)@A
def taubin(X,n,lam=0.5,mu=-0.53):
    for _ in range(n):
        X=X+lam*(Av@X-X); X=X+mu*(Av@X-X)
    return X
def vnormals(X):
    me.vertices.foreach_set('co',X.ravel()); me.update()
    n=np.zeros(nv*3); me.vertices.foreach_get('normal',n); return n.reshape(-1,3)
# ---- masks from skin weights
gi={g.index:g.name for g in hi.vertex_groups}
def wsum(pref):
    w=np.zeros(nv)
    for v in me.vertices:
        for g in v.groups:
            if gi[g.group].startswith(pref): w[v.index]+=g.weight
    return w
FING=('thumb','index','middle','ring','pinky')
w_head=wsum(('head','neck')); w_hand=wsum(('hand',)+FING); w_foot=wsum(('foot',))
w_ua=wsum(('upper_arm','delt')); w_fa=wsum(('forearm','fa_tw')); w_th=wsum(('thigh',)); w_sh=wsum(('shin',))
def smooth_mask(m,n=30):
    for _ in range(n): m=0.5*m+0.5*(Av@m)
    return m
keep=np.clip(1-1.6*smooth_mask(w_head*1.0+w_hand*1.0+w_foot*1.0),0,1)
X0=np.abs(co[:,0]); crotch=(1-ss((X0-0.05)/0.05))*(1-ss((np.abs(co[:,2]-0.86)-0.08)/0.05))
keep*=1-crotch
# ---- 1) definition (band-pass relief, amplified)
def lapsm(X,n):
    for _ in range(n): X=0.5*X+0.5*(Av@X)
    return X
S1=lapsm(co,int(E('NS',6)))            # removes skin-pore scale detail
S2=lapsm(co,int(E('NL',150)))          # the body without its muscle relief (shrinks a bit: compensated below)
n2=vnormals(S2); me.vertices.foreach_set('co',co.ravel()); me.update()
h=((S1-S2)*n2).sum(1)
h=h-lapsm(h,int(E('NB',500)))          # remove the part that comes from the limb/torso curvature (scalar: no shrinking)
h=np.clip(h,-E('HMAX',0.012),E('HMAX',0.012))
shorts=np.zeros(nv,np.float32)
if 'shorts' in me.attributes: me.attributes['shorts'].data.foreach_get('value',shorts)
shk=1-E('SHORTK',0.7)*smooth_mask(shorts.astype(float),10)       # fabric: less relief under the shorts
spine=1-E('SPINEK',0.5)*(1-ss((X0-0.012)/0.03))*(co[:,1]>0.0)     # do not dig the spine groove too much
cleft=(1-ss((X0-0.025)/0.045))*ss((co[:,1]-0.0)/0.03)*(1-ss((np.abs(co[:,2]-0.88)-0.12)/0.05))
dfn=E('KDEF',0.6)*h*keep*shk*spine*(1-cleft)
# ---- 2) mass (normal offsets, smooth masks)
n0=vnormals(co)
def gauss(c,sig): return np.exp(-np.sum((co-np.array(c))**2,1)/(2*sig*sig))
mass=np.zeros(nv)
for s in (1,-1):
    sd=lambda v: (s*v[0],v[1],v[2])
    side=(co[:,0]*s>0)
    sh=np.array(bb['upper_arm.L' if s>0 else 'upper_arm.R'].head_local)
    mass+=E('KDELT',0.007)*gauss(sh+np.array((s*0.035,0.0,-0.02)),0.045)*side            # deltoid cap
    mass+=E('KPEC',0.004)*gauss(sd((0.085,-0.10,1.27)),0.055)*side*(co[:,1]<-0.02)        # pectoral
    mass+=E('KLAT',0.005)*gauss(sd((0.135,0.04,1.17)),0.06)*side                          # lats (V shape)
    mass+=E('KTRAP',0.003)*gauss(sd((0.08,0.03,1.42)),0.045)*side                         # upper traps
    mass+=E('KBACK',0.003)*gauss(sd((0.07,0.10,1.27)),0.06)*side                          # upper back
# upper arms (biceps/triceps), forearms (upper part), thighs, calves: along their bones
def along(bn,t0,t1):
    a=np.array(bb[bn].head_local); b=np.array(bb[bn].tail_local); d=b-a; t=(co-a)@d/(d@d)
    return ss((t-t0)/0.15)*(1-ss((t-t1)/0.15))
armm=np.zeros(nv); legm=np.zeros(nv)
for L in 'LR':
    armm+=E('KUA',0.004)*along('upper_arm.'+L,0.15,0.85)*np.clip(w_ua,0,1)
    armm+=E('KFA',0.002)*along('forearm.'+L,0.0,0.55)*np.clip(w_fa,0,1)
    legm+=E('KTH',0.003)*along('thigh.'+L,0.2,0.85)*np.clip(w_th,0,1)
    legm+=E('KCALF',0.003)*along('shin.'+L,0.1,0.45)*np.clip(w_sh,0,1)*(co[:,1]>np.array(bb['shin.'+L].head_local)[1]-0.01)
mass=mass+armm+legm
mass=smooth_mask(mass,20)*keep
D=(dfn+mass)
D=smooth_mask(D,int(E('DSM',3)))
new=co+n0*D[:,None]
me.vertices.foreach_set('co',new.ravel()); me.update()
print('definition mm: p5 %.1f p95 %.1f max %.1f | mass mm max %.1f'%(np.percentile(dfn,5)*1000,np.percentile(dfn,95)*1000,np.abs(dfn).max()*1000,mass.max()*1000))
bpy.ops.wm.save_as_mainfile(filepath=out)
