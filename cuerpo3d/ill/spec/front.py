# FRONT region (prefix fr_): pectoralis major (clavicular + sternal heads), serratus anterior (digitations),
# external oblique, rectus abdominis (4 segments split by the tendinous intersections, drawn as hard lines: the soft version
# was almost invisible at 16:9; linea alba = the midline line), and the
# sternocleidomastoid.  LEFT side (+x); the right side is mirrored.
# Shared borders: clavicle (sc_l, clav_mid, dp_top), deltopectoral (dp_top, dp_mid, dp_low), pec_arm (dp_low,
# ax_front), lat_front (lat_ax, lat_mid, crest_side), pelvis (crest_side, asis, pubis); the armpit point ar_ax_mid
# comes from spec/arm.py (coracobrachialis | serratus).
import math

LM = {}
CHAINS = {}
_SHARED = {'occ', 'c7', 't3', 't7', 't12', 'l4', 'sac', 'jug', 'xiph', 'pubis', 'sc_l', 'clav_mid', 'trap_clav', 'dp_top',
           'acr', 'sps_med', 'sps_mid', 'sps_lat', 'inf_ang', 'ax_back', 'ax_front', 'dp_mid', 'dp_low', 'delt_ins',
           'lat_ax', 'lat_mid', 'crest_side', 'crest_back', 'psis', 'asis', 'ar_ax_mid'}
_count = {}


def _cr(p0, p1, p2, p3, t):
    return tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


def chain(key, prefix, kind, ctrl, step=0.012, head=()):
    """Catmull-Rom spline through control points (name-or-None, coords); named shared landmarks only shape it."""
    pts = [tuple(c[1]) for c in ctrl]
    out = []

    def put(nm, p):
        if nm is None:
            k = _count.get(prefix, 0); _count[prefix] = k + 1; nm = '%s_%d' % (prefix, k)
        if nm not in _SHARED and nm not in LM:
            LM[nm] = (kind,) + tuple(head) + tuple(round(x, 4) for x in p)
        out.append(nm)
    for i in range(len(pts)):
        put(ctrl[i][0], pts[i])
        if i < len(pts) - 1:
            d = math.dist(pts[i + 1], pts[i])
            m = max(0, int(round(d / step)) - 1)
            for j in range(1, m + 1):
                put(None, _cr(pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)], j / (m + 1.0)))
    CHAINS[key] = out
    return out


def sub(ch, a, b):
    i, j = ch.index(a), ch.index(b)
    return ch[i:j + 1] if i <= j else ch[j:i + 1][::-1]


def soft(ch):
    return [n + '~' for n in ch[:-1]] + [ch[-1]]


def loop(*parts):
    out = []
    for p in parts:
        p = [p] if isinstance(p, str) else list(p)
        for n in p:
            if out and out[-1].rstrip('~!') == n.rstrip('~!'):
                out[-1] = n
            else:
                out.append(n)
    if len(out) > 1 and out[-1].rstrip('~!') == out[0].rstrip('~!'):
        out.pop()
    return out


# ------------------------------------------------------------------ pectoralis major
clav = ['sc_l', 'clav_mid', 'dp_top']
dpg = ['dp_top', 'dp_mid', 'dp_low', 'ax_front']
stern = chain('fr_sternal', 'fr_st', 'F', [('sc_l', (0.025, 1.386)), (None, (0.015, 1.368)), ('fr_pd_m', (0.011, 1.345)),
                                          (None, (0.010, 1.300)), (None, (0.010, 1.255)), ('fr_st_low', (0.012, 1.207))],
              step=0.014)
pec_low = chain('fr_pec_lower', 'fr_pl', 'F', [('ax_front', (0.168, 1.245)), (None, (0.158, 1.220)), ('fr_pl_sa', (0.142, 1.200)),
                                              (None, (0.122, 1.187)), (None, (0.100, 1.181)), ('fr_ra_top', (0.080, 1.182)),
                                              (None, (0.056, 1.187)), (None, (0.033, 1.195)), ('fr_st_low', (0.012, 1.207))])
