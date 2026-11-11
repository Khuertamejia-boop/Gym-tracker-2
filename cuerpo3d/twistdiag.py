# Joint diagnostics per frame: elbow flexion, elbow "sideways" bend (flexion axis vs the rest hinge axis),
# twist of forearm vs upper arm, twist of hand vs forearm, upper arm twist vs swing-only.
import bpy,sys,math
import numpy as np
from mathutils import Vector,Matrix,Quaternion
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
rig=bpy.data.objects['Rig']; pb=rig.pose.bones; bb=rig.data.bones
def wm(n): return pb[n].matrix.to_3x3()        # armature space pose matrix
def rm(n): return bb[n].matrix_local.to_3x3()
for L in 'LR':
    # local rotation of a child relative to parent, pose vs rest: R = (Mp^-1 Mc)_pose * (Mp^-1 Mc)_rest^-1 expressed in child-local
    def rel(c,p):
        Rp=(wm(p).inverted()@wm(c)); Rr=(rm(p).inverted()@rm(c))
        return (Rr.inverted()@Rp)        # rotation in child-rest local frame
    def swing_twist(R):
        q=R.to_quaternion(); # twist about local Y
        tw=Quaternion((q.w,0,q.y,0)); tw.normalize(); sw=q@tw.inverted()
        return math.degrees(2*math.atan2(q.y,q.w)), math.degrees(sw.angle), sw
    e=rel('forearm.'+L,'upper_arm.'+L); tw_e,sw_e,swq=swing_twist(e)
    ax=swq.axis if sw_e>0.5 else Vector((0,0,0))
    h=rel('hand.'+L,'forearm.'+L); tw_h,sw_h,_=swing_twist(h)
    u=rel('upper_arm.'+L,'clavicle.'+L); tw_u,sw_u,_=swing_twist(u)
    print(f"{L} elbow flex {sw_e:5.1f} axis(local) {ax.x:+.2f},{ax.y:+.2f},{ax.z:+.2f} | forearm twist {tw_e:+6.1f} | wrist bend {sw_h:5.1f} twist {tw_h:+6.1f} | shoulder swing {sw_u:5.1f} twist {tw_u:+6.1f}")
