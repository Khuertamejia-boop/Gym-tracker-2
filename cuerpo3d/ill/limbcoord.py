# print (t, angle, radius) of landmarks / points in a limb frame:  python -I limbcoord.py BONE spec... [--pts x,y,z ...]
import sys, numpy as np, math
sys.argv=[sys.argv[0]]+sys.argv[1:]
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from atlas import Body, load_specs, resolve_landmarks
bone=sys.argv[1]; files=[a for a in sys.argv[2:] if a.endswith('.py')]
B=Body(); h,t,u,ea,el=B.limb_frame(bone); L=np.linalg.norm(t-h)
def tc(p):
    r=p-h; tt=r@u/L; rr=r-u*(r@u); return tt, math.degrees(math.atan2(rr@el, rr@ea)), np.linalg.norm(rr)
LM,MU=load_specs(files); pos=resolve_landmarks(B,LM)
names=[a for a in sys.argv[2:] if not a.endswith('.py')]
for k in names:
    if k in pos: print('%-12s t=%.3f ang=%7.1f r=%.3f'%((k,)+tc(pos[k])))
