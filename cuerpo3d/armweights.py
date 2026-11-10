# Clean the skin weights of the upper arm (10-11-2026): on the back / inner side of the upper arm, 5-9 cm below the
# shoulder joint, the smoothed weights still gave 20-30 % to the torso bones (chest / spine). With the arm raised and
# rotated (double biceps) that skin lagged behind the rest of the arm and made a sharp fold along the arm («hombro en
# punta», «plástico mal doblado»). Here the torso share of upper-arm skin fades out between S0 and S1 along the arm
# (from the joint, rest pose) and goes to the upper-arm bone instead.   usage: python armweights.py in.blend out.blend
#   env: S0 (0.035), S1 (0.085), RMAX (radius from the arm axis, 0.10), TORSO (bones, 'chest,spine,hips')
import bpy, sys, os, numpy as np
src, out = sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
bpy.ops.wm.open_mainfile(filepath=src)
hi = bpy.data.objects['Hi']; me = hi.data; nv = len(me.vertices); rig = bpy.data.objects['Rig']; bb = rig.data.bones
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
vg = hi.vertex_groups; gi = {g.name: g.index for g in vg}
TORSO = [n for n in os.environ.get('TORSO', 'chest,spine,hips').split(',') if n in gi]
def W(name):
    w = np.zeros(nv); idx = gi[name]
    for v in me.vertices:
        for g in v.groups:
            if g.group == idx: w[v.index] = g.weight
    return w
tot = 0
for L in 'LR':
    h = np.array(bb['upper_arm.' + L].head_local); t = np.array(bb['upper_arm.' + L].tail_local); u = (t - h) / np.linalg.norm(t - h)
    s = (co - h) @ u; r = np.linalg.norm(co - h - np.outer(s, u), axis=1)
    arm = sum(W(n + '.' + L) for n in ('upper_arm', 'forearm', 'fa_tw1', 'fa_tw2', 'fa_tw3', 'hand') if n + '.' + L in gi)
    f = ss((s - E('S0', 0.035)) / (E('S1', 0.085) - E('S0', 0.035))) * (r < E('RMAX', 0.10)) * (arm > 0.3)
    sel = np.where(f > 1e-3)[0]
    moved = np.zeros(nv)
    for n in TORSO:
        w = W(n); d = w * f; moved += d
        for i in sel:
            if d[i] > 0: vg[gi[n]].add([int(i)], float(w[i] - d[i]), 'REPLACE')
    wu = W('upper_arm.' + L)
    for i in sel:
        if moved[i] > 0: vg[gi['upper_arm.' + L]].add([int(i)], float(wu[i] + moved[i]), 'REPLACE')
    k = int((moved > 1e-3).sum()); tot += k
    print('%s: %d verts, torso share moved to the upper arm: mean %.2f max %.2f' % (L, k, moved[moved > 1e-3].mean() if k else 0, moved.max()))
bpy.ops.wm.save_as_mainfile(filepath=out)
print('armweights: %d verts changed' % tot)
