# Give the mannequin a face: the original detailed head of the Blender "Human Base Meshes" realistic male body (CC0, the
# body our mannequin was made from: same proportions) is added as object 'Cabeza' (+ eyeballs 'Ojo.L', 'Ojo.R'),
# skinned with the body's own weights so it moves exactly like the neck/head. The smooth mannequin head of 'Hi' is pushed
# inside it (topology unchanged, so the muscle atlas and maps stay valid). The renderer snaps the lowest band of the head
# onto the neck (attribute 'snapw') so the joint does not show, and darkens hair / eyebrows / irises with 'tint'.
#   python -I facebuild.py BUNDLE.blend base.blend out.blend     env: CUTZ (1.44), CUTSL (0.32), LEVEL (2), CAPIN (mm, 12)
import bpy, sys, os, math, numpy as np
from mathutils import Vector
from scipy.spatial import cKDTree
E=lambda k,d: float(os.environ.get(k,d))
bun,src,out=sys.argv[-3],sys.argv[-2],sys.argv[-1]
DX=None                                           # the source body sits ~2.26 m to the side in the bundle (exact value from its matrix)
cutz=lambda y: E('CUTZ',1.44)+E('CUTSL',0.32)*(y+0.08)   # tilted cut through the neck (same tilt as headcap.py, 1.5 cm lower)
# ---------------- 1. source head (multires applied) + eyes, from the bundle
bpy.ops.wm.open_mainfile(filepath=bun)
SRCB=os.environ.get('SRCBODY','GEO-body_male_realistic')
o=bpy.data.objects[SRCB]; o.modifiers[0].levels=int(E('LEVEL',2))
dg=bpy.context.evaluated_depsgraph_get(); me=o.evaluated_get(dg).to_mesh()
M=np.array(o.matrix_world); DX=-M[0,3]; print('source offset x %.5f'%DX)
co=np.array([v.co[:] for v in me.vertices]); co=co@M[:3,:3].T+M[:3,3]; co[:,0]+=DX
# ears: face sets of the source mesh (base level) -> per vertex mask, carried to the multires surface by nearest vertex
bm0=o.data; fsv=np.zeros(len(bm0.polygons),int); bm0.attributes['.sculpt_face_set'].data.foreach_get('value',fsv)
b0=np.array([v.co[:] for v in bm0.vertices])@M[:3,:3].T+M[:3,3]; b0[:,0]+=DX
emask0=np.zeros(len(b0))
for p_,f_ in zip(bm0.polygons,fsv):
    if f_ in [int(x) for x in os.environ.get('EARFS','4,5').split(',')]: emask0[list(p_.vertices)]=1.0
from scipy.spatial import cKDTree as _K
earm=emask0[_K(b0).query(co)[1]]
# clean straight cut (bisect along the tilted plane) instead of whole faces: no staircase edge
import bmesh
bm=bmesh.new(); bm.from_mesh(me)
for v,c_ in zip(bm.verts,co): v.co=c_
el_=bm.verts.layers.float.new('earm')
for v,e_ in zip(bm.verts,earm): v[el_]=float(e_)
far=[v for v in bm.verts if v.co.z<cutz(v.co.y)-0.06]; bmesh.ops.delete(bm,geom=far,context='VERTS')
pn=Vector((0,-E('CUTSL',0.32),1.0)).normalized(); pc=Vector((0,-0.08,E('CUTZ',1.44)))
geom=bm.verts[:]+bm.edges[:]+bm.faces[:]
bmesh.ops.bisect_plane(bm,geom=geom,plane_co=pc,plane_no=pn,clear_inner=True)
bm.verts.ensure_lookup_table()
hco=np.array([v.co[:] for v in bm.verts]); idx={v:i for i,v in enumerate(bm.verts)}; hear=np.array([v[el_] for v in bm.verts])
hfaces=[tuple(idx[v] for v in f.verts) for f in bm.faces]
bm.free()
eyes=[]
for n in (SRCB+'.eye.L',SRCB+'.eye.R'):
    e=bpy.data.objects[n]; em=e.evaluated_get(dg).to_mesh(); Me=np.array(e.matrix_world)
    ec=np.array([v.co[:] for v in em.vertices]); ec=ec@Me[:3,:3].T+Me[:3,3]; ec[:,0]+=DX
    eyes.append((n[-1],ec,[tuple(p.vertices) for p in em.polygons]))
