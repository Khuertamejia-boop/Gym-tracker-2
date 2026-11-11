# Feminine face for the female mannequin (owner 28-10-2026: «dale un rostro femenino, aún se le aprecia fisonomía de
# hombre»).  Smooth, local edits of the head of GEO-body_female_realistic (absolute coordinates of that head, metres):
# narrower jaw and chin, shorter chin (shorter lower face), fuller cheeks, softer brow ridge, smaller nose with the tip a
# little up, fuller lips, eyes a little larger.  Every edit is a smooth weight * a small displacement (no seams).
#   deform(co, faces, eyes) -> co, eyes        (eyes = [(side, verts, faces), ...])
# Env (defaults = chosen look): JN jaw narrowing, CN chin narrowing, CH chin up (m), CF/CA cheek fullness (m), BR brow
# ridge in (m), NT nose tip up (m), NOSEK/NOSEW nose projection/width, LP lips forward (m), ES eye scale.
import os, numpy as np
E = lambda k, d: float(os.environ.get(k, d))
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))


def normals(co, faces):
    n = np.zeros_like(co)
    # fan triangulation, vectorised by face size
    by = {}
    for f in faces: by.setdefault(len(f), []).append(f)
    for k, fl in by.items():
        F = np.array(fl)
        for j in range(1, k - 1):
            a, b, c = co[F[:, 0]], co[F[:, j]], co[F[:, j + 1]]
            fn = np.cross(b - a, c - a)
            for col in (0, j, j + 1): np.add.at(n, F[:, col], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def blob(X, Z, x0, z0, rx, rz):
    """2-D gaussian in the front plane, mirrored on both sides when x0 != 0"""
    g = np.exp(-((np.abs(X) - x0) / rx) ** 2 - ((Z - z0) / rz) ** 2)
    return g


def deform(co, faces, eyes, prot=None):
    """prot: 0..1 per vertex, 0 = keep (the band glued to the neck)"""
    co0 = co.copy(); co = co.copy(); X, Y, Z = co[:, 0].copy(), co[:, 1].copy(), co[:, 2].copy()
    hn = normals(co, faces)
    front = ss((-hn[:, 1] - 0.15) / 0.35) * (Y < -0.06)
    # 1. jaw: narrower towards the angle of the jaw and the chin (cheekbones untouched)
    wj = ss((1.500 - Z) / 0.040) * ss((Z - 1.380) / 0.025) * ss((-0.012 - Y) / 0.030)
    wc = ss((1.475 - Z) / 0.035) * ss((-0.075 - Y) / 0.030)
    sx = 1 - E('JN', 0.10) * wj - E('CN', 0.15) * wc
    # 2. shorter chin: everything under the mouth goes up (lower face shorter), only in front of the neck
    wch = ss((1.466 - Z) / 0.040) * ss((-0.068 - Y) / 0.022)
    dz = E('CH', 0.0065) * wch
    # 3. nose tip a little up and shorter, narrower wings (local; same region as before)
    wn = ss((0.024 - np.abs(X)) / 0.008) * ss((Z - 1.482) / 0.006) * ss((1.532 - Z) / 0.008) * ss((-0.138 - Y) / 0.006)
    Yn = Y + wn * (-0.142 - Y) * (1 - E('NOSEK', 0.82))
    sx = sx * (1 - wn * (1 - E('NOSEW', 0.84)))
    wt = ss((0.014 - np.abs(X)) / 0.008) * ss((Z - 1.488) / 0.006) * ss((1.522 - Z) / 0.012) * ss((-0.140 - Y) / 0.006)
    dz = dz + E('NT', 0.0009) * wt
    co[:, 0] = X * sx; co[:, 1] = Yn; co[:, 2] = Z + dz
    # 4. along the normal: fuller cheeks (under the cheekbone and the cheek 'apple'), softer brow ridge, fuller lips
    push = (E('CF', 0.0022) * blob(X, Z, 0.054, 1.494, 0.016, 0.014) * ss((-0.05 - Y) / 0.02)
            + E('CA', 0.0016) * blob(X, Z, 0.036, 1.512, 0.011, 0.009) * front
            - E('BR', 0.0015) * (blob(X, Z, 0.028, 1.562, 0.022, 0.010) + 0.6 * blob(X, Z, 0.0, 1.556, 0.010, 0.008)) * front
            + E('LP', 0.0015) * blob(X, Z, 0.0, 1.467, 0.020, 0.008) * front)
    co = co + hn * push[:, None]
    # 5. eyes a little larger (eyeball + lids around its centre, in the front plane)
    es = E('ES', 0.06); out = []
    for L, ec, ef in eyes:
        c = ec.mean(0)
        r = np.hypot(co[:, 0] - c[0], co[:, 2] - c[2]); w = ss((0.030 - r) / 0.014) * ss((c[1] + 0.012 - co[:, 1]) / 0.010)
        co[:, 0] += (co[:, 0] - c[0]) * es * w; co[:, 2] += (co[:, 2] - c[2]) * es * w
        out.append((L, c + (ec - c) * (1 + es), ef))
        # upper lid a little lower (covers the top of the iris: no 'scared' stare): turn it down around the eye centre
        v = co - c; R3 = np.linalg.norm(v, axis=1)
        wl = ss((0.021 - R3) / 0.007) * ss(v[:, 2] / 0.003) * ss((0.008 - v[:, 1]) / 0.008)
        phi = np.arctan2(v[:, 2], -v[:, 1]) - np.radians(E('LIDA', 6.0)) * wl; R2 = np.hypot(v[:, 2], v[:, 1])
        co[:, 2] = c[2] + R2 * np.sin(phi); co[:, 1] = c[1] - R2 * np.cos(phi)
    if prot is not None:
        co = co0 + (co - co0) * prot[:, None]
    print('femface: jaw %.3f chin %.3f chin up %.1f mm, max move %.1f mm' % (E('JN', 0.10), E('CN', 0.15), E('CH', 0.0065) * 1000,
          np.linalg.norm(co - np.stack([X, Y, Z], 1), axis=1).max() * 1000))
    return co, out


def neck_mask(co, yc=-0.040):
    r = np.hypot(co[:, 0], co[:, 1] - yc)            # only the neck itself (not the shoulders / trapezius)
    return ss((co[:, 1] + 0.100) / 0.020) * ss((0.085 - r) / 0.020)   # and not under the chin / the face


def neck_scale(co, mask, yc=-0.040):
    """slimmer neck: radial scale around a vertical axis (x=0, y=yc), between the base of the neck and the jaw"""
    Z = co[:, 2]; w = ss((Z - 1.335) / 0.035) * ss((1.470 - Z) / 0.035) * mask
    k = 1 - E('NK', 0.05) * w
    co = co.copy(); co[:, 0] *= k; co[:, 1] = yc + (co[:, 1] - yc) * k
    return co
