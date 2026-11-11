# usage: cd $GT3D/w && ../venv/bin/python -I ../objcheck.py -- F1.blend F2.blend ...
# how deep the equipment (objects 'Barra' and 'Discos') goes into the body: min signed distance of its vertices to the
# skin (negative = inside the body), and where
import bpy, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
for f in sys.argv[sys.argv.index('--')+1:]:
    bpy.ops.wm.open_mainfile(filepath=f)
    dg=bpy.context.evaluated_depsgraph_get(); hi=bpy.data.objects['Hi']
    bvh=BVHTree.FromObject(hi,dg)
    out=[]
    for n in ('Barra','Discos'):
        o=bpy.data.objects.get(n)
        if o is None or o.hide_render: continue
        me=o.evaluated_get(dg).to_mesh(); M=o.matrix_world
        best=(1e9,None)
        for v in me.vertices:
            p=M@v.co; loc,nrm,i,d=bvh.find_nearest(p)
            if loc is None: continue
            sd=d if (p-loc).dot(nrm)>0 else -d
            if sd<0:                          # confirm with ray parity (normals between curled fingers can mislead)
                ins=0
                for dv in ((1,0,0),(-1,0,0),(0,0,1),(0,1,0),(0,-1,0)):
                    q=p.copy(); n_=0
                    for _ in range(40):
                        hit=bvh.ray_cast(q,Vector(dv))
                        if hit[0] is None: break
                        n_+=1; q=hit[0]+Vector(dv)*1e-5
                    ins+=n_%2
                if ins<3: sd=d
            if sd<best[0]: best=(sd,tuple(round(x,3) for x in p))
        out.append('%s %+.1f mm at %s'%(n,best[0]*1000,best[1]))
    print(f,' | '.join(out))
