# Preview of a compiled muscle atlas on the rest body, with a coordinate grid and landmark labels for authoring.
#   python -I atlas_preview.py ATLAS.npz OUTPREFIX VIEW [VIEW ...]
# VIEW = KIND[:a,b,size]   KIND in F B L R T, or V<yaw>,<pitch> (e.g. V135,20:0.1,1.2,0.5)
#   a,b = centre in the picture plane (F/B: world x,z  L/R: world y,z  T: x,y  V: picture-plane coords), size = width (m)
# env: RES (px, 900), SMP (8), LABELS (1: landmark names), MNAMES (1: muscle names), GRID (0.02 m minor lines)
# writes OUTPREFIX_<n>.png per view.  Rest body: env ATLAS_BLEND (default w/NB_mc.blend)
import bpy, sys, os, math, numpy as np, colorsys
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from PIL import Image, ImageDraw, ImageFont
S=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E=lambda k,d: float(os.environ.get(k,d))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
atl=np.load(args[0],allow_pickle=True); outp=args[1]; views=args[2:] or ['F','B','L']
bpy.ops.wm.open_mainfile(filepath=os.environ.get('ATLAS_BLEND',os.path.join(S,'w','NB_mc.blend')))
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Hi': o.hide_render=True
ob=bpy.data.objects['Hi']; me=ob.data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
no=np.zeros(nv*3); me.vertices.foreach_get('normal',no); no=no.reshape(-1,3)
names=[str(n) for n in atl['names']]; mid=atl['mid']
def colour(name):
    base=name.rsplit('.',1)[0]; h=(abs(hash(base))%997)/997.0
    if os.environ.get('PYTHONHASHSEED') is None:
        h=(sum(ord(c)*(i+7)*31 for i,c in enumerate(base))%997)/997.0
    r,g,b=colorsys.hsv_to_rgb(h,0.38,0.95); return (r,g,b)
cols=np.array([(0.80,0.80,0.80)]+[colour(n) for n in names[1:]])
kinds=list(atl['kinds']) if 'kinds' in atl.files else []
for i,k in enumerate(kinds):
    if k=='tendon': cols[i+1]=(0.97,0.97,0.93)
vc=cols[mid]
a=me.attributes.get('acol') or me.attributes.new('acol','FLOAT_COLOR','POINT')
a.data.foreach_set('color',np.c_[vc,np.ones(nv)].astype(np.float32).ravel())
rest=np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rest.npz'),allow_pickle=True)
for k in ('h_mid','h_fine'):
    at=me.attributes.get(k) or me.attributes.new(k,'FLOAT','POINT'); at.data.foreach_set('value',(rest[k]*1000).astype(np.float32))
for k in ('bd','bds','fph','fmask','sd','sds'):
    if k not in atl.files: continue
    at=me.attributes.get(k) or me.attributes.new(k,'FLOAT','POINT'); at.data.foreach_set('value',atl[k].astype(np.float32))
m=bpy.data.materials.new('atl'); nt=m.node_tree; N=nt.nodes; L=nt.links; bs=N['Principled BSDF']
bs.inputs['Roughness'].default_value=0.8
def at(n,t='GEOMETRY'):
    x=N.new('ShaderNodeAttribute'); x.attribute_name=n; x.attribute_type=t; return x
c=at('acol').outputs['Color']
def mr(v,a_,b_,c_=0,d_=1):
    x=N.new('ShaderNodeMapRange'); L.new(v,x.inputs['Value']); x.inputs[1].default_value=a_; x.inputs[2].default_value=b_; x.inputs[3].default_value=c_; x.inputs[4].default_value=d_; return x.outputs[0]
def mix(f,A,Bc):
    x=N.new('ShaderNodeMix'); x.data_type='RGBA'
    L.new(f,x.inputs['Factor']) if not isinstance(f,float) else None
    if isinstance(f,float): x.inputs['Factor'].default_value=f
    L.new(A,x.inputs['A']) if not isinstance(A,tuple) else None
    if isinstance(A,tuple): x.inputs['A'].default_value=A
    if isinstance(Bc,tuple): x.inputs['B'].default_value=Bc
    else: L.new(Bc,x.inputs['B'])
    return x.outputs['Result']
