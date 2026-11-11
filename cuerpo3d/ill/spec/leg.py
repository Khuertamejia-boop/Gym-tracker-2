# LEG region (prefix lg_): gluteals, hip, thigh, knee and lower leg down to the ankle (feet stay plain). LEFT side (+x).
#
# Limb landmarks: th(t,a) = ('limb','thigh.L',t,a), t 0 = hip joint (z 0.875) .. 1 = knee (z 0.475);
#                 sh(t,a) = ('limb','shin.L',t,a),  t 0 = knee .. 1 = ankle (z 0.08).
#                 a: 0 front, 90 outer side, 180 back, -90 inner side (back angles may be written >180 to keep
#                 interpolation continuous, e.g. 190 = -170).
# Every border between two muscles is written ONCE below as a polyline of control points (`border(...)`); the helper
# inserts landmarks between consecutive control points of the same kind so that they are <= ~2 cm apart, and the
# muscle loops are assembled from those borders (a leading '-' walks a border backwards), so neighbours always share
# exactly the same landmarks.
import math

def th(t, a): return ('limb', 'thigh.L', t, a)
def sh(t, a): return ('limb', 'shin.L', t, a)

SHARED = {'sac': ('B', 0.0, 0.900), 'psis': ('B', 0.042, 0.930), 'crest_back': ('B', 0.075, 0.965),
          'crest_side': ('MX', 0.0, 0.010, 0.975), 'asis': ('F', 0.105, 0.925), 'pubis': ('F', 0.0, 0.830)}
LM = {}
BORD = {}
STEP = 0.016

def _spec(p):
    if isinstance(p, str): return LM[p] if p in LM else SHARED[p]
    return p

def _lp(s):  # limb spec -> (combined parameter, angle); shin continues the thigh (1..2)
    return (s[2] if s[1] == 'thigh.L' else 1.0 + s[2], s[3])

def _da(a1, a2):  # shortest angle difference a2 - a1
    return ((a2 - a1 + 180.0) % 360.0) - 180.0

def _fam(s):
    if s[0] == 'limb': return ('limb',)
    if s[0] == 'MX': return ('MX', s[1])
    return (s[0],)

def _dist(a, b):
    if a[0] == 'limb':
        (s1, a1), (s2, a2) = _lp(a), _lp(b); r = 0.075 if (s1 + s2) < 2 else 0.05
        return math.hypot((s1 - s2) * 0.40, math.radians(_da(a1, a2)) * r)
    if a[0] == 'MX': return 1.25 * math.hypot(a[2] - b[2], a[3] - b[3])
    if a[0] == 'P': return 1.15 * math.dist(a[1:4], b[1:4])
    return 1.25 * math.hypot(a[1] - b[1], a[2] - b[2])

def _lerp(a, b, f):
    if a[0] == 'limb':
        (s1, a1), (s2, a2) = _lp(a), _lp(b); s = s1 + (s2 - s1) * f; an = a1 + _da(a1, a2) * f
        return th(round(s, 4), round(an, 2)) if s <= 1.0 else sh(round(s - 1.0, 4), round(an, 2))
    if a[0] == 'MX': return ('MX', a[1], round(a[2] + (b[2] - a[2]) * f, 4), round(a[3] + (b[3] - a[3]) * f, 4))
    if a[0] == 'P': return ('P',) + tuple(round(a[i] + (b[i] - a[i]) * f, 4) for i in (1, 2, 3))
    return (a[0], round(a[1] + (b[1] - a[1]) * f, 4), round(a[2] + (b[2] - a[2]) * f, 4))

def J(name, spec):          # junction landmark (corner shared by 3+ regions)
    LM[name] = spec; return name

