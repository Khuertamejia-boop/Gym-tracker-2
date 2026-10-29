# OVERHEAD CABLE TRICEPS EXTENSION (rope, behind the neck) frame: standing with the back to a high pulley, split stance
# (left foot forward, right foot back on the ball of the foot), torso leaning a little forward, upper arms fixed beside
# the head pointing up and forward. Only the elbows move: P=0 stretch (hands behind the neck, elbows fully bent),
# P=1 arms extended forward-up in line with the upper arms. The cable tower is behind the athlete (tricepsoh_geo.py).
# usage: SKIN=cor P=0.5 python tricepsoh.py NB_mc_row3.blend out.blend   (source agarre_final.env)
import bpy,sys,math,os,json
import numpy as np
from mathutils import Vector,Matrix,Quaternion
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,os.environ.get('GT3D','.'))
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
rR=E('ROPER',0.011)
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

R0={n:bb[n].matrix_local.to_3x3() for n in bb.keys()}
H0={n:Vector(bb[n].head_local) for n in bb.keys()}
T0={n:Vector(bb[n].tail_local) for n in bb.keys()}
Lu=bb['upper_arm.L'].length; Lf=bb['forearm.L'].length
Lt=(H0['shin.L']-H0['thigh.L']).length; Ls=(H0['foot.L']-H0['shin.L']).length
rest={}
for L in 'LR':
    u0=(T0['upper_arm.'+L]-H0['upper_arm.'+L]).normalized(); f0=(T0['forearm.'+L]-H0['forearm.'+L]).normalized()
    n0=u0.cross(f0).normalized(); th0=u0.angle(f0)
    h_ua=R0['upper_arm.'+L].transposed()@n0
    kn=(H0['index1.'+L]-H0['pinky1.'+L]); kn_loc=R0['hand.'+L].transposed()@kn
    rest[L]=dict(n0=n0,th0=th0,h_ua=h_ua,kn_loc=kn_loc,
                 ua_fa=R0['upper_arm.'+L].transposed()@R0['forearm.'+L],
                 cl_ua=R0['clavicle.'+L].transposed()@R0['upper_arm.'+L],
                 fa_h=R0['forearm.'+L].transposed()@R0['hand.'+L])
twb={L:[n for n in ('fa_tw1.'+L,'fa_tw2.'+L,'fa_tw3.'+L) if n in pb] for L in 'LR'}
TWF={'fa_tw1':1/3,'fa_tw2':2/3,'fa_tw3':1.0}

# ---------------- body: forward lean, neutral spine, head in line (a little up), shoulder girdle up (arms overhead)
LEAN=E('TOLEAN',24)        # (LEAN, CLV, CLR are taken by agarre_final.env: own names here)
Rp=Matrix.Rotation(math.radians(LEAN),3,'X')            # positive = forward
def pose_upper(loc):
    hb=pb['hips']; R0h=R0['hips']
    hb.rotation_mode='QUATERNION'; hb.rotation_quaternion=(R0h.inverted()@Rp@R0h).to_quaternion()
    hb.location=R0h.inverted()@loc; upd()
    for bn,frac in (('spine',0.4),('chest',0.6)):
        R0b=R0[bn]; pb[bn].rotation_mode='QUATERNION'
        pb[bn].rotation_quaternion=(R0b.inverted()@Matrix.Rotation(math.radians(-E('SPEXT',6)*frac),3,'X')@R0b).to_quaternion()
    upd()
    for bn,fr in (('neck',0.5),('head',0.5)):
        pb[bn].rotation_mode='QUATERNION'; pb[bn].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[bn].tail)-Vector(pb[bn].head); aim(bn,Matrix.Rotation(math.radians(-E('HEADUP',12)*fr),3,'X')@d0)
    clv=E('TOCLV',22); clr=E('TOCLR',0)
    for s,Ls_ in ((1,'L'),(-1,'R')):
        n='clavicle.'+Ls_; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[n].tail)-Vector(pb[n].head)
        aim(n,(Rp@Matrix.Rotation(math.radians(s*clr),3,'Z')@Matrix.Rotation(math.radians(-s*clv),3,'Y')@Rp.inverted())@d0)
# ---------------- split stance: two-bone leg IK to fixed feet (left forward flat, right back on the ball of the foot)
FT={1:Vector((E('FXL',0.11),-E('FFWD',0.30),E('ANKZ',0.085))),-1:Vector((-E('FXR',0.11),E('FBK',0.34),E('ANKZ',0.085)+E('HEELUP',0.05)))}
def leg_ik(s,Ls_):
    H=Vector(pb['thigh.'+Ls_].head); A=FT[s]; v=A-H; d=min(v.length,0.999*(Lt+Ls)); u=v.normalized()
    a=(Lt*Lt-Ls*Ls+d*d)/(2*d); h=math.sqrt(max(Lt*Lt-a*a,0.0))
    kd=Vector((0,-1,0)); kd=(kd-u*(kd@u)).normalized(); K=H+u*a+kd*h
    aim('thigh.'+Ls_,K-H); aim('shin.'+Ls_,A-K)
    aim('foot.'+Ls_,(s*0.18,-1.0,-0.22) if s==1 else (s*0.14,-1.0,-0.70))
    return (A-H).length/(Lt+Ls)
