# Pull-up frame with ANATOMICAL arm kinematics (new body).
#  - elbow = pure hinge: the forearm only bends about the elbow's own hinge axis (no twist, no sideways bend)
#  - the upper arm's twist follows from where the elbow points; the elbow direction is chosen per frame to share the
#    total twist between humeral rotation and forearm pronation inside real ranges (cost minimisation)
#  - forearm pronation goes to the forearm twist bones (if the rig has them) instead of the elbow
#  - shoulder girdle: elevated in the dead hang (passive), depressed/retracted at the top (active)
#  - dead hang = arms almost straight; top = chin over the bar
# P=0 dead hang, P=1 top.  usage: P=0.5 blender -b -P pullup5.py -- base.blend out.blend   (source agarre_final.env)
import bpy,sys,math,os,json
import numpy as np
from mathutils import Vector,Matrix,Quaternion
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import handrig
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
P=E('P',0.0)
ease=lambda t: t*t*(3-2*t); q=ease(P)
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']
for m in list(hi.modifiers):
    if m.type=='ARMATURE': hi.modifiers.remove(m)
md=hi.modifiers.new('Armature','ARMATURE'); md.object=rig; md.use_deform_preserve_volume=E('PV',0)>0; md.show_viewport=False
pb=rig.pose.bones; bb=rig.data.bones
BAR=Vector((0,E('BARY',-0.03),E('BARZ',2.15))); GRIPX=E('GRIPX',0.30); rB=E('BARR',0.0145)
upd=lambda: bpy.context.view_layer.update()
lerp=lambda a,b,t: a+(b-a)*t

def set_rot(n,Mw):
    """give pose bone n the armature-space orientation Mw (3x3); its head stays where the parent chain puts it"""
    p=pb[n]; b=bb[n]; upd()
    par=p.parent.matrix.to_3x3() if p.parent else Matrix.Identity(3)
    rest=b.matrix_local.to_3x3(); prest=b.parent.matrix_local.to_3x3() if b.parent else Matrix.Identity(3)
    loc=(prest.inverted()@rest).inverted()@par.inverted()@Mw
    p.rotation_mode='QUATERNION'; p.rotation_quaternion=loc.to_quaternion(); upd()
def aim(n,target,roll=0.0):
    p=pb[n]; upd(); cur=(p.tail-p.head).normalized(); tv=Vector(target).normalized()
    R=Matrix.Rotation(math.radians(roll),3,tv)@cur.rotation_difference(tv).to_matrix()
    set_rot(n,R@p.matrix.to_3x3())
def frame(y,x):
    """orthonormal 3x3 with columns (y', x', y'^x'), x' = x made perpendicular to y"""
    y=y.normalized(); x=(x-y*(x@y)).normalized(); return Matrix((y,x,y.cross(x))).transposed()
def twist_deg(Rloc):
    qq=Rloc.to_quaternion(); return math.degrees(2*math.atan2(qq.y,qq.w))

# ---------------- rest data per arm
R0={n:bb[n].matrix_local.to_3x3() for n in bb.keys()}
H0={n:Vector(bb[n].head_local) for n in bb.keys()}
T0={n:Vector(bb[n].tail_local) for n in bb.keys()}
Lu=bb['upper_arm.L'].length; Lf=bb['forearm.L'].length
rest={}
for L in 'LR':
    u0=(T0['upper_arm.'+L]-H0['upper_arm.'+L]).normalized(); f0=(T0['forearm.'+L]-H0['forearm.'+L]).normalized()
    n0=u0.cross(f0).normalized(); th0=u0.angle(f0)
    h_ua=R0['upper_arm.'+L].transposed()@n0                      # elbow hinge axis in upper-arm local coords
    kn=(H0['index1.'+L]-H0['pinky1.'+L]); kn_loc=R0['hand.'+L].transposed()@kn   # knuckle line in hand-local coords
    rest[L]=dict(n0=n0,th0=th0,h_ua=h_ua,kn_loc=kn_loc,
                 ua_fa=R0['upper_arm.'+L].transposed()@R0['forearm.'+L],
                 cl_ua=R0['clavicle.'+L].transposed()@R0['upper_arm.'+L],
                 fa_h=R0['forearm.'+L].transposed()@R0['hand.'+L])
HFIX=json.load(open(os.environ['HFIX'])) if os.environ.get('HFIX') else {'L':[0,-0.3,1],'R':[0,-0.3,1]}
twb={L:[n for n in ('fa_tw1.'+L,'fa_tw2.'+L,'fa_tw3.'+L) if n in pb] for L in 'LR'}
TWF={'fa_tw1':1/3,'fa_tw2':2/3,'fa_tw3':1.0}

