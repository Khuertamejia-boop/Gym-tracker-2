# Anatomy-plate render of a posed frame: near-white rounded muscles separated by soft dark creases, faint fibre
# streaks, worked muscles in coral red with deeper red borders and red fibre streaks, dark satin shorts.
#   python -I rendill2.py posed.blend OUTPREFIX     env: NPZ=style.npz (from stylefields.py), camera env as rendill.py
import bpy, sys, math, os, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
C=lambda k,d: tuple(float(x) for x in os.environ.get(k,d).split(','))+(1.0,)
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Hi' and not o.name.startswith('Banco') and not (os.environ.get('SHOWBAR','1')=='1' and o.name in ('Barra','Discos')): o.hide_render=True
ob=bpy.data.objects['Hi']; me=ob.data; nv=len(me.vertices)
have=set()
for f in [x for x in os.environ.get('NPZ','').split(',') if x]:
    d=np.load(f)
    for k in d.files:
        v=d[k]
        if v.shape[0]!=nv: continue
        if k=='disp':
            co=np.zeros(nv*3); me.vertices.foreach_get('co',co); n=np.zeros(nv*3); me.vertices.foreach_get('normal',n)
            me.vertices.foreach_set('co',(co+n*np.repeat(v[:,0],3)*E('DISPK',1)).ravel()); me.update(); continue
        if v.ndim==2 and v.shape[1]==3:
            a=me.attributes.get(k) or me.attributes.new(k,'FLOAT_VECTOR','POINT'); a.data.foreach_set('vector',v.astype(np.float32).ravel())
        else:
            a=me.attributes.get(k) or me.attributes.new(k,'FLOAT','POINT'); a.data.foreach_set('value',v.astype(np.float32))
        have.add(k)
for p in me.polygons: p.use_smooth=True
m=bpy.data.materials.new('plate'); nt=m.node_tree; N=nt.nodes; L=nt.links
bs=N['Principled BSDF']; bs.inputs['Roughness'].default_value=E('ROUGH',0.6)
try: bs.inputs['Specular IOR Level'].default_value=E('SPEC',0.4)
except Exception: pass
# ---------------------------------------------------------------- node helpers
def _in(node,i,v):
    if isinstance(v,(int,float)): node.inputs[i].default_value=v
    elif isinstance(v,tuple): node.inputs[i].default_value=v
    else: L.new(v,node.inputs[i])
def A(n):
    a=N.new('ShaderNodeAttribute'); a.attribute_name=n; a.attribute_type='GEOMETRY'; return a
def F(n,default=0.0):
    return A(n).outputs['Fac'] if n in have or n in me.attributes else default
def M(op,a,b=None,clamp=False):
    x=N.new('ShaderNodeMath'); x.operation=op; x.use_clamp=clamp; _in(x,0,a)
    if b is not None: _in(x,1,b)
    return x.outputs[0]
def SS(v,a,b,c=0.0,d=1.0):   # smoothstep remap
    x=N.new('ShaderNodeMapRange'); x.interpolation_type='SMOOTHSTEP'; _in(x,'Value',v)
    x.inputs['From Min'].default_value=a; x.inputs['From Max'].default_value=b; x.inputs['To Min'].default_value=c; x.inputs['To Max'].default_value=d; return x.outputs['Result']
def MIX(f,a,b,blend='MIX'):
    x=N.new('ShaderNodeMix'); x.data_type='RGBA'; x.blend_type=blend; _in(x,'Factor',f); _in(x,'A',a); _in(x,'B',b); return x.outputs['Result']
def G(v):
    x=N.new('ShaderNodeCombineColor')
    for i in range(3): _in(x,i,v)
    return x.outputs[0]
# ---------------------------------------------------------------- fields
# line distance: |signed distance| (exact after interpolation), but never less than the unsigned distance minus a
# tolerance: where the sign flips between two different borders (medial lines, junctions) no false line appears
MAPS=os.environ.get('MAPS','')
def udim(name,interp='Linear'):
    import glob
    img=bpy.data.images.load(os.path.join(MAPS,name+'.1001.png')); img.source='TILED'
    for f in sorted(glob.glob(os.path.join(MAPS,name+'.*.png'))):
        t=int(f.split('.')[-2])
        if img.tiles.get(t) is None: img.tiles.new(tile_number=t)
    img.filepath=os.path.join(MAPS,name+'.<UDIM>.png'); img.reload(); img.colorspace_settings.name='Non-Color'
    tx=N.new('ShaderNodeTexImage'); tx.image=img; tx.interpolation=interp
    uvn=N.new('ShaderNodeUVMap'); uvn.uv_map=me.uv_layers.active.name; L.new(uvn.outputs['UV'],tx.inputs['Vector'])
    return tx
