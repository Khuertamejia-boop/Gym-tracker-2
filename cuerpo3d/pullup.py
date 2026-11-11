# Pull-up pose for one frame: P=0 dead hang, P=1 chin over the bar.  usage: blender -b -P pullup.py -- in.blend out.blend
import bpy,sys,math,os
import numpy as np
from mathutils import Vector,Matrix,Quaternion
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
P=E('P',0.0)
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']
md=hi.modifiers.new('Armature','ARMATURE'); md.object=rig
BARZ=E('BARZ',2.15); BARY=E('BARY',-0.03)
GRIPX=E('GRIPX',0.30)                      # hands on the bar, x = +-GRIPX (wider than the shoulders)
WRIST_DZ=E('WDZ',0.163); WRIST_DY=E('WDY',0.074)   # wrist below / behind the bar axis (the hand points up and a little forward)
ease=lambda t: t*t*(3-2*t)
q=ease(P)
# shoulder height: hang -> chin over the bar
WZ=BARZ-WRIST_DZ; sh0=WZ-E('HANG',0.50); sh1=WZ-E('TOPD',0.12)
rest_sh=np.array(rig.data.bones['upper_arm.L'].head_local)
dz=(sh0+(sh1-sh0)*q)-rest_sh[2]
dy=E('LEAN',0.06)*q                        # shoulders go back a little at the top
hb=rig.pose.bones['hips']; hb.location=rig.data.bones['hips'].matrix_local.to_3x3().inverted()@Vector((0,dy,dz))   # translation is expressed in the bone's own axes
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
# arms: two-bone IK from the (moved) shoulder to the wrist fixed under the bar
Lu=rig.data.bones['upper_arm.L'].length; Lf=rig.data.bones['forearm.L'].length
for s,L in ((1,'L'),(-1,'R')):
    S=Vector(rig.pose.bones['upper_arm.'+L].head)
    W=Vector((s*GRIPX,BARY+WRIST_DY,BARZ-WRIST_DZ))
    d=(W-S); dist=min(d.length,(Lu+Lf)*0.999); u=d.normalized()
    a=(Lu*Lu-Lf*Lf+dist*dist)/(2*dist); h=math.sqrt(max(Lu*Lu-a*a,0))
    pole=Vector((s*E('PX',0.5),E('PY',0.35),-1.0)); n=(pole-u*(pole@u)).normalized()
    El=S+u*dist*0+u*a+n*h
    aim('upper_arm.'+L,El-S,s*E('ROLL',70)); aim('forearm.'+L,W-El,s*E('FROLL',0)); aim('hand.'+L,(s*E('HX',0.0),-E('HY',0.3),1.0),s*E('HROLL',0))
# legs: knees a little bent, shins back
for s,L in ((1,'L'),(-1,'R')):
    aim('thigh.'+L,(s*0.03,-E('TFWD',0.18),-1)); aim('shin.'+L,(s*0.02,E('SBK',0.7),-0.8))
# hands closed over the bar: every phalanx bends about the world x axis (the bar axis); hands point up, so the curl goes forward (-y)
A=[float(v) for v in os.environ.get('GA','70,60,50').split(',')]; TA=[float(v) for v in os.environ.get('GTA','20,25,25').split(',')]
bpy.context.view_layer.update()
X_=Vector((1,0,0)); sgn=-1.0
pts=[]
for L in 'LR':
    hp=rig.pose.bones['hand.'+L].matrix.copy()
    for f_ in ('index','middle','ring','pinky','thumb'):
        par=hp; prest=rig.data.bones['hand.'+L].matrix_local
        for k in (1,2,3):
            bn=rig.data.bones[f'{f_}{k}.{L}']; pb=rig.pose.bones[f'{f_}{k}.{L}']
            M=par@(prest.inverted()@bn.matrix_local); ax_=M.to_3x3().inverted()@X_
            ang=(TA if f_=='thumb' else A)[k-1]
            qq=Quaternion(ax_.normalized(),math.radians(sgn*ang)); pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=qq
            par=M@qq.to_matrix().to_4x4(); prest=bn.matrix_local
            if f_=='middle' and k>=2: pts.append(par.translation.copy())
            if f_=='middle' and k==3: pts.append(par@Vector((0,bn.length,0)))
bpy.context.view_layer.update()
# the bar: thin (29 mm) and fixed in the world
k_=E('BARR',0.0145)/0.025; bm=bpy.data.objects['Barra'].data
for v in bm.vertices: v.co.y=-0.2962+(v.co.y+0.2962)*k_; v.co.z=0.9366+(v.co.z-0.9366)*k_
bm.update()
g=sum(pts,Vector())/len(pts) if P<=0 or True else None
# bar centre = the loop of the fingers of the hang pose is reproduced every frame: use the wrist target as reference
Bc=g+Vector((0,E('BDY',0.0),E('BDZ',0.0)))   # the bar goes where the fingers close (same place every frame)
for n_ in ('Barra','Discos'):
    o=bpy.data.objects[n_]; o.parent=None; o.location=Bc-Vector((0,-0.2962,0.9366)); o.hide_render=(n_=='Discos')
print('P',P,'shoulder z',round(sh0+(sh1-sh0)*q,3),'finger loop centre',tuple(round(x,3) for x in g))
bpy.ops.wm.save_as_mainfile(filepath=out)
