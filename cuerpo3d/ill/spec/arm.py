# ARM region (prefix ar_): upper arm and forearm, LEFT side.  Points use ('ring', bone, t, angle): t along the bone
# (0 top, 1 bottom), angle around the arm measured from the centre of the cross-section: 0 front, 90 outer side,
# 180 back, -90 inner side.  Rest pose: arms hang ~25 deg out, palms face the thighs (thumb forward), so on the
# forearm 0 = thumb (radial) side, 90 = back of the hand side (extensors), 180 = ulna, -90 = palm side (flexors).
# Upper borders are the deltoid's lower border and the armpit chains of spec/back.py (bk_dl_f_*, delt_ins,
# bk_dl_b_*, bk_dl_b3, bk_dl_tri, longhead_medial) and the shared pec_arm chain (dp_low, ax_front).
U = lambda t, a: ('ring', 'upper_arm.L', t, a)
Fa = lambda t, a: ('ring', 'forearm.L', t, a)

LM = {
    # ---- upper arm: biceps borders
    'ar_bl2': U(0.50, 35), 'ar_bl3': U(0.65, 38), 'ar_bl4': U(0.80, 30), 'ar_btip': U(0.95, 6),
    'ar_bm4': U(0.82, -28), 'ar_bm3': U(0.65, -45), 'ar_bm2': U(0.50, -52),
    # brachialis / triceps lateral head / brachioradialis origin
    'ar_tlf1': U(0.56, 112), 'ar_tlf2': U(0.66, 116), 'ar_brt': U(0.71, 98), 'ar_brf': U(0.85, 60),
    'ar_tlx': U(0.79, 124), 'ar_ecr_top': U(0.88, 126), 'ar_lat_epi': U(0.98, 112),
    # triceps
    'ar_tl_b1': U(0.45, 170), 'ar_tl_b2': U(0.58, 172), 'ar_tt_c': U(0.66, 178), 'ar_tt_l': U(0.73, 145),
    'ar_tlm1': ('P', 0.190, 0.072, 1.222), 'ar_tlm2': U(0.58, -142), 'ar_tlm3': U(0.67, -148), 'ar_tt_m': U(0.71, -165),
    'ar_tmh_low': U(0.90, -160), 'ar_med_epi': U(0.98, -100), 'ar_tmh_f': U(0.80, -118), 'ar_olec': U(1.00, 180),
    # medial upper arm: coracobrachialis and the medial part of the brachialis
    'ar_ax_mid': ('P', 0.172, -0.034, 1.228), 'ar_cb_ins': U(0.56, -92), 'ar_bml': U(0.90, -62), 'ar_bmb': U(0.74, -98),
    # ---- forearm: brachioradialis front border (with the cubital fossa / pronator / flexors) and back border (with ECR)
    'ar_brf1': Fa(0.08, 28), 'ar_brf2': Fa(0.25, 8), 'ar_brf3': Fa(0.45, -4), 'ar_brf4': Fa(0.65, 0), 'ar_brf5': Fa(0.82, 6),
    'ar_br_tip': Fa(0.95, 18),
    'ar_brb1': Fa(0.06, 72), 'ar_brb2': Fa(0.25, 55), 'ar_brb3': Fa(0.45, 45), 'ar_brb4': Fa(0.65, 36), 'ar_brb5': Fa(0.82, 30),
    # extensor carpi radialis / extensor digitorum border, ED / ECU border, ECU / ulna border
    'ar_ecr_tip': Fa(0.93, 48),
    'ar_ed1': Fa(0.07, 108), 'ar_ed2': Fa(0.25, 100), 'ar_ed3': Fa(0.45, 94), 'ar_ed4': Fa(0.65, 84), 'ar_ed5': Fa(0.82, 72),
    'ar_ed_tip': Fa(0.95, 96),
    'ar_eu1': Fa(0.09, 138), 'ar_eu2': Fa(0.25, 142), 'ar_eu3': Fa(0.45, 138), 'ar_eu4': Fa(0.65, 130), 'ar_eu5': Fa(0.82, 122),
    'ar_ecu_tip': Fa(0.94, 140),
    'ar_anc_low': Fa(0.21, 168),
    'ar_ub2': Fa(0.30, 172), 'ar_ub3': Fa(0.45, 170), 'ar_ub4': Fa(0.65, 164), 'ar_ub5': Fa(0.82, 158),
    # flexor carpi ulnaris (ulnar border, palm side) and the flexor group
    'ar_fcu0': Fa(0.04, -160), 'ar_fcu1': Fa(0.20, -170), 'ar_fcu2': Fa(0.45, -168), 'ar_fcu3': Fa(0.70, -163),
    'ar_fcu_tip': Fa(0.94, -152),
    'ar_fl1': Fa(0.10, -122), 'ar_fl2': Fa(0.35, -126), 'ar_fl3': Fa(0.60, -128), 'ar_fl4': Fa(0.80, -128),
    'ar_fl_tip': Fa(0.95, -75),
    # pronator teres (medial epicondyle -> middle of the radius, across the front of the upper forearm)
    'ar_pt_a': Fa(0.05, -38), 'ar_pt_b': Fa(0.24, -10), 'ar_pt_low': Fa(0.52, -22), 'ar_pt_m': Fa(0.30, -62),
    'ar_pt_n': Fa(0.12, -88),
}

