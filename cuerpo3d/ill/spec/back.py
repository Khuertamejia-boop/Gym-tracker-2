# BACK region (prefix bk_): trapezius (upper / middle / lower + the tendinous diamond at C7), deltoid (anterior /
# lateral / posterior heads), infraspinatus, teres minor, teres major, rhomboid major (only its visible triangle of
# auscultation), latissimus dorsi, erector spinae (lumbar columns) and the thoracolumbar fascia.  LEFT side (+x).
#
# Borders are dense landmark chains (generated below with a small spline helper so that no segment is longer than
# ~1.6 cm: the mesh is a ~6 mm quad grid and longer diagonal segments read as detours).  CHAINS lists every border
# in order; other regions must use these exact landmark lists for the borders they share with the back region.
#
# ARM AUTHOR: use these (read-only; print them with  python -I -c "import runpy;print(runpy.run_path('spec/back.py')['CHAINS'])")
#   CHAINS['delt_lower_front']  dp_low ... delt_ins       deltoid | biceps / brachialis (front of the arm)
#   CHAINS['delt_lower_back']   delt_ins ... bk_dl_tri    deltoid | triceps: lateral head below delt_ins..bk_dl_b3,
#                                                        long head below bk_dl_b3..bk_dl_tri
#   bk_dl_b3   = top of the triceps lateral | long head division (on the deltoid edge)
#   bk_dl_tri  = where the triceps LONG HEAD comes out from under the posterior deltoid (its medial edge starts here)
#   CHAINS['longhead_medial']   bk_dl_tri, ..., bk_tt, ..., ax_back   long head medial edge from the deltoid to the
#                               armpit: teres minor touches it along bk_dl_tri..bk_tt, teres major along bk_tt..ax_back
#                               (the long head passes between them)
#   ax_back    = back of the armpit: teres major and the latissimus tendon go under the long head here; the
#                latissimus edge then runs CHAINS['lat_axilla'] (ax_back ... lat_ax) along the torso side of the crease
import math

LM = {}
CHAINS = {}
_SHARED = {'occ', 'c7', 't3', 't7', 't12', 'l4', 'sac', 'jug', 'xiph', 'pubis', 'sc_l', 'clav_mid', 'trap_clav', 'dp_top',
           'acr', 'sps_med', 'sps_mid', 'sps_lat', 'inf_ang', 'ax_back', 'ax_front', 'dp_mid', 'dp_low', 'delt_ins',
           'lat_ax', 'lat_mid', 'crest_side', 'crest_back', 'psis', 'asis'}
_count = {}


def _cr(p0, p1, p2, p3, t):
    return tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


def chain(key, prefix, kind, ctrl, step=0.012, scale=(1.0, 1.0), head=()):
    """Spline through control points; ctrl items: (name-or-None, (a, b)).  Named shared landmarks are only used
    for the shape; named own landmarks are defined here (once).  Returns the list of landmark names."""
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
            d = math.hypot((pts[i + 1][0] - pts[i][0]) * scale[0], (pts[i + 1][1] - pts[i][1]) * scale[1])
            m = max(0, int(round(d / step)) - 1)
            for j in range(1, m + 1):
                put(None, _cr(pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)], j / (m + 1.0)))
    CHAINS[key] = out
    return out


def sub(ch, a, b):
    """part of a chain from landmark a to landmark b (either direction)"""
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
                out[-1] = n            # junction: keep the flag of the segment that follows
            else:
                out.append(n)
    if len(out) > 1 and out[-1].rstrip('~!') == out[0].rstrip('~!'):
        out.pop()
    return out


LIMB = ('upper_arm.L',)
LS = (0.28, 0.060 * math.pi / 180)   # limb (t, deg) -> metres

# ------------------------------------------------------------------ trapezius
occ_line = chain('occ_line', 'bk_oc', 'B', [('occ', (0.0, 1.530)), ('bk_tocc', (0.033, 1.522))])
neck = chain('trap_neck', 'bk_tn', 'MX', [('bk_tocc', (0.025, 1.521)), (None, (0.017, 1.495)), (None, (0.007, 1.465)),
                                          (None, (-0.005, 1.435)), (None, (-0.016, 1.408)), ('trap_clav', (-0.025, 1.385))],
             head=(0.0,))
