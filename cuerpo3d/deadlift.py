# CONVENTIONAL BARBELL DEADLIFT frame (made from barrow.py): P=0 bar on the floor (45 cm plates touching the ground,
# hips back, flat back, shoulders a little ahead of the bar) -> P=1 standing lockout. Feet fixed, the bar goes straight
# up over the mid-foot, arms hang straight; knees extend first, then the hips (the back angle holds until the bar
# passes the knees). Knee bend at the bottom is solved so that the plates touch the floor.
# usage: SKIN=cor P=0.5 python deadlift.py NB_mc_row.blend out.blend   (source agarre_final.env, BARUNI=0)
import bpy,sys,math,os,json
import numpy as np
from mathutils import Vector,Matrix,Quaternion
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,os.environ.get('SCR',os.environ.get('GT3D','/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad')+''))
import handrig
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
P=E('P',0.0)
ease=lambda t: t*t*(3-2*t); q=0.0   # arms always hang (no pull)
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

cl=lambda t: max(0.0,min(1.0,t))
LEAN0=E('LEAN0',55); KDEL=E('KDEL',0.12); HSPAN=E('HSPAN',0.75)
kph=ease(cl(P/E('KSPAN',0.70)))                 # knees: extend from the start
hph=ease(cl((P-KDEL)/(1.0-KDEL)))               # hips: start a bit later
LEAN=LEAN0*(1-hph)+E('LEAN1',0)*hph
Rp=Matrix.Rotation(math.radians(LEAN),3,'X')
GRIPX=E('GRIPX',0.25); KF=0.0
os.environ.setdefault('NECKT',str(E('NECK0',-28)*LEAN/max(LEAN0,1e-6)))
os.environ.setdefault('SPEXT',str(E('SPX1',6)+(E('SPX0',16)-E('SPX1',6))*LEAN/max(LEAN0,1e-6)))
def legs(at):
    global KF
    for s,Ls in ((1,'L'),(-1,'R')):
        a=math.radians(at); b=math.radians(KF-at)
        aim('thigh.'+Ls,(s*0.06,-math.sin(a)*math.cos(Rp.to_euler().x*0)+0,-math.cos(a)))
        aim('shin.'+Ls,(s*0.03,math.sin(b),-math.cos(b)))
        aim('foot.'+Ls,(s*0.12,-1.0,-0.22))
def pose_body(loc,at,qq=None):
    qq=q if qq is None else qq
    hb=pb['hips']; R0h=R0['hips']
    hb.rotation_mode='QUATERNION'; hb.rotation_quaternion=(R0h.inverted()@Rp@R0h).to_quaternion()
    hb.location=R0h.inverted()@loc; upd()
    for bn,frac in (('spine',0.45),('chest',0.55)):         # back extension: flat/arched back, chest out (hip hinge, not a rounded back)
        if bn in pb and E('SPEXT',0)!=0:
            R0b=R0[bn]; pb[bn].rotation_mode='QUATERNION'
            pb[bn].rotation_quaternion=(R0b.inverted()@Matrix.Rotation(math.radians(-E('SPEXT',0)*frac),3,'X')@R0b).to_quaternion()
    upd()
    for bn,fr in (('neck',0.5),('head',0.5)):              # neutral neck, eyes a little ahead on the floor
        pb[bn].rotation_mode='QUATERNION'; pb[bn].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[bn].tail)-Vector(pb[bn].head); aim(bn,Matrix.Rotation(math.radians(-E('NECKT',14)*fr),3,'X')@d0)
    clv=lerp(E('CLV0',-4),E('CLV1',-8),qq); clr=lerp(E('CLR0',-6),E('CLR1',16),qq)   # shoulder blades: spread at the bottom, squeezed at the top
    for s,Ls in ((1,'L'),(-1,'R')):
        n='clavicle.'+Ls; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[n].tail)-Vector(pb[n].head)
        aim(n,(Rp@Matrix.Rotation(math.radians(s*clr),3,'Z')@Matrix.Rotation(math.radians(-s*clv),3,'Y')@Rp.inverted())@d0)
    legs(at)
# rest vertex at the lower end of the sternum (where the bar touches)
C0=np.zeros(len(hi.data.vertices)*3); hi.data.vertices.foreach_get('co',C0); C0=C0.reshape(-1,3)
cand=np.where((np.abs(C0[:,0])<0.02)&(np.abs(C0[:,2]-E('TOUCHZ',1.13))<0.012))[0]; vT=int(cand[np.argmin(C0[cand,1])])
def posed_point(i):
    md.show_viewport=True; upd(); dg=bpy.context.evaluated_depsgraph_get(); mm=hi.evaluated_get(dg).to_mesh()
    v=Vector(mm.vertices[i].co); hi.evaluated_get(dg).to_mesh_clear(); md.show_viewport=False; return v
