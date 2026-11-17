# Upper-arm skin weight around each shoulder recomputed as a smooth "harmonic" field (like heat spreading):
# 1 on the upper arm beyond T1 of its length, 0 on the middle of the chest/back, the neck, and the torso side well
# below the armpit; solved in between (no sharp borders -> no fins/pinches). The torso bones keep their mutual
# proportions for the rest. usage: blender -b -P harmonicw.py -- in.blend out.blend
import bpy,sys,os
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices); rig=bpy.data.objects['Rig']; bb=rig.data.bones
bones={b.name for b in bb}
groups=[g for g in hi.vertex_groups if g.name in bones]; gi={g.index:k for k,g in enumerate(groups)}; names=[g.name for g in groups]
W=np.zeros((nv,len(groups)),np.float32)
for v in me.vertices:
    for g in v.groups:
        k=gi.get(g.group)
        if k is not None: W[v.index,k]=g.weight
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel()
col=lambda n: W[:,names.index(n)]
W0=W.copy()
for L in 'LR':
    a=np.array(bb['upper_arm.'+L].head_local); b=np.array(bb['upper_arm.'+L].tail_local); dv=b-a
    t=(co-a)@dv/(dv@dv); tc=np.clip(t,0,1); dseg=np.linalg.norm(co-(a+tc[:,None]*dv),axis=1)
    dj=np.linalg.norm(co-a,axis=1)
    lower=sum(col(n) for n in names if n.split('.')[0] in ('forearm','hand') and n.endswith('.'+L))
    nh=col('neck')+col('head')
    side=np.sign(a[0])
    arm1=((t>E('T1',0.45))&(dseg<E('ARMR',0.075)))|(lower>0.01)
    tor0=(((co[:,2]<a[2]-E('ZDOWN',0.14))&(dseg>E('ARMR',0.075)))|(co[:,0]*side<E('XMID',0.09))|(nh>0.3))&~arm1
    region=(dj<E('RAD',0.32))&~arm1&~tor0&(co[:,0]*side>0)
    fixed=~region
    u=np.zeros(nv); u[arm1]=1.0
    idx=np.where(region)[0]; pos=-np.ones(nv,int); pos[idx]=np.arange(len(idx))
    Lr=(sp.diags(deg)-A)[idx]
    Ain=Lr[:,idx]; rhs=-(Lr[:,np.where(fixed)[0]]@u[fixed])
    uu=sla.spsolve(Ain.tocsc(),rhs); u[idx]=np.clip(uu,0,1)
    # only change verts in the shoulder area (keep the rest of the body as it was)
    # every vertex of this side within RAD (except forearm/hand) takes the new field: no jump at the region edge
    ch=(dj<E('RAD',0.32))&(lower<0.01)&(co[:,0]*side>0)
    ku=names.index('upper_arm.'+L)
    tor=[names.index(n) for n in ('chest','spine','clavicle.'+L,'neck','hips') if n in names]
    rest=W[ch][:,tor]; s=rest.sum(1,keepdims=True)
    # if a vertex had no torso weight, give the torso part to the chest
    fb=(s[:,0]<1e-6); rest[fb,0]=1.0; s=rest.sum(1,keepdims=True)
    Wn=W[ch].copy()
    others=[k for k in range(len(names)) if k not in tor+[ku]]
    Wn[:,others]=0
    Wn[:,ku]=u[ch]; Wn[:,tor]=rest/s*(1-u[ch])[:,None]
    if E('CLAVF',0)>0:
        # collarbone acting as the shoulder blade: smooth field, 1 around the top of the shoulder, 0 at the spine,
        # the middle of the chest and below the shoulder blade
        kc=names.index('clavicle.'+L); kt=[names.index(n) for n in ('chest','spine','hips') if n in names]
        ac=np.array(bb['clavicle.'+L].tail_local)
        c1=(np.linalg.norm(co-ac,axis=1)<E('CR',0.07))|arm1
        c0=((co[:,0]*side<E('CXMID',0.04))|(co[:,2]<a[2]-E('CZDOWN',0.16))|(nh>0.3))&~c1
        reg2=(dj<E('RAD',0.32))&~c1&~c0&(co[:,0]*side>0)
        cc=np.zeros(nv); cc[c1]=1
        id2=np.where(reg2)[0]; Lr2=(sp.diags(deg)-A)[id2]
        cc[id2]=np.clip(sla.spsolve(Lr2[:,id2].tocsc(),-(Lr2[:,np.where(~reg2)[0]]@cc[~reg2])),0,1)
        cv=cc[ch]; rem=(1-u[ch])
        tr=W0[ch][:,kt]; ts=tr.sum(1,keepdims=True); tr[ts[:,0]<1e-6,0]=1; ts=tr.sum(1,keepdims=True)
        keepn=[names.index(n) for n in ('neck',) if n in names]
        Wn[:,tor]=0
        Wn[:,kc]=rem*cv
        Wn[:,kt]=tr/ts*(rem*(1-cv))[:,None]
        print(L,'collarbone field: mean on the changed verts %.2f'%cv.mean())
    W[ch]=Wn
    print(L,'region',len(idx),'changed',int(ch.sum()),'u mean %.2f'%u[idx].mean())
idx=np.where(np.abs(W-W0).max(1)>1e-6)[0]
for k,g in enumerate(groups):
    vals=W[idx,k]; z=idx[vals<=1e-5]
    if len(z): g.remove([int(i) for i in z])
    for i,w in zip(idx[vals>1e-5],vals[vals>1e-5]): g.add([int(i)],float(w),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=out)
