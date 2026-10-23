# Put the finger bones where the fingers really are (the original rig had them along the knuckle line).
# For each hand: cut the palm away, the mesh falls apart into 5 digits, fit a centre line to each digit and place 3 bones on it.
# usage: blender -b -P fingerfit.py -- in.blend out.blend
import bpy,sys,os,math
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from mathutils import Vector
E=lambda k,d: float(os.environ.get(k,d))
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
Ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',Ed); Ed=Ed.reshape(-1,2)
bones=rig.data.bones
plan={}
for L in 'LR':
    s=1 if L=='L' else -1
    W=np.array(bones['hand.'+L].head_local); F=np.array(bones['forearm.'+L].head_local); ax=(W-F)/np.linalg.norm(W-F)
    al=(co-W)@ax; m=(al>0.0)&(np.linalg.norm(co-W,axis=1)<0.25)&(co[:,0]*s>0.05)
    idx=np.where(m)[0]; P=co[idx]; c=P.mean(0)
    U,S_,Vt=np.linalg.svd(P-c,full_matrices=False)
    e0=Vt[0]*np.sign(Vt[0]@ax)          # along the hand, towards the finger tips
    e2=Vt[2]; e1=np.cross(e2,e0)
    u=(P-W)@e0; l=(P-W)@e1
    # palm centre: around the middle of the palm
    pc=np.array([np.percentile(u,25),np.median(l)])
    d=np.hypot(u-pc[0],l-pc[1])
    # digits = far from the palm centre; cut radius from the inter-finger webs: take a value that splits the mesh into 5 big parts
    best=None
    for R in np.arange(0.050,0.095,0.0025):
        keep=d>R; sel=idx[keep]
        if len(sel)<100: continue
        inr=np.zeros(nv,bool); inr[sel]=True; mm=inr[Ed[:,0]]&inr[Ed[:,1]]; Ee=Ed[mm]
        loc=-np.ones(nv,int); loc[sel]=np.arange(len(sel))
        A=coo_matrix((np.ones(len(Ee)),(loc[Ee[:,0]],loc[Ee[:,1]])),shape=(len(sel),len(sel)))
        nc,lab=connected_components(A,directed=False); cnt=np.bincount(lab)
        big=np.sort(cnt)[::-1]
        if len(big)>=5 and big[4]>800:
            if best is None or big[4]>best[0]: best=(big[4],R,sel,lab,cnt)
    _,R,sel,lab,cnt=best
    comps=np.argsort(cnt)[::-1][:5]
    print(L,'cut radius',round(R,4),'digit sizes',cnt[comps])
    digits=[]
    for cpi in comps:
        Q=co[sel[lab==cpi]]; qc=Q.mean(0)
        # order digits by their angle around the palm centre in the (u,l) plane
        uu=(qc-W)@e0; ll=(qc-W)@e1
        digits.append((math.atan2(ll-pc[1],uu-pc[0]),Q))
    digits.sort(key=lambda t:t[0])
    # the thumb is the digit whose direction is most different from the others' mean
    dirs=[]
    for ang,Q in digits:
        q0=Q.mean(0); _,_,vt=np.linalg.svd(Q-q0,full_matrices=False); dv=vt[0]
        if dv@((q0-W))<0: dv=-dv
        dirs.append(dv)
    mean=np.mean(dirs,0); dev=[math.degrees(math.acos(np.clip(dv@mean/np.linalg.norm(mean),-1,1))) for dv in dirs]
    th=int(np.argmax(dev))
    order=[i for i in range(5) if i!=th]
    # index is the finger next to the thumb
    if abs(order[0]-th)>abs(order[-1]-th): order=order[::-1]
    names=['index','middle','ring','pinky']
    fit={}
    for nm,i in zip(['thumb']+names,[th]+order):
        Q=digits[i][1]; dv=dirs[i]; q0=Q.mean(0)
        t=(Q-q0)@dv; t0,t1=t.min(),t.max()
        # centre line: centroids of slices
        ts=np.linspace(t0+0.003,t1-0.002,12); C=[]
        for tt in ts:
            mm=np.abs(t-tt)<0.003
            C.append(Q[mm].mean(0) if mm.sum()>5 else q0+dv*tt)
        C=np.array(C)
        base=C[0]; tip=q0+dv*t1
        dirb=(C[2]-C[0]); dirb/=np.linalg.norm(dirb)
        if nm=='thumb':
            j0=base-dirb*E('TMB',0.035)          # thumb metacarpal starts deep in the palm
        else:
            j0=base-dirb*E('MCPD',0.016)         # the knuckle (MCP) is under the web
        Ltot=np.linalg.norm(tip-j0)
        fr=[0.0,0.40,0.70,0.97] if nm=='thumb' else [0.0,0.45,0.73,0.97]
        # joint points: walk along the centre line (polyline j0 -> C -> tip)
        poly=np.vstack([j0,C,tip]); seg=np.linalg.norm(np.diff(poly,axis=0),axis=1); cum=np.r_[0,np.cumsum(seg)]
        J=[np.array([np.interp(f*cum[-1],cum,poly[:,k]) for k in range(3)]) for f in fr]
        fit[nm]=J
        print('  ',nm,'length',round(cum[-1],3))
    plan[L]=(fit,e2)
# ---- edit the armature
bpy.context.view_layer.objects.active=rig
for o in bpy.context.view_layer.objects: o.select_set(o==rig)
bpy.ops.object.mode_set(mode='EDIT')
eb=rig.data.edit_bones
for L,(fit,nrm) in plan.items():
    for nm,J in fit.items():
        for k in (1,2,3):
            b=eb[f'{nm}{k}.{L}']; b.use_connect=False
            b.head=Vector(J[k-1]); b.tail=Vector(J[k])
            b.align_roll(Vector(nrm))
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=out)
print('saved',out)