def border(name, pts, step=STEP):
    # interior landmarks are named so that their alphabetical order runs from one end of the border to the other:
    # the compiler orients every segment by name, and a consistent orientation keeps the line continuous.
    seq = []
    for i, p in enumerate(pts):
        if i > 0:
            a, b = _spec(pts[i - 1]), _spec(p)
            if _fam(a) == _fam(b):
                n = int(math.ceil(_dist(a, b) / step))
                for j in range(1, n): seq.append(_lerp(a, b, j / n))
        seq.append(p)
    ends = [x for x in (pts[0], pts[-1])]
    assert isinstance(ends[0], str) and isinstance(ends[1], str), name
    lo, hi = sorted(ends); tag = name[len('lg_b_'):]
    base = (lo + '_' + tag) if lo.startswith('lg_') else ('lg_0' + tag)
    assert not hi.startswith(lo + '_'), name
    inner = [x for x in seq[:-1] if not isinstance(x, str)]
    n = len(inner); out = [pts[0]]; k = 0
    for x in seq[1:-1]:
        k += 1; idx = k if pts[0] == lo else n + 1 - k
        nm = '%s%02d' % (base, idx); LM[nm] = x; out.append(nm)
    out.append(pts[-1])
    assert all(out[i] < out[i + 1] for i in range(len(out) - 1)) or all(out[i] > out[i + 1] for i in range(len(out) - 1)), name
    BORD[name] = out
    return name

def loop(*parts):
    out = []
    for p in parts:
        seq = BORD[p[1:]][::-1] if p.startswith('-') else (BORD[p] if p in BORD else [p])
        for n in seq:
            if not out or out[-1] != n: out.append(n)
    if out[0] == out[-1]: out.pop()
    return out

# ======================================================================= junctions
J('lg_cleft_bot', ('B', 0.0, 0.790))        # lower end of the gluteal cleft (midline, shared by both sides)
J('lg_gm_lo1', ('B', 0.035, 0.768))         # gmax lower border | groin crease | adductor magnus
J('lg_gm_lo2', ('B', 0.062, 0.757))         # adductor magnus | semitendinosus under the gmax
J('lg_ham_top', ('B', 0.090, 0.750))        # semitendinosus | biceps femoris (ischial tuberosity)
J('lg_gm_itb', th(0.36, 128))               # lower lateral corner of the gmax on the ITB
J('lg_troch', th(0.08, 95))                 # greater trochanter: gmed / TFL / ITB / gmax
J('lg_rf_top', th(0.04, 20))                # V between sartorius and TFL where the rectus femoris appears
J('lg_vl_top', th(0.22, 42))                # TFL | RF | VL
J('lg_tfl_tip', th(0.32, 78))               # lower end of the TFL on the ITB
J('lg_ftri', th(0.30, -38))                 # apex of the femoral triangle
J('lg_al_tip', th(0.54, -88))               # lower end of adductor longus (under the sartorius)
J('lg_al_top', ('P', 0.050, -0.104, 0.785))  # adductor longus origin next to the pubic bulge
J('lg_rf_sv', th(0.45, -20))                # top of the vastus medialis (RF | sartorius | VM)
J('lg_rf_lo_l', th(0.79, 14)); J('lg_rf_lo_m', th(0.79, -14))     # RF -> quadriceps tendon
J('lg_pat_sl', th(0.88, 22)); J('lg_pat_sm', th(0.88, -22))       # upper corners of the patella
J('lg_pat_bl', sh(0.02, 14)); J('lg_pat_bm', sh(0.02, -14))       # patellar tendon top (patella apex)
J('lg_tt_l', sh(0.13, 12)); J('lg_tt_m', sh(0.13, -12))           # tibial tuberosity
J('lg_vl_itb_lo', th(0.86, 85))             # VL leaves the ITB
J('lg_itb_bf_lo', th(0.86, 108))            # biceps femoris leaves the ITB
J('lg_gerdy', sh(0.11, 47))                 # Gerdy's tubercle (ITB insertion; TA | EDL top)
J('lg_fib', sh(0.12, 115))                  # fibular head (biceps insertion, peroneus longus origin)
J('lg_edl_top', sh(0.12, 72))
J('lg_vm_sart', th(0.84, -95))              # lower end of VM on the sartorius
J('lg_pes', sh(0.16, -78))                  # pes anserinus (sartorius, gracilis, semitendinosus)
J('lg_gr0', ('P', 0.025, -0.080, 0.752))    # groin crease, front (adductor longus | gracilis)
J('lg_groin2', ('P', 0.009, 0.000, 0.761))  # groin crease, middle (gracilis | adductor magnus)
J('lg_am_tip', th(0.70, -128))
J('lg_sm_top', th(0.50, -152))
J('lg_sm_end', th(1.00, -138))
J('lg_pop_top', th(0.80, 174)); J('lg_pop_lat', th(0.98, 148))   # popliteal fossa corners
J('lg_pop_med', th(0.96, 192)); J('lg_pop_bot', sh(0.12, 178))
J('lg_gc_mid', sh(0.42, 178))               # lower end of the groove between the gastrocnemius heads
J('lg_gcl_tip', sh(0.48, 150)); J('lg_gcm_tip', sh(0.60, 202))  # lower ends of the heads
J('lg_sol_top', sh(0.26, 122)); J('lg_solm_top', sh(0.28, -112))
J('lg_solm_lo_f', sh(0.86, -110))
J('lg_ach_l2', sh(0.97, 162)); J('lg_ach_m2', sh(0.97, 198))
J('lg_pbf', sh(0.55, 83)); J('lg_pbb', sh(0.55, 120)); J('lg_pl_end', sh(0.70, 103))
J('lg_pb_lo_f', sh(0.88, 80)); J('lg_pb_lo_b', sh(0.88, 120))
J('lg_ta_lo_l', sh(0.88, 18)); J('lg_ta_lo_m', sh(0.88, -12))

