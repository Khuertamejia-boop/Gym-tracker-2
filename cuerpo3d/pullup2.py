# Pull-up frame with the procedural fist.  P=0 dead hang, P=1 chin over the bar.
# usage: P=0.5 blender -b -P pullup2.py -- in.blend out.blend
import bpy,bmesh,sys,math,os
import numpy as np
from mathutils import Vector,Matrix
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import hand_geo
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
P=E('P',0.0)
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']
md=hi.modifiers.new('Armature','ARMATURE'); md.object=rig
BARZ=E('BARZ',2.15); BARY=E('BARY',-0.03); GRIPX=E('GRIPX',0.30); BARR=E('BARR',0.0145)
WL=Vector((0.0,-0.095,-0.030))                       # wrist in the hand frame (x, s, t)
fdir=Vector((0.0,-E('FY',0.25),1.0)).normalized()    # finger direction (hands up, a little forward)
Xl=Vector((1,0,0)); sw=(fdir-Xl*(fdir@Xl)).normalized(); tw=Xl.cross(sw).normalized()   # palm normal (towards the bar)
ease=lambda t: t*t*(3-2*t); q=ease(P)
Wz=BARZ+WL.y*sw.z+WL.z*tw.z
sh0=Wz-E('HANG',0.50); sh1=Wz-E('TOPD',0.06)
rest_sh=np.array(rig.data.bones['upper_arm.L'].head_local)
dz=(sh0+(sh1-sh0)*q)-rest_sh[2]; dy=E('LEAN',0.06)*q
hb=rig.pose.bones['hips']; hb.location=rig.data.bones['hips'].matrix_local.to_3x3().inverted()@Vector((0,dy,dz))
bpy.context.view_layer.update()
def aim(bn,target,roll=0.0):
    pb=rig.pose.bones[bn]; b=rig.data.bones[bn]
    bpy.context.view_layer.update()
    cur=(pb.tail-pb.head).normalized()
    tv=Vector(target).normalized(); R=Matrix.Rotation(math.radians(roll),3,tv)@cur.rotation_difference(tv).to_matrix()
    M=pb.matrix.to_3x3(); newM=R@M
    par=pb.parent.matrix.to_3x3() if pb.parent else Matrix.Identity(3)
    rest=b.matrix_local.to_3x3(); prest=b.parent.matrix_local.to_3x3() if b.parent else Matrix.Identity(3)
    local=(prest.inverted()@rest).inverted()@par.inverted()@newM
    pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=local.to_quaternion()
    bpy.context.view_layer.update()
Lu=rig.data.bones['upper_arm.L'].length; Lf=rig.data.bones['forearm.L'].length
Ws={}
for s,L in ((1,'L'),(-1,'R')):
    Bh=Vector((s*GRIPX,BARY,BARZ)); W=Bh+WL.y*sw+WL.z*tw; Ws[L]=(Bh,W)
    S=Vector(rig.pose.bones['upper_arm.'+L].head)
    d=(W-S); dist=min(d.length,(Lu+Lf)*0.999); u=d.normalized()
    a=(Lu*Lu-Lf*Lf+dist*dist)/(2*dist); h=math.sqrt(max(Lu*Lu-a*a,0))
    pole=Vector((s*E('PX',0.5),E('PY',0.35),-1.0)); n=(pole-u*(pole@u)).normalized()
    El=S+u*a+n*h
    aim('upper_arm.'+L,El-S,s*E('ROLL',70)); aim('forearm.'+L,W-El,s*E('FROLL',0)); aim('hand.'+L,fdir,s*E('HROLL',0))
for s,L in ((1,'L'),(-1,'R')):
    aim('thigh.'+L,(s*0.03,-E('TFWD',0.18),-1)); aim('shin.'+L,(s*0.02,E('SBK',0.7),-0.8))
bpy.context.view_layer.update()
# ---- bake the pose into the mesh and cut the old hands at the wrist
dg=bpy.context.evaluated_depsgraph_get(); ev=hi.evaluated_get(dg); em=ev.to_mesh()
nv=len(em.vertices); co=np.zeros(nv*3); em.vertices.foreach_get('co',co); co=co.reshape(-1,3); ev.to_mesh_clear()
for m in list(hi.modifiers):
    if m.type=='ARMATURE': hi.modifiers.remove(m)
me=hi.data; me.vertices.foreach_set('co',co.ravel()); me.update()
kill=np.zeros(nv,bool); info={}
for s,L in ((1,'L'),(-1,'R')):
    Wp=np.array(rig.pose.bones['hand.'+L].head); fh=np.array(rig.pose.bones['forearm.'+L].head)
    ax=Wp-fh; ax/=np.linalg.norm(ax)
    rel=co-Wp; al=rel@ax; rad=np.linalg.norm(rel-np.outer(al,ax),axis=1)
    kill|=(al>-E('CUTB',0.0))&(al<0.30)&(rad<0.10)&(co[:,0]*s>0.05)
    ring=(np.abs(al+E('CUTB',0.0))<0.004)&(rad<0.06)&(co[:,0]*s>0.05)
    info[L]=(float(rad[ring].mean()) if ring.any() else 0.0, Wp)
