# Finger bones traced by hand on the outline of the hand (u = along the hand, l = across), depth taken from the mesh.
# usage: blender -b -P fingerfit2.py -- in.blend out.blend
import bpy,sys,os
import numpy as np
from mathutils import Vector
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
b=rig.data.bones
K=1000/0.24
px=lambda x,y: ((x-20)/K-0.03, (980-y)/K-0.04)
# traced on the plot of the left hand (pixels): knuckle (or thumb base) ... tip
TR={
 'thumb': [(190,650),(115,470),(88,385),(70,290)],
 'index': [(298,470),(325,400),(395,200),(442,52)],
 'middle':[(418,505),(452,445),(560,280),(671,115)],
 'ring':  [(512,592),(543,540),(680,400),(795,270)],
 'pinky': [(583,668),(610,625),(700,550),(786,478)],
}
FR={'thumb':[0.0,0.42,0.71,0.97]}
def frame(L):
    s=1 if L=='L' else -1
    W=np.array(b['hand.'+L].head_local); F=np.array(b['forearm.'+L].head_local); ax=(W-F)/np.linalg.norm(W-F)
    al=(co-W)@ax; m=(al>0.0)&(np.linalg.norm(co-W,axis=1)<0.25)&(co[:,0]*s>0.05)
    P=co[m]; c=P.mean(0); _,_,Vt=np.linalg.svd(P-c,full_matrices=False)
    T=np.array(b['hand.'+L].tail_local)
    e0=Vt[0] if Vt[0]@(T-W)>0 else -Vt[0]
    return W,e0,Vt[1],Vt[2],P
plan={}
# the plot was made for the left hand; the right hand is its mirror image (x -> -x)
W,e0,e1,e2,P=frame('L')
Q=P-W; U=Q@e0; Lc=Q@e1; N=Q@e2
pts={}
for f,tr in TR.items():
    J3=[]
    for (x,y) in tr:
        u,l=px(x,y); mm=np.hypot(U-u,Lc-l)<0.004
        n=0.5*(np.percentile(N[mm],4)+np.percentile(N[mm],96)) if mm.sum()>10 else 0.0   # middle of the tube (front and back skin)
        J3.append(W+u*e0+l*e1+n*e2)
    J3=np.array(J3)
    if f!='thumb':
        # the knuckle (MCP) is not measured inside the palm (front and back skin mix there): extrapolate it from the finger itself
        d0=J3[2]-J3[1]; d0/=np.linalg.norm(d0); J3[0]=J3[1]-d0*float(os.environ.get('MCPD','0.016'))
    seg=np.linalg.norm(np.diff(J3,axis=0),axis=1); cum=np.r_[0,np.cumsum(seg)]
    fr=FR.get(f,[0.0,0.45,0.73,0.97])
    pts[f]=[np.array([np.interp(t*cum[-1],cum,J3[:,k]) for k in range(3)]) for t in fr]
    print(f,'length',round(cum[-1],3))
bpy.context.view_layer.objects.active=rig
for o in bpy.context.view_layer.objects: o.select_set(o==rig)
bpy.ops.object.mode_set(mode='EDIT'); eb=rig.data.edit_bones
for L,s in (('L',1),('R',-1)):
    mir=np.array([s,1,1]); nrm=e2*mir
    for f,J in pts.items():
        for k in (1,2,3):
            bb=eb[f'{f}{k}.{L}']; bb.use_connect=False
            bb.head=Vector(J[k-1]*mir); bb.tail=Vector(J[k]*mir); bb.align_roll(Vector(nrm))
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=out)