clav_ins = chain('trap_clavicle', 'bk_tc', 'T', [('trap_clav', (0.105, -0.025)), (None, (0.130, -0.016)), (None, (0.155, -0.006)),
                                                  (None, (0.175, 0.003)), ('acr', (0.192, 0.010))])
div_um = chain('trap_upper_middle', 'bk_um', 'B', [('bk_td_lat', (0.042, 1.428)), (None, (0.070, 1.418)), (None, (0.100, 1.405)),
                                                  (None, (0.140, 1.391)), (None, (0.170, 1.384)), ('acr', (0.192, 1.380))])
diamond = chain('trap_diamond', 'bk_td', 'B', [('bk_td_top', (0.0, 1.478)), (None, (0.016, 1.463)), (None, (0.031, 1.445)),
                                              ('bk_td_lat', (0.042, 1.428)), (None, (0.030, 1.409)), (None, (0.015, 1.394)),
                                              ('bk_td_bot', (0.0, 1.382))])
div_ml = chain('trap_middle_lower', 'bk_ml', 'B', [('t3', (0.0, 1.335)), ('sps_med', (0.078, 1.335))], step=0.03)
lowtrap = chain('trap_lower_edge', 'bk_tle', 'B', [('sps_med', (0.078, 1.335)), (None, (0.083, 1.310)), ('bk_msb1', (0.087, 1.286)),
                                                  ('bk_tle1', (0.078, 1.266)), (None, (0.064, 1.237)), ('bk_tle3', (0.050, 1.208)),
                                                  (None, (0.033, 1.170)), (None, (0.016, 1.130)), ('t12', (0.0, 1.100))])
# scapular spine (shared chain sps_med, sps_mid, sps_lat, acr) + one own point between sps_lat and acr
LM['bk_sp1'] = ('P', 0.183, 0.020, 1.379)
spine = ['sps_med', 'sps_mid', 'sps_lat', 'bk_sp1', 'acr']
CHAINS['scap_spine'] = spine
midline_up = ['occ', 'bk_td_top', 'c7', 'bk_td_bot', 't3', 't7', 't12']
LM['bk_td_top'] = ('B', 0.0, 1.478)
LM['bk_td_bot'] = ('B', 0.0, 1.382)

# ------------------------------------------------------------------ scapula / rotator cuff / teres
msb = chain('scap_medial', 'bk_ms', 'B', [('bk_msb1', (0.087, 1.286)), ('bk_msb1b', (0.090, 1.270)), (None, (0.094, 1.242)),
                                         ('inf_ang', (0.098, 1.215))])
lat_up = chain('lat_upper', 'bk_lu', 'B', [('bk_tle3', (0.050, 1.208)), (None, (0.074, 1.211)), ('inf_ang', (0.098, 1.215)),
                                          ('bk_lu1', (0.118, 1.219)), (None, (0.145, 1.228)), (None, (0.172, 1.240)),
                                          ('ax_back', (0.196, 1.255))])
tmaj_up = chain('teres_major_upper', 'bk_tmu', 'B', [('inf_ang', (0.098, 1.215)), ('bk_tm0', (0.105, 1.229)), ('bk_is_t2', (0.120, 1.250)),
                                                    (None, (0.140, 1.259)), (None, (0.160, 1.267)), (None, (0.178, 1.275)),
                                                    ('bk_tt', (0.193, 1.282))])
is_tmin = chain('infra_teres_minor', 'bk_itm', 'B', [('bk_is_t2', (0.120, 1.250)), ('bk_is_t1', (0.127, 1.271)), (None, (0.145, 1.290)),
                                                    (None, (0.163, 1.302)), ('bk_dl_is', (0.178, 1.311))])
longhead = chain('longhead_medial', 'bk_lh', 'B', [('bk_dl_tri', (0.203, 1.300)), ('bk_tt', (0.193, 1.283)), (None, (0.192, 1.268)),
                                                  ('ax_back', (0.196, 1.255))])
LM['bk_ax1'] = ('P', 0.1865, 0.055, 1.235)
lat_ax = ['ax_back', 'bk_ax1', 'lat_ax']
CHAINS['lat_axilla'] = lat_ax

