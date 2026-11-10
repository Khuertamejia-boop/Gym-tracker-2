# Round shoulder for raised arms (owner 10-11-2026: «los hombros se ven en punta, antinatural; como plástico mal doblado»).
# Linear skinning stretches the deltoid into a flat band with a ridge when the arm goes up. Here the deltoid is
# modelled as an ELLIPSOID fixed to the posed upper arm (swing only, not the humeral twist): centre a little down the
# arm from the humeral head and a little lateral, radii RA along the arm, RB across. Skin that belongs to the shoulder
# (rest distance to the humeral head < R1, lateral of the torso) and lies INSIDE the ellipsoid is pushed out to its
# surface; the displacement is then smoothed over the surface so the ball blends into the trapezius, the chest and
# the arm without a crease. Runs on the baked mesh (after arap2.py / untwist.py).
#   usage: python shoulderfix.py in.blend out.blend
#   env: DA (centre along the arm, m, 0.030), DL (centre lateral, 0.012), DUP (centre up, along arm x lateral, 0.0),
#        RA (radius along the arm, 0.070), RB (radius across, 0.058), R0/R1 (rest mask, 0.09 / 0.15),
#        XMIN (lateral limit of the mask, 0.10), SM (smoothing iterations, 12), K (strength 0..1, 1),
#        LOWK (how much the lower, armpit side of the ellipsoid pushes, 0.35)
import bpy, sys, os, numpy as np
import scipy.sparse as sp
src, out = sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
here = os.environ.get('GT3D', os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=src)
hi = bpy.data.objects['Hi']; me = hi.data; nv = len(me.vertices); rig = bpy.data.objects['Rig']; pb = rig.pose.bones; bb = rig.data.bones
R = np.load(os.path.join(here, 'ill', 'rest.npz'), allow_pickle=True); co0 = R['co']
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
Ad = sp.coo_matrix((np.ones(len(ed) * 2), (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
dg = np.asarray(Ad.sum(1)).ravel(); dg[dg == 0] = 1
V = np.zeros_like(co); wall = np.zeros(nv)
chest = np.array(pb['chest'].head)
for L, s in (('L', 1), ('R', -1)):
    h0 = np.array(bb['upper_arm.' + L].head_local)
    d0 = np.linalg.norm(co0 - h0, axis=1)
    w = ss((E('R1', 0.15) - d0) / (E('R1', 0.15) - E('R0', 0.09))) * ss((co0[:, 0] * s - E('XMIN', 0.10)) / 0.03)
    w *= E('K', 1.0) * float(ss(E('P', 1.0)))                  # P: pose 0..1 (rest frame untouched, as deltbulge.py)
    h = np.array(pb['upper_arm.' + L].head); t = np.array(pb['upper_arm.' + L].tail); u = (t - h) / np.linalg.norm(t - h)
    lat = h - chest; lat -= u * (lat @ u); lat /= np.linalg.norm(lat)          # away from the torso, across the arm
    up = np.cross(u, lat); up /= np.linalg.norm(up)
    if up[2] < 0: up = -up
    c = h + u * E('DA', 0.030) + lat * E('DL', 0.012) + up * E('DUP', 0.0)
    ra, rb = E('RA', 0.070), E('RB', 0.058)
    idx = np.where(w > 1e-3)[0]
    q = co[idx] - c
    e = np.stack([q @ u / ra, q @ lat / rb, q @ up / rb], 1); f = np.linalg.norm(e, axis=1)
    inside = f < 1.0
    # push radially (in the ellipsoid frame) to the surface; the armpit side (lat < 0) pushes less
    k = np.where(inside, (1.0 / np.maximum(f, 1e-3) - 1.0), 0.0)
    side = ss((e[:, 1] + 0.6) / 0.6) * (1 - E('LOWK', 0.35)) + E('LOWK', 0.35)
    disp = q * (k * side)[:, None]
    V[idx] += disp * w[idx, None]; wall[idx] = np.maximum(wall[idx], w[idx])
    print('%s: shoulder ball centre %s, %d verts in mask, %d inside, max push %.1f mm' % (L, np.round(c, 3), len(idx), int(inside.sum()), np.linalg.norm(disp, axis=1).max() * 1000))
# smooth the displacement over the surface (inside the mask region only), then apply
act = wall > 1e-3
for _ in range(int(E('SM', 12))):
    V = 0.5 * V + 0.5 * (Ad @ V) / dg[:, None]
    V[~act] = 0
co = co + V
me.vertices.foreach_set('co', co.ravel()); me.update()
print('shoulderfix: moved %d verts, max %.1f mm' % (int((np.linalg.norm(V, axis=1) > 1e-4).sum()), np.linalg.norm(V, axis=1).max() * 1000))
bpy.ops.wm.save_as_mainfile(filepath=out)
