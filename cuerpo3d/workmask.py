# Worked-muscle mask 'work' (POINT float 0..1) on the rest body, for the red gradient highlight.
# Muscles are placed anatomically around the limb bones (no texture needed):
#   hamstrings  : back of the thigh, from under the buttock (ischial tuberosity) to behind the knee, posterior +-80 deg
#                 (biceps femoris on the outer-back side, semitendinosus/membranosus on the inner-back side)
#   calves      : gastrocnemius, back of the lower leg from just above the knee to mid-calf
#   quads, glutes, biceps, triceps, delts, pecs, lats : available for other exercises
# The value peaks in the muscle belly and fades to the borders (natural gradient), is a little stronger on the
# bulges of the relief and weaker in the grooves, with a very soft fibre texture along the muscle.
# usage: MUSCLES=hams:1,calves:0.7 python -I workmask.py in.blend out.blend
import bpy,sys,os,math
import numpy as np, scipy.sparse as sp
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
ss=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices); bb=bpy.data.objects['Rig'].data.bones
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1; Av=sp.diags(1/deg)@A
def lapsm(X,n):
    for _ in range(n): X=0.5*X+0.5*(Av@X)
    return X
gi={g.index:g.name for g in hi.vertex_groups}
def wsum(pref):
    w=np.zeros(nv)
    for v in me.vertices:
        for g in v.groups:
            if gi[g.group].startswith(pref): w[v.index]+=g.weight
    return w
def limb(bn,ref=np.array((0,1.0,0))):
    """t along the bone (0 head..1 tail), angle (deg) around the bone measured from direction ref, radius"""
    a=np.array(bb[bn].head_local); b=np.array(bb[bn].tail_local); d=b-a; L=np.linalg.norm(d); u=d/L
    rel=co-a; t=rel@u/L; rad=rel-np.outer(rel@u,u); r=np.linalg.norm(rad,axis=1)
    e1=ref-u*(ref@u); e1/=np.linalg.norm(e1); e2=np.cross(u,e1)
    ang=np.degrees(np.arctan2(rad@e2,rad@e1)); return t,ang,r,e2
def bump(t,t0,t1,pw=0.8):
    x=np.clip((t-t0)/(t1-t0),0,1); return np.sin(np.pi*x)**pw
# relief (bulges +, grooves -) as in musculo.py
S1=lapsm(co,6); S2=lapsm(co,150)
me.vertices.foreach_set('co',S2.ravel()); me.update(); n2=np.zeros(nv*3); me.vertices.foreach_get('normal',n2); n2=n2.reshape(-1,3)
me.vertices.foreach_set('co',co.ravel()); me.update()
h=((S1-S2)*n2).sum(1); h=h-lapsm(h,500); hn=np.clip(h/E('HN',0.004),-1,1)
work=np.zeros(nv)
spec=dict(x.split(':') for x in os.environ.get('MUSCLES','hams:1,calves:0.7').split(','))
for L,s in (('L',1),('R',-1)):
    side=(co[:,0]*s>0)
    w_th=wsum('thigh.'+L); w_sh=wsum('shin.'+L)
    if 'hams' in spec:
        t,ang,r,e2=limb('thigh.'+L)               # ref +Y = back of the thigh
        # outer side is +x for L: rotate so that the band leans a little to the outside (biceps femoris)
        lat=np.sign((e2*np.array((s,0,0))).sum())  # +1 if e2 points outwards
        a=ang*lat                                    # >0 = outer-back
        f=bump(t,E('HT0',0.10),E('HT1',1.00))*(1-ss((np.abs(a-E('HSH',10))-E('HA0',55))/E('HAW',35)))
        fib=1-E('FIB',0.10)*(0.5+0.5*np.cos(2*np.pi*np.radians(ang)*r/E('FIBW',0.011)))
        work=np.maximum(work,float(spec['hams'])*f*fib*np.clip(w_th*1.5,0,1)*side)
    if 'calves' in spec:
        t,ang,r,e2=limb('shin.'+L)
        f=bump(t,E('CT0',-0.06),E('CT1',0.58),0.7)*(1-ss((np.abs(ang)-E('CA0',60))/E('CAW',30)))
        fib=1-E('FIB',0.10)*(0.5+0.5*np.cos(2*np.pi*np.radians(ang)*r/E('FIBW',0.011)))
        work=np.maximum(work,float(spec['calves'])*f*fib*np.clip((w_sh+w_th)*1.5,0,1)*side)
    if 'quads' in spec:
        t,ang,r,e2=limb('thigh.'+L,np.array((0,-1.0,0)))
        f=bump(t,0.12,1.02)*(1-ss((np.abs(ang)-70)/35))
        work=np.maximum(work,float(spec['quads'])*f*np.clip(w_th*1.5,0,1)*side)
