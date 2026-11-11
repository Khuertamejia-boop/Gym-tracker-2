# slimfix.py (11-11-2026) -- biceps and shoulders SLIM% smaller (owner: «bájale un poco al tamaño de bíceps y hombros
#   porque están muy grandes, diría que un 15 %»). The top / front / back of the upper arm and of the shoulder cap moves
#   towards the arm axis by SLIM * its own distance to the axis (a scaling, so the round shapes of elbowfix.py /
#   deltfix.py are kept, only smaller); nothing on the underside (triceps) nor beyond the elbow; only with the arm raised.
#   usage: python slimfix.py in.blend out.blend   env: SLIM (0.15) SS0 / SS1 (-0.22 / 0.92: range along the arm)
#          SCF (0.5: how far round the arm, 0 = top half only) SSM (8) A0/A1 (35 / 85)
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
ok = np.array([m.startswith(('chest', 'clavicle', 'upper_arm')) for m in main])
V = np.zeros_like(co)
for L in 'LR':
    h = np.array(pb['upper_arm.' + L].head); e = np.array(pb['forearm.' + L].head); sg = 1.0 if h[0] > 0 else -1.0
    a = (e - h); La = np.linalg.norm(a); a /= La
    ang = math.degrees(math.acos(np.clip(a @ np.array([0, 0, -1.0]), -1, 1)))
    lift = float(ss((ang - E('A0', 35)) / (E('A1', 85) - E('A0', 35))))
    up = np.array([0, 0, 1.0]) - a * a[2]; up /= np.linalg.norm(up)
    q = co - h; s = (q @ a) / La; rad = q - np.outer(q @ a, a); rr = np.linalg.norm(rad, axis=1)
    cu = (rad @ up) / np.maximum(rr, 1e-6); cf = E('SCF', 0.5)
    w = ss((s - E('SS0', -0.22)) / 0.12) * ss((E('SS1', 0.92) - s) / 0.15) * np.clip((cu + cf) / (1 + cf), 0, 1) ** 0.7
    w = w * (rr < 0.13) * ok * (co[:, 0] * sg > 0.06) * lift
    V -= rad * (E('SLIM', 0.15) * w)[:, None]
    print('%s: arm raised %.0f deg, lift %.2f, verts %d, max %.1f mm' % (L, ang, lift, int((w > 0.02).sum()), (rr * w).max() * E('SLIM', 0.15) * 1000))
for _ in range(int(E('SSM', 8))): V = 0.5 * V + 0.5 * (Ad @ V) / dg[:, None]
me.vertices.foreach_set('co', (co + V).ravel()); me.update()
print('slimfix done')
bpy.ops.wm.save_as_mainfile(filepath=out)
