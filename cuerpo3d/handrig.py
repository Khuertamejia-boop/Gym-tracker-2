# Re-skin the body's own anatomical hand and close it around a bar.
#  reweight(): new, clean skin weights for the hand and every phalanx (nearest bone, then smoothed along the surface)
#  curl():     every phalanx bends about the knuckle line (the axis of the bar), whatever the bone roll is
import bpy,math,os
import numpy as np
import scipy.sparse as sp0
from mathutils import Vector,Quaternion,Matrix
E=lambda k,d: float(os.environ.get(k,d))
FING=('index','middle','ring','pinky','thumb')

def seg_dist(P,a,b):
    d=b-a; L=np.linalg.norm(d); u=d/L; t=np.clip((P-a)@u,0,L); return np.linalg.norm(P-(a+np.outer(t,u)),axis=1)

def reweight(hi,rig,L,co=None):
    me=hi.data; nv=len(me.vertices)
    if co is None:
        co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    bones=rig.data.bones
    W=np.array(bones['hand.'+L].head_local); F=np.array(bones['forearm.'+L].head_local)
    ax=(W-F)/np.linalg.norm(W-F); al=(co-W)@ax
    s=1 if L=='L' else -1
    near=np.linalg.norm(co-W,axis=1)<0.25
    reg=np.where(near&(al>-E('WR0',0.03)-0.005)&(co[:,0]*s>0.05))[0]
    if E('ARMONLY',1)>0:   # only skin that already belongs to the arm (the hips can be near the hand at rest)
        armg={g.index for g in hi.vertex_groups if g.name.endswith('.'+L) and (g.name.split('.')[0] in ('forearm','hand','upper_arm') or g.name[:-3] in FING)}
        aw=np.zeros(nv)
        for i in reg:
            aw[i]=sum(x.weight for x in me.vertices[int(i)].groups if x.group in armg)
        reg=reg[aw[reg]>0.5]
    names=['forearm.'+L,'hand.'+L]+[f'{f}{k}.{L}' for f in FING for k in (1,2,3)]
    segs=[]
    for n in names:
        a=np.array(bones[n].head_local); b=np.array(bones[n].tail_local)
        if n[-3]=='3' and not n.startswith('hand'):          # distal phalanx: reach the fingertip
            b=b+(b-a)/np.linalg.norm(b-a)*E('TIPX',0.018)
        if n.startswith('forearm'): a=a+(b-a)*0.5
        if n.startswith('hand'):                               # the palm ends at the knuckles (the bone itself reaches into the fingers)
            b=np.mean([np.array(bones[f'{f}1.{L}'].head_local) for f in ('index','middle','ring','pinky')],0)
        segs.append((a,b))
    P=co[reg]
    D=np.stack([seg_dist(P,a,b) for a,b in segs],1)
    D[:,1]*=E('HANDK',0.85)                                   # the palm keeps the hand bone
    # a phalanx only takes skin in front of its own joint (no palm behind the knuckle)
    for j,n in enumerate(names):
        if n.startswith(('forearm','hand')): continue
        a,bb=segs[j]; u=(bb-a)/np.linalg.norm(bb-a); t=(P-a)@u
        lim=-E('BACK1',0.004) if n[-3]=='1' else -E('BACKJ',0.010)
        D[t<lim,j]=1e9
    nearest=D.argmin(1)
    Wm=np.zeros((len(reg),len(names))); Wm[np.arange(len(reg)),nearest]=1.0
    # forearm side of the wrist keeps the forearm
    # smooth along the surface (joints blend, fingers do not bleed into each other: they only touch through the web)
    Ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',Ed); Ed=Ed.reshape(-1,2)
    inr=np.zeros(nv,bool); inr[reg]=True; m=inr[Ed[:,0]]&inr[Ed[:,1]]; Ee=Ed[m]
    loc=-np.ones(nv,int); loc[reg]=np.arange(len(reg)); i0=loc[Ee[:,0]]; i1=loc[Ee[:,1]]
    A=sp0.coo_matrix((np.ones(2*len(i0)),(np.r_[i0,i1],np.r_[i1,i0])),shape=(len(reg),len(reg))).tocsr()
    Av=sp0.diags(1/np.maximum(np.asarray(A.sum(1)).ravel(),1))@A
    for _ in range(int(E('WSM',12))): Wm=0.5*Wm+0.5*(Av@Wm)
    Wm/=np.maximum(Wm.sum(1,keepdims=True),1e-9)
    # soft wrist: forearm -> hand over a few centimetres (no step at the wrist)
    t=np.clip((al[reg]+E('WR0',0.03))/E('WRL',0.05),0,1); wf=1-t*t*(3-2*t)
    one=np.zeros(len(names)); one[0]=1.0
    Wm=Wm*(1-wf[:,None])+one[None,:]*wf[:,None]
    # replace the weights of every arm/hand group on these vertices
    regl=reg.tolist()
    allg=[g for g in hi.vertex_groups if g.name.endswith('.'+L) and (g.name.split('.')[0] in ('forearm','hand','upper_arm') or g.name[:-3] in FING)]
    for g in allg: g.remove(regl)
    for j,n in enumerate(names):
        g=hi.vertex_groups[n]; w=Wm[:,j]
        q=np.round(w*40)/40
        for lv in np.unique(q):
            if lv<=0: continue
            g.add(reg[q==lv].tolist(),float(lv),'REPLACE')
    print('reweighted',L,len(reg),'verts')
    return reg

