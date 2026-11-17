# deltfix.py (11-11-2026) -- round shoulder: with the arm raised the deltoid must read as a dome over the head of the
# humerus (owner: «dale ese tipo de redondez al hombro», same recipe as the biceps mound of elbowfix.py).
#   the skin around the shoulder joint moves RADIALLY away from the arm axis by
#   DAMP * lift * profile(along the arm, centre DS0, widths DSA towards the neck / DSB towards the elbow, exponent DPW)
#        * lobe(angle around the arm, centred on "up", wide: front and back of the deltoid too; power DCP, floor DCF)
#   lift = how far the arm is raised (0 below A0 deg from hanging, 1 above A1).  DSMP = light smoothing of the cap first.
#   usage: python deltfix.py in.blend out.blend     env: DAMP (0.010) DS0 (0.06) DSA (0.17) DSB (0.22) DPW (2.6)
#          DCP (0.7) DCF (0.35) DSMP (4) DSM (10) A0/A1 (35 / 85)
import bpy, sys, os, math, numpy as np
import scipy.sparse as sp
src, out = sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
here = os.environ.get('GT3D', os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=src)
me = bpy.data.objects['Hi'].data; nv = len(me.vertices); pb = bpy.data.objects['Rig'].pose.bones
main = np.array([str(x) for x in np.load(os.path.join(here, 'ill', 'rest.npz'), allow_pickle=True)['main']])
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
Ad = sp.coo_matrix((np.ones(len(ed) * 2), (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
dg = np.asarray(Ad.sum(1)).ravel(); dg[dg == 0] = 1
low = np.array([m.startswith(('forearm', 'hand', 'fa_tw', 'f_', 'thumb', 'palm', 'head', 'neck', 'spine.004', 'spine.005', 'spine.006')) for m in main])
V = np.zeros_like(co); W = np.zeros(nv)
for L in 'LR':
    h = np.array(pb['upper_arm.' + L].head); e = np.array(pb['forearm.' + L].head)
    a = (e - h); La = np.linalg.norm(a); a /= La
    ang = math.degrees(math.acos(np.clip(a @ np.array([0, 0, -1.0]), -1, 1)))
    lift = float(ss((ang - E('A0', 35)) / (E('A1', 85) - E('A0', 35))))
    up = np.array([0, 0, 1.0]) - a * a[2]; up /= np.linalg.norm(up)
    q = co - h; s = (q @ a) / La; rad = q - np.outer(q @ a, a); rr = np.linalg.norm(rad, axis=1)
    cu = (rad @ up) / np.maximum(rr, 1e-6)
    ds = s - E('DS0', 0.06); g = np.exp(-0.5 * np.abs(ds / np.where(ds < 0, E('DSA', 0.17), E('DSB', 0.22))) ** E('DPW', 2.6))
    cf = E('DCF', 0.35); lobe = np.clip((cu + cf) / (1 + cf), 0, 1) ** E('DCP', 0.7)
    w = g * lobe * (rr < 0.12) * (~low) * ((h[0] > 0) == (co[:, 0] > 0)) * lift
    V += rad / np.maximum(rr, 1e-6)[:, None] * (E('DAMP', 0.010) * w)[:, None]; W = np.maximum(W, w)
    print('%s: arm raised %.0f deg, lift %.2f, verts %d' % (L, ang, lift, int((w > 0.02).sum())))
if W.max() > 0:
    X = co.copy()
    for _ in range(int(E('DSMP', 4))): X = X + (W * 0.5)[:, None] * ((Ad @ X) / dg[:, None] - X)
    for _ in range(int(E('DSM', 10))): V = 0.5 * V + 0.5 * (Ad @ V) / dg[:, None]
    co = X + V
    me.vertices.foreach_set('co', co.ravel()); me.update()
print('deltfix done')
bpy.ops.wm.save_as_mainfile(filepath=out)
