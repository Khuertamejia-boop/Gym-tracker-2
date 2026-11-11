# Keep the deltoid dome (11-11-2026). arap2.py relaxes the shoulder skin (clean armpit, no pinches) but with the arm
# raised it also flattens the top of the shoulder: the skin over the joint sinks to the level of the bone, the deltoid
# loses its volume («hombro plano / en punta») and the biceps looks like a balloon on a thin arm. The plain skinning
# (CoR) keeps a good dome on top but folds the armpit. So: the TOP of the shoulder comes from the skinned mesh and the
# UNDERSIDE from the relaxed one, blended by the height above the axis of the posed upper arm.
#   usage: python capkeep.py skinned.blend relaxed.blend out.blend     (out = relaxed file with the new positions)
#   env: Y0 / Y1 (height above the arm axis where the blend starts / is complete, m: -0.035 / 0.010),
#        SA0 / SA1 (window along the arm, from the joint: -0.14 .. 0.26, fades 0.06 / 0.08), SM (smoothing of the mask, 8), K (1)
import bpy, sys, os, numpy as np
import scipy.sparse as sp
skin, relaxed, out = sys.argv[-3], sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
def coords(f):
    bpy.ops.wm.open_mainfile(filepath=f)
    hi = bpy.data.objects['Hi']
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(hi.evaluated_get(dg), depsgraph=dg)
    c = np.zeros(len(m.vertices) * 3); m.vertices.foreach_get('co', c); return c.reshape(-1, 3)
Xs = coords(skin)
bpy.ops.wm.open_mainfile(filepath=relaxed)
hi = bpy.data.objects['Hi']; me = hi.data; nv = len(me.vertices); pb = bpy.data.objects['Rig'].pose.bones
Xr = np.zeros(nv * 3); me.vertices.foreach_get('co', Xr); Xr = Xr.reshape(-1, 3)
assert len(Xs) == nv
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
Ad = sp.coo_matrix((np.ones(len(ed) * 2), (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
dg_ = np.asarray(Ad.sum(1)).ravel(); dg_[dg_ == 0] = 1
t = np.zeros(nv)
for L, sg in (('L', 1), ('R', -1)):
    h = np.array(pb['upper_arm.' + L].head); e = np.array(pb['upper_arm.' + L].tail); a = (e - h) / np.linalg.norm(e - h)
    up = np.array([0, 0, 1.0]); up = up - a * (up @ a); up /= np.linalg.norm(up)
    q = Xs - h; s = q @ a; y = q @ up; r = np.linalg.norm(q - np.outer(s, a), axis=1)
    w = ss((y - E('Y0', -0.035)) / (E('Y1', 0.010) - E('Y0', -0.035)))
    w *= ss((s - E('SA0', -0.14)) / 0.06) * ss((E('SA1', 0.26) - s) / 0.08) * (r < 0.16) * (Xs[:, 0] * sg > 0.03)
    t = np.maximum(t, w)
    d = np.linalg.norm(Xs - Xr, axis=1)
    print('%s: dome kept on %d verts; skinned vs relaxed there: mean %.1f mm, max %.1f mm' % (L, int((w > 0.5).sum()), d[w > 0.5].mean() * 1000, d[w > 0.5].max() * 1000))
for _ in range(int(E('SM', 8))): t = 0.5 * t + 0.5 * (Ad @ t) / dg_
X = Xr + (E('K', 1.0) * t)[:, None] * (Xs - Xr)
me.vertices.foreach_set('co', X.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