def curl(rig,L,A=(75,70,55),TA=(15,25,30),axis=None,sc=(1.0,1.0,1.0,1.0)):
    bpy.context.view_layer.update()
    pb=rig.pose.bones
    if axis is None:
        axis=(Vector(pb['index1.'+L].head)-Vector(pb['pinky1.'+L].head)).normalized()
    sgn=1.0 if L=='L' else -1.0
    hp=pb['hand.'+L].matrix.copy(); pts=[]
    for fi,f in enumerate(FING):
        par=hp; prest=rig.data.bones['hand.'+L].matrix_local
        ang=TA if f=='thumb' else A; k_=1.0 if f=='thumb' else sc[fi]
        for k in (1,2,3):
            bn=rig.data.bones[f'{f}{k}.{L}']; p=pb[f'{f}{k}.{L}']
            M=par@(prest.inverted()@bn.matrix_local); ax_=M.to_3x3().inverted()@axis
            q=Quaternion(ax_.normalized(),math.radians(sgn*E('CSG',1.0)*ang[k-1]*k_)); p.rotation_mode='QUATERNION'; p.rotation_quaternion=q
            par=M@q.to_matrix().to_4x4(); prest=bn.matrix_local
            if f in ('index','middle','ring') and k>=2: pts.append(par.translation.copy())
            if f in ('index','middle','ring') and k==3: pts.append(par@Vector((0,bn.length,0)))
    bpy.context.view_layer.update()
    return axis,sum(pts,Vector())/len(pts)

def place_bar(centre,axis,radius=0.0145,hide_discs=True):
    o=bpy.data.objects['Barra']; me=o.data; C0=Vector((0,-0.2962,0.9366))
    k_=radius/0.0125   # the original bar: shaft radius 12.5 mm (the 25 mm parts are the sleeves)
    uni=os.environ.get('BARUNI','0')=='1'   # 1 = pull-up bar: one even thickness (no barbell sleeves)
    for v in me.vertices:
        r0=math.hypot(v.co.y-C0.y,v.co.z-C0.z); k=(radius/r0 if (uni and r0>1e-6) else k_)
        v.co.y=C0.y+(v.co.y-C0.y)*k; v.co.z=C0.z+(v.co.z-C0.z)*k
    me.update()
    R=Vector((1,0,0)).rotation_difference(axis).to_matrix().to_4x4()
    M=Matrix.Translation(centre)@R@Matrix.Translation(-C0)
    for n in ('Barra','Discos'):
        ob=bpy.data.objects[n]; ob.parent=None; ob.matrix_world=M; ob.hide_render=(n=='Discos' and hide_discs)

