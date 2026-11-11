# Dumbbell biceps curl frame (both arms). P=0 arm down (elbow almost straight), P=1 top of the curl.
# Hands keep the approved grip (handrig.wrap2 + thumb_over) around the dumbbell handle; palm forward (supinated).
# usage: P=0.5 blender -b -P curl.py -- base.blend out.blend   (source agarre_final.env first for the grip settings)
import bpy,sys,math,os
import numpy as np
from mathutils import Vector,Matrix
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import handrig
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
P=E('P',0.0)
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']
if hi.data.shape_keys and 'LatsUp' in hi.data.shape_keys.key_blocks: hi.data.shape_keys.key_blocks['LatsUp'].value=0.0
for m in list(hi.modifiers): hi.modifiers.remove(m)
md=hi.modifiers.new('Armature','ARMATURE'); md.object=rig; md.use_deform_preserve_volume=E('PV',1)>0; md.show_viewport=False
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
ease=lambda t: t*t*(3-2*t)
th=math.radians(E('TH0',12)+(E('TH1',138)-E('TH0',12))*ease(P))       # elbow flexion
pb=rig.pose.bones
rB=E('BARR',0.0145)
bars={}
for s,L in ((1,'L'),(-1,'R')):
    # upper arm by the side, a little out (clears the lats) and a little forward; it drifts forward a bit at the top
    ua=Vector((s*E('UAX',0.16),-(E('UAY',0.06)+E('UAYT',0.10)*ease(P)),-1.0)).normalized()
    aim('upper_arm.'+L,ua,s*E('UAROLL',0.0))
    # forearm: bend forward in the arm's own plane; carrying angle (forearm slightly out) fades as the elbow bends
    fw=Vector((0,-1,0)); fw=(fw-ua*(fw@ua)).normalized()
    fa=(ua*math.cos(th)+fw*math.sin(th))
    fa=(fa+Vector((s,0,0))*E('CARRY',0.14)*max(0.0,math.cos(th))).normalized()
    aim('forearm.'+L,fa,0.0)
    # supinated: thumb side outwards -> the knuckle line runs along +-x; turn the forearm about its own axis
    for _ in range(5):
        faw=(Vector(pb['forearm.'+L].tail)-Vector(pb['forearm.'+L].head)).normalized()
        aim('hand.'+L,faw,0.0)
        kn=(Vector(pb['index1.'+L].head)-Vector(pb['pinky1.'+L].head)); kn=(kn-faw*(kn@faw)).normalized()
        want=Vector((s,0,0)); want=(want-faw*(want@faw)).normalized()
        dr=math.degrees(math.atan2(kn.cross(want)@faw, kn@want))
        if abs(dr)<0.5: break
        aim('forearm.'+L,faw,dr)
    # slight wrist curl at the top (as people do), none at the bottom
    faw=(Vector(pb['forearm.'+L].tail)-Vector(pb['forearm.'+L].head)).normalized()
    c=handrig.bar_from_hand(rig,L,rB)
    kn=(Vector(pb['index1.'+L].head)-Vector(pb['pinky1.'+L].head)); ax=(kn-faw*(kn@faw)).normalized()
    handrig.wrap2(rig,L,Vector(c),ax,rB)
    err=handrig.thumb_over(rig,L,Vector(c),ax,rB)
    print(L,'thumb over: IP miss (mm)',round(err*1000,1))
    bars[L]=(Vector(c),ax)
bpy.context.view_layer.update()
# dumbbells: chrome handle + hexagonal rubber heads
for n in ('Barra','Discos'):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
mh=bpy.data.materials.get('bar_metal') or bpy.data.materials.new('bar_metal')
mr=bpy.data.materials.new('dumbbell_rubber'); mr.use_nodes=True
bsdf=mr.node_tree.nodes['Principled BSDF']; bsdf.inputs['Base Color'].default_value=(0.035,0.035,0.04,1); bsdf.inputs['Roughness'].default_value=0.55
def cyl(name,c,ax,r,length,verts,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=length,location=(0,0,0))
    o=bpy.context.active_object; o.name=name
    R=Vector((0,0,1)).rotation_difference(ax).to_matrix().to_4x4()
    o.matrix_world=Matrix.Translation(c)@R
    o.data.materials.append(mat)
    if verts<12: pass
    else: bpy.ops.object.shade_smooth()
    return o
