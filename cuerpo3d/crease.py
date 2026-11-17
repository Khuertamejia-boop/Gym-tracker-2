import bpy,bmesh,sys,numpy as np,collections,math
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
ob=bpy.data.objects['Cuerpo']; me=ob.data
fi=[i for i,m in enumerate(me.materials) if m and m.name=='face_skin'][0]
bm=bmesh.new(); bm.from_mesh(me); bm.normal_update()
c=collections.Counter(); ex=collections.defaultdict(list)
for e in bm.edges:
    if len(e.link_faces)!=2: continue
    a=math.degrees(e.link_faces[0].normal.angle(e.link_faces[1].normal))
    if a>30:
        m=(e.verts[0].co+e.verts[1].co)/2
        if any(f.material_index==fi for f in e.link_faces): continue
        k=(round(m.z,2) if True else 0); c[(round(m.z*20)/20)]+=1; ex[round(m.z*20)/20].append(tuple(round(x,3) for x in m))
for k in sorted(c): print(k,c[k],ex[k][:3])
