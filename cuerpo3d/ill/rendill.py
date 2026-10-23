# Illustration-style render (anatomy-plate look): near-white matte body, crevice darkening, muscle grooves as soft dark
# lines, fibre striations, silhouette darkening, dark shorts, worked muscles in coral red with a darker belly.
# usage: python -I rendill.py posed.blend outprefix     env: NPZ=a.npz[,b.npz] (per-vertex fields), view env as rendarm
import bpy,sys,math,os,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Hi' and not o.name.startswith('Banco') and not (os.environ.get('SHOWBAR','1')=='1' and o.name in ('Barra','Discos')): o.hide_render=True
ob=bpy.data.objects['Hi']; me=ob.data; nv=len(me.vertices)
for f in [x for x in os.environ.get('NPZ','').split(',') if x]:
    d=np.load(f)
    for k in d.files:
        v=d[k]
        if v.shape[0]!=nv: continue
        if v.ndim==1:
            a=me.attributes.get(k) or me.attributes.new(k,'FLOAT','POINT'); a.data.foreach_set('value',v.astype(np.float32))
        elif k=='disp':   # displacement along the current (posed) normals, metres
            co=np.zeros(nv*3); me.vertices.foreach_get('co',co); n=np.zeros(nv*3); me.vertices.foreach_get('normal',n)
            me.vertices.foreach_set('co',(co+n*np.repeat(v[:,0],3)*E('DISPK',1)).ravel()); me.update()
for p in me.polygons: p.use_smooth=True
m=bpy.data.materials.new('ill'); nt=m.node_tree; N=nt.nodes; L=nt.links
bs=N['Principled BSDF']; bs.inputs['Roughness'].default_value=E('ROUGH',0.55)
try: bs.inputs['Specular IOR Level'].default_value=E('SPEC',0.25)
except Exception: pass
def attr(n):
    a=N.new('ShaderNodeAttribute'); a.attribute_name=n; a.attribute_type='GEOMETRY'; return a.outputs['Fac']
def math_(op,a,b=None,clamp=False):
    x=N.new('ShaderNodeMath'); x.operation=op; x.use_clamp=clamp
    for i,v in enumerate((a,b)):
        if v is None: continue
        if isinstance(v,(int,float)): x.inputs[i].default_value=v
        else: L.new(v,x.inputs[i])
    return x.outputs[0]
def mr(v,a,b,c=0.0,d=1.0,smooth=True):
    x=N.new('ShaderNodeMapRange'); x.interpolation_type='SMOOTHSTEP' if smooth else 'LINEAR'
    L.new(v,x.inputs['Value']); x.inputs['From Min'].default_value=a; x.inputs['From Max'].default_value=b
    x.inputs['To Min'].default_value=c; x.inputs['To Max'].default_value=d; return x.outputs['Result']
def mixc(fac,A,B,blend='MIX'):
    x=N.new('ShaderNodeMix'); x.data_type='RGBA'; x.blend_type=blend
    for s,v in (('Factor',fac),('A',A),('B',B)):
        if isinstance(v,(int,float)): x.inputs[s].default_value=v
        elif isinstance(v,tuple): x.inputs[s].default_value=v
        else: L.new(v,x.inputs[s])
    return x.outputs['Result']
def gray(v):
    c=N.new('ShaderNodeCombineColor')
    for i in range(3):
        if isinstance(v,(int,float)): c.inputs[i].default_value=v
        else: L.new(v,c.inputs[i])
    return c.outputs[0]
col=lambda s: tuple(float(x) for x in os.environ.get(s[0],s[1]).split(','))+(1,)
# ---- base colours
skin=col(('SKIN','0.78,0.78,0.78')); red=col(('RED','0.86,0.22,0.11')); redd=col(('REDD','0.55,0.06,0.03')); redl=col(('REDL','0.95,0.45,0.32'))
c=gray(E('SKINV',0.78))
if os.environ.get('WORK','1')=='1' and 'work' in me.attributes:
    w=attr('work')
    rp=N.new('ShaderNodeValToRGB'); el=rp.color_ramp.elements
    el[0].position=0.0; el[0].color=skin; el[1].position=1.0; el[1].color=redd
    e1=el.new(E('WP1',0.25)); e1.color=redl; e2=el.new(E('WP2',0.6)); e2.color=red
    L.new(w,rp.inputs['Fac']); c=rp.outputs['Color']