def curl_local(rig,L,A=(70,80,55),TA=(0,20,25),sgnR=-1.0,ax=(1,0,0)):
    # each phalanx bends about its own local X axis (the bone roll was aligned to the palm normal, so X is the flexion axis)
    sg=E('CSG',1.0)*(1.0 if L=='L' else sgnR)
    for f in FING:
        ang=TA if f=='thumb' else A
        for k in (1,2,3):
            p=rig.pose.bones[f'{f}{k}.{L}']; p.rotation_mode='QUATERNION'
            p.rotation_quaternion=Quaternion(Vector(ax),math.radians(sg*ang[k-1]))
    bpy.context.view_layer.update()
    pb=rig.pose.bones; pts=[]
    for f in ('index','middle','ring'):
        for k in (2,3): pts.append(Vector(pb[f'{f}{k}.{L}'].head))
        pts.append(Vector(pb[f'{f}3.{L}'].tail))
    axis=(Vector(pb['index1.'+L].head)-Vector(pb['pinky1.'+L].head)).normalized()
    return axis,sum(pts,Vector())/len(pts)

def fist(rig,L,A=(70,80,55),TA=(0,25,30),sgnR=-1.0):
    # fingers: first brought together (parallel to the middle finger, rotation about the palm normal = local Z), then flexed about local X
    sg=E('CSG',1.0)*(1.0 if L=='L' else sgnR)
    bones=rig.data.bones
    def dirv(n): b=bones[n]; d=Vector(b.tail_local)-Vector(b.head_local); return d.normalized()
    nrm=Vector(bones['middle1.'+L].z_axis) if hasattr(bones['middle1.'+L],'z_axis') else None
    nrm=(bones['middle1.'+L].matrix_local.to_3x3()@Vector((0,0,1))).normalized()
    dm=dirv('middle1.'+L); dm=(dm-nrm*(dm@nrm)).normalized()
    for f in ('index','middle','ring','pinky','thumb'):
        ang=TA if f=='thumb' else A
        for k in (1,2,3):
            p=rig.pose.bones[f'{f}{k}.{L}']; p.rotation_mode='QUATERNION'
            qf=Quaternion(Vector((1,0,0)),math.radians(sg*ang[k-1]))
            if k==1 and f!='thumb':
                df=dirv(f'{f}1.{L}'); df=(df-nrm*(df@nrm)).normalized()
                a=math.atan2(df.cross(dm)@nrm, df@dm)*E('ADD',0.9)
                # rotation about the palm normal, expressed in the bone's rest frame
                Rl=bones[f'{f}1.{L}'].matrix_local.to_3x3()
                axl=(Rl.inverted()@nrm).normalized()
                p.rotation_quaternion=Quaternion(axl,a)@qf
            elif k==1:
                Rl=bones[f'thumb1.{L}'].matrix_local.to_3x3(); axl=(Rl.inverted()@nrm).normalized()
                p.rotation_quaternion=Quaternion(axl,math.radians(sg*E('TOPP',35)))@Quaternion(Vector((0,1,0)),math.radians(sg*E('TROLL',0)))@qf
            else:
                p.rotation_quaternion=qf
    bpy.context.view_layer.update()
    pb=rig.pose.bones; pts=[]
    for f in ('index','middle','ring'):
        for k in (2,3): pts.append(Vector(pb[f'{f}{k}.{L}'].head))
        pts.append(Vector(pb[f'{f}3.{L}'].tail))
    axis=(Vector(pb['index1.'+L].head)-Vector(pb['pinky1.'+L].head)).normalized()
    return axis,sum(pts,Vector())/len(pts)