print('head verts %d faces %d'%(len(hco),len(hfaces)))
# ---------------- 2. base file: new objects, weights from the body, cap pushed inside
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; rig=bpy.data.objects['Rig']; bme=hi.data; nv=len(bme.vertices)
bco=np.zeros(nv*3); bme.vertices.foreach_get('co',bco); bco=bco.reshape(-1,3)
bno=np.zeros(nv*3); bme.vertices.foreach_get('normal',bno); bno=bno.reshape(-1,3)
gname={g.index:g.name for g in hi.vertex_groups}
def body_weights(idx):
    w={}
    for g in bme.vertices[int(idx)].groups:
        n=gname[g.group]
        if n in rig.data.bones and g.weight>1e-4: w[n]=g.weight
    return w
R=np.load(os.environ.get('RESTNPZ',os.path.join(os.environ.get('GT3D','.'),'ill','rest.npz')),allow_pickle=True); main=np.array([str(m) for m in R['main']])
upper=np.isin(main,['head','neck','chest','clavicle.L','clavicle.R'])
kd=cKDTree(bco[upper]); upid=np.where(upper)[0]
def make(name,verts,faces):
    m=bpy.data.meshes.new(name); m.from_pydata([tuple(v) for v in verts],[],faces); m.update()
    ob=bpy.data.objects.new(name,m); bpy.context.scene.collection.objects.link(ob)
    for p in m.polygons: p.use_smooth=True
    return ob
FEM=os.environ.get('HAIRSTYLE','')=='bun' and E('FEMFACE',1)>0
if FEM:
    # feminine face (femface.py): narrower jaw and chin, shorter chin, fuller cheeks and lips, softer brow ridge, smaller
    # nose, eyes a little larger; slimmer neck (the same function is applied to the body's neck below)
    sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import femface
    ss_f=femface.ss
    # the face edits fade out before the band that is glued to the neck (1.2 cm): no crease at the joint
    hco,eyes=femface.deform(hco,hfaces,eyes,prot=ss_f((hco[:,2]-cutz(hco[:,1])-E('SNAPH',0.012))/0.02))
    hco=femface.neck_scale(hco,femface.neck_mask(hco))
cab=make('Cabeza',hco,hfaces)
# ---- hair (short, buzz cut) and eyebrows: darkness 'tint' for the renderer
ss_=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
hn=np.zeros(len(hco)*3); cab.data.vertices.foreach_get('normal',hn); hn=hn.reshape(-1,3)
# skin (no hair) region seen from the side, (y, z): forehead, temple, sideburn, around the ear, behind the ear, nape
SKIN=np.array([(-0.30,1.30),(-0.30,1.646),(-0.112,1.646),(-0.104,1.632),(-0.096,1.612),(-0.088,1.595),(-0.082,1.578),
               (-0.078,1.566),(-0.072,1.560),(-0.064,1.565),(-0.061,1.585),(-0.052,1.597),(-0.038,1.600),(-0.024,1.596),
               (-0.015,1.585),(-0.010,1.565),(-0.006,1.545),(0.002,1.525),(0.012,1.512),(0.030,1.506),(0.20,1.504),(0.20,1.30)])
# (measured on the head: ear y -0.058..-0.016, z 1.52..1.59; the hair comes down to ~5 mm from the ear)
def sdist(px,py,poly):
    """signed distance of points to a closed polygon (negative inside)"""
    x0,y0=poly[:,0],poly[:,1]; x1,y1=np.roll(x0,-1),np.roll(y0,-1)
    dmin=np.full(len(px),9.0); inside=np.zeros(len(px),bool)
    for i in range(len(poly)):
        ex,ey=x1[i]-x0[i],y1[i]-y0[i]; t=np.clip(((px-x0[i])*ex+(py-y0[i])*ey)/max(ex*ex+ey*ey,1e-12),0,1)
        dmin=np.minimum(dmin,np.hypot(px-(x0[i]+t*ex),py-(y0[i]+t*ey)))
        cr=((y0[i]>py)!=(y1[i]>py))&(px<(x1[i]-x0[i])*(py-y0[i])/np.where(y1[i]-y0[i]==0,1e-12,y1[i]-y0[i])+x0[i]); inside^=cr
    return np.where(inside,-dmin,dmin)
