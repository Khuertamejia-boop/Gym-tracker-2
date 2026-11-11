# Wrap the fingers of the posed body around a bar by building each finger on a curve around the bar
# (no bone rotations: the finger vertices are mapped from their straight rest shape onto a spiral around the bar).
# usage: blender -b -P grippose.py -- in.blend out.blend      (in.blend = arms already posed, fingers straight)
import bpy,sys,os,math
import numpy as np
from mathutils import Vector
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']
RB=E('BARR',0.0145)                       # bar radius (m)
RC=RB+E('FT',0.0085)                      # centre line of the fingers: bar + half finger thickness
RT=RC+E('TTH',0.0175)                     # centre line of the thumb: over the fingers
GY,GZ=E('GDY',0.026),E('GDZ',-0.004)      # bar centre relative to the middle-finger knuckle (y back, z up)
ROLLUP=E('ROLLUP',1.0)
bpy.context.view_layer.update()
# 1) bake the armature pose into the mesh
dg=bpy.context.evaluated_depsgraph_get(); ev=hi.evaluated_get(dg); em=ev.to_mesh()
nv=len(em.vertices); co=np.zeros(nv*3); em.vertices.foreach_get('co',co); co=co.reshape(-1,3); ev.to_mesh_clear()
for m in list(hi.modifiers):
    if m.type=='ARMATURE': hi.modifiers.remove(m)
me=hi.data; me.vertices.foreach_set('co',co.ravel()); me.update()
# 2) finger weights (only the hand region is scanned)
gname={g.index:g.name for g in hi.vertex_groups}
fing=('index','middle','ring','pinky','thumb')
hand=np.where((np.abs(co[:,0])>0.24)&(co[:,2]<1.0)&(co[:,2]>0.65))[0]
W={}                                       # (L, finger) -> {vertex: weight}
for v in hand:
    for g in me.vertices[int(v)].groups:
        n=gname[g.group]
        if n[-2:] in ('.L','.R') and n[:-2][-1:] in ('1','2','3') and n[:-3] in fing:
            key=(n[-1],n[:-3]); W.setdefault(key,{}); W[key][int(v)]=W[key].get(int(v),0.0)+g.weight
pb=rig.pose.bones; print('hand verts',len(hand),'keys',sorted(W.keys())[:12], 'x range',co[:,0].min().round(2),co[:,0].max().round(2),'z min',co[:,2].min().round(2))
def P(b,end='head'): return np.array(getattr(pb[b],end))                      # world (armature at identity)
newco=co.copy(); moved=np.zeros(nv,bool); acc=np.zeros((nv,3))
ss=lambda a,b,x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a),0,1))
Bs=[]
for L in 'LR':
    B=P('middle1.'+L)+np.array([0.0,GY,GZ]); Bs.append(B)
Bc=np.mean(Bs,0)                           # the same bar centre (y,z) for both hands
for L in 'LR':
    sgn=1 if L=='L' else -1
    for f in fing:
        key=(L,f)
        if key not in W: continue
        # vertices that belong mostly to this finger
        ids=np.array([v for v,w in W[key].items() if w>0.03]); wf=np.array([min(W[key][v],1.0) for v in ids])
        if len(ids)==0: continue
        pts=[P(f'{f}1.{L}'),P(f'{f}2.{L}'),P(f'{f}3.{L}'),P(f'{f}3.{L}','tail')]
        t_last=(pts[3]-pts[2]); t_last/=np.linalg.norm(t_last); pts.append(pts[3]+t_last*0.06)
        seg=[pts[i+1]-pts[i] for i in range(4)]; ln=[np.linalg.norm(s) for s in seg]; cum=np.r_[0,np.cumsum(ln)]
        V=co[ids]
        best=np.full(len(ids),1e9); S=np.zeros(len(ids)); Cc=np.zeros((len(ids),3)); Tt=np.zeros((len(ids),3))
        for i in range(4):
            d=seg[i]/ln[i]; t=((V-pts[i])@d); t=np.clip(t,0,ln[i] if i<3 else 1e9)
            c=pts[i]+np.outer(t,d); dist=np.linalg.norm(V-c,axis=1); m=dist<best
            best[m]=dist[m]; S[m]=cum[i]+t[m]; Cc[m]=c[m]; Tt[m]=d
        Dv=V-Cc; up=np.array([0,1.0,0])
        Nr=up[None,:]-np.sum(up[None,:]*Tt,1,keepdims=True)*Tt; Nr/=np.maximum(np.linalg.norm(Nr,axis=1,keepdims=True),1e-9)
        noff=np.sum(Dv*Nr,1)*ROLLUP
        K=pts[0]; rr=RT if f=='thumb' else RC
        dy,dz=K[1]-Bc[1],K[2]-Bc[2]; rK=math.hypot(dy,dz)
        phi0=math.atan2(-dz,-dy); dirn=-1.0 if f=='thumb' else 1.0
        s_=np.maximum(S,0)
        if f=='thumb':
            rad=rr+(rK-rr)*np.exp(-s_/0.015)
        else:
            rad=rr+(rK-rr)*np.exp(-s_/0.012)
        phi=phi0+dirn*s_/np.maximum(rad,1e-6)
        py=Bc[1]-rad*np.cos(phi); pz=Bc[2]-rad*np.sin(phi)
        ny=Bc[1]-py; nz=Bc[2]-pz; nn=np.maximum(np.hypot(ny,nz),1e-9); ny/=nn; nz/=nn      # towards the bar = towards the palm
        wy=py+noff*ny; wz=pz+noff*nz
        w=ss(0.0,E('BLEND',0.012),S)*np.clip(wf*E('WK',1.15),0,1)*(1-ss(E('FR0',0.014),E('FR1',0.026),best))
        acc[ids,1]+=(wy-co[ids,1])*w; acc[ids,2]+=(wz-co[ids,2])*w; moved[ids]=True
        dd=np.linalg.norm(newco[ids]-co[ids],axis=1); print('   disp p50/p99/max cm',(np.percentile(dd,[50,99])*100).round(1),round(dd.max()*100,1),'S max',round(float(S.max()),3),'neg S',int((S<0).sum()),'noff p99',round(float(np.percentile(np.abs(noff),99)),3),'x range',co[ids,0].min().round(3),co[ids,0].max().round(3))
        print(L,f,len(ids),'verts; length',round(float(S.max()),3),'wrap deg',round(math.degrees(S.max()/rr),0))
newco=co+acc
me.vertices.foreach_set('co',newco.ravel()); me.update()
# 3) the bar, thin and centred on the hands
k=RB/0.025; bm=bpy.data.objects['Barra'].data
for v in bm.vertices: v.co.y=-0.2962+(v.co.y+0.2962)*k; v.co.z=0.9366+(v.co.z-0.9366)*k
bm.update()
off=Vector((0.0,Bc[1]+0.2962,Bc[2]-0.9366))
for n in ('Barra','Discos'):
    o=bpy.data.objects[n]; o.parent=None; o.location=off; o.hide_render=False
print('bar centre',Bc.round(4))
bpy.ops.wm.save_as_mainfile(filepath=out)
