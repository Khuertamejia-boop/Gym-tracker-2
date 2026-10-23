# Shoulder helper bones: 'delt.L/R' sit on the shoulder joint, child of the collarbone, and turn HALF as much as the
# upper arm (Copy Rotation, influence 0.5). Skin that was half torso / half arm now follows the half-turn bone, so the
# shoulder bends smoothly instead of pinching. Weight remap per vertex (u = upper-arm weight):
#   helper = 1-|2u-1|,  upper arm = max(0,2u-1),  torso bones scaled to max(0,1-2u).
# usage: blender -b -P addhelper.py -- in.blend out.blend   env HINF (0.5)
import bpy,sys,os
import numpy as np
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
bpy.context.view_layer.objects.active=rig
for o in bpy.context.view_layer.objects: o.select_set(o==rig)
bpy.ops.object.mode_set(mode='EDIT'); eb=rig.data.edit_bones
for L in 'LR':
    ua=eb['upper_arm.'+L]; h=eb.get('delt.'+L) or eb.new('delt.'+L)
    h.head=ua.head.copy(); h.tail=ua.head+(ua.tail-ua.head).normalized()*0.10; h.roll=ua.roll
    h.parent=eb['clavicle.'+L]; h.use_connect=False; h.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
for L in 'LR':
    pb=rig.pose.bones['delt.'+L]
    for c in list(pb.constraints): pb.constraints.remove(c)
    c=pb.constraints.new('COPY_ROTATION'); c.target=rig; c.subtarget='upper_arm.'+L
    c.target_space='LOCAL'; c.owner_space='LOCAL'; c.mix_mode='REPLACE'; c.influence=E('HINF',0.5)
# weights
bones={b.name for b in rig.data.bones}
for L in 'LR':
    if 'delt.'+L not in hi.vertex_groups: hi.vertex_groups.new(name='delt.'+L)
groups=[g for g in hi.vertex_groups if g.name in bones]; gi={g.index:k for k,g in enumerate(groups)}; names=[g.name for g in groups]
W=np.zeros((nv,len(groups)),np.float32)
for v in me.vertices:
    for g in v.groups:
        k=gi.get(g.group)
        if k is not None: W[v.index,k]=g.weight
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
W0=W.copy()
for L in 'LR':
    ku=names.index('upper_arm.'+L); kh=names.index('delt.'+L)
    lower=[names.index(n) for n in names if n.split('.')[0] in ('forearm','hand') and n.endswith('.'+L)]
    j=np.array(rig.data.bones['upper_arm.'+L].head_local)
    u=W[:,ku]; sel=(np.linalg.norm(co-j,axis=1)<0.30)&(u>1e-4)&(u<0.9999)&(W[:,lower].sum(1)<1e-4)
    oth=[k for k in range(len(names)) if k not in (ku,kh)]
    uu=u[sel]; rest=W[sel][:,oth]; rs=rest.sum(1,keepdims=True); rs[rs==0]=1
    Wn=W[sel]
    Wn[:,kh]=1-np.abs(2*uu-1); Wn[:,ku]=np.maximum(0,2*uu-1)
    Wn[:,oth]=rest/rs*np.maximum(0,1-2*uu)[:,None]
    W[sel]=Wn
    print(L,'verts remapped',int(sel.sum()))
idx=np.where(np.abs(W-W0).max(1)>1e-6)[0]
for k,g in enumerate(groups):
    vals=W[idx,k]; z=idx[vals<=1e-5]
    if len(z): g.remove([int(i) for i in z])
    for i,w in zip(idx[vals>1e-5],vals[vals>1e-5]): g.add([int(i)],float(w),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=out)
