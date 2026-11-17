# Hollow armpit for raised arms (owner 10-11-2026: «las axilas no se ven naturales»). With the arm up, the skin between
# the arm and the chest stretched into a taut flat web. In reality the armpit is a hollow: the skin stays close to the
# joint, between the anterior fold (pectoral) and the posterior fold (lat / teres). Here the armpit skin (rest mask:
# below and inside the humeral head, between the chest wall and the arm) that lies OUTSIDE a sphere of radius RAX
# around the joint is pulled in to that sphere, with strength K * smoothstep(P); the pull is smoothed over the surface.
# Runs on the baked mesh (after shoulderfix.py).   usage: python armpitfix.py in.blend out.blend
#   env: RAX (0.055), DA (sphere centre along the arm, 0.015), K (1.0), P (pose 0..1), R0/R1 (rest mask radii
#        0.06 / 0.12), ZB (mask: rest z below the head by this, 0.015), SM (smoothing, 10)
import bpy, sys, os, numpy as np
import scipy.sparse as sp
src, out = sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
here = os.environ.get('GT3D', os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=src)
hi = bpy.data.objects['Hi']; me = hi.data; nv = len(me.vertices); rig = bpy.data.objects['Rig']; pb = rig.pose.bones; bb = rig.data.bones
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
Ad = sp.coo_matrix((np.ones(len(ed) * 2), (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
dg = np.asarray(Ad.sum(1)).ravel(); dg[dg == 0] = 1
V = np.zeros_like(co); wall = np.zeros(nv); lift = float(ss(E('P', 1.0)))
A = np.load(os.path.join(here, 'ill', 'pv', 'bla.npz'), allow_pickle=True); names = [str(x) for x in A['names']]; mid = A['mid'].astype(int)
fold = np.array([n.startswith(('pec_', 'latissimus', 'teres_major')) for n in names])[mid]     # the two folds keep their shape
chest = np.array(pb['chest'].head)
for L, s in (('L', 1), ('R', -1)):
    h = np.array(pb['upper_arm.' + L].head); t = np.array(pb['upper_arm.' + L].tail); u = (t - h) / np.linalg.norm(t - h)
    lat = h - chest; lat -= u * (lat @ u); lat /= np.linalg.norm(lat)
    q = co - h; d = np.linalg.norm(q, axis=1); sa = q @ u; med = -(q @ lat)
    # posed mask: the hollow under the joint, between the arm and the chest wall
    w = ss((E('R1', 0.11) - d) / 0.03) * ss((E('SA', 0.03) - sa) / 0.02) * ss((h[2] - 0.005 - co[:, 2]) / 0.02) * ss((med + 0.02) / 0.03)
    w *= (co[:, 0] * s > 0.08) * (~fold) * E('K', 1.0) * lift
    c = h + u * E('DA', 0.015); rax = E('RAX', 0.045)
    idx = np.where(w > 1e-3)[0]
    qq = co[idx] - c; r = np.linalg.norm(qq, axis=1)
    k = np.clip(1.0 - rax / np.maximum(r, 1e-6), 0, None)
    disp = -qq * k[:, None]
    V[idx] += disp * w[idx, None]; wall[idx] = np.maximum(wall[idx], w[idx])
    print('%s: armpit mask %d verts, max pull %.1f mm' % (L, len(idx), np.linalg.norm(disp, axis=1).max() * 1000 if len(idx) else 0))
act = wall > 1e-3
for _ in range(int(E('SM', 10))):
    V = 0.5 * V + 0.5 * (Ad @ V) / dg[:, None]
    V[~act] = 0
co = co + V
me.vertices.foreach_set('co', co.ravel()); me.update()
print('armpitfix: moved %d verts, max %.1f mm' % (int((np.linalg.norm(V, axis=1) > 1e-4).sum()), np.linalg.norm(V, axis=1).max() * 1000))
bpy.ops.wm.save_as_mainfile(filepath=out)