ax0=np.abs(hco[:,0])
rec=E('HREC',0.009)*ss_((ax0-0.018)/0.032)*(hco[:,1]<-0.10)          # temples recede a little (soft M shape)
ZO=E('ZOFF',0.0)
if os.environ.get('HAIRSTYLE','')=='bun':
    SKIN=np.array([(-0.30,1.30),(-0.30,1.641),(-0.114,1.641),(-0.106,1.630),(-0.097,1.613),(-0.089,1.596),(-0.082,1.582),
                   (-0.074,1.574),(-0.066,1.582),(-0.062,1.598),(-0.052,1.606),(-0.036,1.608),(-0.022,1.602),(-0.012,1.588),
                   (-0.006,1.565),(0.000,1.540),(0.010,1.520),(0.030,1.508),(0.20,1.504),(0.20,1.30)])
sd=sdist(hco[:,1],hco[:,2]-ZO-rec,SKIN)
hair=ss_((sd+E('HSOFT',0.0035))/(2*E('HSOFT',0.0035)))
hair=hair*(1.0-np.clip(hear*1.5,0,1))     # never on the ear itself
# eyebrows (owner's reference photo, 28-10-2026): thick, dense, almost straight, soft arch at the outer third, tail
# thinning and dropping a little; the head (next to the nose) lighter and fuzzy with hairs pointing up.
# 'bw' = coordinate across the hairs (mm) for the renderer's hair strokes; 'bmask' = brow amount
brow=np.zeros(len(hco)); bw=np.zeros(len(hco))
for sg in (1,-1):
    xs=sg*hco[:,0]
    u=(xs-E('BX0',0.011))/(E('BX1',0.062)-E('BX0',0.011)); uc=np.clip(u,0,1)
    if os.environ.get('HAIRSTYLE','')=='bun':      # female: thinner, more arched
        bot=E('BZB',1.5885)+ZO-E('BDROP',0.0003)+0.0026*ss_(uc/0.62)-0.0068*ss_((uc-0.62)/0.38)   # soft arch, head not low (no frown)
        top=bot+E('BTH',0.0060)*(1-0.50*uc)+0.001*ss_(uc/0.5)
    else:
        bot=E('BZB',1.5885)+ZO+0.003*uc-0.005*ss_((uc-0.7)/0.3)
        top=E('BZT',1.5965)+ZO+0.0025*ss_(uc/0.6)-0.0075*ss_((uc-0.6)/0.4)
    mid=0.5*(bot+top); half=0.5*(top-bot)*(0.55+0.45*ss_((1-uc)/0.15))     # rounded thin end of the tail
    inn=ss_((half-np.abs(hco[:,2]-mid))/E('BSOFT',0.0016)+0.5)
    inn*=ss_(u/0.16+0.35)*ss_((1-u)/0.05+0.2)                                 # fuzzy start, thin tail
    inn*=(0.72+0.28*ss_(uc/0.22))*(1-0.12*ss_((uc-0.8)/0.2))                 # lighter head, dense body
    inn*=(xs>0)*(hn[:,1]<-0.25)*(hco[:,1]<-0.09)
    ang=np.radians(80-55*ss_(uc/0.3)-12*ss_((uc-0.5)/0.5))                   # hair direction: up at the head, outwards
    w_=(-np.sin(ang)*(xs-0.035)+np.cos(ang)*(hco[:,2]-1.592-ZO))*1000.0      # small, continuous on each side (no jumps)
    bw[xs>0]=w_[xs>0]; brow=np.maximum(brow,inn)
