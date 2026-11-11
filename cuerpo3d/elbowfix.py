# Natural bent elbow (owner 10-11-2026: «la sangradura no se ve natural»). Two things, on the baked mesh:
#  1. biceps peak: the biceps / brachialis belly (atlas labels) bulges along its normal with the elbow flexion,
#     with the per-muscle dome profile (pv/bla_dome.npz: 0 at the border, 1 on top), amplitude BAMP * flex.
#  2. soft inner crease: the skin on the inner side of the elbow (within ER of the joint, on the side of the
#     bisector of the upper arm and the forearm) is relaxed (Laplacian smoothing of the positions, ESM iterations)
#     and kept outside a small sphere at the joint (radius EJR), so the fold is a rounded valley, not a V.
# flex = smoothstep((angle between upper arm and forearm - F0) / (F1 - F0)), computed from the posed bones.
#   usage: python elbowfix.py in.blend out.blend     env: BAMP (0.014), F0/F1 (20 / 100 deg), ER (0.05), ESM (8),
#          EJR (0.040), EK (crease strength 0..1, 1), MUS (labels, 'biceps_brachii,brachialis'),
#          BMODE=peak (default): BS0 / BSA / BSB / BCP / TAMP / TS0 (biceps ball), FAMP / FS0 / FSW (forearm)
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
main = np.array([str(x) for x in np.load(os.path.join(here, 'ill', 'rest.npz'), allow_pickle=True)['main']])
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
    if os.environ.get('BMODE', 'peak') == 'dome':          # old: the whole labelled belly inflates along its normals
        amp = E('BAMP', 0.014) * flex * dome * lab
        V += nr * amp[:, None]
    else:
        # 'peak' (11-11): a flexed biceps is a short ball with a peak, not a long balloon. The skin of the upper arm
        # moves towards the forearm side (b, across the arm, in the plane of the elbow) by
        # BAMP * flex * gauss(along the arm, centre BS0, widths BSA towards the shoulder / BSB towards the elbow)
        #      * lobe(angle around the arm, power BCP);  the triceps side hangs a little (TAMP, centre TS0).
        a = (e - h) / np.linalg.norm(e - h); La = np.linalg.norm(e - h)
        b = f - a * (f @ a); b /= np.linalg.norm(b)
        qa = co - h; sa = (qa @ a) / La; rad = qa - np.outer(qa @ a, a); rr = np.linalg.norm(rad, axis=1)
        cb = (rad @ b) / np.maximum(rr, 1e-6)
        arm = (main == 'upper_arm.' + L) & (rr < 0.11) & (sa > -0.1) & (sa < 1.15)
        ds = sa - E('BS0', 0.60); g = np.exp(-0.5 * (ds / np.where(ds < 0, E('BSA', 0.17), E('BSB', 0.13))) ** 2)
        dt = sa - E('TS0', 0.45); gt = np.exp(-0.5 * (dt / 0.20) ** 2)
        ampt = E('TAMP', 0.006) * flex * gt * np.clip(-cb, 0, 1) ** 1.5 * arm
        if E('BRAD', 1) > 0:
            # round ball (11-11, owner: «se ve en punta, debe ser redondeado»): the skin moves RADIALLY (away from the
            # arm axis), most in the direction between the forearm side (b) and the medial side of the arm (the side
            # that faces the camera in a front double biceps), BMED = how far towards the medial side; cosine lobe ^BCP
            sgn = 1.0 if L == 'L' else -1.0
            med = sgn * np.cross(a, b); cdir = b + E('BMED', 0.5) * med; cdir /= np.linalg.norm(cdir)
            cc = (rad @ cdir) / np.maximum(rr, 1e-6)
            amp = E('BAMP', 0.014) * flex * g * np.clip(cc, 0, 1) ** E('BCP', 1.0) * arm
            Vp = rad / np.maximum(rr, 1e-6)[:, None] * amp[:, None] - b[None, :] * ampt[:, None]
        else:
            amp = E('BAMP', 0.014) * flex * g * np.clip(cb, 0, 1) ** E('BCP', 1.5) * arm
            Vp = b[None, :] * (amp - ampt)[:, None]
        # forearm (11-11): with the fist closed and the elbow bent the flexor / brachioradialis mass near the elbow
        # fills out: the forearm skin moves away from its axis by FAMP * flex * gauss(along the forearm, centre FS0)
        if E('FAMP', 0.0) > 0:
            af = (w_ - e) / np.linalg.norm(w_ - e); Lf = np.linalg.norm(w_ - e)
            qf = co - e; sf = (qf @ af) / Lf; radf = qf - np.outer(qf @ af, af); rf = np.linalg.norm(radf, axis=1)
            fore = np.isin(main, ['forearm.' + L, 'fa_tw1.' + L, 'fa_tw2.' + L, 'fa_tw3.' + L]) & (rf < 0.09)
            gf = np.exp(-0.5 * ((sf - E('FS0', 0.24)) / E('FSW', 0.17)) ** 2) * (sf > 0.02)
            Vp += radf / np.maximum(rf, 1e-6)[:, None] * (E('FAMP', 0.0) * flex * gf * fore)[:, None]
        for _ in range(int(E('BSM', 6))): Vp = 0.5 * Vp + 0.5 * (Ad @ Vp) / dg[:, None]
        V += Vp
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
