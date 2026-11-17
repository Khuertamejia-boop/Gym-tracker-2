# Shoulder twist correction for poses with a big humeral rotation (double biceps: ~100 deg external rotation).
# The skinning turns all the upper-arm skin with the bone, so the deltoid (whose origin is on the clavicle and the
# scapula, not on the humerus) slides round to the back with it: from behind it became a flat band, from the front a
# grey hole between the chest and the arm. Here the skin near the shoulder turns back about the arm axis by
# UT * (1 - a(s)) * w * twist:   s = position along the rest arm (0 = joint, 1 = elbow), a(s) smooth 0 -> 1 between
# UTS0 and UTS1 (deltoid insertion ~ 0.5), w = smooth 'moves with the upper arm' mask (rest main bone upper_arm,
# smoothed over the surface), twist = roll of the upper arm about its own axis relative to the clavicle (swing-twist).
# Runs on the baked mesh (after arap2.py, before deltbulge.py).   usage: python untwist.py in.blend out.blend
import bpy, sys, os, math, numpy as np
from mathutils import Vector, Quaternion, Matrix
src, out = sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
here = os.environ.get('GT3D', os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=src)
hi = bpy.data.objects['Hi']; me = hi.data; nv = len(me.vertices); rig = bpy.data.objects['Rig']; pb = rig.pose.bones; bb = rig.data.bones
R = np.load(os.path.join(here, 'ill', 'rest.npz'), allow_pickle=True); co0 = R['co']; main = np.array([str(x) for x in R['main']])
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
import scipy.sparse as sp
Ad = sp.coo_matrix((np.ones(len(ed) * 2), (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
dg_ = np.asarray(Ad.sum(1)).ravel(); dg_[dg_ == 0] = 1
ARM = ('upper_arm', 'forearm', 'fa_tw1', 'fa_tw2', 'fa_tw3', 'hand')
for L in 'LR':
    # twist of the upper arm about its own axis, relative to the clavicle
    Rua = pb['upper_arm.' + L].matrix.to_3x3() @ bb['upper_arm.' + L].matrix_local.to_3x3().inverted()
    Rcl = pb['clavicle.' + L].matrix.to_3x3() @ bb['clavicle.' + L].matrix_local.to_3x3().inverted()
    Rrel = (Rcl.inverted() @ Rua).to_quaternion()
    u0 = (Vector(bb['upper_arm.' + L].tail_local) - Vector(bb['upper_arm.' + L].head_local)).normalized()
    sw = u0.rotation_difference(Rrel @ u0); tw = sw.inverted() @ Rrel        # Rrel = swing * twist (twist about u0)
    ang = 2 * math.atan2(Vector(tw[1:]) @ u0, tw.w); ang = (ang + math.pi) % (2 * math.pi) - math.pi
    h = np.array(pb['upper_arm.' + L].head); t = np.array(pb['upper_arm.' + L].tail); u = (t - h) / np.linalg.norm(t - h)
    # which skin turned with the arm: rest main bone on the arm chain, smoothed so the edge is soft
    m = np.isin(main, [a + '.' + L for a in ARM]).astype(float)
    for _ in range(int(E('UTSM', 25))): m = 0.5 * m + 0.5 * (Ad @ m) / dg_
    h0 = np.array(bb['upper_arm.' + L].head_local); Lu = bb['upper_arm.' + L].length
    s = ((co0 - h0) @ np.array(u0)) / Lu
    k = E('UT', 0.6) * (1 - ss((s - E('UTS0', -0.10)) / (E('UTS1', 0.55) - E('UTS0', -0.10)))) * m
    k *= (np.linalg.norm(co0 - h0, axis=1) < E('UTR', 0.30))                  # only around this shoulder
    k[k < 1e-3] = 0
    idx = np.where(k > 0)[0]
    th = -ang * k[idx]                                                       # turn back part of the twist
    p = co[idx] - h; c, sn = np.cos(th)[:, None], np.sin(th)[:, None]
    uu = np.broadcast_to(u, p.shape)
    p = p * c + np.cross(uu, p) * sn + uu * (p @ u)[:, None] * (1 - c)      # Rodrigues about the posed arm axis
    co[idx] = h + p
    print('%s humeral twist %+.1f deg, turned back up to %.1f deg on %d verts' % (L, math.degrees(ang), math.degrees(abs(ang)) * k.max(), len(idx)))
me.vertices.foreach_set('co', co.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
