# CABLE FACE PULL frame: standing tall facing a cable tower, rope attachment at face height. P=0: arms reaching
# forward at shoulder height, neutral grip (thumbs up); P=1: rope pulled to the face, hands beside the ears, elbows
# high and wide (shoulders abducted ~90 deg, externally rotated: forearms up), shoulder blades squeezed together.
# usage: SKIN=cor P=0.5 python facepull.py NB_mc_row.blend out.blend   (source agarre_final.env)
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

LEAN=E('TLEAN',48)                      # torso forward lean from vertical (deg)

# ---------------- standing body
LEAN=E('TLEAN',-3)                      # torso lean from vertical (negative = a little back)
Rp=Matrix.Rotation(math.radians(LEAN),3,'X')
KF=E('KNEEF',10); AT=E('THIGHA',KF/2)
def legs(at):
    for s,Ls in ((1,'L'),(-1,'R')):
        a=math.radians(at); b=math.radians(KF-at)
        aim('thigh.'+Ls,(s*E('LEGX',0.10),-math.sin(a),-math.cos(a)))
        aim('shin.'+Ls,(s*E('SHX',0.04),math.sin(b),-math.cos(b)))
        aim('foot.'+Ls,(s*0.18,-1.0,-0.22))
def pose_body(loc,qq):
    hb=pb['hips']; R0h=R0['hips']
    hb.rotation_mode='QUATERNION'; hb.rotation_quaternion=(R0h.inverted()@Rp@R0h).to_quaternion()
    hb.location=R0h.inverted()@loc; upd()
    for bn,frac in (('spine',0.45),('chest',0.55)):
        R0b=R0[bn]; pb[bn].rotation_mode='QUATERNION'
        pb[bn].rotation_quaternion=(R0b.inverted()@Matrix.Rotation(math.radians(-E('SPEXT',4)*frac),3,'X')@R0b).to_quaternion()
    upd()
    for bn,fr in (('neck',0.5),('head',0.5)):
        pb[bn].rotation_mode='QUATERNION'; pb[bn].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[bn].tail)-Vector(pb[bn].head); aim(bn,Matrix.Rotation(math.radians(-E('NECKT',0)*fr),3,'X')@d0)
    clv=lerp(E('CLV0',4),E('CLV1',10),qq); clr=lerp(E('CLR0',-8),E('CLR1',18),qq)   # protracted reaching -> squeezed
    for s,Ls in ((1,'L'),(-1,'R')):
        n='clavicle.'+Ls; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[n].tail)-Vector(pb[n].head)
        aim(n,(Rp@Matrix.Rotation(math.radians(s*clr),3,'Z')@Matrix.Rotation(math.radians(-s*clv),3,'Y')@Rp.inverted())@d0)
    legs(AT)
pose_body(Vector((0,0,0)),q)
an=(Vector(pb['shin.L'].tail)+Vector(pb['shin.R'].tail))/2
loc=Vector((0,-an.y,E('ANKZ',0.075)-an.z)); pose_body(loc,q)

# ---------------- arms
def hand_matrix(L,s,hd,want):
    A=frame(hd,want); B=frame(Vector((0,1,0)),rest[L]['kn_loc']); return A@B.transposed()
def reset_fingers(L):
    for n in [x for x in pb.keys() if x.endswith('.'+L) and x.split('.')[0][:-1] in ('thumb','index','middle','ring','pinky')]:
        pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0)