# ======================================================================= borders
# --- buttock
border('lg_b_cleft', ['sac', ('B', 0.0, 0.870), ('B', 0.0, 0.840), ('B', 0.0, 0.812), 'lg_cleft_bot'])
border('lg_b_perin', ['lg_cleft_bot', ('B', 0.018, 0.777), 'lg_gm_lo1'])                 # gmax | perineum (plain)
border('lg_b_gm_am', ['lg_gm_lo1', 'lg_gm_lo2'])
border('lg_b_gm_st', ['lg_gm_lo2', 'lg_ham_top'])
border('lg_b_gm_bf', ['lg_ham_top', ('B', 0.115, 0.746), ('B', 0.140, 0.740), ('B', 0.158, 0.735), 'lg_gm_itb'])
border('lg_b_gm_itb', ['lg_gm_itb', th(0.22, 112), 'lg_troch'])
border('lg_b_gm_gmed', ['crest_back', ('P', 0.090, 0.066, 0.957), th(-0.15, 165), th(-0.10, 150), th(-0.05, 135),
                        th(0.00, 120), th(0.04, 105), 'lg_troch'])
border('lg_b_gmed_tfl', ['asis', th(-0.13, 28), th(-0.08, 42), th(-0.03, 58), th(0.02, 74), th(0.05, 86), 'lg_troch'])
# --- TFL / ITB
border('lg_b_tfl_sart', ['asis', th(-0.10, 22), th(-0.03, 21), 'lg_rf_top'])
border('lg_b_tfl_rf', ['lg_rf_top', th(0.13, 33), 'lg_vl_top'])
border('lg_b_tfl_vl', ['lg_vl_top', th(0.27, 60), 'lg_tfl_tip'])
border('lg_b_tfl_itb', ['lg_troch', th(0.20, 90), 'lg_tfl_tip'])
border('lg_b_itb_vl', ['lg_tfl_tip', th(0.50, 86), th(0.70, 88), 'lg_vl_itb_lo'])
border('lg_b_itb_lo_a', ['lg_vl_itb_lo', th(0.95, 80), sh(0.05, 64), 'lg_gerdy'])         # plain in front
border('lg_b_itb_bf', ['lg_gm_itb', th(0.50, 120), th(0.70, 115), 'lg_itb_bf_lo'])
border('lg_b_itb_lo_p', ['lg_itb_bf_lo', th(0.95, 100), sh(0.04, 88), sh(0.08, 68), 'lg_gerdy'])  # plain behind
# --- quadriceps
border('lg_b_rf_vl', ['lg_vl_top', th(0.40, 30), th(0.60, 25), 'lg_rf_lo_l'])
border('lg_b_rf_qt', ['lg_rf_lo_l', th(0.83, 0), 'lg_rf_lo_m'])
border('lg_b_qt_vl', ['lg_rf_lo_l', 'lg_pat_sl'])
border('lg_b_qt_vm', ['lg_rf_lo_m', 'lg_pat_sm'])
border('lg_b_qt_pat', ['lg_pat_sl', th(0.875, 0), 'lg_pat_sm'])                             # patella top (plain)
border('lg_b_vl_lo', ['lg_pat_sl', th(0.90, 48), 'lg_vl_itb_lo'])                           # plain below
border('lg_b_rf_sart', ['lg_rf_top', th(0.20, 5), th(0.33, -8), 'lg_rf_sv'])
border('lg_b_rf_vm', ['lg_rf_sv', th(0.62, -18), 'lg_rf_lo_m'])
border('lg_b_vm_lo', ['lg_pat_sm', th(0.93, -40), th(0.90, -78), 'lg_vm_sart'])            # plain below
border('lg_b_vm_sart', ['lg_rf_sv', th(0.55, -42), th(0.68, -68), 'lg_vm_sart'])
border('lg_b_pt_top', ['lg_pat_bl', 'lg_pat_bm'])
border('lg_b_pt_m', ['lg_pat_bm', 'lg_tt_m'])
border('lg_b_pt_bot', ['lg_tt_m', 'lg_tt_l'])
border('lg_b_pt_l', ['lg_tt_l', 'lg_pat_bl'])
# --- sartorius / femoral triangle / adductors
border('lg_b_sart_lo', ['lg_vm_sart', th(0.97, -112), sh(0.08, -100), 'lg_pes'])          # plain in front
border('lg_b_ip_sart', ['asis', th(-0.10, 10), th(-0.03, 4), th(0.04, 0), th(0.15, -14), th(0.24, -28), 'lg_ftri'])
border('lg_b_ip_bulge', ['pubis', ('P', 0.020, -0.128, 0.826), ('P', 0.040, -0.115, 0.805), 'lg_al_top'])  # plain (bulge)
border('lg_b_ip_al', ['lg_al_top', ('P', 0.048, -0.098, 0.765), 'lg_ftri'])
border('lg_b_al_sart', ['lg_ftri', th(0.40, -58), th(0.47, -74), 'lg_al_tip'])
border('lg_b_gr_sart', ['lg_al_tip', th(0.62, -92), th(0.78, -115), th(0.95, -135), sh(0.06, -122), 'lg_pes'])
border('lg_b_al_gr', ['lg_al_tip', ('P', 0.012, -0.015, 0.670), ('P', 0.008, -0.028, 0.690), ('P', 0.010, -0.047, 0.710), ('P', 0.016, -0.065, 0.730),
                      'lg_gr0'])