DF = ['dp_low', 'bk_dl_f_0', 'bk_dl_f_1', 'bk_dl_f_2', 'bk_dl_f_3', 'bk_dl_f_4', 'bk_dl_f_5']           # deltoid front border (top)
DF2 = ['bk_dl_f_5', 'bk_dl_f_6', 'bk_dl_f_7', 'bk_dl_f_8', 'bk_dl_f_9', 'bk_dl_f_10', 'delt_ins']
DB = ['bk_dl_b_0', 'bk_dl_b_1']
DB2 = ['bk_dl_b_1', 'bk_dl_b_2', 'bk_dl_b_3', 'bk_dl_b_4', 'bk_dl_b_5', 'bk_dl_b_6', 'bk_dl_b3']
LH = ['bk_dl_b3', 'bk_dl_b_7', 'bk_dl_tri', 'bk_lh_0', 'bk_tt', 'bk_lh_1', 'ax_back']

MUSCLES = {
    'biceps_brachii': dict(loop=DF + ['ar_bl2', 'ar_bl3', 'ar_bl4', 'ar_btip', 'ar_bm4', 'ar_bm3', 'ar_bm2', 'ax_front'],
                           seed=U(0.6, 0), origin=('ax_front', 'bk_dl_f_5'), insertion=('ar_btip', 'ar_btip'), sp=6),
    'brachialis': dict(loop=DF2 + DB + ['ar_tlf1', 'ar_tlf2', 'ar_brt', 'ar_brf', 'ar_bl4', 'ar_bl3', 'ar_bl2'],
                       seed=U(0.62, 75), origin=('bk_dl_f_5', 'bk_dl_b_1'), insertion=('ar_brf', 'ar_bl4'), sp=6),
    'brachialis_medial': dict(loop=['ar_bm2', 'ar_bm3', 'ar_bm4', 'ar_bml', 'ar_bmb', 'ar_cb_ins'],
                              seed=U(0.72, -70), origin=('ar_cb_ins', 'ar_bm2'), insertion=('ar_bm4', 'ar_bml'), sp=6, group='brachialis'),
    'coracobrachialis': dict(loop=['ax_front', 'ar_bm2', 'ar_cb_ins', 'ar_ax_mid'],
                             seed=U(0.47, -85), origin=('ar_ax_mid', 'ax_front'), insertion=('ar_bm2', 'ar_cb_ins'), sp=5),
    'triceps_lateral': dict(loop=DB2 + ['ar_tl_b1', 'ar_tl_b2', 'ar_tt_c', 'ar_tt_l', 'ar_tlx', 'ar_tlf2', 'ar_tlf1'],
                            seed=U(0.55, 140), origin=('ar_tlf1', 'bk_dl_b3'), insertion=('ar_tt_c', 'ar_tlx'), sp=6, group='triceps'),
    'triceps_long': dict(loop=LH + ['ar_tlm1', 'ar_tlm2', 'ar_tlm3', 'ar_tt_m', 'ar_tt_c', 'ar_tl_b2', 'ar_tl_b1'],
                         seed=U(0.52, -170), origin=('bk_dl_b3', 'ax_back'), insertion=('ar_tt_m', 'ar_tt_c'), sp=6, group='triceps'),
    'triceps_medial': dict(loop=['ar_tlm1', 'ar_tlm2', 'ar_tlm3', 'ar_tt_m', 'ar_tmh_low', 'ar_med_epi', 'ar_bml', 'ar_bmb', 'ar_cb_ins', 'ar_ax_mid'],
                           seed=('P', 0.215, 0.040, 1.150), origin=('ar_ax_mid', 'ar_tlm1'), insertion=('ar_tmh_low', 'ar_med_epi'), sp=5, group='triceps'),
    'triceps_tendon': dict(loop=['ar_tt_l~', 'ar_tt_c~', 'ar_tt_m~', 'ar_tmh_low', 'ar_olec', 'ar_lat_epi', 'ar_ecr_top', 'ar_tlx~'],
                           seed=U(0.86, 175), kind='tendon', group='triceps'),
    'brachioradialis': dict(loop=['ar_brt', 'ar_brf', 'ar_brf1', 'ar_brf2', 'ar_brf3', 'ar_brf4', 'ar_brf5', 'ar_br_tip',
                                  'ar_brb5', 'ar_brb4', 'ar_brb3', 'ar_brb2', 'ar_brb1', 'ar_ecr_top', 'ar_tlx', 'ar_tlf2'],
                            seed=Fa(0.2, 35), origin=('ar_ecr_top', 'ar_brt'), insertion=('ar_br_tip', 'ar_br_tip'), sp=6),
    'extensor_carpi_radialis': dict(loop=['ar_ecr_top', 'ar_brb1', 'ar_brb2', 'ar_brb3', 'ar_brb4', 'ar_brb5', 'ar_ecr_tip',
                                          'ar_ed5', 'ar_ed4', 'ar_ed3', 'ar_ed2', 'ar_ed1', 'ar_lat_epi'],
                                    seed=Fa(0.3, 78), origin=('ar_ed1', 'ar_brb1'), insertion=('ar_ecr_tip', 'ar_ecr_tip'), sp=5,
                                    group='forearm_extensors'),
    'extensor_digitorum': dict(loop=['ar_lat_epi', 'ar_ed1', 'ar_ed2', 'ar_ed3', 'ar_ed4', 'ar_ed5', 'ar_ecr_tip', 'ar_ed_tip',
                                     'ar_eu5', 'ar_eu4', 'ar_eu3', 'ar_eu2', 'ar_eu1'],
                               seed=Fa(0.4, 118), origin=('ar_eu1', 'ar_ed1'), insertion=('ar_ecr_tip', 'ar_ed_tip'), sp=5,
                               group='forearm_extensors'),
    'anconeus': dict(loop=['ar_lat_epi', 'ar_eu1', 'ar_anc_low', 'ar_olec'],
                     seed=Fa(0.09, 158), origin=('ar_olec', 'ar_lat_epi'), insertion=('ar_eu1', 'ar_anc_low'), sp=4),
    'extensor_carpi_ulnaris': dict(loop=['ar_eu1', 'ar_eu2', 'ar_eu3', 'ar_eu4', 'ar_eu5', 'ar_ed_tip', 'ar_ecu_tip',
                                         'ar_ub5', 'ar_ub4', 'ar_ub3', 'ar_ub2', 'ar_anc_low'],
                                   seed=Fa(0.45, 154), origin=('ar_anc_low', 'ar_eu1'), insertion=('ar_ed_tip', 'ar_ecu_tip'), sp=5,
                                   group='forearm_extensors'),
    'flexor_carpi_ulnaris': dict(loop=['ar_med_epi', 'ar_fcu0', 'ar_fcu1', 'ar_fcu2', 'ar_fcu3', 'ar_fcu_tip', 'ar_fl4',
                                       'ar_fl3', 'ar_fl2', 'ar_fl1'],
                                 seed=Fa(0.4, -148), origin=('ar_fl1', 'ar_fcu0'), insertion=('ar_fcu_tip', 'ar_fcu_tip'), sp=5,
                                 group='forearm_flexors'),
    'pronator_teres': dict(loop=['ar_med_epi', 'ar_pt_a', 'ar_pt_b', 'ar_brf3', 'ar_pt_low', 'ar_pt_m', 'ar_pt_n'],
                           seed=Fa(0.2, -40), origin=('ar_pt_n', 'ar_pt_a'), insertion=('ar_brf3', 'ar_pt_low'), sp=5,
                           group='forearm_flexors'),
    'flexor_group': dict(loop=['ar_med_epi', 'ar_pt_n', 'ar_pt_m', 'ar_pt_low', 'ar_brf3', 'ar_brf4', 'ar_brf5', 'ar_fl_tip',
                               'ar_fcu_tip', 'ar_fl4', 'ar_fl3', 'ar_fl2', 'ar_fl1'],
                         seed=Fa(0.5, -80), origin=('ar_fl1', 'ar_pt_n'), insertion=('ar_brf5', 'ar_fcu_tip'), sp=5,
                         group='forearm_flexors'),
}