hs=[];ds=[]
HL=E('HANDLE',0.135); HR=E('HEADR',0.058); HT=E('HEADT',0.075)
for L,(c,ax) in bars.items():
    hs.append(cyl('h'+L,c,ax,rB,HL+0.01,32,mh))
    for sg in (1,-1):
        ds.append(cyl('d'+L,c+ax*sg*(HL/2+HT/2),ax,HR,HT,6,mr))
def join(objs,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join(); objs[0].name=name; return objs[0]
join(hs,'Barra'); join(ds,'Discos')
md.show_viewport=True
if 'CS' in hi.vertex_groups:
    cs=hi.modifiers.new('CorrectiveSmooth','CORRECTIVE_SMOOTH'); cs.vertex_group='CS'; cs.iterations=int(E('CSIT',40)); cs.factor=E('CSF',1.0)
    cs.smooth_type='LENGTH_WEIGHTED'; cs.rest_source='ORCO'
if E('ELBIT',0)>0:
    # elbow: delta-mush around the joint (cleaner fold when the elbow bends)
    me=hi.data; nv=len(me.vertices); co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    d=np.min([np.linalg.norm(co-np.array(rig.data.bones['forearm.'+L].head_local),axis=1) for L in 'LR'],axis=0)
    t=np.clip((d-E('EL0',0.05))/(E('EL1',0.11)-E('EL0',0.05)),0,1); w=1-t*t*(3-2*t)
    g=hi.vertex_groups.get('EL') or hi.vertex_groups.new(name='EL'); q=np.round(w*64).astype(int)
    for val in np.unique(q[q>0]): g.add([int(i) for i in np.where(q==val)[0]],val/64.0,'REPLACE')
    ce=hi.modifiers.new('CorrectiveSmoothElbow','CORRECTIVE_SMOOTH'); ce.vertex_group='EL'; ce.iterations=int(E('ELBIT',0)); ce.factor=1.0
    ce.smooth_type='LENGTH_WEIGHTED'; ce.rest_source='ORCO'
if E('SHIT',0)>0:
    # shoulder: delta-mush around the joint (the arm comes down from the rest pose; cleaner front of the shoulder)
    me=hi.data; nv=len(me.vertices); co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    d=np.min([np.linalg.norm(co-np.array(rig.data.bones['upper_arm.'+L].head_local),axis=1) for L in 'LR'],axis=0)
    t=np.clip((d-E('SH0',0.08))/(E('SH1',0.18)-E('SH0',0.08)),0,1); w=1-t*t*(3-2*t)
    gidx={g.index:g.name for g in hi.vertex_groups}; nh=np.zeros(nv)
    for i in np.where(w>0)[0]:
        for g_ in me.vertices[int(i)].groups:
            if gidx.get(g_.group) in ('neck','head'): nh[i]+=g_.weight
    w=w*np.clip(1-nh*3,0,1)
    g=hi.vertex_groups.get('SH') or hi.vertex_groups.new(name='SH'); q=np.round(w*64).astype(int)
    for val in np.unique(q[q>0]): g.add([int(i) for i in np.where(q==val)[0]],val/64.0,'REPLACE')
    cs_=hi.modifiers.new('CorrectiveSmoothShoulder','CORRECTIVE_SMOOTH'); cs_.vertex_group='SH'; cs_.iterations=int(E('SHIT',0)); cs_.factor=1.0
    cs_.smooth_type='LENGTH_WEIGHTED'; cs_.rest_source='ORCO'
print('P',P,'elbow',round(math.degrees(th)))
bpy.ops.wm.save_as_mainfile(filepath=out)
