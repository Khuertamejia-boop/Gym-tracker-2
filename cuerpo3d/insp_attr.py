import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
hi=bpy.data.objects['Hi']; me=hi.data
print('verts',len(me.vertices),'faces',len(me.polygons))
for a in me.attributes:
    print(a.name,a.domain,a.data_type)
seg=np.zeros(len(me.polygons),np.float32); me.attributes['mseg'].data.foreach_get('value',seg)
u,c=np.unique(seg,return_counts=True); print('mseg ids',len(u)); print(list(zip(u.astype(int),c)))
mi=np.zeros(len(me.polygons),int); me.polygons.foreach_get('material_index',mi)
print('mats',[m.name if m else None for m in me.materials]); u,c=np.unique(mi,return_counts=True); print(list(zip(u,c)))
for n in ('mq','ln','mu','groove','mdist','work'):
    if n in me.attributes:
        v=np.zeros(len(me.vertices),np.float32); me.attributes[n].data.foreach_get('value',v); print(n,np.percentile(v,[0,5,50,95,100]))
print([m.name for m in hi.modifiers])