# ---------------- body: girdle, head, legs (everything except the arms)
CLV=lerp(E('CLV0',30),E('CLV1',8),q); CLR=lerp(E('CLR0',0),E('CLR1',12),q)
def pose_body(dz,dy,clv,clr,tilt):
    hb=pb['hips']; hb.location=R0['hips'].inverted()@Vector((0,dy,dz)); upd()
    for s,L in ((1,'L'),(-1,'R')):
        n='clavicle.'+L; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[n].tail)-Vector(pb[n].head)
        aim(n,Matrix.Rotation(math.radians(s*clr),3,'Z')@Matrix.Rotation(math.radians(-s*clv),3,'Y')@d0)
    for bn,fr in (('neck',0.4),('head',0.6)):
        pb[bn].rotation_mode='QUATERNION'; pb[bn].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[bn].tail)-Vector(pb[bn].head)
        if tilt: aim(bn,Matrix.Rotation(math.radians(-tilt*fr),3,'X')@d0)
    for s,L in ((1,'L'),(-1,'R')):
        aim('thigh.'+L,(s*0.03,-E('TFWD',0.18),-1)); aim('shin.'+L,(s*0.02,E('SBK',0.7),-0.8))

# ---------------- hand orientation for the grip and where the wrist must be
def hand_matrix(L,s,hd):
    want=Vector((-s,0,0))                                           # knuckle line along the bar, index towards the middle
    A=frame(hd,want); B=frame(Vector((0,1,0)),rest[L]['kn_loc'])
    return A@B.transposed()
def wrist_target(L,s,Mh):
    for n in [x for x in pb.keys() if x.endswith('.'+L) and x[:-3] in ('thumb1','thumb2','thumb3','index1','index2','index3','middle1','middle2','middle3','ring1','ring2','ring3','pinky1','pinky2','pinky3')]:
        pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0)
    set_rot('hand.'+L,Mh)
    c=Vector(handrig.bar_from_hand(rig,L,rB)); Wn=Vector(pb['hand.'+L].head)
    return Vector((s*GRIPX,BAR.y,BAR.z))-(c-Wn)

# ---------------- arm solve (shoulder S and wrist W given): pole search, hinge-consistent upper arm, pure-hinge forearm
def arm_candidates(L,s,S,W,Mh,Mcl):
    r=rest[L]; d=(W-S).length; dmax=(Lu+Lf)*0.9995; d=min(d,dmax)
    u=(W-S).normalized(); a=(Lu*Lu-Lf*Lf+d*d)/(2*d); h=math.sqrt(max(Lu*Lu-a*a,0.0))
    e1=Vector((0,0,1)).cross(u); e1=e1.normalized() if e1.length>1e-6 else Vector((1,0,0)); e2=u.cross(e1)
    pref=Vector((s*lerp(E('PEX0',1.0),E('PEX1',0.6),q),lerp(E('PEY0',-0.15),E('PEY1',-0.25),q),lerp(E('PEZ0',-0.35),E('PEZ1',-1.0),q))).normalized()
    B=frame(Vector((0,1,0)),r['h_ua'])
    best=None; out=[]
    for k in range(180):
        ph=2*math.pi*k/180; npole=e1*math.cos(ph)+e2*math.sin(ph)
        El=S+u*a+npole*h; y1=(El-S).normalized(); y2=(W-El).normalized()
        n=npole.cross(u).normalized(); th=y1.angle(y2)
        Mua=frame(y1,n)@B.transposed()
        Mfa=Matrix.Rotation(th-r['th0'],3,n)@Mua@r['ua_fa']
        tu=twist_deg((r['cl_ua']).transposed()@Mcl.transposed()@Mua)
        tf=twist_deg((r['fa_h']).transposed()@Mfa.transposed()@Mh)
        pa=math.degrees(npole.angle(pref))
        fv=math.degrees(y2.angle(Vector((0,0,1))))       # forearm close to vertical (the pulling line) when the elbow is bent
        bentw=min(1.0,math.degrees(th)/60.0)
        cost=(tu/E('WTU',100))**2+(tf/E('WTF',45))**2+(pa/E('WPA',50))**2+bentw*(fv/E('WFV',25))**2
        out.append((cost,ph,El,Mua,Mfa,tu,tf,pa,math.degrees(th),fv))
    return min(out,key=lambda t:t[0])

def solve_arms(dz,dy,clv,clr,tilt,hk):
    pose_body(dz,dy,clv,clr,tilt)
    res={}
    for s,L in ((1,'L'),(-1,'R')):
        Mcl=pb['clavicle.'+L].matrix.to_3x3()
        S=Vector(pb['upper_arm.'+L].head)
        hd=Vector(HFIX[L]).normalized(); y2=None
        for it in range(4):
            hdd=hd if y2 is None else (hd*(1-hk)+y2*hk).normalized()
            Mh=hand_matrix(L,s,hdd)
            W=wrist_target(L,s,Mh)
            best=arm_candidates(L,s,S,W,Mh,Mcl)
            y2=(W-best[2]).normalized()
        res[L]=(best,Mh,W,S)
    return res

