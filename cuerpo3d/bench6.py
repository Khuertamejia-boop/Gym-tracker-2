# FLAT BARBELL BENCH PRESS frame (new athletic body), same anatomical arm solver as the pull-up (pullup6):
#  pure-hinge elbow, elbow direction chosen per frame (twist shared between humerus and forearm, forearms vertical),
#  forearm twist bones, approved grip; shoulder blades retracted/depressed; centre-of-rotation shoulder skinning.
# P=0 lockout (arms straight over the shoulders), P=1 bar touching the lower chest.
# usage: SKIN=cor P=0.5 python bench6.py NB_mc.blend out.blend   (source agarre_final.env, BARUNI=0)
import bpy,sys,math,os,json
import numpy as np
from mathutils import Vector,Matrix,Quaternion
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,os.environ.get('SCR',os.environ.get('GT3D','/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad')+''))
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
Rb=Matrix.Rotation(math.radians(-90),3,'X')       # lying on the back, head towards +Y, face up
BENCHZ=E('BENCHZ',0.44)                             # top of the bench pad
GRIPX=E('GRIPX',0.38)
def bodyrot(Rl): return Rb@Rl@Rb.inverted()         # a rotation given in the standing body frame -> world
# rest mesh points used to place the body and the bar
me0=hi.data; nv0=len(me0.vertices); C=np.zeros(nv0*3); me0.vertices.foreach_get('co',C); C=C.reshape(-1,3)
Hh=np.array(bb['hips'].head_local)
up_back=C[(np.abs(C[:,0])<0.10)&(C[:,2]>1.15)&(C[:,2]<1.35)][:,1].max()       # upper back (shoulder blades) rests on the pad
HZ=BENCHZ+(up_back-Hh[1])
def to_world(p): return np.array(Vector((0,0,HZ))+Rb@Vector(p-Hh))
def pose_body():
    hb=pb['hips']; R0h=R0['hips']
    hb.rotation_mode='QUATERNION'; hb.rotation_quaternion=(R0h.inverted()@Rb@R0h).to_quaternion()
    hb.location=R0h.inverted()@(Vector((0,0,HZ))-H0['hips']); upd()
    for bn,a in (('spine',E('ARCH',5)),('chest',E('ARCH',5)*0.6)):           # slight arch of the lower back
        pb[bn].rotation_mode='QUATERNION'; pb[bn].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[bn].tail)-Vector(pb[bn].head); aim(bn,bodyrot(Matrix.Rotation(math.radians(-a),3,'X'))@d0)
    for s,L in ((1,'L'),(-1,'R')):                                           # shoulder blades back and down
        n='clavicle.'+L; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[n].tail)-Vector(pb[n].head)
        aim(n,bodyrot(Matrix.Rotation(math.radians(s*E('BCLR',14)),3,'Z')@Matrix.Rotation(math.radians(-s*E('BCLV',-6)),3,'Y'))@d0)
    for bn,fr in (('neck',0.5),('head',0.5)):                                # head resting on the bench
        pb[bn].rotation_mode='QUATERNION'; pb[bn].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[bn].tail)-Vector(pb[bn].head); aim(bn,bodyrot(Matrix.Rotation(math.radians(-E('NECKT',12)*fr),3,'X'))@d0)
    for s,L in ((1,'L'),(-1,'R')):                                           # feet flat on the floor, knees ~90 deg
        aim('thigh.'+L,(s*E('TOUT',0.30),-1.0,-E('TDOWN',0.12)))
        aim('shin.'+L,(s*0.05,E('SBACK',0.10),-1.0))
        aim('foot.'+L,(s*0.12,-1.0,-0.25))
def hand_dir(s):
    a=math.radians(E('WEXT',22)); return Vector((0,math.sin(a),math.cos(a)))  # fingers up, tilted towards the head (wrist slightly extended)
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
    pref=Rb@Vector((s*E('PEX',1.0),E('PEY',0.0),E('PEZ',-0.9))).normalized()   # body frame: out + towards the feet (elbows ~45-60 deg from the torso)
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
def solve_arms():
    pose_body(); res={}
    for s,L in ((1,'L'),(-1,'R')):
        Mcl=pb['clavicle.'+L].matrix.to_3x3(); S=Vector(pb['upper_arm.'+L].head)
        hd=hand_dir(s); y2=None
        for it in range(4):                                   # the hand follows the forearm partly (less wrist bend)
            hdd=hd if y2 is None else (hd*(1-E('HFOL',0.5))+y2*E('HFOL',0.5)).normalized()
            Mh=hand_matrix(L,s,hdd); W=wrist_target(L,s,Mh)
            best=arm_candidates(L,s,S,W,Mh,Mcl); y2=(W-best[2]).normalized()
        res[L]=(best,Mh,W,S)
    return res
# ---------------- bar path: lockout over the shoulders -> touch on the lower chest (slight J-curve)
pose_body()
S=Vector(pb['upper_arm.L'].head)
chest=C[(np.abs(C[:,0])<0.03)&(np.abs(C[:,2]-E('TOUCHZ',1.17))<0.01)]
cf=to_world(chest[np.argmin(chest[:,1])])                                  # front of the lower chest (world)
y_top=S.y+E('YTOP',-0.01); y_bot=cf[1]
z_bot=cf[2]+rB+E('CHGAP',0.006)
BAR=Vector((0,y_top,1.0)); Mh0=hand_matrix('L',1,hand_dir(1)); W0=wrist_target('L',1,Mh0); doff=Vector((GRIPX,BAR.y,BAR.z))-W0
d_lock=math.sqrt(Lu*Lu+Lf*Lf+2*Lu*Lf*math.cos(math.radians(E('FLEX0',8))))
vx=GRIPX-doff.x-S.x; vy=y_top-doff.y-S.y
z_top=S.z+doff.z+math.sqrt(max(d_lock**2-vx*vx-vy*vy,0.0))
BAR=Vector((0,lerp(y_top,y_bot,q),lerp(z_top,z_bot,q)))
print('bar top z %.3f bottom z %.3f, now'%(z_top,z_bot),tuple(round(x,3) for x in BAR))
res=solve_arms()
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
print('P',P)
# ---------------- fingers, barbell with plates, bench, deformers
Bc=Vector((0,BAR.y,BAR.z)); axis=Vector((1,0,0))
for L in 'LR':
    info,err=handrig.wrap2(rig,L,Bc,axis,rB)
    if os.environ.get('TMODE','over')=='over': handrig.thumb_over(rig,L,Bc,axis,rB)
handrig.place_bar(Bc,axis,rB,hide_discs=False)
import bench_geo; bench_geo.make_bench(BENCHZ,y0=E('BY0',-0.30),y1=E('BY1',0.95))
md.show_viewport=True
import skinstack as D_skin
D_skin.build(hi,rig,md,E)
bpy.ops.wm.save_as_mainfile(filepath=out)