def vlerp(a,b,t): return Vector(a)*(1-t)+Vector(b)*t
def arm_candidates(L,s,S,W,Mh,Mcl,pref,fdir):
    r=rest[L]; d=(W-S).length; dmax=(Lu+Lf)*0.9995; d=min(d,dmax)
    u=(W-S).normalized(); a=(Lu*Lu-Lf*Lf+d*d)/(2*d); h=math.sqrt(max(Lu*Lu-a*a,0.0))
    e1=Vector((0,0,1)).cross(u); e1=e1.normalized() if e1.length>1e-6 else Vector((1,0,0)); e2=u.cross(e1)
    B=frame(Vector((0,1,0)),r['h_ua']); out=[]
    for k in range(180):
        ph=2*math.pi*k/180; npole=e1*math.cos(ph)+e2*math.sin(ph)
        El=S+u*a+npole*h; y1=(El-S).normalized(); y2=(W-El).normalized()
        n=npole.cross(u).normalized(); th=y1.angle(y2)
        Mua=frame(y1,n)@B.transposed()
        Mfa=Matrix.Rotation(th-r['th0'],3,n)@Mua@r['ua_fa']
        tu=twist_deg((r['cl_ua']).transposed()@Mcl.transposed()@Mua)
        tf=twist_deg((r['fa_h']).transposed()@Mfa.transposed()@Mh)
        pa=math.degrees(npole.angle(pref))
        fv=math.degrees(y2.angle(fdir)); bentw=min(1.0,math.degrees(th)/60.0)
        cost=(tu/E('WTU',100))**2+(tf/E('WTF',45))**2+(pa/E('WPA',50))**2+bentw*(fv/E('WFV',25))**2
        out.append((cost,ph,El,Mua,Mfa,tu,tf,pa,math.degrees(th),fv))
    return min(out,key=lambda t:t[0])
rR=E('ROPER',0.011)
res={}
for s,Ls in ((1,'L'),(-1,'R')):
    Sx=Vector(pb['upper_arm.'+Ls].head); Mcl=pb['clavicle.'+Ls].matrix.to_3x3()
    # grip centre (rope in the fist): reaching forward at shoulder height -> beside the ear
    G0=Vector((s*E('GX0',0.085),Sx.y-E('REACH',0.50),Sx.z+E('GZ0',0.05)))
    G1=Vector((s*E('GX1',0.165),Sx.y-E('GY1',0.07),Sx.z+E('GZ1',0.17)))
    G=vlerp(G0,G1,q)
    hd=vlerp((-s*0.8,-0.35,-0.25),(-s*0.55,-0.85,0.05),q).normalized()          # fingers: inwards -> inwards/forwards
    want=vlerp((0,0.05,1.0),(0,0.65,0.75),q).normalized()                       # pinky->index line: up -> up/back (thumbs back)
    pref=vlerp((s*0.75,0.0,-0.65),(s*1.0,0.45,0.55),q).normalized()             # elbow: out/down -> out, high and back
    fdir=vlerp((0,-1,0),(0,-0.25,1.0),q).normalized()                           # forearm: forwards -> up
    Mh=hand_matrix(Ls,s,hd,want); reset_fingers(Ls); set_rot('hand.'+Ls,Mh)
    c=Vector(handrig.bar_from_hand(rig,Ls,rR)); doff=c-Vector(pb['hand.'+Ls].head)
    W=G-doff
    best=arm_candidates(Ls,s,Sx,W,Mh,Mcl,pref,fdir)
    res[Ls]=(best,Mh,W,G)
for s,Ls in ((1,'L'),(-1,'R')):
    (cost,ph,El,Mua,Mfa,tu,tf,pa,th,fv),Mh,W,G=res[Ls]
    set_rot('upper_arm.'+Ls,Mua); set_rot('forearm.'+Ls,Mfa)
    for n in twb[Ls]:
        f=TWF[n.split('.')[0]]; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=Quaternion((0,1,0),math.radians(tf*f))
    set_rot('hand.'+Ls,Mh); upd()
    print(f"{Ls} elbow flex {th:5.1f} humeral twist {tu:+6.1f} pronation {tf:+6.1f} forearm-vs-pref {fv:4.0f} reach err {(Vector(pb['forearm.'+Ls].tail)-W).length*1000:.1f}mm")
# rope in each fist: axis along the knuckle line (pinky -> index)
ropes={}
for Ls in 'LR':
    M,kn,n,eh=handrig.palm_frame(rig,Ls); c=Vector(handrig.bar_from_hand(rig,Ls,rR))
    handrig.wrap2(rig,Ls,c,kn,rR); handrig.thumb_over(rig,Ls,c,kn,rR)
    ropes[Ls]=(c,kn.normalized())
for n in ('Barra','Discos'):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render=True; bpy.data.objects[n].hide_viewport=True
md.show_viewport=True
import facepull_geo
facepull_geo.build(ropes,rR,q,E)
import skinstack as D_skin
D_skin.build(hi,rig,md,E)
bpy.ops.wm.save_as_mainfile(filepath=out)
