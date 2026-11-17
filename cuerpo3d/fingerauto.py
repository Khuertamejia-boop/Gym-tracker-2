# Automatic finger centre lines on a clean hand mesh (fingers apart): geodesic distance from the wrist -> 5 tips;
# from each tip, rings of equal geodesic distance -> centroids = tube centre line, until the ring opens into the palm.
# Returns joints per finger (MCP/CMC .. tip) for the LEFT hand (x>0); the right hand is mirrored by the caller.
import numpy as np, scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra
def finger_joints(co,ed,wrist,tipdir,palmnormal,MCPD=0.022,THB=0.035,dbg=None):
    hd=tipdir/np.linalg.norm(tipdir)
    t=(co-wrist)@hd
    reg=np.where((t>-0.01)&(co[:,0]>0.15)&(np.linalg.norm(co-wrist,axis=1)<0.25))[0]
    pos=-np.ones(len(co),int); pos[reg]=np.arange(len(reg))
    e=ed[(pos[ed[:,0]]>=0)&(pos[ed[:,1]]>=0)]
    w=np.linalg.norm(co[e[:,0]]-co[e[:,1]],axis=1)
    n=len(reg); G=sp.coo_matrix((np.r_[w,w],(np.r_[pos[e[:,0]],pos[e[:,1]]],np.r_[pos[e[:,1]],pos[e[:,0]]])),shape=(n,n)).tocsr()
    P=co[reg]; tt=t[reg]
    src=np.where(np.abs(tt)<0.004)[0]
    Dw=dijkstra(G,indices=src,min_only=True)
    # tips: local maxima of the geodesic distance (over a ~1.5 cm ball), the 5 biggest, far apart along the skin
    A=(G>0).astype(np.float32)
    Dm=np.where(np.isfinite(Dw),Dw,-1.0); bm=Dm.copy()
    for _ in range(int(0.015/np.median(w))):
        bm=np.maximum(bm,(A.multiply(bm[None,:])).max(axis=1).toarray().ravel())
    cand=np.where((Dm>=bm-1e-9)&(Dm>0))[0]
    cand=cand[np.argsort(-Dm[cand])]
    tips=[]
    for i in cand:
        if tips:
            dd=dijkstra(G,indices=[i],limit=0.04)[0]
            if any(np.isfinite(dd[j]) for j in tips): continue
        tips.append(i)
        if len(tips)==5: break
    # thumb = the tip furthest from the hand's middle line across the palm side (shortest geodesic among the 5 usually)
    tipD=np.array([Dw[i] for i in tips]); thumb=tips[int(np.argmin(tipD))]
    others=[i for i in tips if i!=thumb]
    side=np.cross(hd,palmnormal); side/=np.linalg.norm(side)
    # index is the finger nearest the thumb across the hand
    sth=(P[thumb]-wrist)@side
    others.sort(key=lambda i: abs(((P[i]-wrist)@side)-sth))
    names=['index','middle','ring','pinky']
    out={}
    for name,tip in [('thumb',thumb)]+list(zip(names,others)):
        Dt=dijkstra(G,indices=[tip])[0]
        cents=[]; bad=0; rads=[]
        for s in np.arange(0.0,0.12,0.003):
            m=np.abs(Dt-s)<0.0015
            if m.sum()<6: continue
            c=P[m].mean(0); rad=np.percentile(np.linalg.norm(P[m]-c,axis=1),90)
            if s>0.01 and rad>E_RAD(name):
                bad+=1
                if bad>=3: break
                continue
            bad=0; cents.append(c); rads.append(rad)
        C=np.array(cents)          # tip -> web
        for _ in range(3): C[1:-1]=0.25*C[:-2]+0.5*C[1:-1]+0.25*C[2:]
        C=C[::-1]                  # web -> tip
        d0=C[min(3,len(C)-1)]-C[0]; d0/=np.linalg.norm(d0)
        ext=THB if name=='thumb' else MCPD
        base=C[0]-d0*ext
        poly=np.vstack([base,C])
        seg=np.linalg.norm(np.diff(poly,axis=0),axis=1); cum=np.r_[0,np.cumsum(seg)]
        fr=[0.0,0.42,0.71,0.97] if name=='thumb' else [0.0,0.45,0.73,0.97]
        J=[np.array([np.interp(f*cum[-1],cum,poly[:,k]) for k in range(3)]) for f in fr]
        out[name]=J
        if dbg is not None: dbg[name]=poly
    return out
_RADMAX={'thumb':0.016,'index':0.0125,'middle':0.013,'ring':0.0125,'pinky':0.011}
def E_RAD(name): return _RADMAX[name]
