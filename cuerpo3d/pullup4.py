# Pull-up frame with the body's own anatomical hands: contact grip (fingers laid on the bar, thumb over them).
# P=0 dead hang, P=1 chin over the bar.  usage: P=0.5 blender -b -P pullup3.py -- SMH_w.blend out.blend
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
for m in list(hi.modifiers):
    if m.type=='ARMATURE': hi.modifiers.remove(m)
md=hi.modifiers.new('Armature','ARMATURE'); md.object=rig; md.use_deform_preserve_volume=E('PV',1)>0; md.show_viewport=False   # posing is faster without the skin
BAR=Vector((0,E('BARY',-0.03),E('BARZ',2.15))); GRIPX=E('GRIPX',0.30)
ease=lambda t: t*t*(3-2*t); q=ease(P)
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
A=[float(v) for v in os.environ.get('GA','75,85,60').split(',')]; TA=[float(v) for v in os.environ.get('GTA','0,30,35').split(',')]
fdir=Vector((0,-E('FY',0.30),1.0)).normalized()
Lu=rig.data.bones['upper_arm.L'].length; Lf=rig.data.bones['forearm.L'].length
off={'L':Vector((0,0.06,-0.16)),'R':Vector((0,0.06,-0.16))}      # wrist relative to the fist centre (refined below)
rest_sh=np.array(rig.data.bones['upper_arm.L'].head_local)
import json
# HFIX: keep the approved grip in every frame -> the hand keeps the same angle to the bar (the wrist absorbs the change)
HFIX=json.load(open(os.environ['HFIX'])) if os.environ.get('HFIX') else {}
# collarbones lift a little with the arms overhead (the shoulder does not take the whole movement)
if E('CLV',0)!=0:
    for s_,L in ((1,'L'),(-1,'R')):
        pbc=rig.pose.bones['clavicle.'+L]; d0=(Vector(pbc.tail)-Vector(pbc.head))
        aim('clavicle.'+L,Matrix.Rotation(math.radians(-s_*E('CLV',0)),3,'Y')@d0,0.0)
for it in range(3):
    # body height from the wrist height
    Wz=BAR.z+off['L'].z
    sh=(Wz-E('HANG',0.50))*(1-q)+(Wz-E('TOPD',0.06))*q
    hb=rig.pose.bones['hips']; hb.location=rig.data.bones['hips'].matrix_local.to_3x3().inverted()@Vector((0,E('LEAN',0.06)*q,sh-rest_sh[2]))
    bpy.context.view_layer.update()
    cs={}
    for s,L in ((1,'L'),(-1,'R')):
        S=Vector(rig.pose.bones['upper_arm.'+L].head)
        W=Vector((s*GRIPX,BAR.y,BAR.z))+off[L]
        d=(W-S); dist=min(d.length,(Lu+Lf)*0.999); u=d.normalized()
        a=(Lu*Lu-Lf*Lf+dist*dist)/(2*dist); h=math.sqrt(max(Lu*Lu-a*a,0))
        pole=Vector((s*E('PX',0.5),E('PY',0.35),-1.0)); n=(pole-u*(pole@u)).normalized()
        El=S+u*a+n*h
        aim('upper_arm.'+L,El-S,s*E('ROLL',70))
        # the knuckle line must run along the bar (thumb side towards the middle): turn the FOREARM (pronation), not the wrist
        pb=rig.pose.bones
        # the knuckle line must run along the bar (thumb side towards the middle): turn the FOREARM (pronation), not the wrist.
        # aim() rotates from the current orientation, so the roll passed is the correction still needed
        aim('forearm.'+L,W-El,0.0)
        for _ in range(4):
            fa=(Vector(pb['forearm.'+L].tail)-Vector(pb['forearm.'+L].head)).normalized()
            aim('hand.'+L,Vector(HFIX[L]) if L in HFIX else (fa*E('HST',0.8)+fdir*(1-E('HST',0.8))).normalized(),0.0)
            kn=(Vector(pb['index1.'+L].head)-Vector(pb['pinky1.'+L].head)); kn=(kn-fa*(kn@fa)).normalized()
            want=Vector((-s,0,0)); want=(want-fa*(want@fa)).normalized()
            dr=math.degrees(math.atan2(kn.cross(want)@fa, kn@want))
            if abs(dr)<0.5: break
            aim('forearm.'+L,W-El,dr)
        c=handrig.bar_from_hand(rig,L,E('BARR',0.0145))
        cs[L]=c
        off[L]=off[L]+((Vector((s*GRIPX,BAR.y,BAR.z))-c))   # move the wrist so the palm meets the bar
    print('iter',it,'fist centres',[tuple(round(x,3) for x in cs[k]) for k in 'LR'])
pbx=rig.pose.bones
for L in 'LR':
    fa=(Vector(pbx['forearm.'+L].tail)-Vector(pbx['forearm.'+L].head)).normalized(); hd=(Vector(pbx['hand.'+L].tail)-Vector(pbx['hand.'+L].head)).normalized()
    print(L,'wrist bend (deg)',round(math.degrees(fa.angle(hd)),1))
if os.environ.get('HDUMP'):
    json.dump({L:list((Vector(pbx['hand.'+L].tail)-Vector(pbx['hand.'+L].head)).normalized()) for L in 'LR'},open(os.environ['HDUMP'],'w'))
for s,L in ((1,'L'),(-1,'R')):
    aim('thigh.'+L,(s*0.03,-E('TFWD',0.18),-1)); aim('shin.'+L,(s*0.02,E('SBK',0.7),-0.8))