if MAPS:
    # exact distances baked per texel (bakemaps.py): crisp continuous lines whatever the mesh density
    dt=udim('dist'); sp_=N.new('ShaderNodeSeparateColor'); L.new(dt.outputs['Color'],sp_.inputs[0])
    bd=M('MULTIPLY',sp_.outputs[0],25.5); bds=M('MULTIPLY',sp_.outputs[1],25.5); tend=sp_.outputs[2]
    sdabs=bd; sdsabs=bds; near=1.0; nears=1.0
    rt=udim('red'); redtex=N.new('ShaderNodeSeparateColor'); L.new(rt.outputs['Color'],redtex.inputs[0]); redtex=redtex.outputs[0]
else:
    bd=F('bd',60.0); sdabs=M('MAXIMUM',M('ABSOLUTE',F('sd',60.0)),M('SUBTRACT',bd,E('EK',2.5))); near=M('LESS_THAN',bd,E('NEAR',8.0))
    bds=F('bds',60.0); sdsabs=M('MAXIMUM',M('ABSOLUTE',F('sds',60.0)),M('SUBTRACT',bds,E('EK',2.5))); nears=M('LESS_THAN',bds,E('NEAR',8.0))
    tend=F('tend',0.0)
fmask=F('fmask',0.0)
# texture coordinates fixed to the body (rest position), so streaks do not swim when the body moves
tc=A('restco').outputs['Vector'] if 'restco' in have else N.new('ShaderNodeTexCoord').outputs['Object']
nz=N.new('ShaderNodeTexNoise'); L.new(tc,nz.inputs['Vector']); nz.inputs['Scale'].default_value=E('NZS',30.0); nz.inputs['Detail'].default_value=3.0
noise=nz.outputs['Fac']
# belly: lighter in the middle of each muscle, greyer towards its borders (soft borders count less)
belly=SS(bd,0.0,E('BW',20.0)); bellys=SS(bds,0.0,E('BWS',10.0),E('BSOFT',0.6),1.0)
belly=M('MULTIPLY',belly,bellys)
belly=M('MAXIMUM',belly,M('MULTIPLY',tend,0.7))
# crease line at hard borders (+ faint at soft ones)
crease=M('MULTIPLY',SS(sdabs,E('LW0',0.5),E('LW1',2.2),1.0,0.0),near)
creases=M('MULTIPLY',SS(sdsabs,E('LW0',0.5)*0.6,E('LW1',2.2)*0.7,E('LSOFT',0.35),0.0),nears)
crease=M('MAXIMUM',crease,creases)
# fibre streaks: thin lines along the fibres, broken up by noise
ph=M('ADD',M('MULTIPLY',F('fph'),E('FSC',0.5)),M('MULTIPLY',noise,E('FJIT',0.6)))
st=SS(M('SINE',M('MULTIPLY',ph,2*math.pi)),E('FS0',0.55),1.0)
streak=M('MULTIPLY',M('MULTIPLY',st,fmask),SS(noise,E('FN0',0.35),E('FN1',0.65),E('FMIN',0.25),1.0))
streak=M('MULTIPLY',streak,SS(bd,1.0,5.0))      # no streaks right on the border lines
# sculpt relief: valleys of the body's own relief a little darker, bulges a little lighter
relief=M('ADD',M('MULTIPLY',F('hf',0.0),E('HFK',1.0)),M('MULTIPLY',F('hm',0.0),E('HMK',0.25)))
relief=SS(relief,-E('HR',3.0),E('HR',3.0),E('HRLO',0.85),E('HRHI',1.05))
# ---------------------------------------------------------------- colours
sk_c=E('SKC',0.90); sk_e=E('SKE',0.55)
white=G(M('MULTIPLY',M('ADD',sk_e,M('MULTIPLY',belly,sk_c-sk_e)),relief))
white=MIX(M('MULTIPLY',streak,E('FIBW',0.10)),white,G(E('FIBWC',0.30)))
white=MIX(M('MULTIPLY',crease,E('LINEW',0.85)),white,G(E('LINEC',0.16)))
rc=C('REDC','0.80,0.17,0.09'); re_=C('REDE','0.36,0.04,0.02'); rl=C('REDL','0.95,0.50,0.36')
redb=MIX(belly,re_,rc)
redb=MIX(1.0,redb,G(relief),'MULTIPLY')
redb=MIX(M('MULTIPLY',SS(noise,0.55,0.85),E('REDHL',0.35)),redb,rl)     # painterly lighter patches
redb=MIX(M('MULTIPLY',streak,E('FIBR',0.35)),redb,C('FIBRC','0.40,0.05,0.02'))
redb=MIX(M('MULTIPLY',crease,E('LINER',0.9)),redb,C('LINERC','0.28,0.03,0.015'))
rmask=redtex if MAPS else M('MULTIPLY',SS(F('rsd',-60.0),-E('RW',0.6),E('RW',0.6)),F('rint',0.0))
col=MIX(rmask,white,redb)
# shorts: dark satin grey, red still shows through faintly where a worked muscle lies under them
sh=SS(F('shorts',0.0),0.45,0.55)
shc=G(E('SHV',0.055)); shr=MIX(M('MULTIPLY',rmask,E('SHRED',0.0)),shc,C('SHREDC','0.35,0.06,0.03'))
col=MIX(sh,col,shr)
# crevice darkening and soft silhouette edge
ao=N.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value=E('AOD',0.05); ao.samples=16
col=MIX(1.0,col,G(M('POWER',ao.outputs['AO'],E('AOP',1.2))),'MULTIPLY')
lw=N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value=0.5
rim=SS(lw.outputs['Facing'],E('RIM0',0.70),E('RIM1',0.98),0.0,E('RIMK',0.45))
col=MIX(rim,col,G(E('RIMC',0.30)))
if os.environ.get('DEBUGD'):   # show the hard-border distance texture (white = on a line)
    col=G(SS(sdabs,0.0,3.0,1.0,0.0)) if MAPS else col
