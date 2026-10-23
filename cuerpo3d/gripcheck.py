# Check a grip without rendering: numbers (bar penetration, finger spacing, torn skin) + shaded point views of the left hand.
# usage: blender -b -P gripcheck.py -- posed.blend out_prefix
import bpy,sys,os,math
import numpy as np
from PIL import Image
E=lambda k,d: float(os.environ.get(k,d))
src,outp=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; rig=bpy.data.objects['Rig']; me=hi.data; nv=len(me.vertices)
for m in hi.modifiers: m.show_viewport=True
c0=np.zeros(nv*3); me.vertices.foreach_get('co',c0); c0=c0.reshape(-1,3)
dg=bpy.context.evaluated_depsgraph_get(); ev=hi.evaluated_get(dg); em=ev.to_mesh()
c1=np.zeros(nv*3); em.vertices.foreach_get('co',c1); c1=c1.reshape(-1,3)
nr=np.zeros(nv*3); em.vertices.foreach_get('normal',nr); nr=nr.reshape(-1,3); ev.to_mesh_clear()
SD=os.environ.get('SIDE','L'); SG=1 if SD=='L' else -1
GX=E('GRIPX',0.30)*SG; B=np.array([GX,E('BARY',-0.03),E('BARZ',2.15)]); rB=E('BARR',0.0145)
reg=(np.linalg.norm(c1-B,axis=1)<0.13)&(c1[:,0]*SG>0.12)
P=c1[reg]; N=nr[reg]
rad=np.hypot(P[:,1]-B[1],P[:,2]-B[2])
print('hand verts',int(reg.sum()))
print('inside the bar (>1 mm deep):',int((rad<rB-0.001).sum()))
print('contact (skin within 0-3 mm of the bar surface):',int(((rad>rB-0.001)&(rad<rB+0.003)).sum()))
print('closest skin to bar axis (mm):',round(float(rad.min())*1000,1),' bar radius',rB*1000)
from collections import Counter
gname={g.index:g.name for g in hi.vertex_groups}
def dom(ids):
    c=Counter()
    for v in ids[::max(1,len(ids)//4000)]:
        gs=me.vertices[int(v)].groups
        gs=[g for g in gs if gname[g.group]!='CS']
        if len(gs): c[max(gs,key=lambda g:g.weight).group]+=1
    return ', '.join(f'{gname[k]}:{n}' for k,n in c.most_common(6))
ri0=np.where(reg)[0]
print('   inside-bar skin by bone:',dom(ri0[rad<rB-0.001]))
print('   touching skin (0-2 mm) by bone:',dom(ri0[(rad>rB-0.001)&(rad<rB+0.002)]))
Ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',Ed); Ed=Ed.reshape(-1,2)
ri=np.where(reg)[0]; inr=np.zeros(nv,bool); inr[ri]=True; e=Ed[inr[Ed[:,0]]&inr[Ed[:,1]]]
l0=np.linalg.norm(c0[e[:,0]]-c0[e[:,1]],axis=1); l1=np.linalg.norm(c1[e[:,0]]-c1[e[:,1]],axis=1); r=l1/np.maximum(l0,1e-9)
print('stretched edges x2: %d  x3: %d  squashed <0.3: %d'%((r>2).sum(),(r>3).sum(),(r<0.3).sum()))
print('   stretched skin by bone:',dom(np.unique(e[r>2].ravel())))
pb=rig.pose.bones
for a,b in (('index','middle'),('middle','ring'),('ring','pinky')):
    for k in (2,3):
        pa=np.array(pb[f'{a}{k}.{SD}'].head); pbb=np.array(pb[f'{b}{k}.{SD}'].head)
        print(f'  gap {a}-{b} joint{k}: {np.linalg.norm(pa-pbb)*1000:.1f} mm',end='')
    print()
import json
RR=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.environ.get('GT3D','/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad')+'','finger_radii.json')))
def segseg(p1,q1,p2,q2,n=24):
    t=np.linspace(0,1,n); A=p1+np.outer(t,q1-p1); Bq=p2+np.outer(t,q2-p2)
    return np.min(np.linalg.norm(A[:,None,:]-Bq[None,:,:],axis=2))
print('skin gap between neighbour fingers (mm, <0 = overlap):')
for a_,b_ in (('index','middle'),('middle','ring'),('ring','pinky')):
    g=[]
    for k in (1,2,3):
        A=pb[f'{a_}{k}.{SD}']; Bb=pb[f'{b_}{k}.{SD}']
        d=segseg(np.array(A.head),np.array(A.tail),np.array(Bb.head),np.array(Bb.tail))
        g.append((d-RR[f'{a_}{k}.L'][0]-RR[f'{b_}{k}.L'][0])*1000)
    print(f'   {a_}-{b_}: '+'  '.join(f'phalanx{k+1} {v:+.1f}' for k,v in enumerate(g)))
tip=np.array(pb[f'thumb3.{SD}'].tail); print('thumb tip distance to bar axis (mm):',round(float(np.hypot(tip[1]-B[1],tip[2]-B[2]))*1000,1))
# shaded point views (no render): orthographic, z-buffer, Lambert
S=E('VS',520); half=E('VH',0.10)
views={'frente':(np.array([0,-1,0]),np.array([0,0,1])),'detras':(np.array([0,1,0]),np.array([0,0,1])),
       'lado':(np.array([SG,0,0]),np.array([0,0,1])),'abajo':(np.array([0,-0.3,-1.0]),np.array([0,1,0]))}
th=np.linspace(0,2*np.pi,90); xs=np.linspace(B[0]-0.12,B[0]+0.12,240)
BP=np.array([[x,B[1]+rB*math.cos(t),B[2]+rB*math.sin(t)] for x in xs for t in th]); BN=np.c_[np.zeros(len(BP)),np.cos(np.tile(th,len(xs))),np.sin(np.tile(th,len(xs)))]
tiles=[]
for name,(vd,up) in views.items():
    vd=vd/np.linalg.norm(vd); rt=np.cross(vd,up); rt/=np.linalg.norm(rt); up2=np.cross(rt,vd)
    img=np.full((int(S),int(S)),255.0); zb=np.full((int(S),int(S)),-1e9)
    for pts,nrm,base in ((P,N,1.0),(BP,BN,0.55)):
        q=pts-B; x=q@rt; y=q@up2; z=-(q@vd)
        u=((x/half+1)*S/2).astype(int); v=((1-y/half)*S/2).astype(int)
        sh=np.clip(-(nrm@vd)*0.75+(nrm@up2)*0.25,0,1)*0.8+0.2
        ok=(u>=1)&(u<S-1)&(v>=1)&(v<S-1)
        for du in (0,1):
            for dv in (0,1):
                uu=u[ok]+du; vv=v[ok]+dv; zz=z[ok]; ss=sh[ok]*255*base
                o=np.argsort(zz); uu,vv,zz,ss=uu[o],vv[o],zz[o],ss[o]
                m=zz>zb[vv,uu]
                img[vv[m],uu[m]]=ss[m]; zb[vv[m],uu[m]]=zz[m]
    tiles.append(Image.fromarray(img.astype(np.uint8)))
sheet=Image.new('L',(int(S)*4,int(S)),255)
for k,t in enumerate(tiles): sheet.paste(t,(k*int(S),0))
sheet.save(outp+'.png'); print('views saved',outp+'.png')
