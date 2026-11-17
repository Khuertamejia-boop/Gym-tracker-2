# BACK DOUBLE BICEPS (bodybuilding pose, for the app background): P=0 the base rest pose (standing, arms down a little
# away from the body, open hands) -> P=1 upper arms out to the sides a little above the shoulders, elbows bent ~105 deg,
# forearms up and a little in, fists closed at head height (palms towards the head), chest up, shoulder blades up.
# Legs stay as at rest. Every part moves along its own smooth path (no equipment).
# usage: SKIN=cor P=0.5 python dblbiceps.py NB_mc_row3.blend out.blend   (source agarre_final.env)
#   env: DBUX/DBUY/DBUZ upper-arm direction at the top (x out, y back, z up), DBFX/DBFY forearm tilt (in / back),
#        DBWF wrist flexion towards the head (deg), DBGR fist roll about the hand axis (deg), DBCLV/DBCLR shoulder
#        girdle up / back (deg), DBSPX chest up (deg), DBLAG elbow bend starts a little after the lift (0..0.5),
#        DBFR fist core radius (m, 0.003), DBDN core distance from the knuckles (0.008; back versions v2: 0.007 / 0.0165),
#        DBFS/DBFE fist closes between these P values
import bpy,sys,math,os
import numpy as np
from mathutils import Vector,Matrix,Quaternion
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,os.environ.get('GT3D','.'))
import handrig
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
P=E('P',0.0)
ease=lambda t: (lambda c: c*c*(3-2*c))(min(max(t,0.0),1.0)); q=ease(P)
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']
for m in list(hi.modifiers):
    if m.type=='ARMATURE': hi.modifiers.remove(m)
md=hi.modifiers.new('Armature','ARMATURE'); md.object=rig; md.use_deform_preserve_volume=E('PV',0)>0; md.show_viewport=False
pb=rig.pose.bones; bb=rig.data.bones
upd=lambda: bpy.context.view_layer.update()
lerp=lambda a,b,t: a+(b-a)*t

def set_rot(n,Mw):
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
    y=y.normalized(); x=(x-y*(x@y)).normalized(); return Matrix((y,x,y.cross(x))).transposed()
def twist_deg(Rloc):
    qq=Rloc.to_quaternion(); return math.degrees(2*math.atan2(qq.y,qq.w))
def sangle(a,b,ax):
    a=(a-ax*(a@ax)).normalized(); b=(b-ax*(b@ax)).normalized(); return math.atan2(a.cross(b)@ax,a@b)

R0={n:bb[n].matrix_local.to_3x3() for n in bb.keys()}
H0={n:Vector(bb[n].head_local) for n in bb.keys()}
T0={n:Vector(bb[n].tail_local) for n in bb.keys()}
Lu=bb['upper_arm.L'].length; Lf=bb['forearm.L'].length
rest={}
for L in 'LR':
    u0=(T0['upper_arm.'+L]-H0['upper_arm.'+L]).normalized(); f0=(T0['forearm.'+L]-H0['forearm.'+L]).normalized()
    n0=u0.cross(f0).normalized(); th0=u0.angle(f0)
    h_ua=R0['upper_arm.'+L].transposed()@n0
    kn=(H0['index1.'+L]-H0['pinky1.'+L]); kn_loc=R0['hand.'+L].transposed()@kn
    rest[L]=dict(u0=u0,f0=f0,n0=n0,th0=th0,h_ua=h_ua,kn_loc=kn_loc,
                 ua_fa=R0['upper_arm.'+L].transposed()@R0['forearm.'+L],
                 cl_ua=R0['clavicle.'+L].transposed()@R0['upper_arm.'+L],
                 fa_h=R0['forearm.'+L].transposed()@R0['hand.'+L])
twb={L:[n for n in ('fa_tw1.'+L,'fa_tw2.'+L,'fa_tw3.'+L) if n in pb] for L in 'LR'}
TWF={'fa_tw1':1/3,'fa_tw2':2/3,'fa_tw3':1.0}
FINGB=[f'{f}{k}' for f in ('thumb','index','middle','ring','pinky') for k in (1,2,3)]