# fibre striations: cos(2*pi*phase) on fields 'fph' (phase, in line units) masked by 'fmask'
if 'fph' in me.attributes:
    ph=attr('fph'); s=math_('SINE',math_('MULTIPLY',ph,2*math.pi))
    st=mr(s,E('FS0',0.55),1.0)                                   # thin bright/dark lines
    fm=math_('MULTIPLY',attr('fmask'),E('FIBK',0.25)) if 'fmask' in me.attributes else E('FIBK',0.25)
    k=math_('MULTIPLY',st,fm); c=mixc(k,c,gray(0.0),'MULTIPLY') if False else mixc(math_('MULTIPLY',k,1.0),c,mixc(0.5,c,gray(0.25),'MULTIPLY'))
# muscle groove lines from the relief (valleys of the fine band-pass)
if 'h_fine' in me.attributes:
    hv=math_('MULTIPLY',attr('h_fine'),-1000.0)                    # mm, positive in valleys
    gl=mr(hv,E('GL0',0.6),E('GL1',2.4),0.0,E('GLK',0.55))
    c=mixc(gl,c,gray(E('GLC',0.18)))
if 'h_mid' in me.attributes:
    hb=math_('MULTIPLY',attr('h_mid'),1000.0)
    br=mr(hb,E('HB0',-5),E('HB1',5),E('HBLO',0.80),E('HBHI',1.08),False)
    c=mixc(1.0,c,gray(br),'MULTIPLY')
if 'bd' in me.attributes:   # distance (mm) to the nearest muscle border
    bl=mr(attr('bd'),E('BL0',0.6),E('BL1',2.2),E('BLK',0.75),0.0)
    c=mixc(bl,c,gray(E('BLC',0.15)))
# dark shorts
sh=mr(attr('shorts'),0.45,0.55,0,1,False)
c=mixc(sh,c,gray(E('SHV',0.09)))
# crevice darkening (AO) and silhouette darkening
ao=N.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value=E('AOD',0.04); ao.samples=16
aop=math_('POWER',ao.outputs['AO'],E('AOP',1.6))
c=mixc(1.0,c,gray(aop),'MULTIPLY')
lw=N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value=0.5
rim=mr(lw.outputs['Facing'],E('RIM0',0.62),E('RIM1',0.97),0.0,E('RIMK',0.55))
c=mixc(rim,c,gray(E('RIMC',0.25)),'MIX')
L.new(c,bs.inputs['Base Color'])
for i in range(max(1,len(me.materials))):
    if len(me.materials): me.materials[i]=m
    else: me.materials.append(m)
# barbell look: black plates, steel bar
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=int(E('SMP',24)); sc.cycles.device='CPU'
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
sc.cycles.use_denoising=(os.environ.get('DENOISE','1')=='1')
w=bpy.data.worlds.new('w'); w.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value=E('AMB',0.45); sc.world=w
_y=math.radians(E('YAW',0))
def rot(x,y,z): return (x*math.cos(_y)-y*math.sin(_y), x*math.sin(_y)+y*math.cos(_y), z)
def light(loc,e,sz=3.0):
    l=bpy.data.lights.new('L','AREA'); l.energy=e; l.size=sz; o=bpy.data.objects.new('L',l); o.location=loc; sc.collection.objects.link(o)
    from mathutils import Vector; d=Vector((0.0,0.0,0.9))-o.location; o.rotation_euler=(-d).to_track_quat('Z','Y').to_euler()
K=E('LK',0.3)
light(rot(-2.4,-3.2,3.4),E('LKEY',260)*K); light(rot(3,-2.5,1.0),E('LFILL',70)*K); light(rot(0.5,3,2.5),E('LBACK',60)*K)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
yaw=math.radians(E('YAW',0)); pit=math.radians(E('PIT',10)); T=(E('TX',0),E('TY',-0.02),E('TZ',0.9)); dist=6
cam.location=(T[0]+dist*math.sin(yaw)*math.cos(pit), T[1]-dist*math.cos(yaw)*math.cos(pit), T[2]+dist*math.sin(pit))
cam.rotation_euler=(math.radians(90)-pit,0,yaw); cam.data.type='ORTHO'; cam.data.ortho_scale=E('OSC',2.0)
sc.render.film_transparent=True; r_=int(E('RES',700)); sc.render.resolution_x=sc.render.resolution_y=r_
sc.render.filepath=out+'.png'; bpy.ops.render.render(write_still=True)
