import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
for nm in ('Cuerpo','Hi'):
    ob=bpy.data.objects[nm]; me=ob.data
    print(nm,'parent',ob.parent.name if ob.parent else None,'mods',[(m.type,getattr(m,'object',None) and m.object.name) for m in ob.modifiers],'groups',len(ob.vertex_groups),'mw',[tuple(round(x,3) for x in r) for r in ob.matrix_world])
    if nm=='Hi':
        tot=np.zeros(len(me.vertices)); ng=np.zeros(len(me.vertices))
        for v in me.vertices:
            for g in v.groups: tot[v.index]+=g.weight; ng[v.index]+=1
        co=np.array([v.co[:] for v in me.vertices]); back=(co[:,1]>0.05)&(np.abs(co[:,0])<0.1)&(co[:,2]>1.0)&(co[:,2]<1.4)
        print('back verts',back.sum(),'tot weight pct',np.percentile(tot[back],[0,5,50,95,100]).round(2),'ngroups',np.percentile(ng[back],[0,50,100]))
        gn={g.index:g.name for g in ob.vertex_groups}
        i=np.where(back)[0][0]; print([ (gn[g.group],round(g.weight,2)) for g in me.vertices[i].groups])
rig=bpy.data.objects['Rig']; print('rig mw',[tuple(round(x,3) for x in r) for r in rig.matrix_world])