# ---------------------------------------------------------------------------------------------
# Contact grip: every finger is laid on the bar surface, in a plane perpendicular to the bar,
# next to its neighbour. Joint positions are found analytically (circle walk), then the bones are aimed at them.
def aim_bone(rig,bn,target):
    pb=rig.pose.bones[bn]; b=rig.data.bones[bn]
    bpy.context.view_layer.update()
    cur=(pb.tail-pb.head).normalized(); tv=Vector(target).normalized()
    R=cur.rotation_difference(tv).to_matrix()
    M=pb.matrix.to_3x3(); newM=R@M
    par=pb.parent.matrix.to_3x3() if pb.parent else Matrix.Identity(3)
    rest=b.matrix_local.to_3x3(); prest=b.parent.matrix_local.to_3x3() if b.parent else Matrix.Identity(3)
    local=(prest.inverted()@rest).inverted()@par.inverted()@newM
    pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=local.to_quaternion()

def reset_fingers(rig,L):
    for f in FING:
        for k in (1,2,3):
            p=rig.pose.bones[f'{f}{k}.{L}']; p.rotation_mode='QUATERNION'; p.rotation_quaternion=(1,0,0,0)
    bpy.context.view_layer.update()

def palm_frame(rig,L):
    """MCP centres, knuckle axis (pinky->index), palm normal (towards the palm side), hand direction (towards the fingers)"""
    bpy.context.view_layer.update()
    pb=rig.pose.bones; mw=rig.matrix_world
    M={f:mw@Vector(pb[f'{f}1.{L}'].head) for f in ('index','middle','ring','pinky')}
    kn=(M['index']-M['pinky']).normalized()
    z=(mw.to_3x3()@pb['middle1.'+L].matrix.to_3x3()@Vector((0,0,1))).normalized()
    n=-z*E('PSG',1.0)          # palm side = bone -Z on both hands (thumb and the thick palm skin are there; +Z is the bony back)
    eh=((sum(M.values(),Vector())/4)-mw@Vector(pb['hand.'+L].head)).normalized()
    eh=(eh-kn*(eh@kn)).normalized(); n=(n-kn*(n@kn)-eh*(n@eh)).normalized()
    return M,kn,n,eh

def bar_from_hand(rig,L,rB):
    """where the bar centre sits in this hand: against the palm, just under the knuckles"""
    M,kn,n,eh=palm_frame(rig,L)
    Mm=sum(M.values(),Vector())/4
    return Mm+n*(rB+E('DN',0.0165))+eh*E('DS',-0.006)

def wrap(rig,L,B,axis,rB):
    """B: a point on the bar axis, axis: bar direction (world). Lay the four fingers on the bar and close the thumb over them."""
    mw=rig.matrix_world; mwi=mw.inverted(); axis=Vector(axis).normalized()
    reset_fingers(rig,L)
    M,kn,n,eh=palm_frame(rig,L)
    rc=rB+E('FT',0.0098)
    pb=rig.pose.bones; info={}
    for f in ('index','middle','ring','pinky'):
        Mf=M[f]; Bf=Vector(B)+axis*((Mf-Vector(B))@axis)
        ea=(Mf-Bf); dM=ea.length; ea.normalize(); eb=axis.cross(ea)
        sg=1.0 if eh@eb>0 else -1.0
        ls=[rig.data.bones[f'{f}{k}.{L}'].length for k in (1,2,3)]
        ls[2]*=E('TIPK',1.0)
        c1=(rc*rc+dM*dM-ls[0]**2)/(2*rc*dM); th=math.acos(max(-1.0,min(1.0,c1)))
        ths=[th]
        for l in ls[1:]: th+=2*math.asin(min(1.0,l/(2*rc))); ths.append(th)
        P=[Bf+rc*(math.cos(t)*ea+sg*math.sin(t)*eb) for t in ths]
        J=[Mf]+P
        for k in (1,2,3):
            aim_bone(rig,f'{f}{k}.{L}',mwi.to_3x3()@(J[k]-J[k-1]))
        info[f]=(Bf,ea,eb,sg,ths)
    # thumb: from its base around the wrist side of the bar, tip resting on the index/middle middle phalanx
    Bi,ea,eb,sg,ths=info['index']
    tgt_ang=ths[1]+E('TANG',-0.35)                       # a bit before the index DIP
    rt=rc+E('TOUT',0.0185)
    Bt=Bi+axis*(((info['middle'][0]-Bi)@axis)*E('TX',0.45))
    T=Bt+rt*(math.cos(tgt_ang)*ea+sg*math.sin(tgt_ang)*eb)
    names=[f'thumb{k}.{L}' for k in (1,2,3)]
    J=[mw@Vector(pb[n_].head) for n_ in names]+[mw@Vector(pb[names[-1]].tail)]
    ls=[(J[i+1]-J[i]).length for i in range(3)]
    # FABRIK, joints kept outside the bar + finger layer
    def push(p,rmin):
        q=Vector(B)+axis*((p-Vector(B))@axis); d=p-q
        return q+d.normalized()*rmin if d.length<rmin else p
    base=J[0].copy()
    for _ in range(40):
        J[3]=T.copy()
        for i in (2,1,0):
            J[i]=J[i+1]+(J[i]-J[i+1]).normalized()*ls[i]; J[i]=push(J[i],rB+E('TCLR',0.012))
        J[0]=base.copy()
        for i in (0,1,2):
            J[i+1]=J[i]+(J[i+1]-J[i]).normalized()*ls[i]
            if i<2: J[i+1]=push(J[i+1],rB+E('TCLR',0.012))
    for k in range(3): aim_bone(rig,names[k],mwi.to_3x3()@(J[k+1]-J[k]))
    bpy.context.view_layer.update()
    return info,(J[3]-T).length

