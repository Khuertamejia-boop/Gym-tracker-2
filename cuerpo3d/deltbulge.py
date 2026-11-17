# Rounder shoulders when the arm is raised (owner 04-11-2026: «el hombro debería verse más redondo y no tan plano»):
# with the arm up the skinning stretches the deltoid into a flat band. Every deltoid vertex (atlas pv/bla.npz, the
# three heads as one muscle) moves out along its posed normal by DBBULGE * lift * smoothstep(dome), dome = the round
# per-muscle profile of pv/bla_dome.npz (0 on the border, 1 on top): zero and flat at the border, so no seam.
# Runs on the baked mesh (after arap2.py).   usage: P=.. python deltbulge.py in.blend out.blend
#   env: P (pose 0..1, the lift is smoothstep(P) as in dblbiceps.py), DBBULGE (m, 0.010), DBBP (shape power, 1)
import bpy, sys, os, numpy as np
src, out = sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
P = E('P', 0.0); lift = float(ss(P))
here = os.environ.get('GT3D', os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=src)
hi = bpy.data.objects['Hi']; me = hi.data; nv = len(me.vertices)
A = np.load(os.path.join(here, 'ill', 'pv', 'bla.npz'), allow_pickle=True)
D = np.load(os.path.join(here, 'ill', 'pv', 'bla_dome.npz'), allow_pickle=True)
names = [str(x) for x in A['names']]; mid = A['mid'].astype(int)        # names[0] is already 'none'
assert len(mid) == nv, (len(mid), nv)
sel = np.isin(mid, [i for i, n in enumerate(names) if n.startswith('deltoid')])
R = np.load(os.path.join(here, 'ill', 'rest.npz'), allow_pickle=True); co0 = R['co']
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
nr = np.zeros(nv * 3); me.vertices.foreach_get('normal', nr); nr = nr.reshape(-1, 3)
mode = os.environ.get('DBMODE', 'tip')
if mode == 'dome':
    w = ss(D['domeraw']) ** E('DBBP', 1.0) * sel
elif mode == 'rest':
    # one smooth round swelling per shoulder: gaussian (rest coordinates) around the centre of the deltoid
    w = np.zeros(nv)
    for s_ in (1, -1):
        side = sel & (co0[:, 0] * s_ > 0); c = co0[side].mean(0)
        w = np.maximum(w, np.exp(-(np.linalg.norm(co0 - c, axis=1) / E('DBSIG', 0.05)) ** 2))
else:
    # 'tip' (default): gaussian in the POSED body over the top of the shoulder: from the shoulder joint DBA along the
    # upper arm, DBY back and DBZ up (m). That is where the raised arm looks flat (straight line from the trapezius).
    rig = bpy.data.objects['Rig']; pb = rig.pose.bones; w = np.zeros(nv)
    for L in 'LR':
        h = np.array(pb['upper_arm.' + L].head); t = np.array(pb['upper_arm.' + L].tail); u = (t - h) / np.linalg.norm(t - h)
        c = h + u * E('DBA', 0.045) + np.array([0, E('DBY', 0.02), E('DBZ', 0.035)])
        w = np.maximum(w, np.exp(-(np.linalg.norm(co - c, axis=1) / E('DBSIG', 0.045)) ** 2))
        print(L, 'shoulder joint', np.round(h, 3), 'bulge centre', np.round(c, 3))
w[w < 0.01] = 0
d = E('DBBULGE', 0.010) * lift * w
V = nr * d[:, None]
# smooth the displacement over the surface (noisy normals of the stretched skin would make it lumpy)
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
act = np.where(d > 0)[0]
if len(act) and E('DBSM', 15) > 0:
    import scipy.sparse as sp
    Ad = sp.coo_matrix((np.ones(len(ed) * 2), (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
    dg_ = np.asarray(Ad.sum(1)).ravel(); dg_[dg_ == 0] = 1
    for _ in range(int(E('DBSM', 15))): V = 0.5 * V + 0.5 * (Ad @ V) / dg_[:, None]
co = co + V
d = np.linalg.norm(V, axis=1)
me.vertices.foreach_set('co', co.ravel()); me.update()
print('deltoid bulge: lift %.2f max %.1f mm on %d verts' % (lift, d.max() * 1000, int((d > 1e-5).sum())))
bpy.ops.wm.save_as_mainfile(filepath=out)