# fibre stripes
ph=at('fph').outputs['Fac']; mm=N.new('ShaderNodeMath'); mm.operation='MULTIPLY'; mm.inputs[1].default_value=2*math.pi; L.new(ph,mm.inputs[0])
sn=N.new('ShaderNodeMath'); sn.operation='SINE'; L.new(mm.outputs[0],sn.inputs[0])
st=mr(sn.outputs[0],0.6,1.0,0,0.35); fm=N.new('ShaderNodeMath'); fm.operation='MULTIPLY'; L.new(st,fm.inputs[0]); L.new(at('fmask').outputs['Fac'],fm.inputs[1])
c=mix(fm.outputs[0],c,(0.2,0.2,0.2,1))
def absn(name):
    x=N.new('ShaderNodeMath'); x.operation='ABSOLUTE'; L.new(at(name).outputs['Fac'],x.inputs[0])
    y=N.new('ShaderNodeMath'); y.operation='SUBTRACT'; L.new(at('bd' if name=='sd' else 'bds').outputs['Fac'],y.inputs[0]); y.inputs[1].default_value=2.5
    z=N.new('ShaderNodeMath'); z.operation='MAXIMUM'; L.new(x.outputs[0],z.inputs[0]); L.new(y.outputs[0],z.inputs[1]); return z.outputs[0]
hs='sd' in atl.files
def near(name,lim=7.0):
    x=N.new('ShaderNodeMath'); x.operation='LESS_THAN'; L.new(at(name).outputs['Fac'],x.inputs[0]); x.inputs[1].default_value=lim; return x.outputs[0]
def mul(a_,b_):
    x=N.new('ShaderNodeMath'); x.operation='MULTIPLY'; L.new(a_,x.inputs[0]); L.new(b_,x.inputs[1]); return x.outputs[0]
c=mix(mul(mr(absn('sds') if hs else at('bds').outputs['Fac'],0.4,1.0,0.6,0),near('bds')),c,(0.35,0.35,0.35,1))
c=mix(mul(mr(absn('sd') if hs else at('bd').outputs['Fac'],0.5,1.1,1,0),near('bd')),c,(0.02,0.02,0.02,1))
rel=N.new('ShaderNodeMath'); rel.operation='ADD'; L.new(at('h_mid').outputs['Fac'],rel.inputs[0]); fm2=N.new('ShaderNodeMath'); fm2.operation='MULTIPLY'; fm2.inputs[1].default_value=E('RFK',1.5); L.new(at('h_fine').outputs['Fac'],fm2.inputs[0]); L.new(fm2.outputs[0],rel.inputs[1])
rv=mr(rel.outputs[0],-E('RLR',7),E('RLR',7),E('RLO',0.55),1.12); cc=N.new('ShaderNodeCombineColor'); [L.new(rv,cc.inputs[i]) for i in range(3)]
mu=N.new('ShaderNodeMix'); mu.data_type='RGBA'; mu.blend_type='MULTIPLY'; mu.inputs['Factor'].default_value=1.0; L.new(c,mu.inputs['A']); L.new(cc.outputs[0],mu.inputs['B']); c=mu.outputs['Result']
L.new(c,bs.inputs['Base Color'])
ob.data.materials.clear(); ob.data.materials.append(m)
for p in me.polygons: p.material_index=0; p.use_smooth=True
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=int(E('SMP',8)); sc.cycles.device='CPU'
sc.cycles.use_denoising=True; sc.render.threads_mode='FIXED'; sc.render.threads=int(E('THREADS',2)); sc.view_settings.view_transform='Standard'
w=bpy.data.worlds.new('w'); w.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value=E('AMB',0.45); sc.world=w
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.type='ORTHO'
lt=bpy.data.lights.new('sun','SUN'); lt.energy=E('SUN',3.0); lo=bpy.data.objects.new('sun',lt); sc.collection.objects.link(lo)
sc.render.film_transparent=False; R_=int(E('RES',900)); sc.render.resolution_x=sc.render.resolution_y=R_
polys=[tuple(p.vertices) for p in me.polygons]; bvh=BVHTree.FromPolygons([tuple(p) for p in co],polys)
def basis(kind):
    if kind=='F': yaw,pit=0,0
    elif kind=='B': yaw,pit=180,0
    elif kind=='L': yaw,pit=90,0
    elif kind=='R': yaw,pit=-90,0
    elif kind=='T': yaw,pit=0,90
    else: yaw,pit=[float(x) for x in kind[1:].split(',')]
    y=math.radians(yaw); p=math.radians(pit)
    back=np.array((math.sin(y)*math.cos(p),-math.cos(y)*math.cos(p),math.sin(p))); f=-back
    r=np.cross(f,(0,0,1.0))
    if np.linalg.norm(r)<1e-6: r=np.array((1.0,0,0))
    r/=np.linalg.norm(r); u=np.cross(r,f); return f,r,u
