# usage: cd $GT3D/w && ../venv/bin/python -I ../headcheck.py -- F1.blend ...     (env RESTNPZ: rest data of the body)
# Do the arms / hands go into the head? Min distance (mm) from the arm, forearm and hand skin to the face/head object
# 'Cabeza' (negative = inside, by the side of the nearest face normal), per arm.
import bpy, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R = np.load(os.environ.get('RESTNPZ', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ill', 'rest.npz')), allow_pickle=True)
main = np.array([str(x) for x in R['main']])
for f in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.open_mainfile(filepath=f)
    dg = bpy.context.evaluated_depsgraph_get(); hi = bpy.data.objects['Hi']; cab = bpy.data.objects['Cabeza']
    me = hi.evaluated_get(dg).to_mesh(); n = len(me.vertices)
    P = np.zeros(n * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
    bv = BVHTree.FromObject(cab, dg); out = []
    for L in 'LR':
        sel = np.where([m.endswith('.' + L) and m.split('.')[0] not in ('clavicle', 'thigh', 'shin', 'foot') for m in main])[0]
        best = (9.0, None)
        for i in sel[::2]:
            loc, nrm, _, d = bv.find_nearest(Vector(P[i]), 0.08)
            if loc is None: continue
            sd = d if (Vector(P[i]) - loc).dot(nrm) > 0 else -d
            if sd < best[0]: best = (sd, main[i])
        out.append('%s %+.1f mm (%s)' % (L, best[0] * 1000, best[1]))
    print(os.path.basename(f), ' | '.join(out))