# round the forearm towards the wrist: over the last 15 cm every cross-section is blended to a circle of the hand's wrist radius
RT=E('WTARGET',0.0285); ss3=lambda x: (lambda t: t*t*(3-2*t))(np.clip(x,0,1)); TZN=E('TAPER',0.15)
for s,L in ((1,'L'),(-1,'R')):
    Wp=np.array(rig.pose.bones['hand.'+L].head); fh=np.array(rig.pose.bones['forearm.'+L].head)
    ax=Wp-fh; ax/=np.linalg.norm(ax); rel=co-Wp; al=rel@ax; perp=rel-np.outer(al,ax); rad=np.linalg.norm(perp,axis=1)
    m=(al>-TZN)&(al<0.0)&(rad<0.10)&(co[:,0]*s>0.05)
    w=ss3((al[m]+TZN)/TZN)
    newrad=rad[m]*(1-w)+RT*w
    co[m]=Wp+np.outer(al[m],ax)+perp[m]*(newrad/np.maximum(rad[m],1e-6))[:,None]
me.vertices.foreach_set('co',co.ravel()); me.update()
print('wrist ring radius (m) L/R',info['L'][0],info['R'][0],'verts cut',int(kill.sum()))
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[bm.verts[i] for i in np.where(kill)[0]],context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
# drop tiny loose islands left around the old hands
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
Ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',Ed); Ed=Ed.reshape(-1,2); nvx=len(me.vertices)
A=coo_matrix((np.ones(len(Ed)),(Ed[:,0],Ed[:,1])),shape=(nvx,nvx)); ncomp,lab=connected_components(A,directed=False)
cnt=np.bincount(lab); small=np.where(cnt<E('ISLE',3000))[0]
c2=np.zeros(nvx*3); me.vertices.foreach_get('co',c2); c2=c2.reshape(-1,3)
# only islands that have faces and are near the hands (keep nothing else untouched)
cand=np.isin(lab,small)&(np.abs(c2[:,0])>0.2)&(c2[:,2]>1.5)
print('tiny islands removed (verts):',int(cand.sum()))
if cand.any():
    bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[bm.verts[i] for i in np.where(cand)[0]],context='VERTS'); bm.to_mesh(me); bm.free(); me.update()
# ---- new hands
hands=[]; Bs=[]
for s,L in ((1,'L'),(-1,'R')):
    Wact=info[L][1]; Bh=Vector(Wact)-WL.y*sw-WL.z*tw; Bs.append(Bh)
    h=hand_geo.build('Hand'+L)
    Xw=Vector((s,0,0)); M=Matrix(((Xw.x,sw.x,tw.x,Bh.x),(Xw.y,sw.y,tw.y,Bh.y),(Xw.z,sw.z,tw.z,Bh.z),(0,0,0,1)))
    h.data.transform(M);
    if s<0:
        bmh=bmesh.new(); bmh.from_mesh(h.data); bmesh.ops.recalc_face_normals(bmh,faces=bmh.faces); bmh.to_mesh(h.data); bmh.free()
    h.data.materials.clear(); hands.append(h)
nv0=len(me.vertices)
with bpy.context.temp_override(active_object=hi,selected_editable_objects=[hi]+hands,selected_objects=[hi]+hands,object=hi):
    bpy.ops.object.join()
me=hi.data; nv1=len(me.vertices); print('joined: verts',nv0,'->',nv1)
for nm,val in (('mq',1.0),('ln',0.0)):
    a=me.attributes.get(nm)
    if a is not None:
        x=np.zeros(len(a.data),np.float32); a.data.foreach_get('value',x); x[nv0:]=val; a.data.foreach_set('value',x)
for pl in me.polygons[len(me.polygons)-1:]: pass
# ---- thin bar centred between the hands
k_=BARR/0.025; bmz=bpy.data.objects['Barra'].data
for v_ in bmz.vertices: v_.co.y=-0.2962+(v_.co.y+0.2962)*k_; v_.co.z=0.9366+(v_.co.z-0.9366)*k_
bmz.update()
Bc=(Bs[0]+Bs[1])/2
for n_ in ('Barra','Discos'):
    o=bpy.data.objects[n_]; o.parent=None; o.location=Vector((0,Bc.y,Bc.z))-Vector((0,-0.2962,0.9366)); o.hide_render=(n_=='Discos')
print('P',P,'bar centre',tuple(round(x,3) for x in Bc))
bpy.ops.wm.save_as_mainfile(filepath=out)
