# Local re-weighting of the TOP of each shoulder (trapezius / acromion): the upper-arm share u is re-solved as a smooth
# harmonic field inside a ball above the joint, with u=0 on the trapezius (medial to XTRAP) and the ORIGINAL weights as
# boundary values everywhere else (armpit, pec, back keep their heat weights -> no seams). The torso part (1-u) keeps
# the original torso proportions; optionally a share CLK of it is moved to the clavicle (girdle) so the trapezius rises
# with the shrug.  usage: python D_weights2.py in.blend out.blend
import bpy, sys, os
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
src, out = sys.argv[-2], sys.argv[-1]
E = lambda k, d: float(os.environ.get(k, d))
bpy.ops.wm.open_mainfile(filepath=src)
hi = bpy.data.objects['Hi']; me = hi.data; nv = len(me.vertices); rig = bpy.data.objects['Rig']; bb = rig.data.bones
bones = {b.name for b in bb if b.use_deform}
groups = [g for g in hi.vertex_groups if g.name in bones]; gi = {g.index: k for k, g in enumerate(groups)}; names = [g.name for g in groups]
W = np.zeros((nv, len(groups)), np.float64)
for v in me.vertices:
    for g in v.groups:
        k = gi.get(g.group)
        if k is not None: W[v.index, k] = g.weight
s = W.sum(1, keepdims=True); s[s == 0] = 1; W /= s
co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
ed = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
el = np.linalg.norm(co[ed[:, 0]] - co[ed[:, 1]], axis=1); wgt = 1.0 / np.maximum(el, 1e-4)
A = sp.coo_matrix((np.r_[wgt, wgt], (np.r_[ed[:, 0], ed[:, 1]], np.r_[ed[:, 1], ed[:, 0]])), shape=(nv, nv)).tocsr()
Lap = (sp.diags(np.asarray(A.sum(1)).ravel()) - A).tocsr()
col = lambda n: W[:, names.index(n)] if n in names else np.zeros(nv)
W0 = W.copy()
sst = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))

def harmonic(u0, free):
    u = u0.copy(); idx = np.where(free)[0]; fx = np.where(~free)[0]
    Lr = Lap[idx]; u[idx] = np.clip(sla.spsolve(Lr[:, idx].tocsc(), -(Lr[:, fx] @ u[fx])), 0, 1); return u

for L in 'LR':
    side = 1.0 if L == 'L' else -1.0
    a = np.array(bb['upper_arm.' + L].head_local); xs = co[:, 0] * side
    ku = names.index('upper_arm.' + L); kc = names.index('clavicle.' + L)
    nh = col('neck') + col('head')
    ctr = a + np.array((side * E('TCX', -0.02), E('TCY', 0.0), E('TCZ', 0.04)))       # centre of the re-weighted ball
    dc = np.linalg.norm(co - ctr, axis=1)
    ball = (dc < E('TRAD', 0.11)) & (xs > 0)
    trap = ball & (xs < E('XTRAP', 0.13)) & (co[:, 2] > a[2] - E('TZD', 0.0))
    if os.environ.get('YB'): trap &= (co[:, 1] > a[1] + E('YB', 0.04))
    u0 = W0[:, ku].copy()
    u0[trap] = 0.0
    if E('TDELT', 0) > 0:     # lateral deltoid fully on the arm
        dl = ball & (xs > E('XDELT', 0.21))
        u0[dl] = 1.0; trap = trap | dl
    keep = W0[:, ku] > E('UKEEP', 0.98)          # arm core keeps its weight
    free = ball & ~trap & ~keep
    u = harmonic(u0, free)
    ch = ball
    tor = [names.index(n) for n in ('chest', 'spine', 'clavicle.' + L, 'neck', 'head', 'hips') if n in names]
    rest = W0[ch][:, tor].copy(); sm = rest.sum(1, keepdims=True)
    fb = sm[:, 0] < 1e-6; rest[fb, tor.index(kc)] = 1.0; sm = rest.sum(1, keepdims=True); rest = rest / sm
    # move a share of the non-clavicle torso part to the clavicle near the top of the shoulder (girdle follows the shrug)
    clk = E('CLK', 0.0) * sst(1 - dc[ch] / E('TRAD', 0.11))
    if E('CLK', 0.0) > 0:
        ic = tor.index(kc); oth = [i for i in range(len(tor)) if i != ic and names[tor[i]] not in ('neck', 'head')]
        mv = rest[:, oth] * clk[:, None]; rest[:, oth] -= mv; rest[:, ic] += mv.sum(1)
    Wn = W0[ch].copy(); others = [k for k in range(len(names)) if k not in tor + [ku]]
    o = Wn[:, others].sum(1)                     # other bones (e.g. stray thigh weight on the back) stay untouched
    uu = np.minimum(u[ch], 1 - o); lost = np.abs(uu - u[ch])
    Wn[:, ku] = uu; Wn[:, tor] = rest * np.clip(1 - o - uu, 0, 1)[:, None]
    W[ch] = Wn
    print(L, 'ball', int(ball.sum()), 'trap', int(trap.sum()), 'free', int(free.sum()), 'mean |du| %.3f' % np.abs(u[ch] - W0[ch, ku]).mean(), 'u clipped by other bones max %.3f' % lost.max())
idx = np.where(np.abs(W - W0).max(1) > 1e-6)[0]
for k, g in enumerate(groups):
    vals = W[idx, k]; z = idx[vals <= 1e-5]
    if len(z): g.remove([int(i) for i in z])
    for i, w in zip(idx[vals > 1e-5], vals[vals > 1e-5]): g.add([int(i)], float(w), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=out)
