# Corrective shape "LatsUp": with the arms overhead the lat "wings" (hidden under the arm at rest) are left sticking
# out; this shape pulls them in towards the body. It is only switched on with the arms up (key value in pullup4: LATK).
# usage: blender -b -P latkey.py -- in.blend out.blend   env AMP (m), ZC, ZW, X0, X1, SM
import bpy,sys,os
import numpy as np, scipy.sparse as sp
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
gi={g.index:g.name for g in hi.vertex_groups}
arm=np.zeros(nv); nh=np.zeros(nv)
for v in me.vertices:
    for g in v.groups:
        n=gi.get(g.group,'')
        if n.startswith(('upper_arm','forearm','hand')): arm[v.index]+=g.weight
        elif n.startswith('delt'): arm[v.index]+=0.5*g.weight
        if n in ('neck','head'): nh[v.index]+=g.weight
ax=np.abs(co[:,0])
zc,zw=E('ZC',1.26),E('ZW',0.08)
fz=np.clip(1-((co[:,2]-zc)/zw)**2,0,1)
fx=np.clip((ax-E('X0',0.13))/(E('X1',0.23)-E('X0',0.13)),0,1); fx=fx*fx*(3-2*fx)
fy=np.clip((co[:,1]+E('YF',0.06))/0.08,0,1)          # back and side, not the chest
amp=E('AMP',0.04)*fz*fx*fy*np.clip(1-arm*E('ARMK',1.5),0,1)*(nh<0.1)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
A=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
deg=np.asarray(A.sum(1)).ravel(); deg[deg==0]=1
for _ in range(int(E('SM',80))): amp=(A@amp)/deg*0.5+amp*0.5
d=-np.c_[co[:,0],np.zeros(nv),np.zeros(nv)]; d/=np.maximum(np.linalg.norm(d,axis=1,keepdims=True),1e-9)
new=co+d*amp[:,None]
if not me.shape_keys: hi.shape_key_add(name='Basis',from_mix=False)
kb=me.shape_keys.key_blocks.get('LatsUp') or hi.shape_key_add(name='LatsUp',from_mix=False)
kb.data.foreach_set('co',new.ravel()); kb.value=0.0
print('LatsUp: verts moved',int((amp>1e-4).sum()),'max mm %.1f'%(amp.max()*1000))
bpy.ops.wm.save_as_mainfile(filepath=out)