# ------------------------------------------------------------------ deltoid
delt_top = chain('delt_top', 'bk_dt', 'T', [('dp_top', (0.128, -0.041)), (None, (0.150, -0.031)), ('bk_acr_a', (0.176, -0.016)),
                                           (None, (0.186, -0.004)), ('acr', (0.192, 0.010))])
delt_back = chain('delt_post_border', 'bk_db', 'B', [('sps_mid', (0.128, 1.356)), (None, (0.141, 1.342)), ('bk_dl_p', (0.155, 1.329)),
                                                    (None, (0.167, 1.319)), ('bk_dl_is', (0.178, 1.311)), (None, (0.191, 1.305)),
                                                    ('bk_dl_tri', (0.203, 1.300))])
delt_lb = chain('delt_lower_back', 'bk_dl_b', 'limb', [('delt_ins', (0.48, 90)), (None, (0.44, 112)), (None, (0.40, 132)),
                                                     (None, (0.35, 150)), ('bk_dl_b3', (0.30, 165)), (None, (0.27, 175)),
                                                     ('bk_dl_tri', (0.24, 182))], scale=LS, head=LIMB)
delt_lf = chain('delt_lower_front', 'bk_dl_f', 'limb', [('dp_low', (0.207, -25)), (None, (0.25, -12)), (None, (0.30, 2)),
                                                      (None, (0.35, 20)), (None, (0.40, 42)), (None, (0.44, 65)),
                                                      ('delt_ins', (0.48, 90))], scale=LS, head=LIMB)
delt_al = chain('delt_ant_lat', 'bk_dal', 'L', [('bk_acr_a', (-0.016, 1.388)), (None, (-0.030, 1.355)), (None, (-0.036, 1.320)),
                                                (None, (-0.036, 1.285)), (None, (-0.032, 1.262)), ('delt_ins', (-0.027, 1.242))])
delt_lp = chain('delt_lat_post', 'bk_dlp', 'L', [('sps_lat', (0.028, 1.376)), (None, (0.032, 1.345)), (None, (0.030, 1.315)),
                                                 (None, (0.020, 1.285)), (None, (0.003, 1.262)), ('delt_ins', (-0.027, 1.242))])

# ------------------------------------------------------------------ latissimus / low back
lat_fas = chain('lat_fascia', 'bk_lf', 'B', [('crest_back', (0.075, 0.965)), (None, (0.084, 0.985)), ('bk_lf1', (0.088, 1.008)),
                                            (None, (0.086, 1.032)), (None, (0.075, 1.052)), ('bk_lf3', (0.058, 1.067)),
                                            (None, (0.036, 1.080)), ('bk_lf4', (0.014, 1.090)), ('t12', (0.0, 1.100))])
es_lat = chain('erector_lateral', 'bk_esl', 'B', [('psis', (0.042, 0.930)), (None, (0.049, 0.955)), (None, (0.054, 0.985)),
                                                 (None, (0.057, 1.015)), (None, (0.058, 1.045)), ('bk_lf3', (0.058, 1.067))])
es_med = chain('erector_medial', 'bk_esm', 'B', [('sac', (0.0, 0.900)), (None, (0.008, 0.930)), (None, (0.012, 0.965)),
                                                (None, (0.013, 1.000)), (None, (0.014, 1.035)), (None, (0.014, 1.065)),
                                                ('bk_lf4', (0.014, 1.090))])