pose_upper(Vector((0,0,0)))
Hm=(Vector(pb['thigh.L'].head)+Vector(pb['thigh.R'].head))/2
D=E('REARK',0.985)*(Lt+Ls); dzs=[]
for s,Ls_ in ((1,'L'),(-1,'R')):                          # hip height: the longer leg almost straight, the other bent
    H=Vector(pb['thigh.'+Ls_].head)-Vector((0,Hm.y,0)); v=FT[s]-H
    dzs.append(FT[s].z+math.sqrt(max(D*D-v.x**2-v.y**2,0.0))-H.z)
loc=Vector((0,-Hm.y,min(dzs))); pose_upper(loc)
kL=leg_ik(1,'L'); kR=leg_ik(-1,'R')
print('legs reach front %.3f rear %.3f lean %.1f'%(kL,kR,LEAN))

# ---------------- arms: upper arm fixed beside the head, elbow = pure hinge from full bend (behind the neck) to straight
def hand_matrix(L,s,hd,want):
    A=frame(hd,want); B=frame(Vector((0,1,0)),rest[L]['kn_loc']); return A@B.transposed()
def reset_fingers(L):
    for n in [x for x in pb.keys() if x.endswith('.'+L) and x.split('.')[0][:-1] in ('thumb','index','middle','ring','pinky')]:
        pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0)
def arm_candidates(L,s,S,W,Mh,Mcl,pref,wpa):
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
        cost=(tu/E('WTU',100))**2+(tf/E('WTF',45))**2+(pa/wpa)**2
        out.append((cost,ph,El,Mua,Mfa,tu,tf,pa,math.degrees(th)))
    return min(out,key=lambda t:t[0])
flex=lerp(E('FLEX0',140),E('FLEX1',8),q)                 # elbow flexion (deg)
xh=Vector((1,0,0))
res={}
for s,Ls_ in ((1,'L'),(-1,'R')):
    S=Vector(pb['upper_arm.'+Ls_].head); Mcl=pb['clavicle.'+Ls_].matrix.to_3x3()
    ud=(Rp@Vector((-s*E('UDX',0.06),-E('UDY',0.30),1.0))).normalized()          # upper arm: up, a little forward and in
    f=(Matrix.Rotation(math.radians(-flex),3,xh)@ud+Vector((-s*lerp(E('FIN0',0.15),E('FIN1',0.06),q),0,0))).normalized()
    El=S+ud*Lu; W=El+f*Lf
    hd=f; want=f.cross(xh)                                  # neutral grip: palms facing, thumbs towards the cable side
    Mh=hand_matrix(Ls_,s,hd,want); reset_fingers(Ls_); set_rot('hand.'+Ls_,Mh)
    u=(W-S).normalized(); pv=(El-S)-u*((El-S)@u); pref=pv.normalized() if pv.length>1e-5 else ud
    best=arm_candidates(Ls_,s,S,W,Mh,Mcl,pref,E('WPA',6))
    res[Ls_]=(best,Mh,W)
for s,Ls_ in ((1,'L'),(-1,'R')):
    (cost,ph,El,Mua,Mfa,tu,tf,pa,th),Mh,W=res[Ls_]
    set_rot('upper_arm.'+Ls_,Mua); set_rot('forearm.'+Ls_,Mfa)
    for n in twb[Ls_]:
        fr=TWF[n.split('.')[0]]; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=Quaternion((0,1,0),math.radians(tf*fr))
    set_rot('hand.'+Ls_,Mh); upd()
    print(f"{Ls_} elbow flex {th:5.1f} (asked {flex:5.1f}) humeral twist {tu:+6.1f} pronation {tf:+6.1f} elbow-dir err {pa:4.0f} reach err {(Vector(pb['forearm.'+Ls_].tail)-W).length*1000:.1f}mm")
ropes={}
for Ls_ in 'LR':
    M_,kn,n_,eh=handrig.palm_frame(rig,Ls_); c=Vector(handrig.bar_from_hand(rig,Ls_,rR))
    handrig.wrap2(rig,Ls_,c,kn,rR); handrig.thumb_over(rig,Ls_,c,kn,rR)
    ropes[Ls_]=(c,kn.normalized())
for n in ('Barra','Discos'):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render=True; bpy.data.objects[n].hide_viewport=True
md.show_viewport=True
import skinstack as D_skin
D_skin.build(hi,rig,md,E)
import tricepsoh_geo
tricepsoh_geo.build(ropes,rR,q,E)
bpy.ops.wm.save_as_mainfile(filepath=out)