border('lg_b_al_top', ['lg_gr0', ('P', 0.037, -0.093, 0.768), 'lg_al_top'])                # plain (pubic bulge)
border('lg_b_gr_top', ['lg_gr0', ('P', 0.012, -0.060, 0.750), ('P', 0.008, -0.040, 0.753), ('P', 0.006, -0.020, 0.758),
                       'lg_groin2'])                                                        # plain (crotch)
border('lg_b_am_top', ['lg_groin2', ('P', 0.010, 0.020, 0.765), ('P', 0.011, 0.040, 0.770), ('P', 0.018, 0.060, 0.775),
                       'lg_gm_lo1'], step=0.026)                                            # plain (perineum)
border('lg_b_am_gr', ['lg_groin2', ('P', 0.012, 0.015, 0.740), ('P', 0.020, 0.030, 0.715), ('P', 0.025, 0.036, 0.702), th(0.45, -118), th(0.58, -124),
                      'lg_am_tip'])
border('lg_b_sm_gr', ['lg_am_tip', th(0.86, -140), 'lg_sm_end'])
border('lg_b_st_gr', ['lg_sm_end', sh(0.07, -128), 'lg_pes'])
border('lg_b_am_st', ['lg_gm_lo2', ('B', 0.064, 0.735), ('B', 0.068, 0.712), ('B', 0.071, 0.692), 'lg_sm_top'])
border('lg_b_sm_am', ['lg_sm_top', th(0.60, -140), 'lg_am_tip'])
border('lg_b_sm_st', ['lg_sm_top', th(0.75, 195), th(0.92, 202), 'lg_sm_end'])
# --- hamstrings / popliteal fossa
border('lg_b_st_bf', ['lg_ham_top', ('B', 0.096, 0.728), ('B', 0.102, 0.706), ('B', 0.107, 0.688), th(0.50, 178),
                       th(0.65, 177), 'lg_pop_top'])