# ------------------------------------------------------------------ muscles
MUSCLES = {
 'trap_upper': dict(loop=loop(sub(diamond, 'bk_td_lat', 'bk_td_top'), 'occ', occ_line, neck, clav_ins, soft(div_um[::-1])),
                    seed=('T', 0.09, 0.0), origin=('bk_td_lat', 'bk_tocc'), insertion=('trap_clav', 'acr'), sp=6, group='trapezius'),
 'trap_middle': dict(loop=loop(sub(diamond, 'bk_td_lat', 'bk_td_bot'), soft(['t3'] + div_ml[1:]), spine, soft(div_um[::-1])),
                     seed=('B', 0.07, 1.375), origin=('bk_td_lat', 't3'), insertion=('sps_med', 'acr'), sp=6, group='trapezius'),
 'trap_lower': dict(loop=loop(['t3', 't7', 't12'], lowtrap[::-1], soft(div_ml[::-1])),
                    seed=('B', 0.035, 1.25), origin=('t3', 't12'), insertion=('sps_med', 'sps_med'), sp=6, group='trapezius'),
 'trap_tendon': dict(loop=loop(['bk_td_top', 'c7', 'bk_td_bot'], diamond[::-1]),
                     seed=('B', 0.010, 1.432), kind='tendon', group='trapezius'),
 'deltoid_anterior': dict(loop=loop(sub(delt_top, 'dp_top', 'bk_acr_a'), soft(delt_al), delt_lf[::-1], 'dp_mid'),
                          seed=('limb', 'upper_arm.L', 0.2, 5), origin=('dp_top', 'bk_acr_a'), insertion=('delt_ins', 'delt_ins'),
                          sp=6, group='deltoid'),
 'deltoid_lateral': dict(loop=loop(sub(delt_top, 'bk_acr_a', 'acr'), ['acr', 'bk_sp1'], soft(delt_lp), soft(delt_al[::-1])),
                         seed=('limb', 'upper_arm.L', 0.2, 88), origin=('bk_acr_a', 'sps_lat'), insertion=('delt_ins', 'delt_ins'),
                         sp=6, group='deltoid'),
 'deltoid_posterior': dict(loop=loop(['sps_lat', 'sps_mid'], delt_back[1:], delt_lb[::-1], soft(delt_lp[::-1])),
                           seed=('limb', 'upper_arm.L', 0.2, 165), origin=('sps_lat', 'sps_mid'), insertion=('delt_ins', 'delt_ins'),
                           sp=6, group='deltoid'),
 'infraspinatus': dict(loop=loop(msb[::-1], sub(lowtrap, 'bk_msb1', 'sps_med'), 'sps_mid', sub(delt_back, 'sps_mid', 'bk_dl_is'),
                                 is_tmin[::-1], sub(tmaj_up, 'bk_is_t2', 'inf_ang')),
                       seed=('B', 0.115, 1.29), origin=('inf_ang', 'sps_med'), insertion=('sps_mid', 'bk_dl_is'), sp=6),
 'teres_minor': dict(loop=loop(is_tmin, sub(delt_back, 'bk_dl_is', 'bk_dl_tri'), sub(longhead, 'bk_dl_tri', 'bk_tt'),
                               sub(tmaj_up, 'bk_tt', 'bk_is_t2')),
                     seed=('B', 0.160, 1.285), origin=('bk_is_t2', 'bk_is_t1'), insertion=('bk_dl_is', 'bk_tt'), sp=5),
 'teres_major': dict(loop=loop(sub(lat_up, 'bk_lu1', 'inf_ang'), tmaj_up, sub(longhead, 'bk_tt', 'ax_back'), sub(lat_up, 'ax_back', 'bk_lu1')),
                     seed=('B', 0.150, 1.249), origin=('bk_lu1', 'bk_tm0'), insertion=('bk_tt', 'ax_back'), sp=6),
 'rhomboid_major': dict(loop=loop(sub(lowtrap, 'bk_tle3', 'bk_msb1'), msb, sub(lat_up, 'inf_ang', 'bk_tle3')),
                        seed=('B', 0.080, 1.235), origin=('bk_tle3', 'bk_tle1'), insertion=('bk_msb1b', 'inf_ang'), sp=5),
 'latissimus_dorsi': dict(loop=loop(['crest_side', 'crest_back'], lat_fas, sub(lowtrap, 't12', 'bk_tle3'), lat_up, lat_ax, 'lat_mid'),
                          seed=('B', 0.12, 1.12), origin=('crest_side', 'bk_tle3'), insertion=('ax_back', 'lat_ax'), sp=7),
 'thoracolumbar_fascia': dict(loop=loop(['crest_back', 'psis'], es_lat, sub(lat_fas, 'bk_lf3', 'crest_back')),
                              seed=('B', 0.072, 1.00), kind='tendon'),
 'erector_spinae': dict(loop=loop(['sac', 'psis'], es_lat, sub(lat_fas, 'bk_lf3', 'bk_lf4'), es_med[::-1]),
                        seed=('B', 0.035, 1.00), origin=('sac', 'psis'), insertion=('bk_lf3', 'bk_lf4'), sp=5),
}