pec_div = chain('fr_pec_div', 'fr_pd', 'F', [('fr_pd_m', (0.011, 1.345)), (None, (0.045, 1.336)), (None, (0.085, 1.326)),
                                            (None, (0.125, 1.311)), (None, (0.155, 1.299)), ('dp_low', (0.178, 1.290))])

# ------------------------------------------------------------------ serratus anterior / external oblique (zig-zag)
# from the lats border (lat_mid) up and forwards to the pectoral's lower border: tips point forwards-down
zig = ['lat_mid', 'fr_sz_t1', 'fr_sz_n1', 'fr_sz_t2', 'fr_sz_n2', 'fr_sz_t3', 'fr_pl_sa']
LM.update({'fr_sz_t1': ('MX', 0.0, -0.052, 1.110), 'fr_sz_n1': ('MX', 0.0, -0.012, 1.136),
           'fr_sz_t2': ('MX', 0.0, -0.074, 1.143), 'fr_sz_n2': ('MX', 0.0, -0.036, 1.167),
           'fr_sz_t3': ('MX', 0.0, -0.092, 1.173)})
CHAINS['fr_zigzag'] = zig
sa_top = ['ax_front', 'ar_ax_mid', 'lat_ax']

# ------------------------------------------------------------------ rectus abdominis + linea alba
ra_lat = chain('fr_rectus_lateral', 'fr_rl', 'F', [('fr_ra_top', (0.080, 1.182)), (None, (0.082, 1.155)), ('fr_i1l', (0.081, 1.128)),
                                                   (None, (0.078, 1.097)), ('fr_i2l', (0.074, 1.067)), (None, (0.070, 1.036)),
                                                   ('fr_i3l', (0.066, 1.006)), (None, (0.062, 0.975)), (None, (0.055, 0.944)),
                                                   (None, (0.045, 0.912)), (None, (0.032, 0.880)), (None, (0.016, 0.853)),
                                                   ('pubis', (0.0, 0.830))], step=0.015)
# medial border = midline (the line between left and right rectus reads as the linea alba)
ra_med = chain('fr_rectus_medial', 'fr_rm', 'F', [('fr_la_top', (0.0, 1.190)), ('fr_i1m', (0.0, 1.124)), ('fr_i2m', (0.0, 1.064)),
                                                  ('fr_i3m', (0.0, 1.004)), (None, (0.0, 0.945)), (None, (0.0, 0.888)),
                                                  ('pubis', (0.0, 0.830))], step=0.03)
i1 = chain('fr_int1', 'fr_ia', 'F', [('fr_i1m', (0.0, 1.124)), (None, (0.030, 1.118)), (None, (0.055, 1.122)), ('fr_i1l', (0.081, 1.128))])
i2 = chain('fr_int2', 'fr_ib', 'F', [('fr_i2m', (0.0, 1.064)), (None, (0.030, 1.059)), (None, (0.052, 1.062)), ('fr_i2l', (0.074, 1.067))])
i3 = chain('fr_int3', 'fr_ic', 'F', [('fr_i3m', (0.0, 1.004)), (None, (0.028, 1.000)), (None, (0.048, 1.002)), ('fr_i3l', (0.066, 1.006))])
LM['fr_la_top'] = ('F', 0.0, 1.190)
ra_top = sub(pec_low, 'fr_ra_top', 'fr_st_low') + ['fr_la_top']

# ------------------------------------------------------------------ sternocleidomastoid
scm_post = chain('fr_scm_post', 'fr_sp', 'MX', [('fr_mast', (0.000, 1.518)), (None, (-0.010, 1.494)), (None, (-0.020, 1.466)),
                                                (None, (-0.030, 1.436)), (None, (-0.037, 1.410)), ('clav_mid', (-0.040, 1.386))],
                 head=(0.0,))