# ---- back and arm muscles (rest pose, body faces -Y, back is +Y)
nrm=np.zeros(nv*3); me.vertices.foreach_get('normal',nrm); nrm=nrm.reshape(-1,3)
w_arm=wsum(('upper_arm','forearm','fa_tw','hand','delt'))
X=np.abs(co[:,0]); Z=co[:,2]
def poly_soft(px,pz,poly,edge):
    """soft inside-mask of a polygon in the (|x|,z) plane: 0 outside, ramps to 1 over 'edge' metres inside"""
    poly=np.array(poly); n=len(poly); inside=np.zeros(len(px),bool); dmin=np.full(len(px),1e9)
    for i in range(n):
        a=poly[i]; b=poly[(i+1)%n]
        cond=((a[1]>pz)!=(b[1]>pz)); xi=a[0]+(pz-a[1])*(b[0]-a[0])/(b[1]-a[1]+1e-12)
        inside^=cond&(px<xi)
        ab=b-a; t=np.clip(((px-a[0])*ab[0]+(pz-a[1])*ab[1])/(ab@ab),0,1)
        dmin=np.minimum(dmin,np.hypot(px-(a[0]+t*ab[0]),pz-(a[1]+t*ab[1])))
    return inside*ss(dmin/edge)
def belly(cx,cz,sx,sz): return np.exp(-((X-cx)/sx)**2-((Z-cz)/sz)**2)
back=ss((nrm[:,1]+E('BACKN',0.25))/0.35)                           # surfaces facing backwards (and the sides a little)
if 'lats' in spec:
    m=poly_soft(X,Z,[(0.025,1.21),(0.025,0.98),(0.13,0.975),(0.175,1.10),(0.165,1.29),(0.12,1.27)],E('LEDGE',0.035))
    work=np.maximum(work,float(spec['lats'])*m*(0.55+0.45*belly(0.12,1.13,0.06,0.10))*back*np.clip(1-1.6*w_arm,0,1))
if 'traps' in spec:   # middle/lower trapezius + rhomboids, between the shoulder blades
    m=poly_soft(X,Z,[(0.0,1.43),(0.07,1.42),(0.13,1.36),(0.09,1.22),(0.0,1.12)],E('TEDGE',0.03))
    work=np.maximum(work,float(spec['traps'])*m*(0.6+0.4*belly(0.05,1.32,0.05,0.08))*back*np.clip(1-1.6*w_arm,0,1))
if 'reardelt' in spec:
    for L_,s_ in (('L',1),('R',-1)):
        c=np.array(bb['upper_arm.'+L_].head_local)+np.array((s_*0.02,0.035,-0.025))
        g=np.exp(-np.sum((co-c)**2,1)/(2*E('RDS',0.035)**2))*ss((nrm[:,1]+0.1)/0.4)
        work=np.maximum(work,float(spec['reardelt'])*ss(g/0.8))
if 'biceps' in spec:
    for L_,s_ in (('L',1),('R',-1)):
        t,ang,r,e2=limb('upper_arm.'+L_,np.array((0,-1.0,0)))
        f=bump(t,0.22,0.95)*(1-ss((np.abs(ang)-55)/30))
        work=np.maximum(work,float(spec['biceps'])*f*np.clip(wsum('upper_arm.'+L_)*1.5,0,1)*(co[:,0]*s_>0))
work=work*(1+E('RELK',0.30)*hn)
work=np.clip(lapsm(work,int(E('WSM',8))),0,1)
a=me.attributes.get('work') or me.attributes.new('work','FLOAT','POINT')
a.data.foreach_set('value',work.astype(np.float32))
print('work verts >0.5:',int((work>0.5).sum()),'max %.2f'%work.max())
bpy.ops.wm.save_as_mainfile(filepath=out)
