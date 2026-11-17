import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
me=bpy.data.objects['Cuerpo'].data
print('custom normals',me.has_custom_normals,[a.name for a in me.attributes])
fl=[p for p in me.polygons if not p.use_smooth]; print('flat faces',len(fl))
# faces near the line
co=np.array([v.co[:] for v in me.vertices])
for p in me.polygons:
    c=p.center
    if 0.12<c.x<0.2 and c.y<-0.06 and 0.505<c.z<0.535: print(round(c.z,4),round(p.area*1e6,1),'mm2',tuple(round(x,2) for x in p.normal), p.material_index)
