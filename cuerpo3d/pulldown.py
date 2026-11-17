# CLOSE-GRIP LAT PULLDOWN frame (V-handle, neutral grip): seated on a flat bench facing a high-pulley tower, thighs
# under the knee roller, torso leaning back a little.  P=0: arms extended overhead holding the handle, shoulder blades
# up (stretch); P=1: handle pulled to the upper chest, elbows down and back by the ribs, shoulder blades down and
# together, chest up.  The machine is built around the posed body (pulldown_geo.py).
# usage: SKIN=cor P=0.5 python pulldown.py NB_mc_row3.blend out.blend   (source agarre_final.env)
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
rB=E('BARR',0.0145)
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
    h_ua=R0['upper_arm.'+L].transposed()@n0
    kn=(H0['index1.'+L]-H0['pinky1.'+L]); kn_loc=R0['hand.'+L].transposed()@kn
    rest[L]=dict(n0=n0,th0=th0,h_ua=h_ua,kn_loc=kn_loc,
                 ua_fa=R0['upper_arm.'+L].transposed()@R0['forearm.'+L],
                 cl_ua=R0['clavicle.'+L].transposed()@R0['upper_arm.'+L],
                 fa_h=R0['forearm.'+L].transposed()@R0['hand.'+L])
twb={L:[n for n in ('fa_tw1.'+L,'fa_tw2.'+L,'fa_tw3.'+L) if n in pb] for L in 'LR'}
TWF={'fa_tw1':1/3,'fa_tw2':2/3,'fa_tw3':1.0}

# ---------------- seated body: pelvis/torso lean back, chest up, head neutral, girdle up (stretch) -> down and back
def pose_body(loc,qq):
    lean=lerp(E('LEAN0',8),E('LEAN1',17),qq)                 # torso lean back from vertical (deg)
    Rp=Matrix.Rotation(math.radians(-lean),3,'X')
    hb=pb['hips']; R0h=R0['hips']
    hb.rotation_mode='QUATERNION'; hb.rotation_quaternion=(R0h.inverted()@Rp@R0h).to_quaternion()
    hb.location=R0h.inverted()@loc; upd()
    spx=lerp(E('SPX0',0),E('SPX1',8),qq)                      # chest up at the bottom (thoracic extension)
    for bn,frac in (('spine',0.4),('chest',0.6)):
        R0b=R0[bn]; pb[bn].rotation_mode='QUATERNION'
        pb[bn].rotation_quaternion=(R0b.inverted()@Matrix.Rotation(math.radians(-spx*frac),3,'X')@R0b).to_quaternion()
    upd()
    for bn,fr in (('neck',0.5),('head',0.5)):                # head stays almost upright (looks ahead / a little up)
        pb[bn].rotation_mode='QUATERNION'; pb[bn].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[bn].tail)-Vector(pb[bn].head)
        aim(bn,Matrix.Rotation(math.radians((lean+spx)*fr*E('HEADK',0.75)+E('NECKT',0)*fr),3,'X')@d0)
    clv=lerp(E('CLV0',26),E('CLV1',2),qq); clr=lerp(E('CLR0',-4),E('CLR1',14),qq)
    for s,Ls in ((1,'L'),(-1,'R')):
        n='clavicle.'+Ls; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[n].tail)-Vector(pb[n].head)
        aim(n,(Rp@Matrix.Rotation(math.radians(s*clr),3,'Z')@Matrix.Rotation(math.radians(-s*clv),3,'Y')@Rp.inverted())@d0)
    for s,Ls in ((1,'L'),(-1,'R')):                          # thighs forward (knees a little lower), shins down, feet flat
        aim('thigh.'+Ls,(s*E('TXL',0.08),-1.0,-E('TDN',0.10)))
        aim('shin.'+Ls,(s*0.03,E('SHB',0.10),-1.0))
        aim('foot.'+Ls,(s*0.18,-1.0,-0.22))
    return lean,Rp
