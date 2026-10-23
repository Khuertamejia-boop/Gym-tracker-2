# SHARED junction landmarks (left side, +x). Every region spec must use these names for borders that meet another
# region, and must not redefine them.  Chains (ordered landmark lists) are borders two regions have in common:
# use the chain's landmarks, in order (or reversed), in both muscles' loops.
LM={
 # midline (x=0)
 'occ':('B',0.0,1.530),      # base of the skull, back (trapezius origin)
 'c7':('B',0.0,1.445),       # vertebra prominens
 't3':('B',0.0,1.335),       # level of the scapular spine root
 't7':('B',0.0,1.215),       # level of the inferior angle of the scapula
 't12':('B',0.0,1.100),      # lower end of the trapezius
 'l4':('B',0.0,0.975),       # level of the iliac crests
 'sac':('B',0.0,0.900),      # top of the sacrum / gluteal cleft (under the shorts)
 'jug':('F',0.0,1.383),      # jugular notch (top of the sternum)
 'xiph':('F',0.0,1.175),     # lower end of the sternum
 'pubis':('F',0.0,0.830),    # pubic symphysis (under the shorts)
 # clavicle chain (medial -> lateral): sc_l, clav_mid, trap_clav, dp_top, acr
 'sc_l':('F',0.025,1.386),   # sternoclavicular joint
 'clav_mid':('F',0.070,1.386),
 'trap_clav':('F',0.105,1.385),  # trapezius anterior border reaches the clavicle
 'dp_top':('F',0.128,1.374),     # top of the deltopectoral groove (pec | deltoid at the clavicle)
 'acr':('T',0.192,0.010),        # acromion (top of the shoulder)
 # scapular spine chain (medial -> lateral): sps_med, sps_mid, sps_lat, acr
 'sps_med':('B',0.078,1.335),
 'sps_mid':('B',0.128,1.356),
 'sps_lat':('B',0.172,1.376),
 'inf_ang':('B',0.098,1.215),    # inferior angle of the scapula
 # armpit
 'ax_back':('B',0.196,1.255),    # back of the armpit (teres major / lats go under the triceps long head)
 'ax_front':('F',0.168,1.245),   # front of the armpit (lower lateral corner of the pectoral)
 'dp_mid':('F',0.150,1.333),     # middle of the deltopectoral groove
 'dp_low':('F',0.178,1.290),     # lower end of the deltopectoral groove (pec tendon goes under the deltoid)
 'delt_ins':('limb','upper_arm.L',0.48,90),   # deltoid insertion (V on the outer arm)
 # flank: lats anterior border, top to bottom
 'lat_ax':('MX',0.0,0.035,1.215),     # (from inside the torso outwards: the hanging arm hides the flank in side views)
 'lat_mid':('MX',0.0,0.030,1.100),
 'crest_side':('MX',0.0,0.010,0.975), # iliac crest at the side (lats | external oblique | gluteus medius)
 'crest_back':('B',0.075,0.965), # posterior iliac crest
 'psis':('B',0.042,0.930),       # posterior superior iliac spine (the low-back dimple)
 'asis':('F',0.105,0.925),       # anterior superior iliac spine (inguinal line asis -> pubis)
}
MUSCLES={}
CHAINS={
 'clavicle':['sc_l','clav_mid','dp_top','acr'],       # lower/front edge: SCM and pectoral above/below, deltoid below dp_top..acr
 'trap_clavicle':['trap_clav','acr'],                  # trapezius insertion along the back edge of the clavicle (only the trapezius uses it;
                                                       # the bony strip of clavicle between it and the deltoid stays plain skin)
 'scap_spine':['sps_med','sps_mid','sps_lat','acr'],   # trapezius above; infraspinatus (sps_med..sps_mid) and posterior deltoid (sps_mid..acr) below
 'lat_front':['lat_ax','lat_mid','crest_side'],
 'deltopectoral':['dp_top','dp_mid','dp_low'],         # pectoral (medial) | deltoid (lateral)
 'pec_arm':['dp_low','ax_front'],                      # lateral edge of the pectoral where it enters the arm
 'pelvis':['sac','psis','crest_back','crest_side','asis','pubis'],   # torso above / leg (gluteals, thigh) below
}
