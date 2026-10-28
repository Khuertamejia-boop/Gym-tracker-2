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
o=bpy.data.objects['GEO-body_male_realistic']; o.modifiers[0].levels=int(E('LEVEL',2))
dg=bpy.context.evaluated_depsgraph_get(); me=o.evaluated_get(dg).to_mesh()
M=np.array(o.matrix_world); DX=-M[0,3]; print('source offset x %.5f'%DX)
co=np.array([v.co[:] for v in me.vertices]); co=co@M[:3,:3].T+M[:3,3]; co[:,0]+=DX
# clean straight cut (bisect along the tilted plane) instead of whole faces: no staircase edge
import bmesh
bm=bmesh.new(); bm.from_mesh(me)
for v,c_ in zip(bm.verts,co): v.co=c_
far=[v for v in bm.verts if v.co.z<cutz(v.co.y)-0.06]; bmesh.ops.delete(bm,geom=far,context='VERTS')
pn=Vector((0,-E('CUTSL',0.32),1.0)).normalized(); pc=Vector((0,-0.08,E('CUTZ',1.44)))
geom=bm.verts[:]+bm.edges[:]+bm.faces[:]
bmesh.ops.bisect_plane(bm,geom=geom,plane_co=pc,plane_no=pn,clear_inner=True)
bm.verts.ensure_lookup_table()
hco=np.array([v.co[:] for v in bm.verts]); idx={v:i for i,v in enumerate(bm.verts)}
hfaces=[tuple(idx[v] for v in f.verts) for f in bm.faces]
bm.free()
eyes=[]
for n in ('GEO-body_male_realistic.eye.L','GEO-body_male_realistic.eye.R'):
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
R=np.load(os.path.join(os.environ.get('GT3D','.'),'ill','rest.npz'),allow_pickle=True); main=np.array([str(m) for m in R['main']])
upper=np.isin(main,['head','neck','chest','clavicle.L','clavicle.R'])
kd=cKDTree(bco[upper]); upid=np.where(upper)[0]
def make(name,verts,faces):
    m=bpy.data.meshes.new(name); m.from_pydata([tuple(v) for v in verts],[],faces); m.update()
    ob=bpy.data.objects.new(name,m); bpy.context.scene.collection.objects.link(ob)
    for p in m.polygons: p.use_smooth=True
    return ob
cab=make('Cabeza',hco,hfaces)
# ---- hair (short, buzz cut) and eyebrows: darkness 'tint' for the renderer
ss_=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
hn=np.zeros(len(hco)*3); cab.data.vertices.foreach_get('normal',hn); hn=hn.reshape(-1,3)
# skin (no hair) region seen from the side, (y, z): forehead, temple, sideburn, around the ear, behind the ear, nape
SKIN=np.array([(-0.30,1.30),(-0.30,1.646),(-0.112,1.646),(-0.100,1.630),(-0.090,1.610),(-0.083,1.592),(-0.080,1.576),
               (-0.075,1.570),(-0.069,1.575),(-0.068,1.602),(-0.060,1.623),(-0.045,1.633),(-0.026,1.631),(-0.008,1.618),
               (0.004,1.600),(0.009,1.572),(0.013,1.545),(0.020,1.522),(0.030,1.508),(0.20,1.504),(0.20,1.30)])   # measured on the head
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
sd=sdist(hco[:,1],hco[:,2]-rec,SKIN)
hair=ss_((sd+E('HSOFT',0.0035))/(2*E('HSOFT',0.0035)))
ear=(ax0>E('EARX',0.074))&(hco[:,1]>-0.075)&(hco[:,1]<0.0)&(hco[:,2]>1.52)&(hco[:,2]<1.645)
hair[ear]=0.0
# eyebrows: arc over each eye (inner end thick, tail thin), only on the front surface
brow=np.zeros(len(hco))
for sg in (1,-1):
    ax_=np.abs(hco[:,0]); xs=sg*hco[:,0]
    u=(xs-E('BX0',0.012))/(E('BX1',0.060)-E('BX0',0.012))            # 0 inner -> 1 tail
    zb=E('BZ0',1.590)+0.012*np.sin(np.clip(u,0,1)*math.pi*0.85)-0.004*np.clip(u,0,1)
    half=E('BW',0.0036)*(1-0.55*np.clip(u,0,1))
    inn=ss_(1-(np.abs(hco[:,2]-zb)-half)/E('BSOFT',0.0018))*ss_(u/0.08)*ss_((1-u)/0.12)
    inn*=(xs>0)*(hn[:,1]<-0.25)*(hco[:,1]<-0.09)
    brow=np.maximum(brow,inn)
tint=np.maximum(hair*E('HAIRT',0.62),brow*E('BROWT',0.60))
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
    ob=make('Ojo.'+L,ec,ef); g=ob.vertex_groups.new(name='head'); g.add(list(range(len(ec))),1.0,'REPLACE')
    m2=ob.modifiers.new('Armature','ARMATURE'); m2.object=rig
    c=ec.mean(0); r=np.linalg.norm(ec-c,axis=1).mean(); fwd=np.array((0,-1.0,0))
    cosang=((ec-c)@fwd)/np.maximum(np.linalg.norm(ec-c,axis=1),1e-9)
    ang=np.degrees(np.arccos(np.clip(cosang,-1,1)))
    # iris (~11 mm wide on a 24 mm eye ~ 27 deg) and pupil (~10 deg): darkness for the renderer's 'tint'
    t=np.where(ang<E('PUPA',10),0.85,np.where(ang<E('IRISA',27),0.42,0.0))
    a=ob.data.attributes.new('tint','FLOAT','POINT'); a.data.foreach_set('value',t.astype(np.float32))
    print('eye',L,'centre',np.round(c,3),'r %.4f'%r)
# body cap pushed inside the new head: from 0.8 cm above the cut, up to CAPIN mm (smooth), only the head region
hb=np.isin(main,['head','neck'])
hh=bco[:,2]-cutz(bco[:,1])
push=np.clip((hh-E('CAP0',0.008))/(E('CAP1',0.03)-E('CAP0',0.008)),0,1); push=push*push*(3-2*push)*hb
bco=bco-bno*(push[:,None]*E('CAPIN',12)/1000.0)
bme.vertices.foreach_set('co',bco.ravel()); bme.update()
print('cap verts pushed',int((push>0.01).sum()))
bpy.ops.wm.save_as_mainfile(filepath=out)