border('lg_b_pop_l', ['lg_pop_top', th(0.90, 160), 'lg_pop_lat'])                          # BF | fossa (plain)
border('lg_b_pop_m', ['lg_pop_top', th(0.88, 186), 'lg_pop_med'])                          # ST | fossa (plain)
border('lg_b_gcm_st', ['lg_pop_med', th(1.0, 200), sh(0.06, 220), sh(0.12, 250), 'lg_pes'])
border('lg_b_pop_bl', ['lg_pop_lat', sh(0.06, 165), 'lg_pop_bot'])                         # plain
border('lg_b_pop_bm', ['lg_pop_med', sh(0.04, 188), 'lg_pop_bot'])                         # plain
border('lg_b_bf_gcl', ['lg_pop_lat', sh(0.06, 130), 'lg_fib'])
border('lg_b_bf_lo', ['lg_itb_bf_lo', th(0.95, 112), sh(0.04, 115), 'lg_fib'])             # plain in front
# --- lower leg
border('lg_b_gc_mid', ['lg_pop_bot', sh(0.30, 178), 'lg_gc_mid'])
border('lg_b_gcl_ach', ['lg_gc_mid', sh(0.46, 165), 'lg_gcl_tip'])
border('lg_b_gcm_ach', ['lg_gc_mid', sh(0.52, 190), 'lg_gcm_tip'])
border('lg_b_gcl_sol', ['lg_gcl_tip', sh(0.36, 133), 'lg_sol_top'])
border('lg_b_gcl_pl', ['lg_sol_top', 'lg_fib'])
border('lg_b_gcm_sol', ['lg_gcm_tip', sh(0.45, 235), 'lg_solm_top'])
border('lg_b_gcm_tib', ['lg_solm_top', sh(0.22, -100), 'lg_pes'])                          # plain (tibia)
border('lg_b_solm_tib', ['lg_solm_top', sh(0.55, -105), 'lg_solm_lo_f'])                   # plain (tibia)
border('lg_b_solm_lo', ['lg_solm_lo_f', sh(0.93, -135), 'lg_ach_m2'])                      # plain (ankle)
border('lg_b_ach_solm', ['lg_gcm_tip', sh(0.72, 200), 'lg_ach_m2'])
border('lg_b_ach_lo', ['lg_ach_m2', sh(0.98, 180), 'lg_ach_l2'])                           # plain (heel)
border('lg_b_ach_soll', ['lg_gcl_tip', sh(0.70, 160), 'lg_ach_l2'])
border('lg_b_soll_lo', ['lg_ach_l2', sh(0.93, 140), 'lg_pb_lo_b'])                         # plain (ankle)
border('lg_b_soll_pb', ['lg_pbb', sh(0.75, 120), 'lg_pb_lo_b'])
border('lg_b_soll_pl', ['lg_sol_top', sh(0.40, 120), 'lg_pbb'])
border('lg_b_pl_pb_b', ['lg_pbb', 'lg_pl_end'])
border('lg_b_pl_pb_f', ['lg_pbf', 'lg_pl_end'])
border('lg_b_pl_edl', ['lg_edl_top', sh(0.35, 80), 'lg_pbf'])
border('lg_b_pl_top', ['lg_edl_top', 'lg_fib'])                                            # plain
border('lg_b_pb_edl', ['lg_pbf', sh(0.75, 82), 'lg_pb_lo_f'])
border('lg_b_pb_lo', ['lg_pb_lo_f', sh(0.90, 100), 'lg_pb_lo_b'])                          # plain (malleolus)
border('lg_b_edl_lo', ['lg_pb_lo_f', sh(0.90, 50), 'lg_ta_lo_l'])                          # plain
border('lg_b_ta_edl', ['lg_gerdy', sh(0.35, 42), sh(0.60, 32), 'lg_ta_lo_l'])
border('lg_b_edl_top', ['lg_gerdy', 'lg_edl_top'])                                         # plain
border('lg_b_ta_top', ['lg_tt_l', sh(0.12, 30), 'lg_gerdy'])                               # plain
border('lg_b_ta_lo', ['lg_ta_lo_l', 'lg_ta_lo_m'])                                         # plain
border('lg_b_ta_tib', ['lg_tt_l', sh(0.22, 0), sh(0.35, -8), sh(0.60, -10), 'lg_ta_lo_m'])  # plain (tibia)
PELVIS_GMED = ['crest_back', 'crest_side', 'asis']   # shared chain (torso above)
PELVIS_GMAX = ['sac', 'psis', 'crest_back']