# head tilts back a little near the top (chin over the bar, face clear of it)
if E('HTILT',0)!=0:
    for bn,fr in (('neck',0.4),('head',0.6)):
        pbn=rig.pose.bones[bn]; d0=(Vector(pbn.tail)-Vector(pbn.head))
        aim(bn,Matrix.Rotation(math.radians(-E('HTILT',0)*fr*q),3,'X')@d0,0.0)
bpy.context.view_layer.update()
Bc=Vector((0,BAR.y,BAR.z)); axis=Vector((1,0,0))
for L in 'LR':
    info,err=handrig.wrap2(rig,L,Bc,axis,E('BARR',0.0145))
    if os.environ.get('TMODE','over')=='over':
        err=handrig.thumb_over(rig,L,Bc,axis,E('BARR',0.0145)); print(L,'thumb over: IP miss (mm)',round(err*1000,1))
    print(L,{f:[round(a) for a in info[f][5]] for f in info})
    print(L,'thumb tip error (mm)',round(err*1000,1))
c=Bc
handrig.place_bar(Bc,axis,E('BARR',0.0145))
md.show_viewport=True
if E('CSM',1)>0 and 'CS' in hi.vertex_groups:
    cs=hi.modifiers.new('CorrectiveSmooth','CORRECTIVE_SMOOTH'); cs.vertex_group='CS'; cs.iterations=int(E('CSIT',10)); cs.factor=E('CSF',0.8)
    cs.smooth_type='LENGTH_WEIGHTED'; cs.rest_source='ORCO'
if E('CS2IT',0)>0:
    # shoulders: the arm turns ~150 degrees there; a corrective smooth around the joint removes the pinched crease
    me=hi.data; nv=len(me.vertices); co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    d=np.min([np.linalg.norm(co-np.array(rig.data.bones['upper_arm.'+L].head_local),axis=1) for L in 'LR'],axis=0)
    t=np.clip((d-E('S2D0',0.09))/(E('S2D1',0.18)-E('S2D0',0.09)),0,1); w=1-t*t*(3-2*t)
    # keep the neck/head out (the head is a separate skin piece: smoothing there leaves marks)
    nh=np.zeros(nv); gidx={g.index:g.name for g in hi.vertex_groups}
    for i in np.where(w>0)[0]:
        for g_ in me.vertices[int(i)].groups:
            if gidx.get(g_.group) in ('neck','head'): nh[i]+=g_.weight
    w=w*np.clip(1-nh*E('S2NECK',3.0),0,1)
    if 'CS2' in hi.vertex_groups: hi.vertex_groups.remove(hi.vertex_groups['CS2'])
    g=hi.vertex_groups.new(name='CS2'); q=np.round(w*64).astype(int)
    for val in np.unique(q[q>0]): g.add([int(i) for i in np.where(q==val)[0]],val/64.0,'REPLACE')
    c2=hi.modifiers.new('CorrectiveSmooth2','CORRECTIVE_SMOOTH'); c2.vertex_group='CS2'; c2.iterations=int(E('CS2IT',0)); c2.factor=E('CS2F',1.0)
    c2.smooth_type='LENGTH_WEIGHTED'; c2.rest_source='ORCO'
if E('AXIT',0)>0:
    # armpit: at rest it is a closed crease; with the arm up it must just stretch. Plain smoothing (no rest detail)
    me=hi.data; nv=len(me.vertices); co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    gidx={g.index:g.name for g in hi.vertex_groups}; wax=np.zeros(nv)
    for L in 'LR':
        j=np.array(rig.data.bones['upper_arm.'+L].head_local)
        near=np.where(np.linalg.norm(co-j,axis=1)<0.20)[0]
        arm=np.zeros(nv); tor=np.zeros(nv)
        for i in near:
            for g_ in me.vertices[int(i)].groups:
                n_=gidx.get(g_.group,'')
                if n_ in ('upper_arm.'+L,'delt.'+L): arm[i]+=g_.weight
                elif n_ in ('chest','spine','clavicle.'+L): tor[i]+=g_.weight
        mix=near[(arm[near]>0.25)&(tor[near]>0.25)&(co[near,2]<j[2]-E('AXDZ',0.05))]
        if len(mix)==0: continue
        ax=co[mix].mean(0); print(L,'armpit centre',np.round(ax,3),'from',len(mix),'verts')
        dd=np.linalg.norm(co-ax,axis=1); t=np.clip((dd-E('AXR0',0.035))/(E('AXR1',0.08)-E('AXR0',0.035)),0,1)
        wax=np.maximum(wax,1-t*t*(3-2*t))
    if 'AX' in hi.vertex_groups: hi.vertex_groups.remove(hi.vertex_groups['AX'])
    g=hi.vertex_groups.new(name='AX'); q=np.round(wax*64).astype(int)
    for val in np.unique(q[q>0]): g.add([int(i) for i in np.where(q==val)[0]],val/64.0,'REPLACE')
    sm=hi.modifiers.new('ArmpitSmooth','SMOOTH'); sm.vertex_group='AX'; sm.factor=E('AXF',0.8); sm.iterations=int(E('AXIT',0))
if hi.data.shape_keys and 'LatsUp' in hi.data.shape_keys.key_blocks:
    hi.data.shape_keys.key_blocks['LatsUp'].value=E('LATK',0.0)
print('P',P,'bar',tuple(round(x,3) for x in c))
bpy.ops.wm.save_as_mainfile(filepath=out)
