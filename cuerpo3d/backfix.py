# backfix.py (11-11-2026) -- back of the double biceps (owner: «trabaja en la espalda»).
#   Measured in the pose: the rear of the shoulder (posterior deltoid) sat ~30 mm IN FRONT of the shoulder blade
#   (infraspinatus / teres) just below it, so from behind the deltoid read as a separate ball over a step; and the
#   middle of the back was one wide shallow valley, without the ridges beside the spine of squeezed shoulder blades.
#   1. rear deltoid: the skin moves radially away from the arm axis, towards the BACK, by
#      RAMP * lift * profile(along the arm, centre RS0, widths RSA towards the spine / RSB towards the elbow) * lobe
#   2. ridges beside the spine: the skin of the back moves backwards MAMP * lift * gauss(|x|, centre MX0, width MXS)
#      * window(height t: 0 at MT0, 1 from MT1 to MT2, 0 at MT3; t = 0 at the 'spine' bone head, 1 at the shoulder joint)
#   lift = how far the arm is raised (0 below A0 deg from hanging, 1 above A1) -> nothing changes with the arms down.
#   usage: python backfix.py in.blend out.blend   env: RAMP (0.022) RS0 (0.08) RSA (0.16) RSB (0.25) RCP (0.8)
#          MAMP (0.010) MX0 (0.038) MXS (0.018) MT0/MT1/MT2/MT3 (0.37 / 0.52 / 0.92 / 1.07) BKSM (8) CSM (30) SAMP (0.009) SX0 / SXJ (0.018 / 0.14) ST0 / ST3 (0.30 / 1.08) CX0/CX1 (0.11 / 0.31) CZ0/CZ1 (-0.15 / -0.04) A0/A1 (35 / 85)
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
nr = np.zeros(nv * 3); me.vertices.foreach_get('normal', nr); nr = nr.reshape(-1, 3)
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
Ad = sp.coo_matrix((np.ones(len(ed) * 2), (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
dg = np.asarray(Ad.sum(1)).ravel(); dg[dg == 0] = 1
trunk = np.array([m.startswith(('chest', 'spine', 'CS', 'clavicle')) for m in main])
okd = np.array([m.startswith(('chest', 'spine', 'CS', 'clavicle', 'upper_arm')) for m in main])
zs = float(np.array(pb['spine'].head)[2]); V = np.zeros_like(co); lifts = []
for L in 'LR':
    h = np.array(pb['upper_arm.' + L].head); e = np.array(pb['forearm.' + L].head); sg = 1.0 if h[0] > 0 else -1.0
    a = (e - h); La = np.linalg.norm(a); a /= La
    ang = math.degrees(math.acos(np.clip(a @ np.array([0, 0, -1.0]), -1, 1)))
    lift = float(ss((ang - E('A0', 35)) / (E('A1', 85) - E('A0', 35)))); lifts.append(lift)
    up = np.array([0, 0, 1.0]) - a * a[2]; up /= np.linalg.norm(up); bd = np.cross(a, up); bd *= np.sign(bd[1])
    q = co - h; s = (q @ a) / La; rad = q - np.outer(q @ a, a); rr = np.linalg.norm(rad, axis=1)
    cb = (rad @ bd) / np.maximum(rr, 1e-6)
    ds = s - E('RS0', 0.08); g = np.exp(-0.5 * np.abs(ds / np.where(ds < 0, E('RSA', 0.16), E('RSB', 0.25))) ** 2.6)
    w = g * np.clip((cb + 0.2) / 1.2, 0, 1) ** E('RCP', 0.8) * (rr < 0.13) * okd * (co[:, 0] * sg > 0.06) * lift
    V += rad / np.maximum(rr, 1e-6)[:, None] * (E('RAMP', 0.022) * w)[:, None]
    t = (co[:, 2] - zs) / (h[2] - zs)
    win = ss((t - E('MT0', 0.37)) / (E('MT1', 0.52) - E('MT0', 0.37))) * ss((E('MT3', 1.07) - t) / (E('MT3', 1.07) - E('MT2', 0.92)))
    gx = np.exp(-0.5 * ((co[:, 0] * sg - E('MX0', 0.038)) / E('MXS', 0.018)) ** 2)
    wm = win * gx * trunk * ss((nr[:, 1] - 0.2) / 0.3) * lift
    V[:, 1] += E('MAMP', 0.010) * wm
    print('%s: arm raised %.0f deg, lift %.2f, rear delt verts %d, ridge verts %d' % (L, ang, lift, int((w > 0.02).sum()), int((wm > 0.02).sum())))
for _ in range(int(E('BKSM', 8))): V = 0.5 * V + 0.5 * (Ad @ V) / dg[:, None]
co = co + V
# 3. the crease between the rear deltoid and the shoulder blade (teres / infraspinatus) is relaxed: positions smoothed
#    CSM times inside a box under the back of the shoulder (x CX0..CX1 from the midline, z CZ0..CZ1 from the joint)
C = np.zeros(nv)
for L, lift in zip('LR', lifts):
    h = np.array(pb['upper_arm.' + L].head); sg = 1.0 if h[0] > 0 else -1.0; X = co[:, 0] * sg; Z = co[:, 2] - h[2]
    c = ss((X - E('CX0', 0.11)) / 0.03) * ss((E('CX1', 0.31) - X) / 0.03) * ss((Z - E('CZ0', -0.15)) / 0.03) * ss((E('CZ1', -0.04) - Z) / 0.03)
    C = np.maximum(C, c * ss((nr[:, 1] + 0.1) / 0.3) * okd * lift)
X = co.copy()
for _ in range(int(E('CSM', 30))): X = X + (C * 0.5)[:, None] * ((Ad @ X) / dg[:, None] - X)
co = X
# 4. squeezed shoulder blades: the skin of the middle of the back SLIDES towards the spine over the surface (same
#    method as pecfix.py, seen from behind): the white strip of the spine gets narrower and the muscles reach it.
#    x moves SAMP * lift * A(height) * k(|x|) towards the midline; k: 0 on the midline, 1 at SX0, 0 again at SXJ
if E('SAMP', 0.009) > 0:
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    me.calc_loop_triangles(); tri = np.zeros(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get('vertices', tri)
    bvh = BVHTree.FromPolygons([Vector(c) for c in co], [tuple(t) for t in tri.reshape(-1, 3)]); Dn = Vector((0, -1, 0))
    ry = lambda x, z: bvh.ray_cast(Vector((x, 2.0, z)), Dn)[0]
    new = co.copy(); n = 0
    for L, lift in zip('LR', lifts):
        h = np.array(pb['upper_arm.' + L].head); sg = 1.0 if h[0] > 0 else -1.0; X = co[:, 0] * sg
        t = (co[:, 2] - zs) / (h[2] - zs); x0, xj = E('SX0', 0.018), E('SXJ', 0.14)
        A = ss((t - E('ST0', 0.30)) / 0.15) * ss((E('ST3', 1.08) - t) / 0.13)
        k = np.where(X < x0, np.clip(X / x0, 0, 1), np.clip((xj - X) / (xj - x0), 0, 1))
        dx = E('SAMP', 0.009) * lift * A * k * trunk
        for i in np.nonzero((dx > 1e-4) & (X > 0) & (nr[:, 1] > -0.2))[0]:
            p = co[i]; h0 = ry(p[0], p[2])
            if h0 is None: continue
            wd = float(ss((0.045 - (h0[1] - p[1])) / 0.025))
            if wd <= 0: continue
            x1 = p[0] - sg * dx[i] * wd; h1 = ry(x1, p[2])
            if h1 is None or abs(h1[1] - h0[1]) > 0.05: continue
            new[i] = (x1, p[1] + (h1[1] - h0[1]) * wd, p[2]); n += 1
    co = new; print('slide verts', n)
me.vertices.foreach_set('co', co.ravel()); me.update()
print('backfix done')
bpy.ops.wm.save_as_mainfile(filepath=out)
