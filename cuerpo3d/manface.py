# Masculine, athletic face for the male mannequin (owner 12-11-2026, with two anatomy illustrations and a photo of a
# skin-fade haircut as references: «hazle un corte de cabello y tipo de rostro como el de las referencias, dale vida al
# rostro»).  Smooth, local edits of the head of GEO-body_male_realistic (absolute coordinates of that head, metres;
# landmarks measured on it: nose tip y -0.164 z 1.539, mouth line z 1.5073, chin y -0.146 z 1.470, angle of the jaw
# x 0.059 y -0.045 z 1.472, cheekbone x 0.075 z 1.55, brow ridge z 1.593, eye centre x 0.033 y -0.122 z 1.574):
# squarer jaw (wider, lower angle, crisper border), wider squarer chin with more projection and a faint cleft, cheekbones
# a little out with a hollow under them, stronger brow ridge with deeper-set eyes, narrower nose, temples a little
# hollow, upper lids a little lower (calm, firm gaze).  Every edit is a smooth weight * a small displacement (no seams).
#   deform(co, faces, eyes, prot) -> co, eyes        (eyes = [(side, verts, faces), ...]; prot 0 = keep, the neck band)
# Env (m unless said; defaults = chosen look; 0 switches an edit off): MJ jaw angle, MJL jaw border, MM masseter,
# MC chin forward, MCW chin width (ratio), MCS chin corners, MCL cleft, MZ cheekbone, MH hollow, MB brow ridge,
# MG glabella, MO orbit, MNW nose width (ratio, 1 = same), MNL nose-to-mouth fold, MNT nose tip down, MU under the eye, MT temple, LIDA upper lid (deg), MK overall strength.
import os, numpy as np
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))