scm_ant = chain('fr_scm_ant', 'fr_sa', 'P', [('fr_mast', (0.050, 0.000, 1.518)), (None, (0.046, -0.025, 1.498)),
                                             (None, (0.037, -0.044, 1.470)), (None, (0.026, -0.057, 1.440)),
                                             (None, (0.017, -0.064, 1.412)), ('fr_scm_st', (0.012, -0.068, 1.392))])
LM['fr_scm_st'] = ('F', 0.012, 1.392)

# ------------------------------------------------------------------ muscles
MUSCLES = {
 'pec_clavicular': dict(loop=loop(clav, ['dp_top', 'dp_mid', 'dp_low'], soft(pec_div[::-1]), sub(stern, 'fr_pd_m', 'sc_l')),
                        seed=('F', 0.06, 1.36), origin=('sc_l', 'dp_top'), insertion=('dp_low', 'dp_low'), sp=6,
                        group='pectoralis_major'),
 'pec_sternal': dict(loop=loop(sub(stern, 'fr_pd_m', 'fr_st_low'), pec_low[::-1], ['ax_front', 'dp_low'], soft(pec_div[::-1])),
                     seed=('F', 0.08, 1.26), origin=('fr_pd_m', 'fr_st_low'), insertion=('ax_front', 'dp_low'), sp=6,
                     group='pectoralis_major'),
 'serratus_anterior': dict(loop=loop(sa_top, 'lat_mid', zig, sub(pec_low, 'fr_pl_sa', 'ax_front')),
                           seed=('MX', 0.0, -0.040, 1.190), origin=('lat_mid', 'fr_pl_sa'), insertion=('ax_front', 'lat_ax'), sp=5),
 'external_oblique': dict(loop=loop(zig, sub(pec_low, 'fr_pl_sa', 'fr_ra_top'), ra_lat, ['pubis', 'asis', 'crest_side', 'lat_mid']),
                          seed=('F', 0.125, 1.05), origin=('lat_mid', 'fr_pl_sa'), insertion=('fr_ra_top', 'asis'), sp=6),
 'rectus_abd_1': dict(loop=loop(ra_top, sub(ra_med, 'fr_la_top', 'fr_i1m'), i1, sub(ra_lat, 'fr_i1l', 'fr_ra_top')),
                      seed=('F', 0.045, 1.155), origin=('fr_i1m', 'fr_i1l'), insertion=('fr_ra_top', 'fr_la_top'), sp=6,
                      group='rectus_abdominis'),
 'rectus_abd_2': dict(loop=loop(i1, sub(ra_lat, 'fr_i1l', 'fr_i2l'), i2[::-1], sub(ra_med, 'fr_i2m', 'fr_i1m')),
                      seed=('F', 0.045, 1.095), origin=('fr_i2l', 'fr_i2m'), insertion=('fr_i1m', 'fr_i1l'), sp=6,
                      group='rectus_abdominis'),
 'rectus_abd_3': dict(loop=loop(i2, sub(ra_lat, 'fr_i2l', 'fr_i3l'), i3[::-1], sub(ra_med, 'fr_i3m', 'fr_i2m')),
                      seed=('F', 0.040, 1.035), origin=('fr_i3l', 'fr_i3m'), insertion=('fr_i2m', 'fr_i2l'), sp=6,
                      group='rectus_abdominis'),
 'rectus_abd_4': dict(loop=loop(i3, sub(ra_lat, 'fr_i3l', 'pubis'), sub(ra_med, 'pubis', 'fr_i3m')),
                      seed=('F', 0.035, 0.96), origin=('pubis', 'pubis'), insertion=('fr_i3m', 'fr_i3l'), sp=6,
                      group='rectus_abdominis'),
 'sternocleidomastoid': dict(loop=loop(scm_ant, ['fr_scm_st', 'sc_l', 'clav_mid'], scm_post[::-1]),
                             seed=('P', 0.040, -0.035, 1.45), origin=('fr_scm_st', 'clav_mid'), insertion=('fr_mast', 'fr_mast'), sp=5),
}
