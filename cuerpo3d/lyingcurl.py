# LYING (PRONE) LEG CURL frame, as in the owner's example: prone on an angled bench (hips highest, separate lower chest
# pad), hands on the front handles, roller behind the ankles, knees curl from almost straight (P=0) to ~105 deg (P=1).
# Hamstrings/calves highlighted with the 'work' attribute (base NB_mc_hs.blend). Machine built around the body.
# usage: SKIN=cor P=0.5 python lyingcurl.py NB_mc_hs.blend out.blend   (source agarre_final.env)
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

TT=E('TTILT',20)                        # torso head-down tilt from horizontal (deg)
Rb=Matrix.Rotation(math.radians(90+TT),3,'X')   # prone: head towards -Y, face down, head lower than the hips
HZ=E('HZ',1.00)                          # hip joint height
FLEX=lerp(E('FLEX0',10),E('FLEX1',105),q)
TH=math.radians(E('THS',17))             # thighs slope down towards the knees
def bodyrot(Rl): return Rb@Rl@Rb.inverted()
def pose_body(loc):
    hb=pb['hips']; R0h=R0['hips']
    hb.rotation_mode='QUATERNION'; hb.rotation_quaternion=(R0h.inverted()@Rb@R0h).to_quaternion()
    hb.location=R0h.inverted()@loc; upd()
    for bn,fr in (('neck',0.55),('head',0.45)):              # head up a little, looking forward-down
        pb[bn].rotation_mode='QUATERNION'; pb[bn].rotation_quaternion=(1,0,0,0); upd()
        d0=Vector(pb[bn].tail)-Vector(pb[bn].head); aim(bn,bodyrot(Matrix.Rotation(math.radians(-E('NECKT',38)*fr),3,'X'))@d0)
    for s,Ls in ((1,'L'),(-1,'R')):
        t=Vector((s*E('TX',0.03),math.cos(TH),-math.sin(TH))).normalized(); aim('thigh.'+Ls,t)
        up=Vector((0,0,1)); post=(up-t*(up@t)).normalized()                 # back of the thigh (faces up)
        f=math.radians(FLEX); sd=(t*math.cos(f)+post*math.sin(f)).normalized(); aim('shin.'+Ls,sd)
        ps=(post*math.cos(f)-t*math.sin(f)).normalized()                     # back of the shin (calf side)
        d=math.radians(E('PLANT',35)); fd=(-ps*math.cos(d)+sd*math.sin(d)).normalized(); aim('foot.'+Ls,fd)
pose_body(Vector((0,0,0)))
hj=(Vector(pb['thigh.L'].head)+Vector(pb['thigh.R'].head))/2
loc=Vector((0,-hj.y,HZ-hj.z)); pose_body(loc)
KNEE={s:Vector(pb['shin.'+Ls].head) for s,Ls in ((1,'L'),(-1,'R'))}
SHIN={s:(Vector(pb['shin.'+Ls].tail)-Vector(pb['shin.'+Ls].head)).normalized() for s,Ls in ((1,'L'),(-1,'R'))}
# ---------------- hands on the front handles (pronated, handle along X)
def hand_matrix(L,s,hd,want):
    A=frame(hd,want); B=frame(Vector((0,1,0)),rest[L]['kn_loc']); return A@B.transposed()
def reset_fingers(L):
    for n in [x for x in pb.keys() if x.endswith('.'+L) and x.split('.')[0][:-1] in ('thumb','index','middle','ring','pinky')]:
        pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=(1,0,0,0)
def arm_candidates(L,s,S,W,Mh,Mcl):
    r=rest[L]; d=(W-S).length; dmax=(Lu+Lf)*0.9995; d=min(d,dmax)
    u=(W-S).normalized(); a=(Lu*Lu-Lf*Lf+d*d)/(2*d); h=math.sqrt(max(Lu*Lu-a*a,0.0))
    e1=Vector((0,0,1)).cross(u); e1=e1.normalized() if e1.length>1e-6 else Vector((1,0,0)); e2=u.cross(e1)
    pref=Vector((s*E('PEX',1.0),E('PEY',0.4),E('PEZ',-0.6))).normalized()   # elbows out, towards the hips and down
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
        bentw=0.0   # arms hang: no forearm-vertical preference
        cost=(tu/E('WTU',100))**2+(tf/E('WTF',45))**2+(pa/E('WPA',50))**2+bentw*(fv/E('WFV',25))**2
        out.append((cost,ph,El,Mua,Mfa,tu,tf,pa,math.degrees(th),fv))
    return min(out,key=lambda t:t[0])

HAX=Vector((1,0,0)); HANDLE={}; res={}
d_arm=math.sqrt(Lu*Lu+Lf*Lf+2*Lu*Lf*math.cos(math.radians(E('FLEXA',95))))
for s,Ls in ((1,'L'),(-1,'R')):
    S=Vector(pb['upper_arm.'+Ls].head); Mcl=pb['clavicle.'+Ls].matrix.to_3x3()
    hd=Vector((0,-E('HDY',0.6),-1)).normalized(); want=Vector((-s,0,0))
    Mh=hand_matrix(Ls,s,hd,want); reset_fingers(Ls); set_rot('hand.'+Ls,Mh)
    c=Vector(handrig.bar_from_hand(rig,Ls,rB)); doff=c-Vector(pb['hand.'+Ls].head)
    dr=Vector((s*E('HXD',0.15),-E('HYD',0.55),-1.0)).normalized()             # from the shoulder: forward (to the head) and down
    W=S+dr*d_arm; HANDLE[s]=W+doff
    best=arm_candidates(Ls,s,S,W,Mh,Mcl); res[Ls]=(best,Mh,W,S)
for s,Ls in ((1,'L'),(-1,'R')):
    (cost,ph,El,Mua,Mfa,tu,tf,pa,th,fv),Mh,W,S=res[Ls]
    set_rot('upper_arm.'+Ls,Mua); set_rot('forearm.'+Ls,Mfa)
    for n in twb[Ls]:
        f=TWF[n.split('.')[0]]; pb[n].rotation_mode='QUATERNION'; pb[n].rotation_quaternion=Quaternion((0,1,0),math.radians(tf*f))
    set_rot('hand.'+Ls,Mh); upd()
    info,err=handrig.wrap2(rig,Ls,HANDLE[s],HAX,rB)
    if os.environ.get('TMODE','over')=='over': handrig.thumb_over(rig,Ls,HANDLE[s],HAX,rB)
    print(f"{Ls} elbow flex {th:5.1f} humeral twist {tu:+6.1f} pronation {tf:+6.1f} handle {tuple(round(x,3) for x in HANDLE[s])}")
print('P',P,'knee flex',round(FLEX,1))
for n in ('Barra','Discos'):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render=True
md.show_viewport=True
import skinstack as D_skin
D_skin.build(hi,rig,md,E)
import lyingcurl_geo
lyingcurl_geo.build(hi,rig,KNEE,SHIN,HANDLE,Rb,TH,E)
bpy.ops.wm.save_as_mainfile(filepath=out)
