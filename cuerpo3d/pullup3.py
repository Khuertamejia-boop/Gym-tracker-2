# Pull-up frame with the body's own anatomical hands (re-rigged fingers) closed around the bar.
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
md=hi.modifiers.new('Armature','ARMATURE'); md.object=rig; md.use_deform_preserve_volume=True
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
            aim('hand.'+L,(fa*E('HST',0.8)+fdir*(1-E('HST',0.8))).normalized(),0.0)
            kn=(Vector(pb['index1.'+L].head)-Vector(pb['pinky1.'+L].head)); kn=(kn-fa*(kn@fa)).normalized()
            want=Vector((-s,0,0)); want=(want-fa*(want@fa)).normalized()
            dr=math.degrees(math.atan2(kn.cross(want)@fa, kn@want))
            if abs(dr)<0.5: break
            aim('forearm.'+L,W-El,dr)
        ax,c=handrig.fist(rig,L,A,TA)
        cs[L]=c
        Wp=Vector(pb['hand.'+L].head)
        off[L]=off[L]+((Vector((s*GRIPX,BAR.y,BAR.z))-c))   # move the wrist so the fist centre lands on the bar
    print('iter',it,'fist centres',[tuple(round(x,3) for x in cs[k]) for k in 'LR'])
for s,L in ((1,'L'),(-1,'R')):
    aim('thigh.'+L,(s*0.03,-E('TFWD',0.18),-1)); aim('shin.'+L,(s*0.02,E('SBK',0.7),-0.8))
bpy.context.view_layer.update()
c=(cs['L']+cs['R'])/2; axis=(cs['L']-cs['R']).normalized()
handrig.place_bar(c+Vector((0,E('BDY',0.0),E('BDZ',0.0))),axis,E('BARR',0.0145))
print('P',P,'bar',tuple(round(x,3) for x in c))
bpy.ops.wm.save_as_mainfile(filepath=out)