def normals(co, faces):
    n = np.zeros_like(co)
    by = {}
    for f in faces: by.setdefault(len(f), []).append(f)
    for k, fl in by.items():
        F = np.array(fl)
        for j in range(1, k - 1):
            a, b, c = co[F[:, 0]], co[F[:, j]], co[F[:, j + 1]]
            fn = np.cross(b - a, c - a)
            for col in (0, j, j + 1): np.add.at(n, F[:, col], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def deform(co, faces, eyes, prot=None):
    co0 = co.copy(); co = co.copy(); X, Y, Z = co0[:, 0], co0[:, 1], co0[:, 2]
    hn = normals(co0, faces); K = E('MK', 1.0)
    AX = np.abs(X); sx = np.tanh(X / 0.004)                              # smooth sign (no jump on the midline)
    front = ss((-hn[:, 1] - 0.10) / 0.35) * (Y < -0.06)
    g3 = lambda c, r: np.exp(-((AX - c[0]) / r[0]) ** 2 - ((Y - c[1]) / r[1]) ** 2 - ((Z - c[2]) / r[2]) ** 2)
    D = np.zeros_like(co)

    def add(w, v): D[:] += w[:, None] * np.asarray(v)[None, :] if np.ndim(v) == 1 else w[:, None] * v

    lat = lambda a, b, c: np.stack([sx * a, np.full(len(X), b), np.full(len(X), c)], 1)   # (outwards, y, z) per side
    # 1. angle of the jaw: out, down and a little back -> squarer face (jaw / cheekbone width 0.80 -> ~0.86)
    add(g3((0.059, -0.045, 1.474), (0.020, 0.024, 0.020)) * K * E('MJ', 0.0060), lat(0.85, 0.10, -0.45))
    # 2. masseter (the muscle over the angle): a little fuller
    add(g3((0.062, -0.066, 1.500), (0.018, 0.022, 0.018)) * K * E('MM', 0.0014), hn)
    # 3. lower border of the jaw, from the angle to the chin: out and down -> a crisp jawline with its own shadow
    A_, B_ = np.array((0.057, -0.050, 1.468)), np.array((0.026, -0.128, 1.458))
    P = np.stack([AX, Y, Z], 1); ab = B_ - A_; t = np.clip(((P - A_) @ ab) / (ab @ ab), 0, 1)
    dseg = np.linalg.norm(P - (A_ + t[:, None] * ab), axis=1)
    add(np.exp(-(dseg / 0.012) ** 2) * K * E('MJL', 0.0030), lat(0.60, -0.20, -0.75))
    # 4. chin: forward, wider and squarer, with a faint vertical cleft
    add(np.exp(-(X / 0.020) ** 2 - ((Y + 0.146) / 0.020) ** 2 - ((Z - 1.466) / 0.014) ** 2) * K * E('MC', 0.0030), (0.0, -1.0, -0.25))
    add(g3((0.017, -0.139, 1.459), (0.010, 0.012, 0.010)) * K * E('MCS', 0.0030), lat(0.50, -0.50, -0.70))
    add(np.exp(-(X / 0.0028) ** 2 - ((Z - 1.467) / 0.007) ** 2) * (Y < -0.130) * K * E('MCL', 0.0007), (0.0, 1.0, 0.0))
    wcw = ss((1.482 - Z) / 0.020) * ss((-0.118 - Y) / 0.020)
    D[:, 0] += X * K * E('MCW', 0.12) * wcw
    # 5. cheekbones a little out, hollow under them (lean, athletic cheek)
    add(g3((0.066, -0.100, 1.548), (0.016, 0.022, 0.012)) * K * E('MZ', 0.0022), hn)
    add(-g3((0.056, -0.104, 1.503), (0.014, 0.020, 0.016)) * K * E('MH', 0.0030), hn)
    # 6. brow ridge forward (and the bridge between the brows), the hollow above the lid a little deeper: deep-set eyes
    add(np.exp(-((AX - 0.030) / 0.024) ** 2 - ((Z - 1.594) / 0.0075) ** 2) * front * K * E('MB', 0.0025), (0.0, -1.0, 0.0))
    add(np.exp(-(X / 0.011) ** 2 - ((Z - 1.591) / 0.008) ** 2) * front * K * E('MG', 0.0010), (0.0, -1.0, 0.0))
    add(np.exp(-((AX - 0.034) / 0.015) ** 2 - ((Z - 1.5845) / 0.0035) ** 2) * front * K * E('MO', 0.0012), (0.0, 1.0, 0.0))
    # 7. nose a little narrower (wings and bridge)
    wn = ss((0.026 - AX) / 0.008) * ss((Z - 1.512) / 0.006) * ss((1.566 - Z) / 0.010) * ss((-0.136 - Y) / 0.006)
    D[:, 0] -= X * (1 - E('MNW', 0.90)) * K * wn
    # 7b. fold from the wing of the nose towards the corner of the mouth: a faint groove (a grown man's cheek)
    A2, B2 = np.array((0.0205, -0.146, 1.529)), np.array((0.0305, -0.136, 1.499))
    ab2 = B2 - A2; t2 = np.clip(((P - A2) @ ab2) / (ab2 @ ab2), 0, 1)
    d2 = np.linalg.norm(P - (A2 + t2[:, None] * ab2), axis=1)
    add(-np.exp(-(d2 / 0.0045) ** 2) * front * K * E('MNL', 0.0004), hn)
    # 7c. nose tip a little down (the nostrils show less from the front); under the eye a little fuller (no 'bags')
    add(np.exp(-(X / 0.012) ** 2 - ((Y + 0.160) / 0.012) ** 2 - ((Z - 1.537) / 0.010) ** 2) * K * E('MNT', 0.0015), (0.0, 0.0, -1.0))
    add(np.exp(-((AX - 0.034) / 0.013) ** 2 - ((Z - 1.5615) / 0.0045) ** 2) * front * K * E('MU', 0.0006), hn)
    # 8. temples a little hollow
    add(-g3((0.071, -0.080, 1.604), (0.014, 0.022, 0.018)) * K * E('MT', 0.0010), hn)
    co = co0 + D
    # 9. upper lids a little lower: turned down around each eye centre (same construction as femface.py)
    out = []
    for L, ec, ef in eyes:
        c = ec.mean(0); v = co - c; R3 = np.linalg.norm(v, axis=1)
        wl = ss((0.021 - R3) / 0.007) * ss(v[:, 2] / 0.003) * ss((0.008 - v[:, 1]) / 0.008)
        phi = np.arctan2(v[:, 2], -v[:, 1]) - np.radians(E('LIDA', 6.0)) * wl; R2 = np.hypot(v[:, 2], v[:, 1])
        co[:, 2] = c[2] + R2 * np.sin(phi); co[:, 1] = c[1] - R2 * np.cos(phi)
        out.append((L, ec, ef))
    if prot is not None:
        co = co0 + (co - co0) * prot[:, None]
    print('manface: max move %.1f mm (jaw angle %.1f, chin %.1f, brow %.1f mm)' % (np.linalg.norm(co - co0, axis=1).max() * 1000,
          K * E('MJ', 0.0060) * 1000, K * E('MC', 0.0030) * 1000, K * E('MB', 0.0025) * 1000))
    return co, out
