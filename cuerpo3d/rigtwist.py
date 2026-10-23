# Forearm twist bones: the radius turns around the ulna, so pronation/supination is spread along the forearm skin
# (0 at the elbow -> full at the wrist) instead of happening at the wrist (candy-wrapper).
# Adds fa_tw1..3.L/R (children of the forearm, same roll) and splits the forearm skin weight between
# forearm (twist 0), fa_tw1 (1/3), fa_tw2 (2/3), fa_tw3 (full) by position along the forearm.
# The pose script turns fa_twK about its own Y by K/3 of the hand's twist.
# usage: blender -b -P rigtwist.py -- in.blend out.blend
import bpy,sys,os
import numpy as np
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
NODES=[float(x) for x in os.environ.get('TWNODES','0.12,0.40,0.66,0.92').split(',')]   # forearm, tw1, tw2, tw3 positions (0 elbow .. 1 wrist)
bpy.context.view_layer.objects.active=rig
for o in bpy.context.view_layer.objects: o.select_set(o==rig)
bpy.ops.object.mode_set(mode='EDIT'); eb=rig.data.edit_bones
for L in 'LR':
    fa=eb['forearm.'+L]; d=fa.tail-fa.head
    for k,(t0,t1) in enumerate(((0.33,0.55),(0.55,0.78),(0.78,1.0)),1):
        b=eb.get(f'fa_tw{k}.{L}') or eb.new(f'fa_tw{k}.{L}')
        b.head=fa.head+d*t0; b.tail=fa.head+d*t1; b.roll=fa.roll; b.parent=fa; b.use_connect=False; b.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
for L in 'LR':
    b=rig.data.bones['forearm.'+L]; a=np.array(b.head_local); c=np.array(b.tail_local); ax=c-a
    t=(co-a)@ax/(ax@ax)
    gf=hi.vertex_groups['forearm.'+L]
    tw=[hi.vertex_groups.get(f'fa_tw{k}.{L}') or hi.vertex_groups.new(name=f'fa_tw{k}.{L}') for k in (1,2,3)]
    gid=gf.index; wf=np.zeros(nv)
    for v in me.vertices:
        for g in v.groups:
            if g.group==gid: wf[v.index]=g.weight
    sel=np.where(wf>0)[0]
    # hat functions over the nodes
    tt=np.clip(t[sel],NODES[0],NODES[-1])
    H=np.zeros((len(sel),4))
    for k in range(4):
        if k>0:
            m=(tt>=NODES[k-1])&(tt<=NODES[k]); H[m,k]=(tt[m]-NODES[k-1])/(NODES[k]-NODES[k-1])
        if k<3:
            m=(tt>=NODES[k])&(tt<=NODES[k+1]); H[m,k]=np.maximum(H[m,k],(NODES[k+1]-tt[m])/(NODES[k+1]-NODES[k]))
    H/=H.sum(1,keepdims=True)
    groups=[gf]+tw
    for k,g in enumerate(groups):
        w=wf[sel]*H[:,k]; qv=np.round(w*100)/100
        z=sel[qv<=0]
        if len(z): g.remove([int(i) for i in z])
        for lv in np.unique(qv[qv>0]): g.add([int(i) for i in sel[qv==lv]],float(lv),'REPLACE')
    print(L,'forearm skin verts split',len(sel))
bpy.ops.wm.save_as_mainfile(filepath=out)
