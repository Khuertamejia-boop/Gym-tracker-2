# pecfix.py (11-11-2026) -- pectoral that reaches the arm (owner: «ahora trabaja en el pectoral»).
#   With the arm raised the pec must sweep up into the arm (front fold of the armpit). In the doll its outer edge stayed
#   on the chest (square block) and a band of flank skin (serratus label, white) filled the fold up to the arm.
#   Fix = the skin SLIDES over the surface, the shape does not change: every front-facing vertex of the region moves
#   sideways in the front view (x) by PAMP * lift * A(height) * k(x) and is put back on the posed surface (ray along y).
#     k(x): 0 at XIN, 1 at the pec edge X0, back to 0 at the arm junction XJ (the white band is squeezed into the groove)
#     A(z): 0 below Z0, 1 at Z1, 0 again at ZT            (all offsets from the shoulder joint, metres)
#   PCOR > 0: the lower outer corner also slides up (gaussian of radius PCS around the corner PCX / PCZ).
#   usage: python pecfix.py in.blend out.blend   env: PAMP (0.045) XIN (-0.06) X0 (0.021) XJ (0.085) Z0 (-0.108)
#          Z1 (-0.028) ZT (0.0) PCOR (0) PCX (-0.01) PCZ (-0.155) PCS (0.035) PDP (0.045) A0/A1 (35 / 85)
import bpy, sys, os, math, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
import scipy.sparse as sp
src, out = sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
bpy.ops.wm.open_mainfile(filepath=src)
me = bpy.data.objects['Hi'].data; nv = len(me.vertices); pb = bpy.data.objects['Rig'].pose.bones
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
nr = np.zeros(nv * 3); me.vertices.foreach_get('normal', nr); nr = nr.reshape(-1, 3)
me.calc_loop_triangles(); tri = np.zeros(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get('vertices', tri)
bvh = BVHTree.FromPolygons([Vector(c) for c in co], [tuple(t) for t in tri.reshape(-1, 3)])
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
Ad = sp.coo_matrix((np.ones(len(ed) * 2), (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
dg = np.asarray(Ad.sum(1)).ravel(); dg[dg == 0] = 1
new = co.copy(); D = Vector((0, 1, 0))
for L in 'LR':
    h = np.array(pb['upper_arm.' + L].head); e = np.array(pb['forearm.' + L].head); sg = 1.0 if h[0] > 0 else -1.0
    a = (e - h) / np.linalg.norm(e - h)
    ang = math.degrees(math.acos(np.clip(a @ np.array([0, 0, -1.0]), -1, 1)))
    lift = float(ss((ang - E('A0', 35)) / (E('A1', 85) - E('A0', 35))))
    X = co[:, 0] * sg - h[0] * sg; Z = co[:, 2] - h[2]
    xin, x0, xj = E('XIN', -0.06), E('X0', 0.021), E('XJ', 0.085); z0, z1, zt = E('Z0', -0.108), E('Z1', -0.028), E('ZT', 0.0)
    k = np.where(X < x0, ss((X - xin) / (x0 - xin)), np.clip((xj - X) / (xj - x0), 0, 1))
    A = ss((Z - z0) / (z1 - z0)) * ss((zt - Z) / (zt - z1))
    dx = E('PAMP', 0.045) * lift * A * k
    g = np.exp(-0.5 * (((X - E('PCX', -0.01)) ** 2 + (Z - E('PCZ', -0.155)) ** 2) / E('PCS', 0.035) ** 2))
    dz = E('PCOR', 0.0) * lift * g; dx = dx + 0.4 * dz
    # warp in the front view: the vertex moves sideways and keeps its depth BEHIND the visible surface (S = depth of the
    # first surface the camera sees at that point), so the visible skin stays exactly on the posed surface and what
    # hangs just behind it (ledges, the groove of the armpit) follows without folding; fades out PDP m behind the surface
    n = 0; ry = lambda x, z: bvh.ray_cast(Vector((x, -2.0, z)), D)[0]
    for i in np.nonzero((np.hypot(dx, dz) > 1e-4) & (co[:, 1] < h[1] + 0.04))[0]:
        p = co[i]; h0 = ry(p[0], p[2])
        if h0 is None: continue
        wd = float(ss((E('PDP', 0.045) - (p[1] - h0[1])) / 0.025))
        if wd <= 0: continue
        x1 = p[0] + sg * dx[i] * wd; z1_ = p[2] + dz[i] * wd; h1 = ry(x1, z1_)
        if h1 is None or abs(h1[1] - h0[1]) > 0.06: continue
        new[i] = (x1, p[1] + (h1[1] - h0[1]) * wd, z1_); n += 1
    print('%s: arm raised %.0f deg, lift %.2f, verts moved %d' % (L, ang, lift, n))
me.vertices.foreach_set('co', new.ravel()); me.update()
print('pecfix done')
bpy.ops.wm.save_as_mainfile(filepath=out)