# ---------------- fists: closed around a thin (invisible) core, computed once at rest; then blended in with P
fistq={}
for L in 'LR':
    os.environ['DN']=str(E('DBDN',0.008))                    # core close to the palm: a closed fist, no hole
    M_,kn,n_,eh=handrig.palm_frame(rig,L); rF=E('DBFR',0.003); c=Vector(handrig.bar_from_hand(rig,L,rF))
    handrig.wrap2(rig,L,c,kn,rF); handrig.thumb_over(rig,L,c,kn,rF)
    fistq[L]={b:Quaternion(pb[b+'.'+L].rotation_quaternion) for b in FINGB}
    handrig.reset_fingers(rig,L)
qfist=ease((P-E('DBFS',0.15))/(E('DBFE',0.85)-E('DBFS',0.15)))

# ---------------- body: chest up a little, shoulder girdle up (arms raised), head in line
for bn,frac in (('spine',0.4),('chest',0.6)):
    R0b=R0[bn]; pb[bn].rotation_mode='QUATERNION'
    pb[bn].rotation_quaternion=(R0b.inverted()@Matrix.Rotation(math.radians(-E('DBSPX',4)*frac*q),3,'X')@R0b).to_quaternion()
upd()
for bn in ('neck','head'):                         # head back to its rest direction (cancel the chest tilt)
    pb[bn].rotation_mode='QUATERNION'; pb[bn].rotation_quaternion=(1,0,0,0); upd()
    aim(bn,T0[bn]-H0[bn])
for s,Ls_ in ((1,'L'),(-1,'R')):
    n='clavicle.'+Ls_; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0); upd()
    d0=Vector(pb[n].tail)-Vector(pb[n].head)
    aim(n,(Matrix.Rotation(math.radians(s*E('DBCLR',4)*q),3,'Z')@Matrix.Rotation(math.radians(-s*E('DBCLV',14)*q),3,'Y'))@d0)

# ---------------- arms: swing + humeral rotation + elbow bend, each blended from rest; hand follows the forearm
def hand_matrix(L,hd,want):
    A=frame(hd,want); B=frame(Vector((0,1,0)),rest[L]['kn_loc']); return A@B.transposed()
def arm_candidates(L,s,S,W,Mh,Mcl,pref,wpa):
    r=rest[L]; d=(W-S).length; dmax=(Lu+Lf)*0.9995; d=min(d,dmax)
    u=(W-S).normalized(); a=(Lu*Lu-Lf*Lf+d*d)/(2*d); h=math.sqrt(max(Lu*Lu-a*a,0.0))
    e1=Vector((0,0,1)).cross(u); e1=e1.normalized() if e1.length>1e-6 else Vector((1,0,0)); e2=u.cross(e1)
    B=frame(Vector((0,1,0)),r['h_ua']); out=[]
    for k in range(360):
        ph=2*math.pi*k/360; npole=e1*math.cos(ph)+e2*math.sin(ph)
        El=S+u*a+npole*h; y1=(El-S).normalized(); y2=(W-El).normalized()
        n=npole.cross(u).normalized(); th=y1.angle(y2)
        Mua=frame(y1,n)@B.transposed()
        Mfa=Matrix.Rotation(th-r['th0'],3,n)@Mua@r['ua_fa']
        tu=twist_deg((r['cl_ua']).transposed()@Mcl.transposed()@Mua)
        tf=twist_deg((r['fa_h']).transposed()@Mfa.transposed()@Mh)
        pa=math.degrees(npole.angle(pref))
        cost=(tu/E('WTU',100))**2+(tf/E('WTF',45))**2+(pa/wpa)**2
        out.append((cost,ph,El,Mua,Mfa,tu,tf,pa,math.degrees(th)))
    return min(out,key=lambda t:t[0])
