# how well the per-vertex signed distance reproduces each border line: interpolate sd at the curve points
import bpy, sys, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
from mathutils.geometry import barycentric_transform
a=np.load(sys.argv[1],allow_pickle=True); r=np.load('rest.npz',allow_pickle=True); co=r['co']
lt=r['lt']; lv=r['lv']; off=np.r_[0,np.cumsum(lt)]
tris=[]
for i in range(len(lt)):
    p=lv[off[i]:off[i+1]]
    for k in range(1,len(p)-1): tris.append((p[0],p[k],p[k+1]))
tris=np.array(tris); bvh=BVHTree.FromPolygons([tuple(p) for p in co],[tuple(int(x) for x in t) for t in tris])
sd=a['sd'].astype(float); bd=a['bd'].astype(float)
cp=a['curve_pts']; cid=a['curve_id']; soft=a['curve_soft']
hard=~soft[cid.astype(int)]
P=cp[hard][::3]
vals=[]
for p in P:
    loc,n,i,d=bvh.find_nearest(Vector(p)); t=tris[i]
    A,B_,C=[Vector(co[j]) for j in t]
    # barycentric weights
    v0=B_-A; v1=C-A; v2=Vector(loc)-A; d00=v0.dot(v0); d01=v0.dot(v1); d11=v1.dot(v1); d20=v2.dot(v0); d21=v2.dot(v1); den=d00*d11-d01*d01
    w1=(d11*d20-d01*d21)/den; w2=(d00*d21-d01*d20)/den; w0=1-w1-w2
    s=w0*sd[t[0]]+w1*sd[t[1]]+w2*sd[t[2]]; b=w0*bd[t[0]]+w1*bd[t[1]]+w2*bd[t[2]]
    vals.append((abs(s),b,p))
v=np.array([x[0] for x in vals]); b=np.array([x[1] for x in vals]); pts=np.array([x[2] for x in vals])
lineD=np.maximum(v,b-2.5)
print('curve samples',len(v),'|sd| at curve: p50 %.2f p90 %.2f p99 %.2f   gaps(lineD>1.0mm) %.1f%%'%(np.percentile(v,50),np.percentile(v,90),np.percentile(v,99),100*np.mean(lineD>1.0)))
bad=pts[lineD>1.0]
if len(bad): print('example gap points',np.round(bad[:8],3).tolist())
