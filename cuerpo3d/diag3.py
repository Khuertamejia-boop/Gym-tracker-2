import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
ob=bpy.data.objects['Cuerpo']; me=ob.data
gn={g.index:g.name for g in ob.vertex_groups}
co=np.array([v.co[:] for v in me.vertices])
for tgt in [(0.24,-0.06,1.30),(0.26,0.0,1.33),(0.30,0.0,1.25),(0.2,-0.07,1.36),(0.27,0.03,1.28)]:
    i=np.argmin(np.linalg.norm(co-np.array(tgt),axis=1)); v=me.vertices[i]
    print(tgt,'->',co[i].round(3),sorted([(round(g.weight,2),gn[g.group]) for g in v.groups],reverse=True))
