# usage: cd $GT3D/w && ../venv/bin/python -I ../armcheck.py -- F1.blend ...     (env RESTNPZ: rest data of the body)
# Do the arms go into the torso? For each posed frame and arm: how many arm skin points (just outside the arm skin,
# 1.5 mm along its normal) lie INSIDE the body (ray parity on the whole closed mesh) = arm sunk into the torso, and
# the smallest gap between the arm (upper arm + forearm) and the torso skin, away from the armpit (shared skin).
import bpy, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree
R = np.load(os.environ.get('RESTNPZ', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ill', 'rest.npz')), allow_pickle=True)
co0 = R['co']; main = np.array([str(x) for x in R['main']]); bn = [str(x) for x in R['bn']]
ARM = ('upper_arm', 'forearm', 'fa_tw1', 'fa_tw2', 'fa_tw3')
TOR = ('chest', 'spine', 'hips')
DIRS = [Vector(d).normalized() for d in ((1, 0.1, 0.05), (-1, 0.05, 0.1), (0.05, 1, 0.1), (0.1, -1, 0.05), (0.05, 0.1, 1))]
def inside(bvh, p):
    k = 0
    for dv in DIRS:
        q = p.copy(); c = 0
        for _ in range(30):
            hit = bvh.ray_cast(q, dv)
            if hit[0] is None: break
            c += 1; q = hit[0] + dv * 1e-5
        k += c % 2
    return k >= 3
for f in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.open_mainfile(filepath=f)
    dg = bpy.context.evaluated_depsgraph_get(); hi = bpy.data.objects['Hi']
    me = hi.evaluated_get(dg).to_mesh(); n = len(me.vertices)
    P = np.zeros(n * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
    N = np.zeros(n * 3); me.vertices.foreach_get('normal', N); N = N.reshape(-1, 3)
    bvh = BVHTree.FromObject(hi, dg)
    out = []
    for L, s in (('L', 1), ('R', -1)):
        sh = R['bh'][bn.index('upper_arm.' + L)]
        far = np.linalg.norm(co0 - sh, axis=1) > 0.11                      # away from the shoulder / armpit (rest)
        arm = np.where(np.isin(main, [a + '.' + L for a in ARM]) & far)[0]
        tor = np.where(np.isin(main, TOR) & (np.linalg.norm(co0 - sh, axis=1) > 0.09))[0]
        d, j = cKDTree(P[tor]).query(P[arm])
        cand = arm[d < 0.02]                                               # only arm skin near the torso can be inside it
        bad = [i for i in cand[::2] if inside(bvh, Vector(P[i] + N[i] * 0.0015))]
        if bad and os.environ.get('WHERE'):
            b=np.array(bad); r_=np.linalg.norm(co0[b]-sh,axis=1)
            print('  ',L,'rest dist to shoulder cm: p10 %.1f p50 %.1f p90 %.1f'%tuple(np.percentile(r_*100,[10,50,90])),'labels',{k:int((main[b]==k).sum()) for k in set(main[b])},'torso hit labels',{k:int(v) for k,v in zip(*np.unique(main[tor][j[np.isin(arm,b)]],return_counts=True))})
        out.append('%s gap %.1f mm, arm skin inside the torso: %d pts' % (L, d.min() * 1000, len(bad)))
    print(os.path.basename(f), ' | '.join(out))
