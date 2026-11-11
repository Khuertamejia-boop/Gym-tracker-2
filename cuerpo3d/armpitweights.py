# Clean arm / torso skin weights around the armpit (11-11-2026). Replaces armweights.py.
# The base weights bled across the gap between the hanging arm and the flank: serratus / lat skin 10-20 cm below
# the joint had 50-80 % arm weight (the flank went up with the arm: a stretched web in front of the armpit, a dot
# poking through the triceps), and the inner skin of the upper arm had 20-30 % torso weight (sharp fold along the arm).
# Here the arm share (sum of the arm chain) of every vertex near the shoulder is solved again as a harmonic function
# on the mesh:  1 on the arm (surface coordinate H > H1, see below), 0 on the ribs
# (serratus, obliques, abs, the pec beyond DPEC of the joint, the lat beyond DLAT) and wherever it was 0 before;
# the top of the shoulder (deltoid, clavicle, trapezius: everything above the joint) keeps its old value; the skin in
# between (armpit, lateral pec, upper lat / teres) is free. The other bones keep their proportions.
#   usage: python armpitweights.py in.blend out.blend
#   env: H1 / H0 (surface coordinate above which the skin is arm / below which rib labels are ribs: 0.42 / 0.25),
#        DPEC (0.15), DLAT (0.20), DMAX (0.50), SMO (smoothing passes of the result, 3)
import bpy, sys, os, numpy as np
import scipy.sparse as sp, scipy.sparse.linalg as spl
src, out = sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
here = os.environ.get('GT3D', os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=src)
hi = bpy.data.objects['Hi']; me = hi.data; nv = len(me.vertices); rig = bpy.data.objects['Rig']; bb = rig.data.bones
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
Ad = sp.coo_matrix((np.ones(len(ed) * 2), (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
dg = np.asarray(Ad.sum(1)).ravel(); dg[dg == 0] = 1
A = np.load(os.path.join(here, 'ill', 'pv', 'bla.npz'), allow_pickle=True); names = [str(x) for x in A['names']]; mid = A['mid'].astype(int)
lab = np.array([names[m].split('.')[0] for m in mid])
main = np.array([str(x) for x in np.load(os.path.join(here, 'ill', 'rest.npz'), allow_pickle=True)['main']])
vg = hi.vertex_groups; gname = [g.name for g in vg]; ng = len(gname)
W = np.zeros((ng, nv), np.float32)
for v in me.vertices:
    for g in v.groups: W[g.group, v.index] = g.weight
W0 = W.copy()
RIBS = ['serratus_anterior', 'external_oblique', 'rectus_abd_1', 'rectus_abd_2', 'rectus_abd_3', 'rectus_abd_4', 'erector_spinae',
        'rhomboid_major', 'trap_lower', 'trap_middle', 'thoracolumbar_fascia', 'sternocleidomastoid']
ARMM = ['biceps_brachii', 'brachialis', 'brachialis_medial', 'triceps_long', 'triceps_medial', 'triceps_lateral', 'triceps_tendon',
        'coracobrachialis', 'anconeus', 'brachioradialis']
dbg = {}
for L, sg in (('L', 1), ('R', -1)):
    chain = [i for i, n in enumerate(gname) if n.endswith('.' + L) and not n.startswith(('clavicle', 'thigh', 'shin', 'foot', 'toe'))]
    other = [i for i in range(ng) if i not in chain]
    h = np.array(bb['upper_arm.' + L].head_local); t = np.array(bb['upper_arm.' + L].tail_local); u = (t - h) / np.linalg.norm(t - h)
    q = co - h; d = np.linalg.norm(q, axis=1); s = q @ u; r = np.linalg.norm(q - np.outer(s, u), axis=1)
    a0 = W[chain].sum(0)
    side = co[:, 0] * sg > 0.02
    reg = side & (d < E('DMAX', 0.50))
    # arm or flank? Where the hanging arm rests against the flank the two skins are a few mm apart and neither the
    # distance to the bone nor the atlas label can tell them apart. H does: a harmonic coordinate ON the surface,
    # 1 from the elbow on, 0 on the trunk (x < 0.10); in the contact zone the flank has 0.14-0.20, the inner arm 0.46-0.59
    one = np.array([m.endswith('.' + L) and m.startswith(('forearm', 'fa_tw', 'hand', 'thumb', 'index', 'middle', 'ring', 'pinky')) for m in main])
    one |= (main == 'upper_arm.' + L) & (s > 0.26)
    zero = ~one & ((co[:, 0] * sg < 0.10) | (co[:, 2] < 1.0))
    Hh = np.zeros(nv); Hh[one] = 1; fh = np.where(~one & ~zero)[0]; Lp_ = sp.diags(dg) - Ad
    Hh[fh] = spl.spsolve(Lp_[fh][:, fh].tocsc(), -(Lp_[fh] @ Hh))
    arm1 = reg & (Hh > E('H1', 0.42)) & ~np.isin(lab, ['deltoid_anterior', 'deltoid_lateral', 'deltoid_posterior'])
    ribs0 = reg & ((np.isin(lab, RIBS) & (Hh < E('H0', 0.25))) | ((lab == 'pec_sternal') & (d > E('DPEC', 0.15))) | ((lab == 'latissimus_dorsi') & (d > E('DLAT', 0.20))) | (a0 < 0.01))
    ribs0 &= ~arm1
    top = reg & ~arm1 & ~ribs0 & ((co[:, 2] > h[2] - E('ZTOP', 0.0)) | np.isin(lab, ['deltoid_anterior', 'deltoid_lateral', 'deltoid_posterior', 'pec_clavicular', 'trap_upper', 'infraspinatus', 'teres_minor']))
    free = reg & ~arm1 & ~ribs0 & ~top
    x = a0.astype(np.float64).copy(); x[arm1] = 1.0; x[ribs0] = 0.0
    # outside the region: keep the old values (boundary)
    fi = np.where(free)[0]
    Lp = sp.diags(dg) - Ad
    Lff = Lp[fi][:, fi].tocsc(); rhs = -(Lp[fi] @ np.where(free, 0.0, x))
    x[fi] = spl.spsolve(Lff, rhs)
    mov = free | arm1 | ribs0
    for _ in range(int(E('SMO', 3))):
        xs = (Ad @ x) / dg; x = np.where(free, 0.5 * x + 0.5 * xs, x)
    x = np.clip(x, 0, 1)
    # write back: arm chain share -> x, the rest -> 1 - x, proportions kept
    ua = gname.index('upper_arm.' + L); ch = gname.index('chest'); cl = gname.index('clavicle.' + L)
    idx = np.where(mov & (np.abs(x - a0) > 1e-4))[0]
    oth0 = W[other][:, idx].sum(0); arm0 = a0[idx]
    for k in chain:
        W[k, idx] = np.where(arm0 > 1e-4, W[k, idx] / np.maximum(arm0, 1e-6) * x[idx], x[idx] if k == ua else 0.0)
    for k in other:
        W[k, idx] = np.where(oth0 > 1e-4, W[k, idx] / np.maximum(oth0, 1e-6) * (1 - x[idx]), (1 - x[idx]) if k == (cl if True else ch) else 0.0)
    print('%s: arm tube %d, ribs %d, shoulder top kept %d, free %d; changed %d verts, mean |d| %.2f max %.2f' % (
        L, arm1.sum(), ribs0.sum(), top.sum(), free.sum(), len(idx), np.abs(x[idx] - arm0).mean(), np.abs(x[idx] - arm0).max()))
    dbg[L] = (a0, x, arm1, ribs0, top, free)
# write the changed weights
chg = np.where(np.abs(W - W0).max(0) > 1e-4)[0]
for k in range(ng):
    g = vg[k]; col = W[k]; col0 = W0[k]
    for i in chg:
        if abs(col[i] - col0[i]) > 1e-5:
            if col[i] > 1e-4: g.add([int(i)], float(col[i]), 'REPLACE')
            else: g.remove([int(i)])
print('armpitweights: %d verts rewritten' % len(chg))
if os.environ.get('DBG'):
    np.savez(os.environ['DBG'], co=co, a0=dbg['L'][0], x=dbg['L'][1], arm1=dbg['L'][2], ribs0=dbg['L'][3], top=dbg['L'][4], free=dbg['L'][5])
bpy.ops.wm.save_as_mainfile(filepath=out)