a_=cab.data.attributes.new('bmask','FLOAT','POINT'); a_.data.foreach_set('value',brow.astype(np.float32))
a_=cab.data.attributes.new('bw','FLOAT','POINT'); a_.data.foreach_set('value',bw.astype(np.float32))
tint=np.maximum(hair*E('HAIRT',0.51),brow*E('BROWT',0.95))
if os.environ.get('HAIRSTYLE','')=='bun' and E('FEMFACE',1)>0:
    ss1=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
    # lips: a little darker (natural lip colour in a grey plate), upper lip thinner than the lower one
    # (28-10 v3) real lip shape: mouth line measured on the head (corners a little lower), upper lip with the cupid's bow
    # (two peaks, dip in the middle), fuller rounded lower lip, soft 0.8 mm edge; a thin darker mouth line
    W_=E('LIPW',0.0235); ax_=np.abs(hco[:,0])/W_; Zh=hco[:,2]
    zm=E('LIPZ',1.4673)-E('LIPDN',0.0015)*np.clip(np.abs(hco[:,0])/0.022,0,1.2)**2     # corners only a little lower (not sad)
    hu=(0.0088+0.0017*np.exp(-((np.abs(hco[:,0])-0.0058)/0.0030)**2))*np.clip(1-ax_**2.2,0,1)**0.65
    hl=0.0102*np.clip(1-ax_**2,0,1)**0.6
    lin=lambda t: np.clip(t,0,1)                      # linear ramps ~2 mm (wider than the mesh): smooth edge, no staircase
    lip=lin((zm+hu-Zh)/E('LIPS',0.0022)+0.5)*lin((Zh-zm+hl)/E('LIPS',0.0022)+0.5)*ss1((1-ax_)/0.10)
    lip=lip*(1+0.12*(Zh>zm))*(hn[:,1]<-0.3)*(hco[:,1]<-0.13)
    mline=np.exp(-((Zh-zm)/0.0011)**2)*ss1((1-ax_)/0.15)*(hn[:,1]<-0.1)*(hco[:,1]<-0.13)
    # lash line: dark along the upper lid margin (thicker towards the outer corner), lighter below
    lash=np.zeros(len(hco))
    for L_,ec_,ef_ in eyes:
        c_=ec_.mean(0); r_=np.linalg.norm(ec_-c_,axis=1).mean(); v_=hco-c_; d_=np.linalg.norm(v_,axis=1)
        near=ss1((r_+E('LASHD',0.0032)-d_)/0.0012)*(v_[:,1]<0)
        up=ss1(v_[:,2]/0.002); outer=0.75+0.25*ss1((np.sign(c_[0])*v_[:,0])/0.008)
        lash=np.maximum(lash,near*(up*outer*E('LASHT',0.92)+(1-up)*E('LASHB',0.35)))
    tint=np.maximum.reduce([tint,lip*E('LIPT',0.36),mline*E('MLINE',0.55),lash])
    print('lips verts',int((lip>0.5).sum()),'lash verts',int((lash>0.5).sum()))
# hair volume: pulled-back hair lies a few mm over the skull (fuller head, soft step at the hairline)
if E('HVOL',0)>0:
    hv=E('HVOL',0)/1000.0*hair*(0.6+0.4*np.clip((hco[:,2]-hco[:,2].min())/(hco[:,2].max()-hco[:,2].min()),0,1))
    hco=hco+hn*hv[:,None]; cab.data.vertices.foreach_set('co',hco.astype(np.float32).ravel()); cab.data.update()
# hair strands: across-strand coordinate 'hw' (mm) = angle around the axis head centre -> bun (strands run to the bun)
if os.environ.get('HAIRSTYLE','')=='bun':
    BC=np.array((0.0,E('BUNY',0.018),E('BUNZ',1.612)))         # bun centre (female head)
    HC=np.array((0.0,-0.045,1.53))
    ax=(BC-HC)/np.linalg.norm(BC-HC); e1=np.cross(ax,(1.0,0,0)); e1/=np.linalg.norm(e1); e2=np.cross(ax,e1)
    rv=hco-HC; phi=np.arctan2(rv@e2,rv@e1)
    hw=phi*90.0
    a_=cab.data.attributes.new('hmask','FLOAT','POINT'); a_.data.foreach_set('value',hair.astype(np.float32))
    a_=cab.data.attributes.new('hw','FLOAT','POINT'); a_.data.foreach_set('value',hw.astype(np.float32))
    # the bun: a slightly flattened ball of hair, twisted strands ('hw' around its own axis), on the head bone
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=E('BUNR',0.034),location=tuple(BC))
    bun=bpy.context.active_object; bun.name='Ojo.Mono'
    bc=np.array([v.co[:] for v in bun.data.vertices]); M_=np.array(bun.matrix_world); bc=bc@M_[:3,:3].T+M_[:3,3]
    rel=bc-BC; rel=rel-np.outer(rel@ax,ax)*(1-E('BUNFLAT',0.72))          # flattened along the axis
    bc=BC+rel; bun.matrix_world.identity()
    bun.data.vertices.foreach_set('co',bc.astype(np.float32).ravel()); bun.data.update()
    for p_ in bun.data.polygons: p_.use_smooth=True
    rv=bc-BC; ang_=np.arctan2(rv@e2,rv@e1); tw=(rv@ax)/E('BUNR',0.034)
    a_=bun.data.attributes.new('tint','FLOAT','POINT'); a_.data.foreach_set('value',np.full(len(bc),E('HAIRT',0.51),np.float32))
    a_=bun.data.attributes.new('hmask','FLOAT','POINT'); a_.data.foreach_set('value',np.ones(len(bc),np.float32))
    a_=bun.data.attributes.new('hw','FLOAT','POINT'); a_.data.foreach_set('value',((ang_+1.2*tw)*40.0).astype(np.float32))
    g=bun.vertex_groups.new(name='head'); g.add(list(range(len(bc))),1.0,'REPLACE')
    mb=bun.modifiers.new('Armature','ARMATURE'); mb.object=rig
