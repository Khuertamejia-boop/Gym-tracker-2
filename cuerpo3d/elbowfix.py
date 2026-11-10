# Natural bent elbow (owner 10-11-2026: «la sangradura no se ve natural»). Two things, on the baked mesh:
#  1. biceps peak: the biceps / brachialis belly (atlas labels) bulges along its normal with the elbow flexion,
#     with the per-muscle dome profile (pv/bla_dome.npz: 0 at the border, 1 on top), amplitude BAMP * flex.
#  2. soft inner crease: the skin on the inner side of the elbow (within ER of the joint, on the side of the
#     bisector of the upper arm and the forearm) is relaxed (Laplacian smoothing of the positions, ESM iterations)
#     and kept outside a small sphere at the joint (radius EJR), so the fold is a rounded valley, not a V.
# flex = smoothstep((angle between upper arm and forearm - F0) / (F1 - F0)), computed from the posed bones.
#   usage: python elbowfix.py in.blend out.blend     env: BAMP (0.014), F0/F1 (20 / 100 deg), ER (0.05), ESM (8),
#          EJR (0.040), EK (crease strength 0..1, 1), MUS (labels, 'biceps_brachii,brachialis')
import bpy, sys, os, math, numpy as np
import scipy.sparse as sp
src, out = sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
here = os.environ.get('GT3D', os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=src)
hi = bpy.data.objects['Hi']; me = hi.data; nv = len(me.vertices); rig = bpy.data.objects['Rig']; pb = rig.pose.bones
A = np.load(os.path.join(here, 'ill', 'pv', 'bla.npz'), allow_pickle=True); names = [str(x) for x in A['names']]; mid = A['mid'].astype(int)
D = np.load(os.path.join(here, 'ill', 'pv', 'bla_dome.npz'), allow_pickle=True); dome = ss(D['domeraw'])
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
nr = np.zeros(nv * 3); me.vertices.foreach_get('normal', nr); nr = nr.reshape(-1, 3)
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
Ad = sp.coo_matrix((np.ones(len(ed) * 2), (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
dg = np.asarray(Ad.sum(1)).ravel(); dg[dg == 0] = 1
MUS = os.environ.get('MUS', 'biceps_brachii,brachialis').split(',')
V = np.zeros_like(co); crease_w = np.zeros(nv)
for L in 'LR':
    h = np.array(pb['upper_arm.' + L].head); e = np.array(pb['forearm.' + L].head); w_ = np.array(pb['forearm.' + L].tail)
    u = (h - e) / np.linalg.norm(h - e); f = (w_ - e) / np.linalg.norm(w_ - e)
    ang = math.degrees(math.acos(np.clip(u @ f, -1, 1)))                   # 180 = straight, small = fully bent
    flex = float(ss((180 - ang - E('F0', 20)) / (E('F1', 100) - E('F0', 20))))
    # 1. biceps peak
    lab = np.array([any(n == m + '.' + L for m in MUS) for n in names])[mid]
    amp = E('BAMP', 0.014) * flex * dome * lab
    V += nr * amp[:, None]
    # 2. inner crease: mask in the pose
    bis = u + f; bis /= np.linalg.norm(bis)                                 # points into the crease (inner side)
    q = co - e; d = np.linalg.norm(q, axis=1)
    cw = ss((E('ER', 0.05) - d) / 0.02) * ss(((q @ bis) / np.maximum(d, 1e-6) - 0.1) / 0.4) * flex * E('EK', 1.0)
    crease_w = np.maximum(crease_w, cw)
    print('%s: elbow angle %.0f deg, flex %.2f, biceps verts %d (max %.1f mm), crease verts %d' % (L, ang, flex, int((amp > 1e-4).sum()), amp.max() * 1000, int((cw > 0.05).sum())))
co = co + V
# relax the crease region: smoothed positions blended by the mask, then kept outside the joint sphere
act = crease_w > 1e-3
if act.any():
    X = co.copy()
    for _ in range(int(E('ESM', 8))):
        Xs = (Ad @ X) / dg[:, None]; X = np.where(act[:, None], X + crease_w[:, None] * 0.5 * (Xs - X), X)
    co = X
    for L in 'LR':
        e = np.array(pb['forearm.' + L].head); q = co - e; d = np.linalg.norm(q, axis=1); r = E('EJR', 0.040)
        push = act & (d < r) & (d > 1e-6)
        co[push] = e + q[push] * (r / d[push])[:, None]
me.vertices.foreach_set('co', co.ravel()); me.update()
print('elbowfix done')
bpy.ops.wm.save_as_mainfile(filepath=out)
