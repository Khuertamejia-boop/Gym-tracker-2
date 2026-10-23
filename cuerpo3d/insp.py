import bpy,numpy as np
bpy.ops.wm.open_mainfile(filepath='F_f9.blend')
h=bpy.data.objects['Hi']; print([ (a.name,a.domain) for a in h.data.attributes][:30])
print([m.name for m in h.data.materials])
rig=bpy.data.objects['Rig']
for b in rig.data.bones:
    if any(k in b.name for k in ('thigh','shin','foot','pelvis','spine','neck','head')): print(b.name,np.round(b.head_local,3),np.round(b.tail_local,3))
print([o.name for o in bpy.data.objects])