# ---------------- body height: dead hang = arms almost straight (FLEX0), top = head over the bar (CHINH)
def S_of(clv,clr,dy,tilt):
    pose_body(0.0,dy,clv,clr,tilt); return Vector(pb['upper_arm.L'].head), Vector(pb['head'].head)
d_hang=math.sqrt(Lu*Lu+Lf*Lf+2*Lu*Lf*math.cos(math.radians(E('FLEX0',10))))
S0,_=S_of(E('CLV0',30),E('CLR0',0),0.0,0.0)
Mh0=hand_matrix('L',1,Vector(HFIX['L']).normalized()); W0=wrist_target('L',1,Mh0)
v=W0-S0; dz_hang=v.z-math.sqrt(max(d_hang**2-v.x**2-v.y**2,0.0))
_,Hd1=S_of(E('CLV1',8),E('CLR1',12),E('LEAN',0.20),E('HTILT',25))
dz_top=(BAR.z+E('CHINH',0.075))-Hd1.z
dz=lerp(dz_hang,dz_top,q); dy=E('LEAN',0.20)*q
res=solve_arms(dz,dy,CLV,CLR,E('HTILT',25)*q,E('HFOL',0.35))
for s,L in ((1,'L'),(-1,'R')):
    (cost,ph,El,Mua,Mfa,tu,tf,pa,th,fv),Mh,W,S=res[L]
    set_rot('upper_arm.'+L,Mua); set_rot('forearm.'+L,Mfa)
    # forearm twist bones carry the pronation (fraction along the forearm); hand gets its exact orientation
    for n in twb[L]:
        f=TWF[n.split('.')[0]]; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=Quaternion((0,1,0),math.radians(tf*f))
    set_rot('hand.'+L,Mh); upd()
    c=Vector(handrig.bar_from_hand(rig,L,rB)); err=(c-Vector((s*GRIPX,BAR.y,BAR.z))).length
    fa=(Vector(pb['forearm.'+L].tail)-Vector(pb['forearm.'+L].head)).normalized(); hdv=(Vector(pb['hand.'+L].tail)-Vector(pb['hand.'+L].head)).normalized()
    print(f"{L} elbow {180-th:5.1f}deg (flex {th:5.1f}) pole {math.degrees(ph):5.0f} humeral twist {tu:+6.1f} pronation {tf:+6.1f} elbow-dir {pa:4.0f} forearm-vs-vertical {fv:4.0f} wrist bend {math.degrees(fa.angle(hdv)):4.1f} bar err {err*1000:.1f}mm reach err {(Vector(pb['forearm.'+L].tail)-W).length*1000:.1f}mm")
print('P',P,'dz %.3f dy %.3f clv %.1f'%(dz,dy,CLV))
# ---------------- fingers on the bar, bar, deformers
Bc=Vector((0,BAR.y,BAR.z)); axis=Vector((1,0,0))
for L in 'LR':
    info,err=handrig.wrap2(rig,L,Bc,axis,rB)
    if os.environ.get('TMODE','over')=='over': handrig.thumb_over(rig,L,Bc,axis,rB)
handrig.place_bar(Bc,axis,rB)
md.show_viewport=True
if E('CSM',1)>0 and 'CS' in hi.vertex_groups:
    cs=hi.modifiers.new('CorrectiveSmooth','CORRECTIVE_SMOOTH'); cs.vertex_group='CS'; cs.iterations=int(E('CSIT',10)); cs.factor=E('CSF',0.8)
    cs.smooth_type='LENGTH_WEIGHTED'; cs.rest_source='ORCO'
if E('CS2IT',0)>0:
    me=hi.data; nv=len(me.vertices); co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    d=np.min([np.linalg.norm(co-np.array(bb['upper_arm.'+L].head_local),axis=1) for L in 'LR'],axis=0)
    t=np.clip((d-E('S2D0',0.09))/(E('S2D1',0.18)-E('S2D0',0.09)),0,1); w=1-t*t*(3-2*t)
    nh=np.zeros(nv); gidx={g.index:g.name for g in hi.vertex_groups}
    for i in np.where(w>0)[0]:
        for g_ in me.vertices[int(i)].groups:
            if gidx.get(g_.group) in ('neck','head'): nh[i]+=g_.weight
    w=w*np.clip(1-nh*E('S2NECK',3.0),0,1)
    if 'CS2' in hi.vertex_groups: hi.vertex_groups.remove(hi.vertex_groups['CS2'])
    g=hi.vertex_groups.new(name='CS2'); qq=np.round(w*64).astype(int)
    for val in np.unique(qq[qq>0]): g.add([int(i) for i in np.where(qq==val)[0]],val/64.0,'REPLACE')
    c2=hi.modifiers.new('CorrectiveSmooth2','CORRECTIVE_SMOOTH'); c2.vertex_group='CS2'; c2.iterations=int(E('CS2IT',0)); c2.factor=E('CS2F',1.0)
    c2.smooth_type='LENGTH_WEIGHTED'; c2.rest_source='ORCO'
bpy.ops.wm.save_as_mainfile(filepath=out)