# ---------------------------------------------------------------------------------------------
# Contact grip v2: every phalanx is TANGENT to the bar (touches it without going in), joints lie outside.
# Phalanx thickness measured on the mesh (palm side), fingers packed side by side along the bar.
import json
_RAD=None
def radii():
    global _RAD
    if _RAD is None:
        p=os.environ.get('FRADII') or os.path.join(os.path.dirname(os.path.abspath(__file__)),'finger_radii.json')
        _RAD=json.load(open(p))
    return _RAD

def _seg_d(p,q):
    d=q-p; t=max(0.0,min(1.0,-(p@d)/max(d@d,1e-12))); return np.linalg.norm(p+t*d)

def solve_finger(dM,ls,rcs,a0=None,wrap_deg=0.0):
    from scipy.optimize import least_squares
    M=np.array([dM,0.0])
    def joints(x):
        a1,q2,q3=x; a=[a1,a1+q2,a1+q2+q3]; J=[M]
        for l,ak in zip(ls,a): J.append(J[-1]+l*np.array([math.cos(ak),math.sin(ak)]))
        return J
    def res(x):
        J=joints(x); r=[]
        for k in range(3):
            d=_seg_d(J[k],J[k+1]); r.append((d-rcs[k])*(4.0 if d<rcs[k] else 1.0))
        r.append(0.02*(x[1]-x[2])*0.2)          # keep PIP and DIP flexion similar
        if wrap_deg:
            tp=J[3]; ang=math.atan2(tp[1],tp[0])%(2*math.pi)
            r.append(E('WRAPW',0.02)*(ang-math.radians(wrap_deg)))
        return r
    x0=[math.radians(100),math.radians(80),math.radians(60)] if a0 is None else a0
    sol=least_squares(res,x0,bounds=([math.radians(10),0.0,0.0],[math.radians(200),math.radians(E('PIPMAX',120)),math.radians(E('DIPMAX',95))]))
    return joints(sol.x),sol.x