qa=q                                                        # lift
LAG=E('DBLAG',-0.2)                                         # >0 elbow bend + humeral rotation later, <0 earlier
qe=ease((P-LAG)/(1-LAG)) if LAG>=0 else ease(P/(1+LAG))
res={}
for s,Ls_ in ((1,'L'),(-1,'R')):
    r=rest[Ls_]; S=Vector(pb['upper_arm.'+Ls_].head); Mcl=pb['clavicle.'+Ls_].matrix.to_3x3()
    uT=Vector((s*E('DBUX',1.0),E('DBUY',-0.03),E('DBUZ',0.16))).normalized()
    fT=Vector((-s*E('DBFX',0.42),E('DBFY',0.0),1.0)).normalized()
    nT=uT.cross(fT).normalized(); thT=uT.angle(fT)
    Rsw=r['u0'].rotation_difference(uT)                     # swing of the upper arm (shortest)
    Rq=Quaternion().slerp(Rsw,qa)
    ud=Rq@r['u0']
    n_sw=Rsw@r['n0']; tau=sangle(n_sw,nT,uT)                # humeral rotation still needed at the top
    nh=Quaternion(ud,tau*qe)@(Rq@r['n0'])
    th=lerp(r['th0'],thT,qe)
    f=Quaternion(nh,th)@ud
    El=S+ud*Lu; W=El+f*Lf
    # hand: at rest as in the base; at the top a fist, wrist bent towards the head, thumb side back
    np_=(fT.cross(Vector((0,1,0))) if s==1 else Vector((0,1,0)).cross(fT)).normalized()        # palm normal (towards the head)
    wf=math.radians(E('DBWF',28)); hdT=(fT*math.cos(wf)+np_*math.sin(wf)).normalized()
    wantT=Quaternion(hdT,math.radians(s*E('DBGR',0)))@Vector((0,1,0))
    Mh1=hand_matrix(Ls_,hdT,wantT)
    F0=frame(r['f0'],r['n0']); F1=frame(fT,nT); Fq=frame(f,nh)
    Q0=(F0.transposed()@R0['hand.'+Ls_]).to_quaternion(); Q1=(F1.transposed()@Mh1).to_quaternion()
    Mh=Fq@Q0.slerp(Q1,qe).to_matrix()
    pref=(El-S)-(W-S).normalized()*((El-S)@(W-S).normalized()); pref=pref.normalized() if pref.length>1e-5 else nh
    best=arm_candidates(Ls_,s,S,W,Mh,Mcl,pref,E('WPA',4))
    res[Ls_]=(best,Mh,W,math.degrees(th),math.degrees(tau))
for s,Ls_ in ((1,'L'),(-1,'R')):
    (cost,ph,El,Mua,Mfa,tu,tf,pa,th),Mh,W,thw,taud=res[Ls_]
    set_rot('upper_arm.'+Ls_,Mua); set_rot('forearm.'+Ls_,Mfa)
    for n in twb[Ls_]:
        fr=TWF[n.split('.')[0]]; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=Quaternion((0,1,0),math.radians(tf*fr))
    set_rot('hand.'+Ls_,Mh); upd()
    for b in FINGB:
        p=pb[b+'.'+Ls_]; p.rotation_mode='QUATERNION'; p.rotation_quaternion=Quaternion().slerp(fistq[Ls_][b],qfist)
    upd()
    print(f"{Ls_} elbow {th:5.1f} (asked {thw:5.1f}) humeral rot at top {taud:+6.1f} twist {tu:+6.1f} pronation {tf:+6.1f} "
          f"elbow-dir err {pa:4.0f} reach err {(Vector(pb['forearm.'+Ls_].tail)-W).length*1000:.1f}mm wrist {tuple(round(v,3) for v in W)}")
print('P %.3f lift %.3f elbow %.3f fist %.3f'%(P,qa,qe,qfist))
for n in ('Barra','Discos'):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render=True; bpy.data.objects[n].hide_viewport=True
md.show_viewport=True
import skinstack as D_skin
D_skin.build(hi,rig,md,E)
bpy.ops.wm.save_as_mainfile(filepath=out)
