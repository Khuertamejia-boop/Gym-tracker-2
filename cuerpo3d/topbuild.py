# Sports top (+ clean shorts waistband) for the female mannequin, same dark smooth fabric as the shorts (attribute
# 'shorts' of 'Hi'). Every edge is an analytic line: the attribute holds a LINEAR ramp of the signed distance to that
# line (TW wide, much wider than the mesh), and the renderer cuts it at 0.5 -> clean straight / round edges inside the
# triangles instead of the jagged vertex staircase.   python -I topbuild.py in.blend out.blend   (env RESTNPZ = female rest)
import bpy, sys, os, numpy as np, scipy.sparse as sp
E=lambda k,d: float(os.environ.get(k,d))
src,out=sys.argv[-2],sys.argv[-1]
F=np.load(os.environ['RESTNPZ'],allow_pickle=True); co=F['co']; main=np.array([str(x) for x in F['main']]); ed=F['ed']
x=np.abs(co[:,0]); y=co[:,1]; z=co[:,2]; nv=len(co)
TW=E('TW',0.012)
ramp=lambda sd: np.clip(0.5+sd/TW,0,1)
cs=lambda a,b,t: a+(b-a)*0.5*(1-np.cos(np.pi*np.clip(t,0,1)))
# ---- top: signed functions (metres, >0 inside), combined with min (and) / max (or)
zb0=E('TZB',1.100)
top_f=np.where(x<0.085,E('TZN',1.262)+E('TNK',7.0)*x**2,cs(E('TZN',1.262)+E('TNK',7.0)*0.085**2,E('TZS',1.235),(x-0.085)/0.045))
sd_front=np.minimum(z-zb0,top_f-z)
wz=np.interp(z,[1.10,1.16,1.22,1.27,1.31],[0.30,0.16,0.09,0.055,0.045])
sd_back=np.minimum.reduce([z-zb0,wz-x,E('TZBT',1.315)-z])
wf=np.clip(0.5-y/E('TFB',0.05),0,1)                       # front/back blend over the sides (no hard split)
sd_body=wf*sd_front+(1-wf)*sd_back
xs_f=np.interp(z,[1.28,1.34,1.40],[0.088,0.090,0.092]); xs_b=np.interp(z,[1.30,1.35,1.40],[0.048,0.072,0.092])
xs=wf*xs_f+(1-wf)*xs_b
sd_strap=np.minimum(E('TSW',0.032)/2-np.abs(x-xs),z-1.26)
# armholes (28-10, owner: «mejora la ropa debajo del brazo»): the fabric used to stop where the skin belongs to the arm
# bone -> vertex staircase under the arm. Now it stops at a smooth cylinder around the upper arm bone (wider towards the
# armpit): a clean curve from the front fold, under the armpit, to the back fold. Straps are not cut by it.
bn=[str(b) for b in F['bn']]; ia=bn.index('upper_arm.L'); ah,at_=F['bh'][ia],F['bt'][ia]; ad=(at_-ah)/np.linalg.norm(at_-ah)
P_=np.stack([x,y,z],1); nrm=F['no'].copy(); nrm[:,0]*=np.where(co[:,0]<0,-1.0,1.0)   # normals in the |x| frame
v_=P_-ah; rr=np.linalg.norm(v_-np.outer(v_@ad,ad),axis=1); rad=(v_-np.outer(v_@ad,ad))/np.maximum(rr[:,None],1e-9)
arms=(x>0.08)&((rad*nrm).sum(1)>0.5)&(rr<0.09)                       # arm surface (normal away from the bone)
cen=np.array([P_[arms&(np.abs(z-z0)<0.006)].mean(0) for z0 in np.arange(1.08,1.19,0.02)])   # real centre of the arm
am=cen.mean(0); _,_,vt=np.linalg.svd(cen-am); ad=vt[0]*np.sign(-vt[0][2])
v_=P_-am; r_arm=np.linalg.norm(v_-np.outer(v_@ad,ad),axis=1)
rc=np.interp(z,[1.10,1.20,1.24,1.28],[E('RC0',0.056),E('RC1',0.058),E('RC2',0.064),E('RC3',0.072)])
sd_arm=r_arm-rc
keep=~np.isin(main,['head','forearm.L','forearm.R','hand.L','hand.R','fa_tw1.L','fa_tw1.R','fa_tw2.L','fa_tw2.R','fa_tw3.L','fa_tw3.R'])
top=ramp(np.maximum(np.minimum(sd_body,sd_arm),sd_strap))*keep
# ---- shorts: same fabric; replace the jagged waist edge with a smooth line (front 0.908, sides 0.926, back 0.940)
bpy.ops.wm.open_mainfile(filepath=src)
me=bpy.data.objects['Hi'].data
a=me.attributes['shorts']; sh=np.zeros(nv,np.float32); a.data.foreach_get('value',sh)
th=np.degrees(np.arctan2(co[:,0],-co[:,1]))
zw=np.interp(np.abs(th),[0,30,60,90,120,150,180],[0.908,0.912,0.912,0.926,0.943,0.943,0.940])-E('WDROP',0.006)
A=sp.coo_matrix((np.ones(2*len(ed)),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
dil=(sh>0.5).astype(float)
for _ in range(int(E('DILR',4))): dil=np.maximum(dil,(A@dil>0).astype(float))
shorts=np.minimum(dil*(z<1.0),ramp(zw-z))
shorts=np.where(z<0.85,np.maximum(shorts,(sh>0.5)*1.0),shorts)   # legs: keep the original openings (cut by SHORTZ)
a.data.foreach_set('value',np.maximum(shorts,top).astype(np.float32))
print('top verts',int((top>0.5).sum()),'shorts verts',int((shorts>0.5).sum()))
bpy.ops.wm.save_as_mainfile(filepath=out)