def wrap2(rig,L,B,axis,rB):
    mw=rig.matrix_world; mwi=mw.inverted(); axis=Vector(axis).normalized(); B=Vector(B)
    reset_fingers(rig,L)
    M,kn,n,eh=palm_frame(rig,L)
    R=radii(); pb=rig.pose.bones
    fing=('index','middle','ring','pinky')
    # side-by-side packing along the bar (from the middle finger outwards), PIP level
    ax0={f:(M[f]-B)@axis for f in fing}
    r2={f:R[f'{f}2.L'][0] for f in fing}
    tgt={'middle':ax0['middle']}
    sgn=1.0 if ax0['index']>ax0['middle'] else -1.0
    tgt['index']=tgt['middle']+sgn*(r2['middle']+r2['index'])*E('PACK',1.0)
    tgt['ring']=tgt['middle']-sgn*(r2['middle']+r2['ring'])*E('PACK',1.0)
    tgt['pinky']=tgt['ring']-sgn*(r2['ring']+r2['pinky'])*E('PACK',1.0)
    info={}
    for f in fing:
        Mf=M[f]; Bf=B+axis*((Mf-B)@axis)
        ea=(Mf-Bf); dM=ea.length; ea.normalize(); eb=axis.cross(ea)
        sg=1.0 if eh@eb>0 else -1.0
        ls=[rig.data.bones[f'{f}{k}.{L}'].length for k in (1,2,3)]
        rcs=[rB+R[f'{f}{k}.L'][1]+E('CLR',0.0008)+(E('CLR3',0.0) if k==3 else 0.0)+(E('CLRP',0.0) if f=='pinky' else 0.0) for k in (1,2,3)]
        J2,x=solve_finger(dM,ls,rcs,wrap_deg=E('WRAP',250)*(E('WRAPP',0.93) if f=='pinky' else 1.0))
        J=[Bf+float(p[0])*ea+sg*float(p[1])*eb for p in J2]
        # bring the finger next to its neighbour: shift PIP, DIP, tip along the bar
        sh=tgt[f]-ax0[f]
        for k in (1,2,3): J[k]=J[k]+axis*(sh*(1.0 if k>=1 else 0.0))
        if f!='middle':      # finger tips taper: close the last few millimetres towards the middle finger
            tp=E('TIPPACK',0.0025)*(1 if tgt[f]<tgt['middle'] else -1)*(1 if f!='pinky' else 1.4)
            J[3]=J[3]+axis*tp; J[2]=J[2]+axis*tp*0.5
        for k in (1,2,3): aim_bone(rig,f'{f}{k}.{L}',mwi.to_3x3()@(J[k]-J[k-1]))
        info[f]=(Bf,ea,eb,sg,x,[math.degrees(v) for v in x])
    # thumb: under the bar (the side the fingers leave free) to the front, resting on the index / middle finger tips
    bpy.context.view_layer.update()
    def polar(p):
        q=B+axis*((p-B)@axis); return q,(p-q)
    def sangle(a,b):   # signed angle a->b about the bar axis
        return math.atan2(a.cross(b)@axis, a@b)
    tipI=mw@Vector(pb['index3.'+L].tail); tipM=mw@Vector(pb['middle3.'+L].tail)
    tip=tipI*(1-E('TX',0.35))+tipM*E('TX',0.35)
    q0,vt=polar(tip); _,vm=polar(M['index']); _,vp=polar(mw@Vector(pb['index2.'+L].head))
    a_tm=sangle(vt,vm)
    # the arc tip->MCP that does not contain the PIP is the free side
    a_tp=sangle(vt,vp)
    if (a_tm>0)==(a_tp>0) and abs(a_tp)<abs(a_tm): a_tm=a_tm-math.copysign(2*math.pi,a_tm)
    rot=lambda v,a: Matrix.Rotation(a,3,axis)@v
    rt=vt.length+R['index3.L'][1]*0.6+R['thumb3.L'][1]*E('TOUTK',0.8)
    T=q0+rot(vt.normalized(),a_tm*E('TFR',0.16))*rt
    names=[f'thumb{k}.{L}' for k in (1,2,3)]
    J=[mw@Vector(pb[n_].head) for n_ in names]+[mw@Vector(pb[names[-1]].tail)]
    ls=[(J[i+1]-J[i]).length for i in range(3)]
    # start the chain on the free side so the solver goes under the bar
    _,v0=polar(J[0]); a_0t=sangle(v0,(T-polar(T)[0]))
    for k,fr in ((1,0.45),(2,0.80)):
        qq,_=polar(J[0]*(1-fr)+T*fr); J[k]=qq+rot(v0.normalized(),a_0t*fr)*(v0.length*(1-fr)+rt*fr)
    tr=[R['thumb1.L'][0]*0.6,R['thumb2.L'][1],R['thumb3.L'][1]]
    def push(p,rmin):
        q=B+axis*((p-B)@axis); d=p-q
        return q+d.normalized()*rmin if d.length<rmin else p
    base=J[0].copy()
    for _ in range(80):
        J[3]=T.copy()
        for i in (2,1,0):
            J[i]=J[i+1]+(J[i]-J[i+1]).normalized()*ls[i]
            if i>0: J[i]=push(J[i],rB+tr[i]+0.002)
        J[0]=base.copy()
        for i in (0,1,2):
            J[i+1]=J[i]+(J[i+1]-J[i]).normalized()*ls[i]
            if i<2: J[i+1]=push(J[i+1],rB+tr[i+1]+0.002)
            if i==1 and E('TPRESS',1.0)>0:          # the thumb pad rests on the bar
                q=B+axis*((J[2]-B)@axis); dd=J[2]-q; J[2]=q+dd.normalized()*(rB+tr[2]*E('TPK',0.85))
    for k in range(3): aim_bone(rig,names[k],mwi.to_3x3()@(J[k+1]-J[k]))
    bpy.context.view_layer.update()
    return info,(J[3]-T).length