# stance: ankle fixed at y=0, z=ANKZ; for a given knee bend the thigh angle is chosen so that the shoulders sit over
# the bar (mid-foot, MIDF ahead of the ankle) + SHDY (shoulders a bit ahead at the bottom)
def solve_at(kf,shdy):
    global KF
    KF=kf
    def err(at10):
        pose_body(Vector((0,0,0)),at10,0.0)
        sh_=(Vector(pb['upper_arm.L'].head)+Vector(pb['upper_arm.R'].head))/2
        an_=(Vector(pb['shin.L'].tail)+Vector(pb['shin.R'].tail))/2
        return abs((sh_.y-an_.y)-(-E('MIDF',0.05)+shdy))
    c=min(np.arange(E('ATMIN',-6),E('ATMAX',100),3.0),key=err)
    return min(np.arange(c-3,c+3.01,0.5),key=err)
def place(kf,shdy):
    at=solve_at(kf,shdy); pose_body(Vector((0,0,0)),at,0.0)
    an_=(Vector(pb['shin.L'].tail)+Vector(pb['shin.R'].tail))/2
    lc=Vector((0,-an_.y,E('ANKZ',0.075)-an_.z)); pose_body(lc,at,0.0); return at,lc
YBAR=-E('MIDF',0.05)
def bar_z_hang():
    reset_fingers('L'); set_rot('hand.L',hand_matrix('L',1,Vector((0,E('HDY',0.0),-1)).normalized(),Vector((-1,0,0))))
    doff_=Vector(handrig.bar_from_hand(rig,'L',rB))-Vector(pb['hand.L'].head)
    S_=Vector(pb['upper_arm.L'].head)
    dh=math.sqrt(Lu*Lu+Lf*Lf+2*Lu*Lf*math.cos(math.radians(E('FLEX0',6))))
    vx=GRIPX-doff_.x-abs(S_.x); vy=S_.y-YBAR+doff_.y*0-doff_.y
    return S_.z+doff_.z-math.sqrt(max(dh*dh-vx*vx-vy*vy,0.0))
# ---------------- bar path: arms hanging -> touch under the lower chest (vertical path under the shoulders)
def hand_matrix(L,s,hd,want):
    A=frame(hd,want); B=frame(Vector((0,1,0)),rest[L]['kn_loc']); return A@B.transposed()
def reset_fingers(L):
    for n in [x for x in pb.keys() if x.endswith('.'+L) and x.split('.')[0][:-1] in ('thumb','index','middle','ring','pinky')]:
        pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0)
def arm_candidates(L,s,S,W,Mh,Mcl):
    r=rest[L]; d=(W-S).length; dmax=(Lu+Lf)*0.9995; d=min(d,dmax)
    u=(W-S).normalized(); a=(Lu*Lu-Lf*Lf+d*d)/(2*d); h=math.sqrt(max(Lu*Lu-a*a,0.0))
    e1=Vector((0,0,1)).cross(u); e1=e1.normalized() if e1.length>1e-6 else Vector((1,0,0)); e2=u.cross(e1)
    pref=Vector((s*E('PEX',0.45),E('PEY',1.0),E('PEZ',0.35))).normalized()   # elbows back (towards the hips), a little out and up
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
        fv=math.degrees(y2.angle(Vector((0,0,-1))))       # forearm close to vertical (the pulling line) when the elbow is bent
        bentw=min(1.0,math.degrees(th)/60.0)   # forearms hang vertically under the elbows when pulling
        cost=(tu/E('WTU',100))**2+(tf/E('WTF',45))**2+(pa/E('WPA',50))**2+bentw*(fv/E('WFV',25))**2
        out.append((cost,ph,El,Mua,Mfa,tu,tf,pa,math.degrees(th),fv))
    return min(out,key=lambda t:t[0])

SHDY0=E('SHDY',-0.03)
z_floor=E('PLATER',0.225)
Rp_frame=Rp; env_frame=(os.environ['NECKT'],os.environ['SPEXT'])
Rp=Matrix.Rotation(math.radians(LEAN0),3,'X'); os.environ['NECKT']=str(E('NECK0',-28)); os.environ['SPEXT']=str(E('SPX0',16))
lo,hi_=E('KFMIN',20),E('KFMAX',130)
for it in range(9):                      # bar height falls as the knees bend: bisection
    kk=0.5*(lo+hi_); place(kk,SHDY0); zh=bar_z_hang()
    if zh>z_floor: lo=kk
    else: hi_=kk