L.new(col,bs.inputs['Base Color'])
# shorts a little glossier
rg=MIX(sh,G(E('ROUGH',0.6)),G(E('SHROUGH',0.42)))
sep=N.new('ShaderNodeSeparateColor'); L.new(rg,sep.inputs[0]); L.new(sep.outputs[0],bs.inputs['Roughness'])
me.materials.clear(); me.materials.append(m)
for p in me.polygons: p.material_index=0
# barbell: matte black plates, satin steel bar
for o in bpy.data.objects:
    if o.type=='MESH' and o.name in ('Discos','Barra'):
        mm=bpy.data.materials.new(o.name+'_m'); b2=mm.node_tree.nodes['Principled BSDF']
        if o.name=='Discos': b2.inputs['Base Color'].default_value=(0.025,0.025,0.025,1); b2.inputs['Roughness'].default_value=0.55
        else: b2.inputs['Base Color'].default_value=(0.35,0.35,0.36,1); b2.inputs['Metallic'].default_value=0.8; b2.inputs['Roughness'].default_value=0.35
        if os.environ.get('KEEPBARMAT')!='1': o.data.materials.clear(); o.data.materials.append(mm)
# ---------------------------------------------------------------- scene
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=int(E('SMP',32)); sc.cycles.device='CPU'
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'; sc.view_settings.exposure=E('EXPO',0.55)
sc.cycles.use_denoising=(os.environ.get('DENOISE','1')=='1')
sc.render.threads_mode='FIXED'; sc.render.threads=int(E('THREADS',4))
w=bpy.data.worlds.new('w'); w.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value=E('AMB',0.28); sc.world=w
_y=math.radians(E('YAW',0))
def rot(x,y,z): return (x*math.cos(_y)-y*math.sin(_y), x*math.sin(_y)+y*math.cos(_y), z)
def light(loc,e,sz=3.0):
    l=bpy.data.lights.new('L','AREA'); l.energy=e; l.size=sz; o=bpy.data.objects.new('L',l); o.location=loc; sc.collection.objects.link(o)
    from mathutils import Vector; d=Vector((0.0,0.0,0.9))-o.location; o.rotation_euler=(-d).to_track_quat('Z','Y').to_euler()
K=E('LK',0.3)
light(rot(E('KX',-2.4),E('KY',-3.2),E('KZ',3.4)),E('LKEY',360)*K,E('KSZ',3.0)); light(rot(3,-2.5,1.0),E('LFILL',50)*K); light(rot(0.5,3,2.5),E('LBACK',50)*K)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
yaw=math.radians(E('YAW',0)); pit=math.radians(E('PIT',10)); T=(E('TX',0),E('TY',-0.02),E('TZ',0.9)); dist=6
cam.location=(T[0]+dist*math.sin(yaw)*math.cos(pit), T[1]-dist*math.cos(yaw)*math.cos(pit), T[2]+dist*math.sin(pit))
cam.rotation_euler=(math.radians(90)-pit,0,yaw); cam.data.type='ORTHO'; cam.data.ortho_scale=E('OSC',2.0)
sc.render.film_transparent=(os.environ.get('TRANSP','1')=='1'); r_=int(E('RES',700)); sc.render.resolution_x=sc.render.resolution_y=r_
sc.render.filepath=out+'.png'; bpy.ops.render.render(write_still=True)