def thumb_over(rig,L,B,axis,rB):
    """Thumb across the front of the fingers (like a real full grip): the last phalanx lies on the index finger,
    roughly along the bar, pointing to the middle finger. Two-bone IK CMC -> IP, then the tip."""
    mw=rig.matrix_world; mwi=mw.inverted(); pb=rig.pose.bones; R=radii(); B=Vector(B); axis=Vector(axis).normalized()
    bpy.context.view_layer.update()
    def polar(p):
        q=B+axis*((p-B)@axis); return q,(p-q)
    names=[f'thumb{k}.{L}' for k in (1,2,3)]
    A=mw@Vector(pb[names[0]].head)
    l1=rig.data.bones[names[0]].length; l2=rig.data.bones[names[1]].length; l3=rig.data.bones[names[2]].length
    dip=mw@Vector(pb['index3.'+L].head); tipI=mw@Vector(pb['index3.'+L].tail)
    P=dip*(1-E('TIPOS',0.45))+tipI*E('TIPOS',0.45)
    q,vv=polar(P); out=vv.normalized()
    IP=P+out*(R['index3.L'][0]*E('TOVK',0.75)+R['thumb3.L'][1]*0.7)
    side=1.0 if ((mw@Vector(pb['middle1.'+L].head))-(mw@Vector(pb['index1.'+L].head)))@axis>0 else -1.0
    # tip: towards the middle finger along the bar, bending a little round the fist
    tdir=(axis*side*math.cos(math.radians(E('TBEND',20)))-out*math.sin(math.radians(E('TBEND',20)))).normalized()
    TIP=IP+tdir*l3
    # two-bone IK from the CMC to the IP, knuckle (MCP) kept away from the bar
    d=IP-A; dist=d.length; u=d/dist
    if dist>l1+l2: IPr=A+u*(l1+l2)*0.999; dist=(IPr-A).length
    a=(l1*l1-l2*l2+dist*dist)/(2*dist); h=math.sqrt(max(l1*l1-a*a,0.0))
    mid=(A+IP)/2; _,pole=polar(mid); pole=pole.normalized()
    n=(pole-u*(pole@u)).normalized()
    MCP=A+u*a+n*h
    IPa=MCP+(IP-MCP).normalized()*l2
    aim_bone(rig,names[0],mwi.to_3x3()@(MCP-A))
    aim_bone(rig,names[1],mwi.to_3x3()@(IPa-MCP))
    aim_bone(rig,names[2],mwi.to_3x3()@(TIP-IP))
    bpy.context.view_layer.update()
    return (IPa-IP).length