a=cab.data.attributes.new('tint','FLOAT','POINT'); a.data.foreach_set('value',tint.astype(np.float32))
print('hair verts',int((hair>0.5).sum()),'brow verts',int((brow>0.5).sum()))
# weights: nearest body vertex of the ORIGINAL surface (neck band) / head bone for the face
d,ii=kd.query(hco); src_ids=upid[ii]
grp={}
for vi,bi in enumerate(src_ids):
    for n,wv in body_weights(bi).items():
        g=grp.get(n) or cab.vertex_groups.new(name=n); grp[n]=g; g.add([vi],wv,'REPLACE')
am=cab.modifiers.new('Armature','ARMATURE'); am.object=rig
# snap band: 1 at the cut edge -> 0 at 1.2 cm above it
h=hco[:,2]-cutz(hco[:,1]); snapw=np.clip(1-h/E('SNAPH',0.012),0,1); snapw=snapw*snapw*(3-2*snapw)
a=cab.data.attributes.new('snapw','FLOAT','POINT'); a.data.foreach_set('value',snapw.astype(np.float32))
for L,ec,ef in eyes:
    ob=make('Ojo.'+L,ec,ef)
    bpy.context.view_layer.objects.active=ob; sm=ob.modifiers.new('s','SUBSURF'); sm.levels=int(E('EYESUB',3))
    bpy.ops.object.modifier_apply(modifier='s'); ec=np.array([v.co[:] for v in ob.data.vertices])
    g=ob.vertex_groups.new(name='head'); g.add(list(range(len(ec))),1.0,'REPLACE')
    m2=ob.modifiers.new('Armature','ARMATURE'); m2.object=rig
    c=ec.mean(0); r=np.linalg.norm(ec-c,axis=1).mean(); fwd=np.array((0,-1.0,0))
    cosang=((ec-c)@fwd)/np.maximum(np.linalg.norm(ec-c,axis=1),1e-9)
    ang=np.degrees(np.arccos(np.clip(cosang,-1,1)))
    # iris (~11 mm wide on a 24 mm eye ~ 27 deg) and pupil (~10 deg): darkness for the renderer's 'tint'
    sm_=lambda a,b,x: np.clip((x-a)/(b-a),0,1)**2*(3-2*np.clip((x-a)/(b-a),0,1))
    t=0.45*(1-sm_(E('IRISA',27)-1.5,E('IRISA',27)+1.0,ang))+0.42*(1-sm_(E('PUPA',10)-1.0,E('PUPA',10)+1.0,ang))
    a=ob.data.attributes.new('tint','FLOAT','POINT'); a.data.foreach_set('value',t.astype(np.float32))
    print('eye',L,'centre',np.round(c,3),'r %.4f'%r)
# body cap pushed inside the new head: from 0.8 cm above the cut, up to CAPIN mm (smooth), only the head region
hb=np.isin(main,['head','neck'])
hh=bco[:,2]-cutz(bco[:,1])
push=np.clip((hh-E('CAP0',0.008))/(E('CAP1',0.03)-E('CAP0',0.008)),0,1); push=push*push*(3-2*push)*hb
bco=bco-bno*(push[:,None]*E('CAPIN',12)/1000.0)
if FEM: bco=femface.neck_scale(bco,femface.neck_mask(bco))
# guarantee: no vertex of the old cap pokes through the new head (keep it >= CAPMIN mm inside)
from mathutils.bvhtree import BVHTree
_bv=BVHTree.FromPolygons([tuple(v) for v in hco],[tuple(f) for f in hfaces])
moved_=0
for i in np.where(hb&(hh>E('CAP0',0.008)))[0]:
    loc,nrm,_,dist=_bv.find_nearest(Vector(bco[i]))
    if loc is None: continue
    sdist_=(bco[i]-np.array(loc))@np.array(nrm)
    if sdist_>-E('CAPMIN',3)/1000.0: bco[i]=np.array(loc)-np.array(nrm)*E('CAPMIN',3)/1000.0; moved_+=1
print('cap verts clamped inside',moved_)
bme.vertices.foreach_set('co',bco.ravel()); bme.update()
print('cap verts pushed',int((push>0.01).sum()))
bpy.ops.wm.save_as_mainfile(filepath=out)
