# Phalanx thickness measured on the mesh: [side half-width, palm-side thickness] per bone (left hand), metres.
import bpy,sys,os,json,numpy as np
src=sys.argv[-2]; outj=sys.argv[-1]
P_=float(os.environ.get('PCT',90))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; rig=bpy.data.objects['Rig']; me=hi.data; nv=len(me.vertices)
co=np.zeros(nv*3); (me.shape_keys.key_blocks['Basis'].data if me.shape_keys else me.vertices).foreach_get('co',co); co=co.reshape(-1,3)
gi={g.index:g.name for g in hi.vertex_groups}
best={}
for v in me.vertices:
    if co[v.index,0]<0.2: continue
    gs=[(g.weight,gi[g.group]) for g in v.groups if gi[g.group] not in ('CS','CS2','AX','SH','EL')]
    if gs: w,n=max(gs); best.setdefault(n,[]).append(v.index)
out={}
for f in ('thumb','index','middle','ring','pinky'):
    for k in (1,2,3):
        n=f'{f}{k}.L'; b=rig.data.bones[n]; M=np.array(b.matrix_local); idx=np.array(best.get(n,[]))
        q=(np.linalg.inv(M)@np.c_[co[idx],np.ones(len(idx))].T).T[:,:3]
        m=(q[:,1]>0.15*b.length)&(q[:,1]<0.85*b.length) if k<3 else (q[:,1]>0.1*b.length)&(q[:,1]<0.6*b.length)
        q=q[m]
        side=np.percentile(np.abs(q[:,0]),P_); palm=np.percentile(np.maximum(-q[:,2],0),P_)
        out[n]=[float(side),float(palm)]
json.dump(out,open(outj,'w'))
for n,v in out.items(): print(n,'%.1f %.1f'%(v[0]*1000,v[1]*1000))