# ======================================================================= muscles
MUSCLES = {
 'gluteus_maximus': dict(loop=loop(*PELVIS_GMAX, 'lg_b_gm_gmed', '-lg_b_gm_itb', '-lg_b_gm_bf', '-lg_b_gm_st',
                                   '-lg_b_gm_am', '-lg_b_perin', '-lg_b_cleft'),
                         seed=('B', 0.09, 0.83), origin=('lg_cleft_bot', 'crest_back'),
                         insertion=('lg_troch', 'lg_gm_itb'), sp=7),
 'gluteus_medius': dict(loop=loop(*PELVIS_GMED, 'lg_b_gmed_tfl', '-lg_b_gm_gmed'),
                        seed=('MX', 0.10, 0.02, 0.93), origin=('crest_back', 'asis'),
                        insertion=('lg_troch', 'lg_troch'), sp=6),
 'tensor_fasciae_latae': dict(loop=loop('lg_b_tfl_sart', 'lg_b_tfl_rf', 'lg_b_tfl_vl', '-lg_b_tfl_itb', '-lg_b_gmed_tfl'),
                              seed=th(0.15, 60), origin=('lg_troch', 'lg_rf_top'),
                              insertion=('lg_tfl_tip', 'lg_tfl_tip'), sp=5),
 'iliotibial_band': dict(loop=loop('lg_b_tfl_itb', 'lg_b_itb_vl', 'lg_b_itb_lo_a', '-lg_b_itb_lo_p', '-lg_b_itb_bf',
                                   'lg_b_gm_itb'),
                         seed=th(0.55, 103), kind='tendon'),
 'iliopsoas': dict(loop=loop('asis', 'pubis', 'lg_b_ip_bulge', 'lg_b_ip_al', '-lg_b_ip_sart'),
                   seed=th(0.12, -25), origin=('asis', 'pubis'), insertion=('lg_ftri', 'lg_ftri'), sp=6),
 'sartorius': dict(loop=loop('lg_b_tfl_sart', 'lg_b_rf_sart', 'lg_b_vm_sart', 'lg_b_sart_lo', '-lg_b_gr_sart',
                             '-lg_b_al_sart', '-lg_b_ip_sart'),
                   seed=th(0.50, -55), origin=('asis', 'asis'), insertion=('lg_pes', 'lg_pes'), sp=5),
 'rectus_femoris': dict(loop=loop('lg_b_tfl_rf', 'lg_b_rf_vl', 'lg_b_rf_qt', '-lg_b_rf_vm', '-lg_b_rf_sart'),
                        seed=th(0.45, 5), origin=('lg_rf_top', 'lg_rf_top'), insertion=('lg_rf_lo_l', 'lg_rf_lo_m'), sp=6),
 'vastus_lateralis': dict(loop=loop('lg_b_rf_vl', 'lg_b_qt_vl', 'lg_b_vl_lo', '-lg_b_itb_vl', '-lg_b_tfl_vl'),
                          seed=th(0.55, 60), origin=('lg_vl_itb_lo', 'lg_vl_top'),
                          insertion=('lg_rf_lo_l', 'lg_pat_sl'), sp=6),
 'vastus_medialis': dict(loop=loop('lg_b_rf_vm', 'lg_b_qt_vm', 'lg_b_vm_lo', '-lg_b_vm_sart'),
                         seed=th(0.78, -45), origin=('lg_vm_sart', 'lg_rf_sv'), insertion=('lg_rf_lo_m', 'lg_pat_sm'), sp=6),
 'quadriceps_tendon': dict(loop=loop('lg_b_rf_qt', 'lg_b_qt_vm', '-lg_b_qt_pat', '-lg_b_qt_vl'),
                           seed=th(0.84, 0), kind='tendon'),
 'patellar_tendon': dict(loop=loop('lg_b_pt_top', 'lg_b_pt_m', 'lg_b_pt_bot', 'lg_b_pt_l'), seed=sh(0.08, 0), kind='tendon'),
 'adductor_longus': dict(loop=loop('lg_b_ip_al', 'lg_b_al_sart', 'lg_b_al_gr', 'lg_b_al_top'),
                         seed=th(0.38, -58), origin=('lg_gr0', 'lg_al_top'), insertion=('lg_al_tip', 'lg_al_tip'), sp=6,
                         group='adductors'),
 'gracilis': dict(loop=loop('lg_b_gr_top', 'lg_b_am_gr', 'lg_b_sm_gr', 'lg_b_st_gr', '-lg_b_gr_sart', 'lg_b_al_gr'),
                  seed=th(0.60, -110), origin=('lg_gr0', 'lg_groin2'), insertion=('lg_pes', 'lg_pes'), sp=5,
                  group='adductors'),
 'adductor_magnus': dict(loop=loop('lg_b_am_top', 'lg_b_gm_am', 'lg_b_am_st', 'lg_b_sm_am', '-lg_b_am_gr'),
                         seed=th(0.42, -138), origin=('lg_groin2', 'lg_gm_lo2'), insertion=('lg_am_tip', 'lg_am_tip'),
                         sp=6, group='adductors'),
 'semitendinosus': dict(loop=loop('lg_b_st_bf', 'lg_b_pop_m', 'lg_b_gcm_st', '-lg_b_st_gr', '-lg_b_sm_st', '-lg_b_am_st',
                                  'lg_b_gm_st'),
                        seed=th(0.45, 188), origin=('lg_gm_lo2', 'lg_ham_top'), insertion=('lg_pes', 'lg_pes'), sp=6),
 'semimembranosus': dict(loop=loop('lg_b_sm_st', '-lg_b_sm_gr', '-lg_b_sm_am'),
                         seed=th(0.75, -150), origin=('lg_am_tip', 'lg_sm_top'), insertion=('lg_sm_end', 'lg_sm_end'), sp=6),
 'biceps_femoris': dict(loop=loop('lg_b_gm_bf', 'lg_b_itb_bf', 'lg_b_bf_lo', '-lg_b_bf_gcl', '-lg_b_pop_l', '-lg_b_st_bf'),
                        seed=th(0.55, 150), origin=('lg_ham_top', 'lg_gm_itb'), insertion=('lg_fib', 'lg_fib'), sp=6),
 'gastrocnemius_medial': dict(loop=loop('lg_b_gcm_st', '-lg_b_gcm_tib', '-lg_b_gcm_sol', '-lg_b_gcm_ach', '-lg_b_gc_mid',
                                        '-lg_b_pop_bm'),
                              seed=sh(0.35, 210), origin=('lg_pop_bot', 'lg_pop_med'), insertion=('lg_gcm_tip', 'lg_gc_mid'),
                              sp=6, group='gastrocnemius'),
 'gastrocnemius_lateral': dict(loop=loop('lg_b_pop_bl', 'lg_b_gc_mid', 'lg_b_gcl_ach', 'lg_b_gcl_sol', 'lg_b_gcl_pl',
                                         '-lg_b_bf_gcl'),
                               seed=sh(0.30, 155), origin=('lg_fib', 'lg_pop_bot'), insertion=('lg_gc_mid', 'lg_gcl_tip'),
                               sp=6, group='gastrocnemius'),
 'soleus_medial': dict(loop=loop('lg_b_solm_tib', 'lg_b_solm_lo', '-lg_b_ach_solm', 'lg_b_gcm_sol'),
                       seed=sh(0.65, -125), origin=('lg_gcm_tip', 'lg_solm_lo_f'), insertion=('lg_ach_m2', 'lg_ach_m2'),
                       sp=5, group='soleus'),
 'soleus_lateral': dict(loop=loop('lg_b_soll_pl', 'lg_b_soll_pb', '-lg_b_soll_lo', '-lg_b_ach_soll', 'lg_b_gcl_sol'),
                        seed=sh(0.62, 138), origin=('lg_gcl_tip', 'lg_pb_lo_b'), insertion=('lg_ach_l2', 'lg_ach_l2'),
                        sp=5, group='soleus'),
 'achilles': dict(loop=loop('lg_b_gcl_ach', 'lg_b_ach_soll', '-lg_b_ach_lo', '-lg_b_ach_solm', '-lg_b_gcm_ach'),
                  seed=sh(0.80, 180), kind='tendon'),
 'tibialis_anterior': dict(loop=loop('lg_b_ta_top', 'lg_b_ta_edl', 'lg_b_ta_lo', '-lg_b_ta_tib'),
                           seed=sh(0.40, 15), origin=('lg_tt_l', 'lg_gerdy'), insertion=('lg_ta_lo_l', 'lg_ta_lo_m'), sp=5),
 'extensor_digitorum_longus': dict(loop=loop('lg_b_edl_top', 'lg_b_pl_edl', 'lg_b_pb_edl', 'lg_b_edl_lo', '-lg_b_ta_edl'),
                                   seed=sh(0.50, 60), origin=('lg_gerdy', 'lg_edl_top'), insertion=('lg_pb_lo_f', 'lg_ta_lo_l'),
                                   sp=5),
 'peroneus_longus': dict(loop=loop('lg_b_pl_top', '-lg_b_gcl_pl', 'lg_b_soll_pl', 'lg_b_pl_pb_b', '-lg_b_pl_pb_f',
                                   '-lg_b_pl_edl'),
                         seed=sh(0.40, 100), origin=('lg_edl_top', 'lg_fib'), insertion=('lg_pl_end', 'lg_pl_end'), sp=5,
                         group='peroneus'),
 'peroneus_brevis': dict(loop=loop('lg_b_pl_pb_f', '-lg_b_pl_pb_b', 'lg_b_soll_pb', '-lg_b_pb_lo', '-lg_b_pb_edl'),
                         seed=sh(0.80, 100), origin=('lg_pbf', 'lg_pbb'), insertion=('lg_pb_lo_b', 'lg_pb_lo_f'), sp=5,
                         group='peroneus'),
}
