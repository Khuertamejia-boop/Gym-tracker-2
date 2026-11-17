# Arm proportions: the model had a short, very thick upper arm (25 cm, ~48 cm girth) and a long forearm (30 cm).
# One continuous map along the arm's centre line (shoulder -> elbow -> wrist): the elbow slides DU down the upper
# arm's line (upper arm longer, forearm shorter, wrist and hand fixed) and the thickness follows a smooth profile
# (1 at the shoulder, KU mid upper arm, KE elbow, KF forearm belly, 1 at the wrist). No band at the elbow.
# Moves the elbow bones too. Applies to every shape key.
# usage: blender -b -P armfix.py -- in.blend out.blend   env DU (m), KU, KE, KF
import bpy,sys,os
import numpy as np
from scipy.spatial import cKDTree
from mathutils import Vector
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices); rig=bpy.data.objects['Rig']; bb=rig.data.bones
co=np.zeros(nv*3)
if me.shape_keys: me.shape_keys.key_blocks['Basis'].data.foreach_get('co',co)
else: me.vertices.foreach_get('co',co)
co=co.reshape(-1,3)
gi={g.index:g.name for g in hi.vertex_groups}
W={}
for v in me.vertices:
    for g in v.groups:
        n=gi.get(g.group,'')
        if n.startswith(('upper_arm','forearm','delt','hand')): W.setdefault(n,np.zeros(nv))[v.index]=g.weight
D=np.zeros_like(co); newelbow={}
DU=E('DU',0.04)
for L in 'LR':
    a=np.array(bb['upper_arm.'+L].head_local); b=np.array(bb['upper_arm.'+L].tail_local); c=np.array(bb['forearm.'+L].tail_local)
    uu=(b-a)/np.linalg.norm(b-a); lu=np.linalg.norm(b-a); uf=(c-b)/np.linalg.norm(c-b); lf=np.linalg.norm(c-b)
    newelbow[L]=b+uu*DU
    z=np.zeros(nv)
    wu=W.get('upper_arm.'+L,z)+0.5*W.get('delt.'+L,z); wf=W.get('forearm.'+L,z); wh=W.get('hand.'+L,z)
    side=np.sign(a[0])
    # centre line from slice centres (the bones are not always in the middle of the arm)
    pts=[]
    for (o,u,l,w) in ((a,uu,lu,wu),(b,uf,lf,wf)):
        q=co-o; t=(q@u)/l
        for t0 in np.arange(0.0 if o is b else 0.15,1.0001,0.05):
            m=(np.abs(t-t0)<0.025)&(w>0.8)&(co[:,0]*side>0)
            if m.sum()>30: pts.append(co[m].mean(0))
            else: pts.append(o+u*l*t0)
    pts=np.array([a]+pts+[c]) if False else np.array(pts)
    # start the line at the joint itself, end at the wrist; smooth it (rounds the elbow corner a little)
    pts=np.vstack([a,pts,c])
    for _ in range(10): pts[1:-1]=0.25*pts[:-2]+0.5*pts[1:-1]+0.25*pts[2:]
    seg=np.linalg.norm(np.diff(pts,axis=0),axis=1); sc=np.r_[0,np.cumsum(seg)]
    S=np.arange(0,sc[-1],0.002); C=np.column_stack([np.interp(S,sc,pts[:,k]) for k in range(3)])
    se=S[np.argmin(np.linalg.norm(C-b,axis=1))]; sw=S[-1]
    # thickness profile along the line
    sk=[0, 0.25*se, 0.5*se, 0.8*se, se, se+0.3*(sw-se), se+0.6*(sw-se), sw-0.02, sw]
    kk=[1, 1-(1-E('KU',0.80))*0.4, E('KU',0.80), E('KU',0.80), E('KE',0.86), E('KF',0.88), E('KF',0.88), 1.0, 1.0]
    m=((wu+wf)>1e-4)&(co[:,0]*side>0)
    idx=np.where(m)[0]
    tr=cKDTree(C); d,j=tr.query(co[idx])
    s=S[j]; q=C[j]; r=co[idx]-q
    k=np.interp(s,sk,kk)
    h=np.where(s<=se,s/se,1-(s-se)/(sw-se)); h=np.clip(h,0,1)
    w=np.clip(wu[idx]+wf[idx],0,1)*np.clip(1-wh[idx]*2,0,1)
    D[idx]+=w[:,None]*(DU*uu[None,:]*h[:,None]+r*(k-1)[:,None])
    print(L,'centre line %.1f cm (elbow at %.1f), verts %d'%(sw*100,se*100,len(idx)))
if E('ELSM',0)>0:
    # soften the elbow crease ring (Taubin: no shrinking), only around the elbow
    import scipy.sparse as sp
    ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
    A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
    dg_=np.asarray(A.sum(1)).ravel(); dg_[dg_==0]=1
    X=co+D
    dd=np.min([np.linalg.norm(X-newelbow[L],axis=1) for L in 'LR'],axis=0)
    mk=np.clip((E('ELR',0.06)-dd)/0.03,0,1); mk=(mk*mk*(3-2*mk))[:,None]
    for _ in range(int(E('ELSM',0))):
        for f_ in (0.5,-0.53): X=X+mk*f_*((A@X)/dg_[:,None]-X)
    D=X-co
mv=np.linalg.norm(D,axis=1); print('verts moved',int((mv>1e-4).sum()),'max mm %.1f'%(mv.max()*1000))
if me.shape_keys:
    for kb in me.shape_keys.key_blocks:
        kk_=np.zeros(nv*3); kb.data.foreach_get('co',kk_); kb.data.foreach_set('co',(kk_.reshape(-1,3)+D).ravel())
me.vertices.foreach_set('co',(co+D).ravel()); me.update()
bpy.context.view_layer.objects.active=rig
for o in bpy.context.view_layer.objects: o.select_set(o==rig)
bpy.ops.object.mode_set(mode='EDIT'); eb=rig.data.edit_bones
for L,b2 in newelbow.items():
    r1=eb['upper_arm.'+L].roll; eb['upper_arm.'+L].tail=Vector(b2); eb['upper_arm.'+L].roll=r1
    r2=eb['forearm.'+L].roll; eb['forearm.'+L].head=Vector(b2); eb['forearm.'+L].roll=r2
bpy.ops.object.mode_set(mode='OBJECT')
for L in 'LR': print(L,'upper arm %.1f cm, forearm %.1f cm'%(rig.data.bones['upper_arm.'+L].length*100,rig.data.bones['forearm.'+L].length*100))
bpy.ops.wm.save_as_mainfile(filepath=out)