DEF={'F':(0,1.0,1.9),'B':(0,1.0,1.9),'L':(0,1.0,1.9),'R':(0,1.0,1.9),'T':(0,0,1.0)}
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13); fsm=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
except Exception: font=fsm=ImageFont.load_default()
lmn=[str(x) for x in atl['lm_names']]; lmp=atl['lm_pos']
for vi,vw in enumerate(views):
    kind,_,rest=vw.partition(':')
    f,r,u=basis(kind)
    if rest:
        ca,cb,size=[float(x) for x in rest.split(',')]
        if kind in ('B','R'): ca=-ca
    else: ca,cb,size=DEF.get(kind,(0,1.0,1.9))
    centre=ca*r+cb*u; loc=centre-4.0*f
    M=Matrix(((r[0],u[0],-f[0]),(r[1],u[1],-f[1]),(r[2],u[2],-f[2])))
    cam.matrix_world=Matrix.Translation(Vector(loc))@M.to_4x4(); cam.data.ortho_scale=size
    ld=-f+0.9*u+0.5*r; ld/=np.linalg.norm(ld); lo.rotation_euler=Vector(-ld).to_track_quat('-Z','Y').to_euler() if False else Vector(tuple(ld)).to_track_quat('Z','Y').to_euler()
    fn=f'{outp}_{vi}.png'; sc.render.filepath=fn; bpy.ops.render.render(write_still=True)
    im=Image.open(fn).convert('RGB'); dr=ImageDraw.Draw(im,'RGBA')
    def px(P):
        a_=(P-centre)@r; b_=(P-centre)@u; return (R_/2+a_/size*R_, R_/2-b_/size*R_)
    # grid in world coordinates of the picture plane
    lab={'F':('x','z',1),'B':('x','z',-1),'L':('y','z',1),'R':('y','z',-1),'T':('x','y',1)}.get(kind,('a','b',1))
    g=E('GRID',0.02); a0=ca-size/2; a1=ca+size/2; b0=cb-size/2; b1=cb+size/2
    k0=int(math.floor(a0/g)); k1=int(math.ceil(a1/g))
    for k in range(k0,k1+1):
        v=k*g; X=R_/2+(v-ca)/size*R_; major=(k%5==0)
        dr.line([(X,0),(X,R_)],fill=(0,90,255,90 if major else 35),width=1)
        if major: dr.text((X+2,2),'%s=%.2f'%(lab[0],v*lab[2]),fill=(0,60,200,255),font=fsm)
    k0=int(math.floor(b0/g)); k1=int(math.ceil(b1/g))
    for k in range(k0,k1+1):
        v=k*g; Y=R_/2-(v-cb)/size*R_; major=(k%5==0)
        dr.line([(0,Y),(R_,Y)],fill=(0,90,255,90 if major else 35),width=1)
        if major: dr.text((2,Y+1),'%s=%.2f'%(lab[1],v),fill=(0,60,200,255),font=fsm)
    if os.environ.get('LABELS','1')=='1':
        for n,P in zip(lmn,lmp):
            if os.environ.get('LSIDE','L')!='both' and not n.endswith('@L'): continue
            o=P-3*f
            hit=bvh.ray_cast(Vector(o),Vector(f))
            if hit[0] is None or np.linalg.norm(np.array(hit[0])-P)>0.006: continue
            X,Y=px(P)
            if not (0<=X<R_ and 0<=Y<R_): continue
            dr.ellipse([X-3,Y-3,X+3,Y+3],fill=(230,0,90,255)); dr.text((X+4,Y-7),n[:-2],fill=(150,0,60,255),font=fsm)
    if os.environ.get('MNAMES','1')=='1':
        vis=(no@(-f))>0.35
        for i,n in enumerate(names[1:],1):
            sel=(mid==i)&vis
            if sel.sum()<30: continue
            P=co[sel].mean(0); X,Y=px(P)
            if 0<=X<R_ and 0<=Y<R_:
                t=n; dr.text((X-len(t)*3.2,Y-6),t,fill=(0,0,0,255),font=font)
    im.save(fn)
    print('wrote',fn)
