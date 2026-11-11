# Volume-preserving skinning for the shoulders: "optimized centres of rotation" (Le & Hodgins, SIGGRAPH 2016).
# Each vertex gets a rest-pose centre of rotation p* = similarity-weighted average of the surface whose bone weights
# look like its own. At pose time:  v' = R_q (v - p*) + LBS(p*)  with R_q = normalised blend of the bone quaternions.
# -> no LBS collapse / candy-wrapper (the rotation part is a quaternion blend) and no DQS joint bulge (the translation
#    comes from LBS of a point that sits inside the joint).
import numpy as np, os, time
import bpy

SIG = 0.1

def bone_list(hi, rig):
    return [b.name for b in rig.data.bones if b.use_deform and b.name in hi.vertex_groups]

def weights(hi, names, sel=None):
    me = hi.data; nv = len(me.vertices); gi = {hi.vertex_groups[n].index: k for k, n in enumerate(names)}
    W = np.zeros((nv, len(names)), np.float32)
    for v in me.vertices:
        for g in v.groups:
            k = gi.get(g.group)
            if k is not None: W[v.index, k] = g.weight
    return W

def precompute(co, tris, W, verts, sig=SIG, tsub=1, log=print):
    """centres of rotation for the vertices `verts` (indices). co rest coords (N,3), tris (T,3), W normalised (N,nb)."""
    t0 = time.time()
    Wt = W[tris].mean(1)                                    # (T,nb)
    nzt = (Wt > 1e-4).sum(1) >= 2
    tsel = np.where(nzt)[0][::tsub]
    Wt = Wt[tsel]; tri = tris[tsel]
    a = co[tri]; ct = a.mean(1); ar = 0.5 * np.linalg.norm(np.cross(a[:, 1] - a[:, 0], a[:, 2] - a[:, 0]), axis=1) * tsub
    Wv = W[verts]
    nb = W.shape[1]
    num = np.zeros((len(verts), 3)); den = np.zeros(len(verts))
    used = np.where((Wv > 1e-4).any(0))[0]
    for jj, j in enumerate(used):
        for k in used[jj + 1:]:
            P = Wv[:, j] * Wv[:, k]; Q = Wt[:, j] * Wt[:, k]
            iv = np.where(P > 1e-6)[0]; it = np.where(Q > 1e-6)[0]
            if len(iv) == 0 or len(it) == 0: continue
            Qa = (Q[it] * ar[it]).astype(np.float32); wtj = Wt[it, j].astype(np.float32); wtk = Wt[it, k].astype(np.float32); C = ct[it].astype(np.float32)
            ch = max(1, int(2e7 // len(it)))
            for s0 in range(0, len(iv), ch):
                ii = iv[s0:s0 + ch]
                d = (Wv[ii, j][:, None] * wtk[None] - Wv[ii, k][:, None] * wtj[None]) / sig
                S = np.exp(-d * d) * Qa[None]
                S *= P[ii][:, None]
                num[ii] += S @ C; den[ii] += S.sum(1)
    p = co[verts].copy()
    ok = den > 1e-12
    p[ok] = num[ok] / den[ok][:, None]
    log(f'CoR precompute: {len(verts)} verts, {len(tsel)} tris, {time.time() - t0:.1f}s, no-CoR {int((~ok).sum())}')
    return p, ok

def quat_from_mats(R):
    """R (n,3,3) -> quaternions (n,4) w,x,y,z"""
    n = len(R); q = np.zeros((n, 4))
    tr = R[:, 0, 0] + R[:, 1, 1] + R[:, 2, 2]
    for i in range(n):
        m = R[i]
        if tr[i] > 0:
            s = np.sqrt(tr[i] + 1.0) * 2; q[i] = [0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
        elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
            s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2; q[i] = [(m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s]
        elif m[1, 1] > m[2, 2]:
            s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2; q[i] = [(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s]
        else:
            s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2; q[i] = [(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s]
    return q / np.linalg.norm(q, axis=1, keepdims=True)

def mats_from_quat(q):
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - z * w); R[:, 0, 2] = 2 * (x * z + y * w)
    R[:, 1, 0] = 2 * (x * y + z * w); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - x * w)
    R[:, 2, 0] = 2 * (x * z - y * w); R[:, 2, 1] = 2 * (y * z + x * w); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R

def bone_mats(rig, names):
    """skinning matrices (armature space) of the deform bones: pose @ rest^-1"""
    pb = rig.pose.bones; bb = rig.data.bones
    M = np.array([np.array(pb[n].matrix @ bb[n].matrix_local.inverted()) for n in names])
    return M

def skin(co, W, M, p, verts):
    """CoR skinning of `verts`. co rest coords, W normalised weights (N,nb), M (nb,4,4), p CoRs (len(verts),3)"""
    Wv = W[verts].astype(np.float64)
    R = M[:, :3, :3]; T = M[:, :3, 3]
    Q = quat_from_mats(R)
    piv = Q[np.argmax(Wv, 1)]                               # sign-align to the dominant bone
    sg = np.sign(piv @ Q.T); sg[sg == 0] = 1
    q = (Wv * sg) @ Q; q /= np.linalg.norm(q, axis=1, keepdims=True)
    Ri = mats_from_quat(q)
    # LBS of the centre of rotation
    lp = np.einsum('vb,bij,vj->vi', Wv, R, p) + Wv @ T
    v = co[verts] - p
    return np.einsum('vij,vj->vi', Ri, v) + lp

def lbs(co, W, M, verts):
    Wv = W[verts].astype(np.float64); R = M[:, :3, :3]; T = M[:, :3, 3]
    return np.einsum('vb,bij,vj->vi', Wv, R, co[verts]) + Wv @ T
