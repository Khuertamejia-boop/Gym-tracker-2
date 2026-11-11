# quick deformation test: MODE=down (arms by the side, elbows 90) or MODE=up (arms overhead)
import bpy,sys,math,os
from mathutils import Vector,Matrix
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']
def aim(bn,target,roll=0.0):
    pb=rig.pose.bones[bn]; b=rig.data.bones[bn]; bpy.context.view_layer.update()
    cur=(pb.tail-pb.head).normalized(); tv=Vector(target).normalized()
    R=Matrix.Rotation(math.radians(roll),3,tv)@cur.rotation_difference(tv).to_matrix()
    M=pb.matrix.to_3x3(); newM=R@M
    par=pb.parent.matrix.to_3x3() if pb.parent else Matrix.Identity(3)
    rest=b.matrix_local.to_3x3(); prest=b.parent.matrix_local.to_3x3() if b.parent else Matrix.Identity(3)
    pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=((prest.inverted()@rest).inverted()@par.inverted()@newM).to_quaternion()
    bpy.context.view_layer.update()
mode=os.environ.get('MODE','down')
for s,L in ((1,'L'),(-1,'R')):
    if mode=='down':
        aim('upper_arm.'+L,(s*0.15,-0.05,-1)); aim('forearm.'+L,(s*0.05,-1,-0.1))
    else:
        aim('clavicle.'+L,Matrix.Rotation(math.radians(-s*30),3,'Y')@(Vector(rig.pose.bones['clavicle.'+L].tail)-Vector(rig.pose.bones['clavicle.'+L].head)))
        aim('upper_arm.'+L,(s*0.30,0.0,1)); aim('forearm.'+L,(s*0.05,0.05,1))
bpy.ops.wm.save_as_mainfile(filepath=out)
