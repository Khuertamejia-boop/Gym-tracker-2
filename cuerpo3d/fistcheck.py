# usage: cd $GT3D/w && ../venv/bin/python -I ../fistcheck.py -- F1.blend ...   min distance from the fists (skin near the grips) to the face
import bpy,sys,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
for f in sys.argv[sys.argv.index('--')+1:]:
    bpy.ops.wm.open_mainfile(filepath=f)
    dg=bpy.context.evaluated_depsgraph_get(); hi=bpy.data.objects['Hi']; cab=bpy.data.objects['Cabeza']
    m=hi.evaluated_get(dg).to_mesh(); P=np.array([hi.matrix_world@v.co for v in m.vertices])
    bv=BVHTree.FromObject(cab,dg)
    g=[o for o in bpy.data.objects if o.name.startswith('Banco_grip')]
    cc=np.array([list(o.matrix_world.translation) for o in g])
    fist=P[np.min(np.linalg.norm(P[:,None,:]-cc[None],axis=2),axis=1)<0.06]
    d=[]
    for p in fist[::2]:
        loc,nrm,i,dd=bv.find_nearest(Vector(p)); d.append(dd if loc is not None else 9)
    # head region of the evaluated Cabeza in world
    cm=cab.evaluated_get(dg).to_mesh(); C=np.array([cab.matrix_world@v.co for v in cm.vertices])
    print(f,'grips',np.round(cc,3).tolist(),'fist verts',len(fist),'min %.1f mm'%(min(d)*1000),'cab z %.3f..%.3f'%(C[:,2].min(),C[:,2].max()), 'cab matrix', cab.matrix_world.translation[:], 'mods',[x.type for x in cab.modifiers])