KF0=(0,kk,zh)
Rp=Rp_frame; os.environ['NECKT'],os.environ['SPEXT']=env_frame
print('bottom knee bend %.0f bar z %.3f (want %.3f)'%(KF0[1],KF0[2],z_floor))
kf=KF0[1]*(1-kph)+E('KF1',3)*kph
AT,loc=place(kf,SHDY0*(1-hph))
sh={s:Vector(pb['upper_arm.'+Ls].head) for s,Ls in ((1,'L'),(-1,'R'))}
zb=bar_z_hang() if P>0 else KF0[2]
if P>0: zb=max(zb,z_floor)
# the bar must never go into the legs: if the skin in front of the legs at bar height is ahead of the bar line,
# the bar moves forward to just touch it (it slides along the thighs at the top, as in a real deadlift)
_R=np.load(os.path.join(os.environ.get('GT3D',os.path.dirname(os.path.abspath(__file__))),'ill','rest.npz'),allow_pickle=True)
_legs=np.isin(np.array([str(m) for m in _R['main']]),['thigh.L','thigh.R','shin.L','shin.R','hips','foot.L','foot.R'])
def leg_front(z):
    md.show_viewport=True; upd(); dg=bpy.context.evaluated_depsgraph_get(); ev=hi.evaluated_get(dg); mm=ev.to_mesh()
    co=np.zeros(len(mm.vertices)*3); mm.vertices.foreach_get('co',co); co=co.reshape(-1,3); ev.to_mesh_clear(); md.show_viewport=False
    if len(co)!=len(_legs): return None
    band=_legs&(np.abs(co[:,0])<E('LEGX',0.30))&(np.abs(co[:,2]-z)<rB+E('GAP',0.006))
    if not band.any(): return None
    # nearest skin to the bar circle: the most forward point, corrected for its height offset from the bar axis
    dz=np.clip(np.abs(co[band,2]-z),0,rB+E('GAP',0.006)); reach=np.sqrt(np.maximum((rB+E('GAP',0.006))**2-dz*dz,0))
    return float(np.min(co[band,1]-reach))
YBAR0=YBAR
for it in range(3):
    fy=leg_front(zb)
    YBAR=YBAR0 if fy is None else min(YBAR0,fy)
    if P>0: zb=max(bar_z_hang(),z_floor)
print('bar y %.3f (line %.3f)'%(YBAR,YBAR0))
BAR=Vector((0,YBAR,zb))
hd0=Vector((0,E('HDY',0.0),-1)).normalized()
print('P %.3f lean %.1f knee %.1f thigh %.1f bar z %.3f'%(P,LEAN,kf,AT,BAR.z))
HAX=Vector((1,0,0)); res={}
for s,Ls in ((1,'L'),(-1,'R')):
    Sx=sh[s]; Mcl=pb['clavicle.'+Ls].matrix.to_3x3(); hd=hd0; y2=None
    for it in range(4):
        hdd=hd if y2 is None else (hd*(1-E('HFOL',0.5))+y2*E('HFOL',0.5)).normalized()
        Mh=hand_matrix(Ls,s,hdd,Vector((-s,0,0))); reset_fingers(Ls); set_rot('hand.'+Ls,Mh)
        c=Vector(handrig.bar_from_hand(rig,Ls,rB)); doff=c-Vector(pb['hand.'+Ls].head)
        W=Vector((s*GRIPX,BAR.y,BAR.z))-doff
        best=arm_candidates(Ls,s,Sx,W,Mh,Mcl); y2=(W-best[2]).normalized()
    res[Ls]=(best,Mh,W,Sx)
for s,Ls in ((1,'L'),(-1,'R')):
    (cost,ph,El,Mua,Mfa,tu,tf,pa,th,fv),Mh,W,Sx=res[Ls]
    set_rot('upper_arm.'+Ls,Mua); set_rot('forearm.'+Ls,Mfa)
    for n in twb[Ls]:
        f=TWF[n.split('.')[0]]; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=Quaternion((0,1,0),math.radians(tf*f))
    set_rot('hand.'+Ls,Mh); upd()
    print(f"{Ls} elbow flex {th:5.1f} humeral twist {tu:+6.1f} pronation {tf:+6.1f} forearm-vs-vertical {fv:4.0f} reach err {(Vector(pb['forearm.'+Ls].tail)-W).length*1000:.1f}mm")
Bc=Vector((0,BAR.y,BAR.z)); axis=Vector((1,0,0))
for Ls in 'LR':
    handrig.wrap2(rig,Ls,Bc,axis,rB)
    if os.environ.get('TMODE','over')=='over': handrig.thumb_over(rig,Ls,Bc,axis,rB)
handrig.place_bar(Bc,axis,rB,hide_discs=False)
md.show_viewport=True
import skinstack as D_skin
D_skin.build(hi,rig,md,E)
bpy.ops.wm.save_as_mainfile(filepath=out)
