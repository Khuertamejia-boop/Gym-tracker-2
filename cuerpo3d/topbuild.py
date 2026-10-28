# Sports top for the female mannequin: same dark smooth fabric as the shorts (attribute 'shorts' of 'Hi'), drawn on the
# female rest body: elastic band under the bust, cups with a round neckline, side panels under the arms, straps over the
# shoulders and a racerback (Y) at the back.   python -I topbuild.py in.blend out.blend   (env RESTNPZ = female rest)
import bpy, sys, os, numpy as np
E=lambda k,d: float(os.environ.get(k,d))
src,out=sys.argv[-2],sys.argv[-1]
F=np.load(os.environ['RESTNPZ'],allow_pickle=True); co=F['co']; main=np.array([str(x) for x in F['main']])
ss=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
x=np.abs(co[:,0]); y=co[:,1]; z=co[:,2]; e=E('TSOFT',0.0025)
step=lambda v: ss(v/(2*e)+0.5)                         # soft 0 -> 1 across 0
torso=np.isin(main,['chest','spine','clavicle.L','clavicle.R','neck'])
zb0=E('TZB',1.100)                                     # lower edge of the band
front=y<0.0
# front: neckline scoop rising towards the straps; side panel up to below the armpit
neck_f=E('TZN',1.262)+E('TNK',7.0)*x**2
side_top=E('TZS',1.225)
top_f=np.where(x<0.105,neck_f,side_top)
cov_f=step(z-zb0)*step(top_f-z)*front
# back: racerback, full width at the band, narrowing to the middle of the upper back
wz=np.interp(z,[1.10,1.16,1.22,1.27,1.31],[0.30,0.16,0.09,0.055,0.045])
cov_b=step(z-zb0)*step(wz-x)*step(E('TZBT',1.315)-z)*(~front)
# straps: 3 cm wide, front (from the cup top at |x|~0.085) over the shoulder to the back (|x|~0.045 at z 1.31)
def strap(xc,w): return step(w/2-np.abs(x-xc))
sf=strap(np.interp(z,[1.28,1.34,1.40],[0.088,0.090,0.092]),E('TSW',0.030))*step(z-1.28)*front
sb=strap(np.interp(z,[1.30,1.35,1.40],[0.048,0.072,0.092]),E('TSW',0.030))*step(z-1.29)*(~front)
top=np.maximum.reduce([cov_f,cov_b,sf,sb])*torso
bpy.ops.wm.open_mainfile(filepath=src)
me=bpy.data.objects['Hi'].data; nv=len(me.vertices)
a=me.attributes['shorts']; sh=np.zeros(nv,np.float32); a.data.foreach_get('value',sh)
a.data.foreach_set('value',np.maximum(sh,top).astype(np.float32))
print('top verts',int((top>0.5).sum()))
bpy.ops.wm.save_as_mainfile(filepath=out)