lean,Rp=pose_body(Vector((0,0,0)),q)
hm=(Vector(pb['thigh.L'].head)+Vector(pb['thigh.R'].head))/2; an=(Vector(pb['shin.L'].tail)+Vector(pb['shin.R'].tail))/2
loc=Vector((0,-hm.y,E('ANKZ',0.085)-an.z))                    # hip joints at y=0, ankles just above the floor
def ref_handles():
    """handle centre at the top (arms extended) and at the bottom (upper chest), each with its own body pose"""
    out=[]
    for qq in (0.0,1.0):
        _,Rq=pose_body(loc,qq); upd()
        S={s:Vector(pb['upper_arm.'+Ls].head) for s,Ls in ((1,'L'),(-1,'R'))}; Sm=(S[1]+S[-1])/2
        if qq==0.0:
            d_ext=math.sqrt(Lu*Lu+Lf*Lf+2*Lu*Lf*math.cos(math.radians(E('FLEX0',2))))*E('REACHK',1.025)
            hx=E('GX',0.055); dx=S[1].x-hx; hy=Sm.y-E('GY0',0.10)
            # the wrist (not the grip) is at arm's length; the grip centre is ~DGRIP further along the hand
            hz=Sm.z+math.sqrt(max(d_ext**2-dx*dx-(hy-Sm.y)**2,0.0))+E('DGRIP',0.075)
            out.append(Vector((0,hy,hz)))
        else:
            out.append(Sm+Rq@Vector((0,-E('GY1',0.24),-E('GZ1',0.08))))
    return out
HT,HB=ref_handles()
lean,Rp=pose_body(loc,q); upd()
cdir_=(HT-HB).normalized(); fwd=Vector((0,-1,0)); fwd=(fwd-cdir_*(fwd@cdir_)).normalized()
Hc=HT.lerp(HB,q)+fwd*(E('BULGE',0.045)*4*q*(1-q))           # down the cable line, a little forward in front of the face
cdir=(HT-HB).normalized()                                     # cable direction (towards the high pulley)
print('handle top',tuple(round(v,3) for v in HT),'bottom',tuple(round(v,3) for v in HB),'lean %.1f'%lean)

# ---------------- arms (pole search, pure-hinge elbow; approved grip)
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
        cost=(tu/E('WTU',100))**2+(tf/E('WTF',45))**2+(pa/WPA_)**2+bentw*(fv/E('WFV',25))**2
        out.append((cost,ph,El,Mua,Mfa,tu,tf,pa,math.degrees(th),fv))
    return min(out,key=lambda t:t[0])
res={}
for s,Ls in ((1,'L'),(-1,'R')):
    Sx=Vector(pb['upper_arm.'+Ls].head); Mcl=pb['clavicle.'+Ls].matrix.to_3x3()
    G=Hc+Vector((s*E('GX',0.055),0,0))
    hd=vlerp((-s*0.12,0.05,1.0),(-s*0.18,-0.12,1.0),q).normalized()         # fingers up, a little inwards
    want=Vector((0,1,0))                                                     # pinky->index backwards: thumbs back (neutral grip)
    # elbow: out at the top -> at the bottom by the sides of the body, EOX out from the shoulder and EOY forward (torso
    # frame): the upper arm clears the lats and the forearms rise in front of the ribs to the hands (no arm inside the torso)
    Et=Sx+Rp@Vector((s*E('EOX',0.13),-E('EOY',0.06),-0.25))
    pref=vlerp((s*1.0,-0.35,0.15),(Et-Sx).normalized(),q).normalized()
    WPA_=lerp(E('WPA',50),E('WPA1',8),q)
    fdir=vlerp((-s*0.1,0.0,1.0),(0.0,-0.05,1.0),q).normalized()             # forearm: up -> vertical under the hand
    Mh=hand_matrix(Ls,s,hd,want); reset_fingers(Ls); set_rot('hand.'+Ls,Mh)
    c=Vector(handrig.bar_from_hand(rig,Ls,rB)); doff=c-Vector(pb['hand.'+Ls].head)
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
grips={}
for Ls in 'LR':
    M_,kn,n_,eh=handrig.palm_frame(rig,Ls); c=Vector(handrig.bar_from_hand(rig,Ls,rB))
    handrig.wrap2(rig,Ls,c,kn,rB); handrig.thumb_over(rig,Ls,c,kn,rB)
    grips[Ls]=(c,kn.normalized())
for n in ('Barra','Discos'):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render=True; bpy.data.objects[n].hide_viewport=True
md.show_viewport=True
import skinstack as D_skin
D_skin.build(hi,rig,md,E)
import pulldown_geo
pulldown_geo.build(hi,rig,grips,rB,q,HT,HB,cdir,E)
bpy.ops.wm.save_as_mainfile(filepath=out)
