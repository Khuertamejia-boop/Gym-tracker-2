# Skeleton for the Blender Human Base Mesh (realistic male): same bone names/hierarchy as the old 'Rig' so every
# script keeps working. Joints measured from the mesh (arm/leg slices, automatic finger centre lines).
# Copies the bar objects from the old file. Automatic (heat) skin weights.
# usage: blender -b -P newrig.py -- body.blend old_with_bar.blend out.blend
import bpy,sys,os,math
import numpy as np
from mathutils import Vector
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fingerauto
body,old,out=sys.argv[-3],sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=body)
hi=bpy.data.objects['Hi']; me=hi.data
co=np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
def yc(z,xmax=0.03):
    m=(np.abs(co[:,2]-z)<0.005)&(np.abs(co[:,0])<xmax); return 0.5*(co[m,1].min()+co[m,1].max())
def legc(z):
    m=(np.abs(co[:,2]-z)<0.004)&(co[:,0]>0.0)&(co[:,0]<0.30); P=co[m]; return P.mean(0)
J={}
for n,z0,z1 in (('hips',0.90,0.99),('spine',0.99,1.17),('chest',1.17,1.40),('neck',1.40,1.49),('head',1.49,1.684)):
    J[n]=(np.array([0,yc(z0)+0.012,z0]),np.array([0,yc(min(z1,1.66))+0.012,z1]))
S=np.array([0.175,-0.033,1.355]); EL=np.array([0.293,-0.020,1.103]); WR=np.array([0.375,-0.063,0.881])
J['clavicle']=(np.array([0.025,yc(1.385)-0.01,1.385]),S)
J['upper_arm']=(S,EL); J['forearm']=(EL,WR)
W,hd,nrm=np.load(os.path.join(os.path.dirname(out) or '.','hand_W_hd_nrm.npy'))
F=fingerauto.finger_joints(co,ed,W,hd,nrm)
# knuckle line: the index MCP sits just behind the middle one (the free part of the index is short)
um=(F['middle'][0]-W)@hd; ui=(F['index'][0]-W)@hd
if ui>um-0.004:
    d=F['index'][1]-F['index'][0]; d/=np.linalg.norm(d); k=(ui-(um-0.004))/max(d@hd,1e-3)
    F['index'][0]=F['index'][0]-d*k
mm=F['middle'][0]; J['hand']=(WR,mm+(mm-WR)*0.08)
# legs
HJ=np.array([0.092,legc(0.85)[1],0.875]); KN=legc(0.475); KN[2]=0.475; AN=legc(0.09); AN[2]=0.08
foot=co[(co[:,0]>0.05)&(co[:,2]<0.05)]; toe=foot[np.argmin(foot[:,1])]; ball=AN.copy(); ball[1]=toe[1]+0.05; ball[2]=0.025; ball[0]=toe[0]
J['thigh']=(HJ,KN); J['shin']=(KN,AN); J['foot']=(AN,ball)
for k in ('thigh','shin','foot','upper_arm','forearm','hand','clavicle'): print(k,np.round(J[k][0],3),np.round(J[k][1],3))
# armature
arm=bpy.data.armatures.new('Rig'); rig=bpy.data.objects.new('Rig',arm); bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig
for o in bpy.context.view_layer.objects: o.select_set(o==rig)
bpy.ops.object.mode_set(mode='EDIT'); eb=arm.edit_bones
def mk(name,h,t,parent=None,roll_vec=None,deform=True):
    b=eb.new(name); b.head=Vector(h); b.tail=Vector(t)
    if parent: b.parent=eb[parent]
    b.use_deform=deform
    if roll_vec is not None: b.align_roll(Vector(roll_vec))
    return b
fwd=(0,-1,0)
mk('hips',*J['hips'],roll_vec=fwd); mk('spine',*J['spine'],'hips',fwd); mk('chest',*J['chest'],'spine',fwd)
mk('neck',*J['neck'],'chest',fwd); mk('head',*J['head'],'neck',fwd)
for L,s in (('L',1),('R',-1)):
    mir=np.array([s,1,1]); back=nrm*mir      # back of the hand -> bone +Z (palm = -Z, as before)
    mk('clavicle.'+L,J['clavicle'][0]*mir,J['clavicle'][1]*mir,'chest',(0,0,1))
    mk('upper_arm.'+L,J['upper_arm'][0]*mir,J['upper_arm'][1]*mir,'clavicle.'+L,back)
    mk('forearm.'+L,J['forearm'][0]*mir,J['forearm'][1]*mir,'upper_arm.'+L,back)
    mk('hand.'+L,J['hand'][0]*mir,J['hand'][1]*mir,'forearm.'+L,back)
    for f in ('thumb','index','middle','ring','pinky'):
        P=F[f]; par='hand.'+L
        for k in (1,2,3):
            mk(f'{f}{k}.{L}',P[k-1]*mir,P[k]*mir,par,back); par=f'{f}{k}.{L}'
    ua=(J['upper_arm'][1]-J['upper_arm'][0]); ua/=np.linalg.norm(ua)
    mk('delt.'+L,J['upper_arm'][0]*mir,(J['upper_arm'][0]+ua*0.10)*mir,'clavicle.'+L,back,deform=False)
    mk('thigh.'+L,J['thigh'][0]*mir,J['thigh'][1]*mir,'hips',fwd)
    mk('shin.'+L,J['shin'][0]*mir,J['shin'][1]*mir,'thigh.'+L,fwd)
    mk('foot.'+L,J['foot'][0]*mir,J['foot'][1]*mir,'shin.'+L,(0,0,1))
mk('bar',(0,-0.296,0.937),(0.3,-0.296,0.937),None,(0,0,1),deform=False)
bpy.ops.object.mode_set(mode='OBJECT')
for L in 'LR':
    c=rig.pose.bones['delt.'+L].constraints.new('COPY_ROTATION'); c.target=rig; c.subtarget='upper_arm.'+L
    c.target_space='LOCAL'; c.owner_space='LOCAL'; c.mix_mode='REPLACE'; c.influence=0.5
# automatic weights (bone heat) on the deforming bones
for o in bpy.context.view_layer.objects: o.select_set(o in (hi,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
print('groups',len(hi.vertex_groups))
for L in 'LR':
    rig.data.bones['delt.'+L].use_deform=True
    if 'delt.'+L not in hi.vertex_groups: hi.vertex_groups.new(name='delt.'+L)
# the bar objects from the old file
with bpy.data.libraries.load(old) as (src,dst): dst.objects=[n for n in src.objects if n in ('Barra','Discos')]
for o in dst.objects:
    if o: bpy.context.scene.collection.objects.link(o)
    for m in o.modifiers:
        if m.type=='ARMATURE': m.object=rig
bpy.ops.wm.save_as_mainfile(filepath=out)
