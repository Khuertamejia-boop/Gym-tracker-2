# latfix.py (11-11-2026) -- lat spread / V shape with the arms raised (owner: «mejorar dorsales y la forma V»).
#   Before: the trunk was a box from the armpit down to the low ribs and then cut in to the waist. In the reference
#   photos the outline is a diagonal from just under the armpit (widest) to the waist.
#   The skin of the back-side flank moves sideways (and a little back) by
#   LAMP * lift * profile(height) * lobe(angle around the trunk)
#   height t = 0 at the 'spine' bone head (waist), 1 at the shoulder joint: 0 below LT0, max at LTP, 0 again at LT1
#   lobe: gaussian around the vertical axis of the trunk, centre LTH deg behind pure lateral, width LSG deg
#   lift = how far the arm is raised (0 below A0 deg from hanging, 1 above A1) -> nothing changes with the arms down.
#   usage: python latfix.py in.blend out.blend    env: LAMP (0.028) LT0 (0.22) LTP (0.74) LT1 (0.99) LTH (30) LSG (35)
#          LBK (0.25, how much of the push goes backwards) LS1 / LSW (0.45 / 0.38: fade along the arm) LSM (14) A0/A1 (35 / 85)
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
ok = np.array([m.startswith(('chest', 'spine', 'CS', 'hips', 'clavicle', 'upper_arm')) for m in main])
zs = float(np.array(pb['spine'].head)[2]); yc = float(np.array(pb['chest'].head)[1])
V = np.zeros_like(co)
for L in 'LR':
    h = np.array(pb['upper_arm.' + L].head); e = np.array(pb['forearm.' + L].head); sg = 1.0 if h[0] > 0 else -1.0
    a = (e - h); La = np.linalg.norm(a); a /= La
    ang = math.degrees(math.acos(np.clip(a @ np.array([0, 0, -1.0]), -1, 1)))
    lift = float(ss((ang - E('A0', 35)) / (E('A1', 85) - E('A0', 35))))
    t = (co[:, 2] - zs) / (h[2] - zs); t0, tp, t1 = E('LT0', 0.22), E('LTP', 0.74), E('LT1', 0.99)
    prof = np.where(t < tp, ss((t - t0) / (tp - t0)), ss((t1 - t) / (t1 - tp)))
    th = np.degrees(np.arctan2(co[:, 1] - yc, np.maximum(co[:, 0] * sg, 1e-6)))        # 0 = lateral, + = towards the back
    lobe = np.exp(-0.5 * ((th - E('LTH', 30)) / E('LSG', 35)) ** 2)
    s = ((co - h) @ a) / La                                                              # fades out along the arm
    w = prof * lobe * ok * (co[:, 0] * sg > 0.05) * ss((E('LS1', 0.45) - s) / E('LSW', 0.38)) * lift
    dirv = np.array([sg, E('LBK', 0.25), 0.0]); dirv /= np.linalg.norm(dirv)
    V += dirv[None, :] * (E('LAMP', 0.028) * w)[:, None]
    print('%s: arm raised %.0f deg, lift %.2f, verts %d' % (L, ang, lift, int((w > 0.02).sum())))
for _ in range(int(E('LSM', 14))): V = 0.5 * V + 0.5 * (Ad @ V) / dg[:, None]
me.vertices.foreach_set('co', (co + V).ravel()); me.update()
print('latfix done')
bpy.ops.wm.save_as_mainfile(filepath=out)
