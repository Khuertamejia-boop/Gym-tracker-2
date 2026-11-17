# Anatomy-plate look by SCULPTING, not drawing: the muscle map is turned into real relief at render time
# (subdivided mesh + material displacement): every muscle is a rounded pillow, its border a deep soft groove, so the
# light itself makes the gradients; fibres are a fine relief + light/dark streaks; worked muscles coral red.
#   python -I rendsculpt.py posed.blend OUTPREFIX      env: MAPS=<bakemaps dir> NPZ=<stylefields npz>, camera env
import bpy, sys, math, os, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
C=lambda k,d: tuple(float(x) for x in os.environ.get(k,d).split(','))+(1.0,)
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Hi' and not (os.environ.get('SHOWBAR','1')=='1' and o.name in ('Barra','Discos')) and not (o.name.startswith('Banco') and os.environ.get('HIDEBANCO','0')!='1') and not (os.environ.get('FACE','1')=='1' and (o.name=='Cabeza' or o.name.startswith('Ojo.'))): o.hide_render=True
ob=bpy.data.objects['Hi']; me=ob.data; nv=len(me.vertices); have=set()
for f in [x for x in os.environ.get('NPZ','').split(',') if x]:
    d=np.load(f)
    for k in d.files:
        v=d[k]
        if v.shape[0]!=nv or k=='disp': continue
        if v.ndim==2 and v.shape[1]==3:
            a=me.attributes.get(k) or me.attributes.new(k,'FLOAT_VECTOR','POINT'); a.data.foreach_set('vector',v.astype(np.float32).ravel())
        else:
            a=me.attributes.get(k) or me.attributes.new(k,'FLOAT','POINT'); a.data.foreach_set('value',v.astype(np.float32))
        have.add(k)
for p in me.polygons: p.use_smooth=True
_rest=np.load(os.environ.get('RESTNPZ',os.path.join(os.path.dirname(os.path.abspath(__file__)),'rest.npz')),allow_pickle=True)   # RESTNPZ: female body (rest_f.npz)
_am=np.array([str(x) in ('upper_arm.L','forearm.L','fa_tw1.L','fa_tw2.L','fa_tw3.L') for x in _rest['main']],np.float32)
a=me.attributes.get('armmask') or me.attributes.new('armmask','FLOAT','POINT'); a.data.foreach_set('value',_am); have.add('armmask')
# lower forearm = tendons: less relief, softer lines (fade 0 above TF0 of the forearm length -> 1 at TF1)
_co=_rest['co']; _bn=[str(x) for x in _rest['bn']]; _tf=np.zeros(len(_co))
for _s in 'LR':
    _h=_rest['bh'][_bn.index('forearm.'+_s)]; _t=_rest['bt'][_bn.index('forearm.'+_s)]; _d=_t-_h
    _u=((_co-_h)@_d)/(_d@_d); _side=np.sign(_h[0])
    _f=np.clip((_u-E('TF0',0.55))/(E('TF1',0.85)-E('TF0',0.55)),0,1); _f=_f*_f*(3-2*_f)
    _tf=np.maximum(_tf,_f*(np.abs(np.linalg.norm(np.cross(_co-_h,_d/np.linalg.norm(_d)),axis=1))<0.07)*(_co[:,0]*_side>0))
a=me.attributes.get('tfade') or me.attributes.new('tfade','FLOAT','POINT'); a.data.foreach_set('value',_tf.astype(np.float32)); have.add('tfade')
_cab=bpy.data.objects.get('Cabeza')
if _cab is not None and _cab.data.attributes.get('face') is not None and os.environ.get('FACE','1')=='1':
    # head with face shading (facebuild.py FACEATTR=1): the neck of the body takes the same shading little by little
    # (attribute 'face': 0 at the base of the neck -> 1 under the jaw, only around the neck), so head and neck are one piece
    _zn=float(_rest['bh'][_bn.index('neck')][2])
    _f=np.clip((_co[:,2]-(_zn-E('FNZ0',0.012)))/E('FNZH',0.070),0,1); _f=_f*_f*(3-2*_f)
    _g=np.clip((E('FNR1',0.120)-np.hypot(_co[:,0],_co[:,1]+0.02))/(E('FNR1',0.120)-E('FNR0',0.080)),0,1); _g=_g*_g*(3-2*_g)
    a=me.attributes.get('face') or me.attributes.new('face','FLOAT','POINT'); a.data.foreach_set('value',(_f*_g).astype(np.float32))
NEWHEAD=_cab is not None and _cab.data.attributes.get('face') is not None and os.environ.get('FACE','1')=='1' and E('HEADPLAIN',1)>0
if NEWHEAD:
    # (12-11-2026) clean joint between the head and the neck. The body's UV map has a seam all round the neck 0-4 mm above
    # the cut of the head, and the muscle maps stop there (the head island is plain skin): the copied drawing ended on
    # the head band in a ragged ledge (the saw-tooth line that showed in the close-ups). Now the head is plain skin
    # everywhere ('plainh' = 1: no map-driven relief, lines, fibres or red on it), so the drawing of the neck ends on
    # the straight edge of the head; and the true displacement of the body fades out towards that edge ('hfd': 1 from
    # HFD0 + HFD m away from the head, 0 under it), so the neck's relief cannot poke through the band glued over it.
    from scipy.spatial import cKDTree as _KDh
    _hv=np.array([v.co[:] for v in _cab.data.vertices])
    _dh=_KDh(_hv).query(_co)[0]; _hf=np.clip((_dh-E('HFD0',0.0015))/E('HFD',0.006),0,1); _hf=_hf*_hf*(3-2*_hf)
    a=me.attributes.get('hfd') or me.attributes.new('hfd','FLOAT','POINT'); a.data.foreach_set('value',_hf.astype(np.float32))
    a=_cab.data.attributes.get('plainh') or _cab.data.attributes.new('plainh','FLOAT','POINT'); a.data.foreach_set('value',np.ones(len(_hv),np.float32))
    # (13-11-2026, owner: «todavía se ve la unión del cuello y la cabeza, una línea marcada, las texturas son distintas»)
    # The muscle drawing of the neck stopped dead on the plain head. Now it FADES OUT before it gets there: 'hd' = rest
    # height of every body vertex over the cut plane of the head (linear in the rest position, so it is exact inside
    # every face); the shader turns it into plain skin from NECKFADE m below the cut (drawing whole) to NECKFADE0 m below
    # it (plain, like the head). Lines, fibres, relief, border shading and red all fade together.
    _cz=float(_cab.get('cutz',1.44)); _cs=float(_cab.get('cutsl',0.32))
    a=me.attributes.get('hd') or me.attributes.new('hd','FLOAT','POINT'); a.data.foreach_set('value',(_co[:,2]-(_cz+_cs*(_co[:,1]+0.08))).astype(np.float32))
_abl=os.path.join(os.path.dirname(os.path.abspath(__file__)),'pv','bla.npz')     # muscle atlas (labels per body vertex)
if E('PLAIN1',0)>0 and os.path.exists(_abl):
    # the muscle drawing fades out where it reaches the head (attribute 'plain': 1 = plain skin, no map-driven relief,
    # lines, fibres or red). The neck muscles (sternocleidomastoid) end in a ragged edge under the ear / jaw in the
    # atlas; on the body that edge was hidden inside the head, but the head ('Cabeza') copies the drawing of the body
    # skin under it and showed it as a saw-tooth line. Distance (rest pose) to the unlabelled skin of the head:
    # 1 up to PLAIN0 m, 0 from PLAIN1 m on. The trapezius keeps its drawing up to the skull (clean border there).
    from scipy.spatial import cKDTree as _KD
    _ab=np.load(_abl,allow_pickle=True); _lab=np.array([str(x) for x in _ab['names']])[_ab['mid'].astype(int)]
    _mn=np.array([str(x) for x in _rest['main']]); _seed=(_lab=='none')&(_mn=='head')
    if len(_lab)==nv and _seed.any():
        _dd=_KD(_co[_seed]).query(_co)[0]
        _pl=1.0-np.clip((_dd-E('PLAIN0',0.003))/(E('PLAIN1',0)-E('PLAIN0',0.003)),0,1); _pl=_pl*_pl*(3-2*_pl)
        _pl=_pl*(~np.char.startswith(_lab,'trap'))
        a=me.attributes.get('plain') or me.attributes.new('plain','FLOAT','POINT'); a.data.foreach_set('value',_pl.astype(np.float32)); have.add('plain')
if E('SHORTZ',0)>0:
    # shorter shorts: cut the existing shorts mask at a higher hem (rest-pose height), a little higher on the outside
    _sh=np.zeros(nv,np.float32); me.attributes['shorts'].data.foreach_get('value',_sh)
    _ax=np.abs(_co[:,0])
    _zh=E('SHORTZ',0.74)+E('SHSL',0.25)*np.clip(_ax-E('SHX0',0.10),0,0.08)-E('SHBK',0.0)*np.clip(_co[:,1]/0.10,0,1)
    _t=np.clip((_co[:,2]-_zh)/E('SHBAND',0.008)+0.5,0,1)
    if E('SHLIN',1)>0: _t=np.clip((_co[:,2]-_zh)/E('SHBANDL',0.012)+0.5,0,1)   # linear ramp: the 0.5 cut is a clean line
    else: _t=_t*_t*(3-2*_t)
    me.attributes['shorts'].data.foreach_set('value',(_sh*_t).astype(np.float32))
sub=ob.modifiers.new('sub','SUBSURF'); sub.levels=int(E('SUBD',2)); sub.render_levels=int(E('SUBD',2)); sub.uv_smooth='PRESERVE_BOUNDARIES'
m=bpy.data.materials.new('sculpt'); nt=m.node_tree; N=nt.nodes; L=nt.links
m.displacement_method=os.environ.get('DISPM','BOTH')
bs=N['Principled BSDF']; bs.inputs['Roughness'].default_value=E('ROUGH',0.55)
try: bs.inputs['Specular IOR Level'].default_value=E('SPEC',0.35)
except Exception: pass
def _in(node,i,v):
    if isinstance(v,(int,float)): node.inputs[i].default_value=v
    elif isinstance(v,tuple): node.inputs[i].default_value=v
    else: L.new(v,node.inputs[i])
def A(n): a=N.new('ShaderNodeAttribute'); a.attribute_name=n; a.attribute_type='GEOMETRY'; return a
def F(n,default=0.0): return A(n).outputs['Fac'] if n in have else default
def M(op,a,b=None,clamp=False):
    x=N.new('ShaderNodeMath'); x.operation=op; x.use_clamp=clamp; _in(x,0,a)
    if b is not None: _in(x,1,b)
    return x.outputs[0]
def SS(v,a,b,c=0.0,d=1.0):
    x=N.new('ShaderNodeMapRange'); x.interpolation_type='SMOOTHSTEP'; _in(x,'Value',v)
    x.inputs['From Min'].default_value=a; x.inputs['From Max'].default_value=b; x.inputs['To Min'].default_value=c; x.inputs['To Max'].default_value=d; return x.outputs['Result']
def MIX(f,a,b,blend='MIX'):
    x=N.new('ShaderNodeMix'); x.data_type='RGBA'; x.blend_type=blend; _in(x,'Factor',f); _in(x,'A',a); _in(x,'B',b); return x.outputs['Result']
def G(v):
    x=N.new('ShaderNodeCombineColor')
    for i in range(3): _in(x,i,v)
    return x.outputs[0]
MAPS=os.environ['MAPS']
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
dt=udim('dist'); sp_=N.new('ShaderNodeSeparateColor'); L.new(dt.outputs['Color'],sp_.inputs[0])
d=M('MULTIPLY',sp_.outputs[0],25.5); ds=M('MULTIPLY',sp_.outputs[1],25.5); tend=sp_.outputs[2]
# per-border strength (linemap.py): a weak border (two worked muscles, a merged pair) is drawn as if it were far away
if os.path.exists(os.path.join(MAPS,'lstr.1001.png')):
    _lt=udim('lstr'); _ls=N.new('ShaderNodeSeparateColor'); L.new(_lt.outputs['Color'],_ls.inputs[0]); lstr=_ls.outputs[0]
    ladd=M('MULTIPLY',M('SUBTRACT',1.0,lstr),E('LDW',25.0))
else:
    lstr=1.0; ladd=0.0
d=M('ADD',d,ladd)
rt=udim('red'); rs=N.new('ShaderNodeSeparateColor'); L.new(rt.outputs['Color'],rs.inputs[0]); red=rs.outputs[0]
if E('RSOFT',0)>0 and os.path.exists(os.path.join(MAPS,'redd16.1001.png')):
    # soft outer border of the red: the red fades in over RSOFT mm from the border with the grey muscles
    _rd=udim('redd16','Cubic'); _rds=N.new('ShaderNodeSeparateColor'); L.new(_rd.outputs['Color'],_rds.inputs[0])
    _rmm=M('MULTIPLY',_rds.outputs[0],64.0)
    red=M('MULTIPLY',red,SS(_rmm,0.0,E('RSOFT',0),E('RSOFT0',0.15),1.0))
if E('SPINEW',0)>0 and 'restco' in have:
    # light strip along the spine (supraspinous ligament / erector edge) between the two worked sides, as in the plates
    _rc=N.new('ShaderNodeSeparateXYZ'); L.new(A('restco').outputs['Vector'],_rc.inputs[0])
    _ax=M('ABSOLUTE',_rc.outputs['X'])
    _sp=SS(_ax,E('SPINEW',0.010),E('SPINEW',0.010)+E('SPINEF',0.010),0.0,1.0)
    _zon=M('MULTIPLY',SS(_rc.outputs['Z'],E('SPZ0',0.98),E('SPZ0',0.98)+0.03),SS(_rc.outputs['Z'],E('SPZ1',1.46),E('SPZ1',1.46)-0.03))
    _zon=M('MULTIPLY',_zon,SS(_rc.outputs['Y'],0.02,0.05))
    red=M('MULTIPLY',red,M('SUBTRACT',1.0,M('MULTIPLY',_zon,M('SUBTRACT',1.0,_sp))))
# ---- pillow profile: 0 in the groove -> 1 inside the muscle   g = 1 - exp(-(d/W)^P)
def pillow(dist,W,P):
    return M('SUBTRACT',1.0,M('EXPONENT',M('MULTIPLY',M('POWER',M('DIVIDE',dist,W),P),-1.0)))
pln=M('MAXIMUM',F('plain'),A('plainh').outputs['Fac'])     # body attribute (PLAIN1, off by default) / head attribute (PLH1)
if NEWHEAD and E('NECKFADE',0.030)>0:      # the neck drawing fades to plain skin towards the head (the head has no 'hd': 0 -> plain)
    pln=M('MAXIMUM',pln,SS(A('hd').outputs['Fac'],-E('NECKFADE',0.030),-E('NECKFADE0',0.004)))
red=M('MULTIPLY',red,M('SUBTRACT',1.0,pln))
npl=M('SUBTRACT',1.0,pln)          # 0 where the skin is plain (head): no map-driven relief, lines or fibres
gh=pillow(d,E('W',7.0),E('P',1.5)); gs=pillow(ds,E('WS',5.0),E('P',1.5))
# fibres: phase field from the atlas, broken into bundles by noise (fixed to the body via its rest position)
tc=A('restco').outputs['Vector'] if 'restco' in have else N.new('ShaderNodeTexCoord').outputs['Object']
nz=N.new('ShaderNodeTexNoise'); L.new(tc,nz.inputs['Vector']); nz.inputs['Scale'].default_value=E('NZS',35.0); nz.inputs['Detail'].default_value=4.0
noise=nz.outputs['Fac']
nz2=N.new('ShaderNodeTexNoise'); L.new(tc,nz2.inputs['Vector']); nz2.inputs['Scale'].default_value=E('NZS2',120.0); nz2.inputs['Detail'].default_value=2.0
fine=nz2.outputs['Fac']
if os.path.exists(os.path.join(MAPS,'fph16.1001.png')) and E('FPHTEX',1)>0:
    # fibre phase baked per texel and blurred inside each muscle (bakemaps.py): smooth stripes, no triangle kinks
    _ft=udim('fph16','Cubic'); _fs=N.new('ShaderNodeSeparateColor'); L.new(_ft.outputs['Color'],_fs.inputs[0]); fph_src=M('MULTIPLY',_fs.outputs[0],128.0)
    _mt=udim('fmask16','Cubic'); _ms=N.new('ShaderNodeSeparateColor'); L.new(_mt.outputs['Color'],_ms.inputs[0]); fmask_src=_ms.outputs[0]
else:
    fph_src=F('fph'); fmask_src=F('fmask')
ph=M('ADD',M('MULTIPLY',fph_src,E('FSC',0.7)),M('MULTIPLY',noise,E('FJIT',0.8)))
if os.environ.get('FMODE','streak')=='streak':
    # painterly streaks: random brightness per thin band across the fibres (1D noise of the fibre phase)
    n1=N.new('ShaderNodeTexNoise'); n1.noise_dimensions='1D'; n1.inputs['Scale'].default_value=E('FSTS',1.0); n1.inputs['Detail'].default_value=E('FSTD',2.0)
    L.new(M('ADD',M('MULTIPLY',fph_src,E('FSTR',3.0)),M('MULTIPLY',noise,E('FSTJ',0.6))),n1.inputs['W'])
    wave=SS(n1.outputs['Fac'],E('FS0',0.35),E('FS1',0.70))
else:
    wave=M('MULTIPLY',M('ADD',M('SINE',M('MULTIPLY',ph,2*math.pi)),1.0),0.5)          # 0..1 across each fibre bundle
bund=SS(noise,E('FB0',0.30),E('FB1',0.70),E('FBMIN',0.2),1.0)                    # some bundles stronger than others
fib=M('MULTIPLY',M('MULTIPLY',wave,bund),M('MULTIPLY',fmask_src,SS(d,0.5,4.0)))   # 0 on grooves / tendons
# ---- height (mm). With 'dome' (bulge.py): each muscle a smooth round bulge (amplitude damp) cut by a crisp crease
# along its hard borders and a faint one along soft borders; otherwise the distance-only pillow.
if os.path.exists(os.path.join(MAPS,'dome.1001.png')):
    dome_t=udim('dome','Cubic').outputs['Color']; damp_t=M('MULTIPLY',udim('damp','Cubic').outputs['Color'],16.0)
    dsep=N.new('ShaderNodeSeparateColor'); L.new(dome_t,dsep.inputs[0]); dome_t=dsep.outputs[0]
else:
    dome_t=F('dome'); damp_t=F('damp')
if 'dome' in have or os.path.exists(os.path.join(MAPS,'dome.1001.png')):
    crease=SS(d,0.0,E('CW',3.0)); creases=SS(ds,0.0,E('CWS',2.5),E('CSOFT',0.6),1.0)
    shape=M('MULTIPLY',M('MULTIPLY',dome_t,crease),creases)
    shape=M('MULTIPLY',shape,M('ADD',M('MULTIPLY',gh,E('GHK',0.3)),1.0-E('GHK',0.3)))
    h=M('MULTIPLY',damp_t,M('SUBTRACT',shape,E('MIDF',0.7)))
    GD=0.0; GSD=0.0
    gh=M('MULTIPLY',dome_t,crease)       # also drives the groove darkening below
else:
    GD=E('GD',3.0); GSD=E('GSD',1.0)
    h=M('ADD',M('MULTIPLY',gh,GD),M('MULTIPLY',gs,GSD))
    h=M('SUBTRACT',h,M('MULTIPLY',M('MULTIPLY',tend,E('TFLAT',0.5)),M('MULTIPLY',gh,GD)))
    h=M('SUBTRACT',h,GD+GSD)
h=M('ADD',h,M('MULTIPLY',fib,E('FIBH',0.12)))
h=M('ADD',h,M('MULTIPLY',M('SUBTRACT',fine,0.5),E('SKINH',0.06)))
h=M('MULTIPLY',h,M('SUBTRACT',1.0,SS(A('shorts').outputs['Fac'],0.3,0.6)))      # the shorts fabric stays smooth
h=M('MULTIPLY',h,npl)
if NEWHEAD: h=M('MULTIPLY',h,A('hfd').outputs['Fac'])      # no displacement on the head (no such attribute) nor on the neck right under it
dn=N.new('ShaderNodeDisplacement'); dn.space='OBJECT'
L.new(M('DIVIDE',h,1000.0),dn.inputs['Height']); dn.inputs['Midlevel'].default_value=0.0; dn.inputs['Scale'].default_value=E('DSC',1.0)
L.new(dn.outputs['Displacement'],N['Material Output'].inputs['Displacement'])
# ---- colour: white clay, slightly darker in the grooves; red with deeper red grooves and visible fibre streaks
cav=M('MULTIPLY',M('MULTIPLY',M('SUBTRACT',1.0,gh),E('CAVK',0.35)),npl)
white=MIX(cav,G(E('SKC',0.88)),G(E('SKG',0.45)))
wst=M('MULTIPLY',M('MULTIPLY',M('SUBTRACT',1.0,wave),SS(d,0.5,4.0)),M('SUBTRACT',1.0,tend))   # faint grey streaks on white muscles too
white=MIX(M('MULTIPLY',M('MULTIPLY',wst,E('FIBW',0.06)),npl),white,G(E('FIBWC',0.45)))
rc=C('REDC','0.86,0.26,0.15'); rg=C('REDG','0.42,0.06,0.03'); rl=C('REDL','1.0,0.62,0.48')
redb=MIX(M('MULTIPLY',M('SUBTRACT',1.0,gh),E('CAVR',0.75)),rc,rg)
redb=MIX(M('MULTIPLY',fib,E('FIBR',0.45)),redb,C('FIBRC','0.55,0.08,0.04'))
redb=MIX(M('MULTIPLY',M('MULTIPLY',M('SUBTRACT',1.0,wave),bund),M('MULTIPLY',fmask_src,E('FIBL',0.25))),redb,rl)
core=M('MULTIPLY',M('MULTIPLY',SS(d,E('LW0',0.3),E('LW1',1.4),1.0,0.0),E('LINEK',0.45)),M('SUBTRACT',1.0,M('MULTIPLY',F('tfade'),E('TFL',0.5))))      # thin dark core at the bottom of each groove
core=M('MULTIPLY',core,npl)
white=MIX(core,white,G(E('LINEC',0.30)))
redb=MIX(core,redb,C('LINERC','0.30,0.04,0.02'))
col=MIX(red,white,redb)
sh=SS(A('shorts').outputs['Fac'],0.45,0.55)
col=MIX(sh,col,G(E('SHV',0.055)))
ao=N.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value=E('AOD',0.02); ao.samples=16
col=MIX(1.0,col,G(M('POWER',ao.outputs['AO'],E('AOP',1.0))),'MULTIPLY')
lw=N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value=0.5            # soft grey contour at the silhouette
rim=SS(lw.outputs['Facing'],E('RIM0',0.72),E('RIM1',0.98),0.0,E('RIMK',0.55))
col=MIX(rim,col,G(E('RIMC',0.28)))
L.new(col,bs.inputs['Base Color'])
if os.environ.get('SHADE')=='matcap':
    # illustration shading: tone chosen from the surface direction seen from the camera (key from the upper left),
    # so the tonal steps (white crest, grey flank, dark valley) are set exactly; ambient occlusion deepens the grooves
    geo=N.new('ShaderNodeNewGeometry'); vt=N.new('ShaderNodeVectorTransform'); vt.vector_type='NORMAL'; vt.convert_from='WORLD'; vt.convert_to='CAMERA'
    nrm=geo.outputs['Normal']
    if E('BUMPK',0)>0 and 'shape' in dir():
        # exaggerated muscle roundness for the shading only: bump from each muscle's dome
        bp=N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=E('BUMPS',1.0); bp.inputs['Distance'].default_value=E('BUMPK',0)/1000.0
        if os.environ.get('PROF')=='dome2':
            # smooth parabolic bulge (Poisson dome) scaled by the muscle's local half-width, crisp only at the border
            hw=udim('halfw','Cubic'); hsep=N.new('ShaderNodeSeparateColor'); L.new(hw.outputs['Color'],hsep.inputs[0])
            wv=M('MAXIMUM',M('MULTIPLY',hsep.outputs[0],64.0),2.0)
            dr_=udim('domeraw','Cubic'); dsep2=N.new('ShaderNodeSeparateColor'); L.new(dr_.outputs['Color'],dsep2.inputs[0])
            t16=udim('dh16','Cubic'); s16=N.new('ShaderNodeSeparateColor'); L.new(t16.outputs['Color'],s16.inputs[0]); dprof=M('ADD',M('MULTIPLY',s16.outputs[0],64.0),ladd)
            u16=udim('ds16','Cubic'); v16=N.new('ShaderNodeSeparateColor'); L.new(u16.outputs['Color'],v16.inputs[0]); dsprof=M('MULTIPLY',v16.outputs[0],64.0)
            prof=M('POWER',dsep2.outputs[0],E('DRP',1.0))
            prof=M('ADD',prof,M('MULTIPLY',M('SUBTRACT',1.0,prof),M('MULTIPLY',M('SUBTRACT',1.0,lstr),E('PFLAT',0.8))))
            edge=SS(dprof,0.0,E('CWB',3.0),E('EDGE0',0.0),1.0)
            soft_=SS(dsprof,0.0,E('SBW',6.0),E('SBD',0.75),1.0)
            hb=M('MULTIPLY',M('MULTIPLY',M('MULTIPLY',prof,wv),edge),soft_)
            _o=os.environ.get('HBONLY')
            if _o=='w': hb=M('MULTIPLY',wv,0.3)
            if _o=='p': hb=M('MULTIPLY',prof,20.0)
            if _o=='d': hb=dprof
            if _o=='e': hb=M('MULTIPLY',edge,10.0)
            hb=M('MULTIPLY',hb,M('SUBTRACT',1.0,M('MULTIPLY',tend,E('TBF',0.7))))
            hb=M('MULTIPLY',hb,M('SUBTRACT',1.0,SS(A('shorts').outputs['Fac'],0.3,0.6)))
            hb=M('MULTIPLY',hb,M('SUBTRACT',1.0,M('MULTIPLY',F('tfade'),E('TFB',0.75))))
            hb=M('MULTIPLY',hb,M('ADD',E('GBUMP',1.0),M('MULTIPLY',red,E('RBUMP',1.0)-E('GBUMP',1.0))))   # GBUMP / RBUMP: roundness of grey / red muscles
            hb=M('MULTIPLY',hb,npl)
            L.new(hb,bp.inputs['Height'])
        elif os.path.exists(os.path.join(MAPS,'halfw.1001.png')) and os.environ.get('PROF','round')=='round':
            # round cross-section: each muscle bulges like a cylinder of its own local width
            hw=udim('halfw','Cubic'); hsep=N.new('ShaderNodeSeparateColor'); L.new(hw.outputs['Color'],hsep.inputs[0])
            wv=M('MAXIMUM',M('MULTIPLY',hsep.outputs[0],64.0),2.0)
            if os.path.exists(os.path.join(MAPS,'dh16.1001.png')):
                t16=udim('dh16','Cubic'); s16=N.new('ShaderNodeSeparateColor'); L.new(t16.outputs['Color'],s16.inputs[0]); dprof=M('MULTIPLY',s16.outputs[0],64.0)
                u16=udim('ds16','Cubic'); v16=N.new('ShaderNodeSeparateColor'); L.new(u16.outputs['Color'],v16.inputs[0]); dsprof=M('MULTIPLY',v16.outputs[0],64.0)
            else: dprof=d; dsprof=ds
            s_=M('MINIMUM',M('DIVIDE',dprof,wv),1.0)
            arc=M('SQRT',M('SUBTRACT',1.0,M('POWER',M('SUBTRACT',1.0,s_),2.0)))      # circle profile 0..1
            arc=M('POWER',arc,E('ARCP',1.0))
            soft_=SS(dsprof,0.0,E('SBW',6.0),E('SBD',0.75),1.0)                         # soft dip along soft borders
            hb=M('MULTIPLY',M('MULTIPLY',arc,wv),soft_)
            hb=M('MULTIPLY',hb,M('SUBTRACT',1.0,M('MULTIPLY',tend,E('TBF',0.7))))
            hb=M('MULTIPLY',hb,M('SUBTRACT',1.0,SS(A('shorts').outputs['Fac'],0.3,0.6)))
            L.new(hb,bp.inputs['Height'])
        else:
            L.new(M('MULTIPLY',shape,damp_t),bp.inputs['Height'])
        nrm=bp.outputs['Normal']
    L.new(nrm,vt.inputs['Vector'])
    kx,ky,kz=E('MKX',-0.55),E('MKY',0.55),E('MKZ',0.62); kn=math.sqrt(kx*kx+ky*ky+kz*kz)
    dp=N.new('ShaderNodeVectorMath'); dp.operation='DOT_PRODUCT'; L.new(vt.outputs['Vector'],dp.inputs[0]); dp.inputs[1].default_value=(kx/kn,ky/kn,-kz/kn)    # camera space: surfaces facing the camera have normal z < 0
    lam=dp.outputs['Value']
    t=M('DIVIDE',M('ADD',lam,E('WRAP',0.6)),1.0+E('WRAP',0.6),True)
    fc=A('face').outputs['Fac']        # 1 on the head and the eyes (facebuild.py FACEATTR=1), 0 on the body (no such attribute)
    if E('EDGEK',0)>0:
        # per-muscle shading like a drawn plate: every muscle is darker/more intense along its border and fades to
        # light towards its middle; the band width follows the muscle's own width so it reads at any distance
        def _tex16(name,scale):
            tx_=udim(name,'Cubic'); sp__=N.new('ShaderNodeSeparateColor'); L.new(tx_.outputs['Color'],sp__.inputs[0]); return M('MULTIPLY',sp__.outputs[0],scale)
        ew=M('MAXIMUM',M('MULTIPLY',_tex16('halfw',64.0),M('ADD',E('EWF',0.75),M('MULTIPLY',red,E('EWFR',0.75)-E('EWF',0.75)))),E('EMM',5.0))
        eg=SS(M('MINIMUM',M('DIVIDE',M('ADD',_tex16('dh16',64.0),ladd),ew),1.0),0.0,1.0)
        eg=M('POWER',eg,E('EGP',0.8))
        if E('EROUND',0)>0:
            # rounded (dome) profile instead of a straight ramp: light quickly away from the border, broad soft middle,
            # so a long muscle does not get a crest along its middle ("tent" look)
            # EROUNDR: own value for the worked (red) muscles; lower = the gradient reaches the middle of the muscle
            eg=MIX(M('ADD',E('EROUND',0),M('MULTIPLY',red,E('EROUNDR',E('EROUND',0))-E('EROUND',0)),True),eg,M('SUBTRACT',1.0,M('POWER',M('SUBTRACT',1.0,eg),2.0)))
        egs=SS(M('MINIMUM',M('DIVIDE',_tex16('ds16',64.0),E('ESW',6.0)),1.0),0.0,1.0,E('ESOFT',0.7),1.0)
        eg=M('MULTIPLY',eg,egs)
        emin=M('ADD',E('EMIN',0.35),M('MULTIPLY',tend,E('ETMIN',0.75)-E('EMIN',0.35)))   # tendons: same gradient, softer
        emin=M('ADD',emin,M('MULTIPLY',red,E('ERMIN',0.35)-E('EMIN',0.35)))              # worked (red) muscles: own border depth
        ef=M('ADD',emin,M('MULTIPLY',eg,M('SUBTRACT',1.0,emin)))            # 1 in the middle, emin at the border
        ef=M('ADD',ef,M('MULTIPLY',SS(A('shorts').outputs['Fac'],0.3,0.6),M('SUBTRACT',1.0,ef)))   # not on the shorts
        ef=M('ADD',ef,M('MULTIPLY',M('MULTIPLY',F('tfade'),E('TFE',0.6)),M('SUBTRACT',1.0,ef)))       # lower forearm: tendons, lighter
        ef=M('ADD',ef,M('MULTIPLY',pln,M('SUBTRACT',1.0,ef)))                                 # plain skin (head): no border shading
        # border darkening mostly on the shadow (lower) side of each muscle: lit borders stay light, like the plates
        tl_=t
        sidew=SS(tl_,E('SIDEHI',0.75),E('SIDELO',0.35),1.0,0.0)                    # 1 in shadow, 0 in light
        smin=M('ADD',E('SIDEMIN',1.0),M('MULTIPLY',red,E('SIDEMINR',1.0)-E('SIDEMIN',1.0)))   # weight kept on the lit side
        sidew=M('ADD',smin,M('MULTIPLY',sidew,M('SUBTRACT',1.0,smin)))
        ef=M('SUBTRACT',1.0,M('MULTIPLY',M('SUBTRACT',1.0,ef),sidew))
        elt_=M('ADD',E('ELT',1.0),M('MULTIPLY',red,E('ELTR',E('ELT',1.0))-E('ELT',1.0)))   # ELTR: how much the light models the worked (red) muscles
        elt_=M('ADD',elt_,M('MULTIPLY',fc,E('FELT',E('ELT',1.0))-E('ELT',1.0)))             # FELT: the same for the face (planes of the face read)
        t=M('MULTIPLY',M('ADD',M('MULTIPLY',t,elt_),M('SUBTRACT',1.0,elt_)),ef)   # ELT<1 = less light, more drawing
        if os.environ.get('MDEBUG')=='eg': outdbg=eg
    if E('FCON',1.0)!=1.0:
        # face: more contrast between its light and dark planes (around FPIV), as in a drawn portrait
        _tc=M('ADD',M('MULTIPLY',M('SUBTRACT',t,E('FPIV',0.6)),E('FCON',1.0)),E('FPIV',0.6),True)
        t=M('ADD',t,M('MULTIPLY',fc,M('SUBTRACT',_tc,t)))
    rp=N.new('ShaderNodeValToRGB'); el=rp.color_ramp.elements; rp.color_ramp.interpolation='EASE' if os.environ.get('RAMPI','')=='ease' else 'LINEAR'
    stops=[float(x) for x in os.environ.get('TSTOPS','0.0,0.30,0.55,0.80,1.0').split(',')]
    tones=[float(x) for x in os.environ.get('TONES','0.30,0.48,0.72,0.92,1.0').split(',')]
    lin=lambda v: v**2.2                      # tones are given as screen (display) values
    el[0].position=stops[0]; el[0].color=(lin(tones[0]),)*3+(1,); el[1].position=stops[-1]; el[1].color=(lin(tones[-1]),)*3+(1,)
    for p_,t_ in zip(stops[1:-1],tones[1:-1]): e_=el.new(p_); e_.color=(lin(t_),)*3+(1,)
    L.new(t,rp.inputs['Fac'])
    # specular sheen: half vector between key and view (camera +z)
    hx,hy,hz=kx/kn,ky/kn,-(kz/kn+1.0); hn=math.sqrt(hx*hx+hy*hy+hz*hz)
    dh=N.new('ShaderNodeVectorMath'); dh.operation='DOT_PRODUCT'; L.new(vt.outputs['Vector'],dh.inputs[0]); dh.inputs[1].default_value=(hx/hn,hy/hn,hz/hn)
    spec=M('MULTIPLY',SS(dh.outputs['Value'],E('SP0',0.90),1.0),E('SPK',0.25))
    # silhouette: grey contour where the surface turns away from the camera
    sep=N.new('ShaderNodeSeparateXYZ'); L.new(vt.outputs['Vector'],sep.inputs[0])
    rimf=SS(M('MULTIPLY',sep.outputs['Z'],-1.0),E('MR0',0.0),E('MR1',0.30),E('MRC',0.55),1.0)
    shade=MIX(1.0,rp.outputs['Color'],G(rimf),'MULTIPLY')
    shade=MIX(1.0,shade,G(M('POWER',ao.outputs['AO'],E('MAOP',1.0))),'MULTIPLY')
    if E('FAOP',0)>0:
        # face: short-range occlusion (eye sockets, nostrils, under the lip, inside the ear, hairline step) -> depth
        ao2=N.new('ShaderNodeAmbientOcclusion'); ao2.inputs['Distance'].default_value=E('FAOD',0.02); ao2.samples=16
        shade=MIX(fc,shade,MIX(1.0,shade,G(M('POWER',ao2.outputs['AO'],E('FAOP',0))),'MULTIPLY'))
    albedo=MIX(1.0,col,G(1.0/max(E('SKC',0.88),1e-3)),'MULTIPLY')        # albedo normalised so white muscle = 1
    outc=MIX(1.0,albedo,shade,'MULTIPLY')
    if os.environ.get('REDRAMP','1')=='1':
        # worked muscles: shading goes from deep saturated red (shadow) to pale coral (light), never to brown/grey
        rr=N.new('ShaderNodeValToRGB'); re=rr.color_ramp.elements
        rstops=[float(x) for x in os.environ.get('RSTOPS','0.0,0.35,0.60,0.82,1.0').split(',')]
        rcols=[tuple(float(c)/255.0 for c in x.split('/')) for x in os.environ.get('RCOLS','140/55/38,182/82/56,222/112/78,238/150/112,248/195/165').split(',')]
        lin3=lambda c: tuple(v**2.2 for v in c)+(1,)
        re[0].position=rstops[0]; re[0].color=lin3(rcols[0]); re[1].position=rstops[-1]; re[1].color=lin3(rcols[-1])
        for p_,c_ in zip(rstops[1:-1],rcols[1:-1]): e_=re.new(p_); e_.color=lin3(c_)
        tr_=M('ADD',M('MULTIPLY',M('SUBTRACT',t,E('RPIV',0.5)),E('REDCON',1.0)),E('RPIV',0.5),True)
        L.new(tr_,rr.inputs['Fac'])
        # keep the red pattern (fibre streaks, darker grooves) as a relative factor of the plain red albedo
        rpat=MIX(1.0,redb,C('REDINV','%f,%f,%f'%(1/0.86,1/0.26,1/0.15)),'MULTIPLY')
        rsh=MIX(1.0,rr.outputs['Color'],rpat,'MULTIPLY')
        rsh=MIX(1.0,rsh,G(rimf),'MULTIPLY'); rsh=MIX(1.0,rsh,G(M('POWER',ao.outputs['AO'],E('MAOP',1.0))),'MULTIPLY')
        # SHRED>0: worked muscles under the shorts show through the fabric (e.g. glutes in a deadlift)
        outc=MIX(M('MULTIPLY',red,M('SUBTRACT',1.0,M('MULTIPLY',sh,1.0-E('SHRED',0.0)))),outc,rsh)
    # face: hair, eyebrows, irises / pupils darker (attribute 'tint' 0..1 on the head objects; 0 on the body)
    _tn=A('tint').outputs['Fac']
    if E('BROWSTK',0.55)>0:
        # eyebrow hair strokes: thin stripes across 'bw' (mm), broken by noise; stronger at the brow's soft edges
        _bm=A('bmask').outputs['Fac']; _nz=N.new('ShaderNodeTexNoise'); _nz.inputs['Scale'].default_value=E('BRNZ',260.0)
        _ph=M('ADD',M('DIVIDE',A('bw').outputs['Fac'],E('BRSW',0.55)),M('MULTIPLY',_nz.outputs['Fac'],E('BRJ',0.9)))
        _st=SS(M('SINE',M('MULTIPLY',_ph,2*math.pi)),-0.3,0.5)                  # 1 on a hair, 0 between hairs
        _nb=N.new('ShaderNodeTexNoise'); _nb.inputs['Scale'].default_value=E('BRNB',1400.0)
        _st=M('MULTIPLY',_st,SS(_nb.outputs['Fac'],0.32,0.55,0.35,1.0))         # hairs of different lengths
        _edge=M('SUBTRACT',1.0,SS(_bm,0.55,0.95))                                 # sparse hairs at the edges
        _k=M('MULTIPLY',E('BROWSTK',0.55),M('ADD',0.35,M('MULTIPLY',_edge,0.65)))
        _tn=M('MULTIPLY',_tn,M('SUBTRACT',1.0,M('MULTIPLY',M('MULTIPLY',_k,M('SUBTRACT',1.0,_st)),SS(_bm,0.02,0.2))))
    if E('HAIRSTK',0.45)>0:
        # long hair pulled back: strands converging on the bun ('hw' across the strands, mm), broken by noise
        _hm=A('hmask').outputs['Fac']; _nh=N.new('ShaderNodeTexNoise'); _nh.inputs['Scale'].default_value=E('HRNZ',180.0)
        _hp=M('ADD',M('DIVIDE',A('hw').outputs['Fac'],E('HRSW',0.9)),M('MULTIPLY',_nh.outputs['Fac'],E('HRJ',1.2)))
        _hs=SS(M('SINE',M('MULTIPLY',_hp,2*math.pi)),-0.4,0.7)
        _nh2=N.new('ShaderNodeTexNoise'); _nh2.inputs['Scale'].default_value=E('HRNB',420.0)
        _hs=M('MULTIPLY',_hs,SS(_nh2.outputs['Fac'],0.35,0.6,0.45,1.0))           # strands of uneven brightness
        _tn=M('MULTIPLY',_tn,M('SUBTRACT',1.0,M('MULTIPLY',M('MULTIPLY',E('HAIRSTK',0.45),M('SUBTRACT',1.0,_hs)),SS(_hm,0.05,0.4))))
    if E('HSTK',0)>0:
        # short hair (skin fade): fine grain x soft clumps on the hair darkness, fixed to the head ('hrest' = rest position)
        _hc=A('hrest').outputs['Vector']
        _s1=N.new('ShaderNodeTexNoise'); L.new(_hc,_s1.inputs['Vector']); _s1.inputs['Scale'].default_value=E('HSTS',1400.0); _s1.inputs['Detail'].default_value=1.0
        _s2=N.new('ShaderNodeTexNoise'); L.new(_hc,_s2.inputs['Vector']); _s2.inputs['Scale'].default_value=E('HSTS2',260.0); _s2.inputs['Detail'].default_value=2.0
        _g=M('MULTIPLY',SS(_s1.outputs['Fac'],E('HST0',0.35),E('HST1',0.65)),SS(_s2.outputs['Fac'],0.25,0.75,E('HSTC',0.75),1.0))
        _tn=M('MULTIPLY',_tn,M('SUBTRACT',1.0,M('MULTIPLY',M('MULTIPLY',A('hstip').outputs['Fac'],E('HSTK',0)),M('SUBTRACT',1.0,_g))))
    outc=MIX(_tn,outc,MIX(1.0,G(E('TINTV',0.05)),shade,'MULTIPLY'))   # TINTV is linear (0.05 ~ dark grey on screen)
    outc=MIX(A('glint').outputs['Fac'],outc,G(1.0))                    # eyes: catchlight and brighter white (facebuild.py EYEV2=1)
    outc=MIX(1.0,outc,G(spec),'ADD')
    if os.environ.get('MDEBUG')=='n':
        mp=N.new('ShaderNodeVectorMath'); mp.operation='MULTIPLY_ADD'; L.new(vt.outputs['Vector'],mp.inputs[0]); mp.inputs[1].default_value=(0.5,0.5,0.5); mp.inputs[2].default_value=(0.5,0.5,0.5)
        outc=mp.outputs['Vector']
    if os.environ.get('MDEBUG')=='t': outc=G(t)
    if os.environ.get('MDEBUG')=='fc': outc=G(fc)
    if os.environ.get('MDEBUG')=='eg': outc=G(outdbg)
    if os.environ.get('MDEBUG')=='red': outc=G(red)
    if os.environ.get('MDEBUG')=='lstr': outc=G(lstr) if not isinstance(lstr,float) else G(1.0)
    if os.environ.get('MDEBUG')=='dh': outc=G(SS(d,0.0,3.0,0.0,1.0))
    if os.environ.get('MDEBUG')=='s': outc=shade
    if os.environ.get('MDEBUG')=='lab':
        lt_=udim('lab','Closest'); ls_=N.new('ShaderNodeSeparateColor'); L.new(lt_.outputs['Color'],ls_.inputs[0])
        hsv=N.new('ShaderNodeCombineColor'); hsv.mode='HSV'; L.new(M('FRACT',M('MULTIPLY',M('SINE',M('MULTIPLY',ls_.outputs[0],255*12.9898)),43758.5453)),hsv.inputs[0]); hsv.inputs[1].default_value=0.6; hsv.inputs[2].default_value=0.9
        outc=MIX(1.0,hsv.outputs[0],G(M('POWER',SS(d,0.0,1.0),1.0)),'MULTIPLY')
    if os.environ.get('MDEBUG')=='tm':
        cc=N.new('ShaderNodeCombineColor'); L.new(t,cc.inputs[0]); L.new(F('armmask'),cc.inputs[1]); L.new(red,cc.inputs[2]); outc=cc.outputs[0]
    if os.environ.get('MDEBUG')=='a': outc=albedo
    if os.environ.get('MDEBUG')=='plain': outc=G(pln)
    if os.environ.get('MDEBUG')=='hb': outc=G(M('MULTIPLY',hb,0.1))
    if os.environ.get('MDEBUG')=='h': outc=G(M('ADD',M('MULTIPLY',h,0.2),0.5))
    if os.environ.get('MDEBUG')=='snap':      # head band glued to the neck: red = band weight, green = head (hrest present), blue = plain
        _cc=N.new('ShaderNodeCombineColor'); L.new(A('snapw').outputs['Fac'],_cc.inputs[0]); L.new(M('MINIMUM',M('MULTIPLY',M('ABSOLUTE',N.new('ShaderNodeSeparateXYZ').outputs[2]),0.0),1.0),_cc.inputs[1]); L.new(SS(A('hstip').outputs['Fac'],-1.0,1.0,0.3,1.0),_cc.inputs[2]); outc=_cc.outputs[0]
    em=N.new('ShaderNodeEmission'); L.new(outc,em.inputs['Color']); em.inputs['Strength'].default_value=1.0
    L.new(em.outputs[0],N['Material Output'].inputs['Surface'])
rg_=MIX(sh,G(E('ROUGH',0.55)),G(0.42)); sp2=N.new('ShaderNodeSeparateColor'); L.new(rg_,sp2.inputs[0]); L.new(sp2.outputs[0],bs.inputs['Roughness'])
me.materials.clear(); me.materials.append(m)
for p in me.polygons: p.material_index=0
for o in bpy.data.objects:
    if o.type=='MESH' and o.name in ('Discos','Barra'):
        mm=bpy.data.materials.new(o.name+'_m'); b2=mm.node_tree.nodes['Principled BSDF']
        if o.name=='Discos': b2.inputs['Base Color'].default_value=(0.025,0.025,0.025,1); b2.inputs['Roughness'].default_value=0.55
        else: b2.inputs['Base Color'].default_value=(0.35,0.35,0.36,1); b2.inputs['Metallic'].default_value=0.8; b2.inputs['Roughness'].default_value=0.35
        o.data.materials.clear(); o.data.materials.append(mm)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=int(E('SMP',32)); sc.cycles.device='CPU'
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'; sc.view_settings.exposure=E('EXPO',0.6)
sc.cycles.use_denoising=True; sc.render.threads_mode='FIXED'; sc.render.threads=int(E('THREADS',4))
w=bpy.data.worlds.new('w'); w.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value=E('AMB',0.25); sc.world=w
_y=math.radians(E('YAW',0))
def rot(x,y,z): return (x*math.cos(_y)-y*math.sin(_y), x*math.sin(_y)+y*math.cos(_y), z)
def light(loc,e,sz=3.0):
    l=bpy.data.lights.new('L','AREA'); l.energy=e; l.size=sz; o=bpy.data.objects.new('L',l); o.location=loc; sc.collection.objects.link(o)
    from mathutils import Vector; dd=Vector((E('TX',0),E('TY',0),E('TZ',0.9)))-o.location; o.rotation_euler=(-dd).to_track_quat('Z','Y').to_euler()
K=E('LK',0.3)
light(rot(E('KX',-3.0),E('KY',-2.0),E('KZ',3.4)),E('LKEY',450)*K,E('KSZ',2.5)); light(rot(3,-2.5,1.0),E('LFILL',40)*K); light(rot(0.5,3,2.5),E('LBACK',50)*K)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
yaw=math.radians(E('YAW',0)); pit=math.radians(E('PIT',10)); T=(E('TX',0),E('TY',-0.02),E('TZ',0.9)); dist=6
cam.location=(T[0]+dist*math.sin(yaw)*math.cos(pit), T[1]-dist*math.cos(yaw)*math.cos(pit), T[2]+dist*math.sin(pit))
cam.rotation_euler=(math.radians(90)-pit,0,yaw); cam.data.type='ORTHO'; cam.data.ortho_scale=E('OSC',2.0)
sc.render.film_transparent=True; r_=int(E('RES',800)); sc.render.resolution_x=sc.render.resolution_y=r_
if E('RX',0)>0: sc.render.resolution_x=int(E('RX',0)); sc.render.resolution_y=int(E('RY',0))   # e.g. 1920x1080 (OSC = view width)
# ---- face (objects 'Cabeza', 'Ojo.L', 'Ojo.R' from facebuild.py): bake their skinning, glue the lowest band of the
# head onto the posed neck of 'Hi' (no visible joint), same material with a constant UV taken from the crown of the
# mannequin head (plain skin there: no muscle lines), optional subdivision
_heads=[o for o in bpy.data.objects if o.type=='MESH' and (o.name=='Cabeza' or o.name.startswith('Ojo.')) and not o.hide_render]
if _heads:
    from mathutils.bvhtree import BVHTree
    _dg=bpy.context.evaluated_depsgraph_get()
    _bvh=BVHTree.FromObject(ob,_dg)
    _vi=np.zeros(len(me.loops),int); me.loops.foreach_get('vertex_index',_vi)
    _uv=np.zeros(len(me.loops)*2); me.uv_layers['UVMap'].data.foreach_get('uv',_uv); _uv=_uv.reshape(-1,2)
    _top=int(np.argmax(np.where(np.array([str(x)=='head' for x in _rest['main']]),np.array(_rest['co'])[:,2],-9)))
    _cuv=_uv[np.where(_vi==_top)[0][0]]
    # Cabeza takes the drawing of the body skin underneath (UVs per face from ONE body triangle, so no jumps at UV seams,
    # and the per-vertex body attributes): the neck lines, fibres and shading continue across the joint
    _uvt=np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),'uvtri.npz')); _tv=_uvt['tv']; _tuv=_uvt['tuv']
    from mathutils import Vector as _V
    _rco=np.array(_rest['co'])
    _tbvh=BVHTree.FromPolygons([tuple(p) for p in _rco],[tuple(int(i) for i in t) for t in _tv])
    def _bary(P,t):
        a,b,c=_rco[_tv[t]]; v0=b-a; v1=c-a; v2=P-a
        d00=v0@v0; d01=v0@v1; d11=v1@v1; d20=v2@v0; d21=v2@v1; den=max(d00*d11-d01*d01,1e-18)
        v=(d11*d20-d01*d21)/den; w=(d00*d21-d01*d20)/den; return np.array((1-v-w,v,w))
    def _clampbary(P,t):
        """barycentric coordinates of the point of triangle t nearest to P (never outside the triangle)"""
        a,b,c=_rco[_tv[t]]; ab=b-a; ac=c-a; ap=P-a; d1=ab@ap; d2=ac@ap
        if d1<=0 and d2<=0: return np.array((1.0,0,0))
        bp=P-b; d3=ab@bp; d4=ac@bp
        if d3>=0 and d4<=d3: return np.array((0,1.0,0))
        vc=d1*d4-d3*d2
        if vc<=0 and d1>=0 and d3<=0: v=d1/(d1-d3); return np.array((1-v,v,0))
        cp=P-c; d5=ab@cp; d6=ac@cp
        if d6>=0 and d5<=d6: return np.array((0,0,1.0))
        vb_=d5*d2-d1*d6
        if vb_<=0 and d2>=0 and d6<=0: w=d2/(d2-d6); return np.array((1-w,0,w))
        va=d3*d6-d5*d4
        if va<=0 and (d4-d3)>=0 and (d5-d6)>=0: w=(d4-d3)/((d4-d3)+(d5-d6)); return np.array((0,1-w,w))
        den=1.0/(va+vb_+vc); v=vb_*den; w=vc*den; return np.array((1-v-w,v,w))
    _islc=[]
    def _islands():
        """UV island of every body triangle (triangles that share a vertex with the same UV belong together)"""
        if not _islc:
            from scipy.sparse import coo_matrix; from scipy.sparse.csgraph import connected_components
            nt_=len(_tv); key=np.concatenate([_tv.reshape(-1,1).astype(np.float64),np.round(_tuv.reshape(-1,2),5)],1)
            _,uid=np.unique(key,axis=0,return_inverse=True); uid=np.asarray(uid).ravel(); nu=int(uid.max())+1
            rows=np.repeat(np.arange(nt_),3); g=coo_matrix((np.ones(len(rows)),(rows,nt_+uid)),shape=(nt_+nu,nt_+nu))
            _islc.append(connected_components(g,directed=False)[1][:nt_])
        return _islc[0]
    def _transfer(o):
        hm=o.data; n_=len(hm.vertices); rc=np.zeros(n_*3); hm.vertices.foreach_get('co',rc); rc=rc.reshape(-1,3)
        vt=np.zeros(n_,int); vb=np.zeros((n_,3))
        for i in range(n_):
            loc,nrm,t,_=_tbvh.find_nearest(_V(rc[i])); vt[i]=t; vb[i]=_bary(np.array(loc),t)
        for k in list(have):
            src=me.attributes.get(k)
            if src is None or src.domain!='POINT': continue
            if src.data_type=='FLOAT':
                v=np.zeros(nv); src.data.foreach_get('value',v); val=(v[_tv[vt]]*vb).sum(1)
                a_=hm.attributes.get(k) or hm.attributes.new(k,'FLOAT','POINT'); a_.data.foreach_set('value',val.astype(np.float32))
            elif src.data_type=='FLOAT_VECTOR':
                v=np.zeros(nv*3); src.data.foreach_get('vector',v); v=v.reshape(-1,3); val=(v[_tv[vt]]*vb[:,:,None]).sum(1)
                a_=hm.attributes.get(k) or hm.attributes.new(k,'FLOAT_VECTOR','POINT'); a_.data.foreach_set('vector',val.astype(np.float32).ravel())
        if NEWHEAD and os.path.exists(_abl) and E('HEADTRAP',0)>0:      # off since 13-11-2026: the neck drawing fades out before the head (NECKFADE)
            # the trapezius keeps its drawing (and its red) on the head: it goes up the nape to the skull. 'plainh' is 1
            # everywhere on the head except where the skin underneath is labelled trapezius (smooth 0.2..0.8 of the label)
            _ab3=np.load(_abl,allow_pickle=True); _lb3=np.array([str(x) for x in _ab3['names']])[_ab3['mid'].astype(int)]
            if len(_lb3)==nv:
                _tr3=(np.char.startswith(_lb3,'trap').astype(float)[_tv[vt]]*vb).sum(1); _tr3=np.clip((_tr3-0.2)/0.6,0,1); _tr3=_tr3*_tr3*(3-2*_tr3)
                a_=hm.attributes.get('plainh') or hm.attributes.new('plainh','FLOAT','POINT'); a_.data.foreach_set('value',(1.0-_tr3).astype(np.float32))
        if E('PLH1',0)>0 and os.path.exists(_abl):
            # 'plainh' (12-11-2026): on the head the copied neck drawing fades to plain skin before it reaches the
            # unlabelled skin of the head. In the atlas the sternocleidomastoid ends under the ear / jaw in a ragged
            # edge (raw label border along the body's coarse triangles); on the body it is hidden inside the head, but
            # the head band showed it as a saw-tooth line. 1 up to PLH0 m from that skin, 0 from PLH1 m on; the
            # trapezius keeps its drawing up to the skull.
            from scipy.spatial import cKDTree as _KD2
            _ab2=np.load(_abl,allow_pickle=True); _lb2=np.array([str(x) for x in _ab2['names']])[_ab2['mid'].astype(int)]
            _mn2=np.array([str(x) for x in _rest['main']])
            if len(_lb2)==nv:
                _nn=(((_lb2=='none')&(_mn2=='head')).astype(float)[_tv[vt]]*vb).sum(1); _tr=(np.char.startswith(_lb2,'trap').astype(float)[_tv[vt]]*vb).sum(1)
                _sd=_nn>0.5
                if _sd.any():
                    _dd=_KD2(rc[_sd]).query(rc)[0]
                    _ph=1.0-np.clip((_dd-E('PLH0',0.0015))/(E('PLH1',0)-E('PLH0',0.0015)),0,1); _ph=_ph*_ph*(3-2*_ph)*(1-np.clip(_tr,0,1))
                    a_=hm.attributes.get('plainh') or hm.attributes.new('plainh','FLOAT','POINT'); a_.data.foreach_set('value',_ph.astype(np.float32))
        if not hm.uv_layers: hm.uv_layers.new(name='UVMap')
        uvd=np.zeros((len(hm.loops),2)); lv=np.zeros(len(hm.loops),int); hm.loops.foreach_get('vertex_index',lv)
        # FACEUVV=1 (12-11-2026): UV per VERTEX (its own nearest body triangle), so the drawing is continuous from face to
        # face. Before, every face took the UVs of ONE body triangle (extrapolated). The body's UV map has a seam all
        # round the neck, 0-4 mm above the cut of the head (the head is its own UV island): the head band crosses it,
        # the faces on either side took triangles of different islands and, the seam running along the body's coarse
        # edges, the band showed a saw-tooth line. Now: a face whose vertices all land on one island uses their own UVs;
        # a face that straddles the seam is kept on the island of its centre, and its vertices on the other island are
        # clamped to the nearest point of that triangle (no extrapolation outside the island).
        if E('FACEUVV',1 if NEWHEAD else 0)>0:
            _isl=_islands(); _uvv=np.einsum('ij,ijk->ik',vb,_tuv[vt]); _iv=_isl[vt]; _nfb=0
            for p_ in hm.polygons:
                ls=list(p_.loop_indices); vs=lv[ls]; u_=_uvv[vs]
                if (_iv[vs]==_iv[vs[0]]).all() and np.abs(u_-u_.mean(0)).max()<E('FACEUVJ',0.03): uvd[ls]=u_; continue
                _nfb+=1; cen=rc[vs].mean(0); _,_,t,_=_tbvh.find_nearest(_V(cen))
                for li,v_ in zip(ls,vs):
                    uvd[li]=_uvv[v_] if (_iv[v_]==_isl[t] and np.abs(_uvv[v_]-_tuv[t].mean(0)).max()<E('FACEUVJ',0.03)) else _clampbary(rc[v_],t)@_tuv[t]
            print('face UV per vertex: %d of %d faces straddle a UV seam (clamped to one island)'%(_nfb,len(hm.polygons)))
        else:
            for p_ in hm.polygons:
                ls=list(p_.loop_indices); cen=rc[lv[ls]].mean(0); _,_,t,_=_tbvh.find_nearest(_V(cen))
                for li in ls: uvd[li]=_bary(rc[lv[li]],t)@_tuv[t]
        hm.uv_layers[0].data.foreach_set('uv',uvd.ravel())
    # the lowest band of the head fades out (transparent) over the identical neck skin underneath: no visible edge
    _out=N['Material Output']; _lk=[l for l in nt.links if l.to_node==_out and l.to_socket.name=='Surface']
    if _lk and E('FACEFADE',0)>0:
        _srcs=_lk[0].from_socket; nt.links.remove(_lk[0])
        _tr=N.new('ShaderNodeBsdfTransparent'); _mx=N.new('ShaderNodeMixShader')
        _fa=SS(A('snapw').outputs['Fac'],E('FADE0',0.25),E('FADE1',0.85))
        L.new(_fa,_mx.inputs[0]); L.new(_srcs,_mx.inputs[1]); L.new(_tr.outputs[0],_mx.inputs[2]); L.new(_mx.outputs[0],_out.inputs['Surface'])
    from mathutils import Vector as _V2
    _snaph=float(_cab.get('snaph',0.012)) if _cab is not None else 0.012
    _nfk=float(_cab.get('nfk',0.0)) if (_cab is not None and NEWHEAD) else 0.0     # > 0: head built with the neck fit (facebuild.py NECKFIT)
    def _resth(w_):
        """rest height over the cut of the head (m) from 'snapw' (inverse of its smoothstep)"""
        return _snaph*(0.5+np.sin(np.arcsin(np.clip(1-2*w_,-1,1))/3))
    def _glue(hc,_hn,w_):
        """glue the lowest band of the head (weights 'snapw') onto the posed neck skin; hc is changed in place"""
        _ray=E('FACERAY',0)>0
        if _nfk>0:
            # (13-11-2026) head built with the neck fit: its stump already lies on the neck skin with the same slope,
            # lifting off it like a thin wedge (NFK mm per mm of height). The glue only keeps that true on the posed,
            # subdivided body: over the lowest FACEGH m the band goes to FACEOFF0 + FACEK.h over the neck skin (weight
            # 1 at the edge -> 0 at FACEGH, where the hidden cap of the mannequin head starts to dive inside), and
            # nowhere lower than half of that. FACEOFF0 is NEGATIVE: the very edge of the head is 0.02 mm UNDER the neck
            # skin and the head comes out of it 0.3 mm higher, at 3 deg. There is no step at all (any step, even 0.05 mm
            # where the straight edge bridged a hollow of the nape, cast a hair-thin line of occlusion shadow), and a few
            # mm higher the two skins are far enough apart not to interleave.
            _hh=_resth(w_); _wg=np.clip(1-_hh/E('FACEGH',0.008),0,1); _wg=_wg*_wg*(3-2*_wg); _k=E('FACEK',_nfk); _o0=E('FACEOFF0',-0.00002)
        for i in np.where(w_>1e-3)[0]:
            loc=None
            if _ray:
                _r=_bvh.ray_cast(_V2(hc[i]+_hn[i]*0.03),_V2(-_hn[i]),0.07)
                if _r[0] is not None: loc=np.array(_r[0]); nrm=_hn[i]
            if loc is None:
                loc,nrm,_,_=_bvh.find_nearest(hc[i])
                if loc is None: continue
            loc=np.array(loc); nrm=np.array(nrm)
            if _nfk>0:
                # towards the neck skin + wedge: a vertex that is too LOW is lifted with the full weight of the band; one
                # that is too HIGH is brought down only on the lowest FACEG2 m (the edge must touch the skin; higher up
                # the head keeps its own line and does not follow the hidden skin where that bends in under it)
                _c=_o0+_k*_hh[i]; _s=float((hc[i]-loc)@nrm); _u=min(max(1-_hh[i]/E('FACEG2',0.0006),0.0),1.0); _u=_u*_u*(3-2*_u)
                if float(np.linalg.norm(hc[i]-loc))<0.004: hc[i]=hc[i]+nrm*((_c-_s)*(_wg[i] if _s<_c else _u))
                _s=float((hc[i]-loc)@nrm); _fm=_o0+0.5*_k*min(_hh[i],E('FACEGH',0.008))
                if _s<_fm and float(np.linalg.norm(hc[i]-loc))<0.002: hc[i]=hc[i]+nrm*(_fm-_s)
                continue
            # new-style head: the edge of the band stays FACEOFF0 over the neck and no band vertex ends up lower than
            # FACEMIN over the neck skin. 13-11-2026: 0.03 mm (with 0.6 mm, and still with 0.15, that little step cast a thin
            # line of ambient-occlusion shadow on the neck all along the edge; now both skins look the same there -
            # plain, same normals - so it no longer matters if they interleave a little)
            q=loc+nrm*(E('FACEOFF',0.0006)*(1-w_[i])+E('FACEOFF0',0.00003 if NEWHEAD else 0.0)*w_[i]); hc[i]=hc[i]+(q-hc[i])*w_[i]
            _fm=E('FACEMIN',0.00003 if NEWHEAD else -1.0)
            if _fm>-1.0:
                _s=float((hc[i]-loc)@nrm)
                if _s<_fm: hc[i]=hc[i]+nrm*(_fm-_s)
    for o in _heads:
        if o.name=='Cabeza' and E('FACEUV',1)>0:
            _transfer(o); o.data.update(); bpy.context.view_layer.update(); _dg=bpy.context.evaluated_depsgraph_get(); _dg.update()
        oe=o.evaluated_get(_dg); nm=bpy.data.meshes.new_from_object(oe,preserve_all_data_layers=True,depsgraph=_dg)
        o.modifiers.clear(); o.data=nm; o.matrix_world=o.matrix_world
        n_=len(nm.vertices); hc=np.zeros(n_*3); nm.vertices.foreach_get('co',hc); hc=hc.reshape(-1,3)
        if 'snapw' in nm.attributes:
            w_=np.zeros(n_); nm.attributes['snapw'].data.foreach_get('value',w_)
            # FACERAY=1 (12-11-2026): the neck skin under each band vertex is found with a ray along the head's own normal,
            # from outside inwards (first hit = the OUTER skin of the neck). With the nearest point (before) a vertex
            # could be pulled either to the neck skin or to the cap of the mannequin head that dives inside just above:
            # neighbours alternated and the band came out as a saw-tooth line 3-6 mm above the edge of the head.
            _hn=np.zeros(n_*3); nm.vertices.foreach_get('normal',_hn); _hn=_hn.reshape(-1,3)
            if os.environ.get('JOINTDBG') and o.name=='Cabeza':
                _hh0=_resth(w_)*1000; _i0=np.where(w_>1e-3)[0]; _s0=np.zeros(len(_i0))
                for k_,i in enumerate(_i0):
                    loc,nrm,_,_=_bvh.find_nearest(hc[i]); _s0[k_]=float((hc[i]-np.array(loc))@np.array(nrm))*1000
                _a0=np.abs(np.degrees(np.arctan2(hc[_i0][:,0]-hc[_i0][:,0].mean(),-(hc[_i0][:,1]-hc[_i0][:,1].mean()))))
                for a0,a1 in ((0,30),(30,60),(60,90),(90,120),(120,150),(150,181)):
                    print('JOINTDBG before the glue: ang %3d-%3d  head over neck skin (mm)  '%(a0,a1)+'  '.join('h %g-%g: %+.2f..%+.2f'%(h0,h1,_s0[(_a0>=a0)&(_a0<a1)&(_hh0[_i0]>=h0)&(_hh0[_i0]<h1)].min(),_s0[(_a0>=a0)&(_a0<a1)&(_hh0[_i0]>=h0)&(_hh0[_i0]<h1)].max()) for h0,h1 in ((0,1),(1,3),(3,6),(6,8)) if ((_a0>=a0)&(_a0<a1)&(_hh0[_i0]>=h0)&(_hh0[_i0]<h1)).any()))
            if o.name=='Cabeza' and _nfk>0 and E('JOINTBODY',1)>0:
                # (13-11-2026) the same two touches facebuild.py gives the neck at rest, again on the POSED body: a pose
                # moves the neck skin with the shoulders and leaves it a few degrees off the line of the head (a fine
                # crease along the joint in the close-ups). The last JBT m of visible neck under the cut turn onto the
                # plane of the head skin above them (all the way at the cut, nothing JBT lower), and the hidden skin of
                # the lowest JBS m over the cut goes half the wedge under the head. Only body vertices within 6 mm of the
                # head; at rest they hardly move.
                _pl=[tuple(p_.vertices) for p_ in nm.polygons]; _hb=BVHTree.FromPolygons([tuple(v) for v in hc],_pl)
                _bc=np.zeros(nv*3); me.vertices.foreach_get('co',_bc); _bc=_bc.reshape(-1,3); _b0=_bc.copy()
                _hdr=_co[:,2]-(_cz+_cs*(_co[:,1]+0.08)); _D=E('JBT',0.006); _Sj=E('JBS',0.005); _dj=np.zeros((nv,3)); _vis=np.zeros(nv,bool)
                for i in np.where((_hdr>-_D)&(_hdr<=_Sj)&(np.hypot(_co[:,0],_co[:,1]+0.03)<0.11))[0]:
                    loc,nrm,fi_,dist=_hb.find_nearest(_bc[i])
                    if loc is None or dist>0.006: continue
                    loc=np.array(loc); vs_=list(_pl[fi_])               # smooth normal of the head skin there (not the flat face: no facets)
                    wv_=1.0/np.maximum(np.linalg.norm(hc[vs_]-loc,axis=1),1e-5); nrm=(_hn[vs_]*wv_[:,None]).sum(0); nrm=nrm/max(np.linalg.norm(nrm),1e-12)
                    d_=float((_bc[i]-loc)@nrm)
                    if _hdr[i]<=0.0003: v_=min(max(1+_hdr[i]/_D,0.0),1.0); _dj[i]=-nrm*d_*v_*v_*(3-2*v_); _vis[i]=True
                    else: t_=min(_hdr[i]/0.003,1.0); _dj[i]=-nrm*(d_+E('JBD',0.0003)*t_*t_*(3-2*t_)+0.5*_nfk*_hdr[i])      # hidden: up to JBD under the band, from 3 mm over the cut (clear of it once both are subdivided)
                _ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',_ed); _ed=_ed.reshape(-1,2); _ed=_ed[_vis[_ed[:,0]]&_vis[_ed[:,1]]]
                for _ in range(int(E('JBSM',2))):                         # the turn of the visible neck, smoothed along the skin
                    _ac=_dj.copy(); _cn=np.ones(nv); np.add.at(_ac,_ed[:,0],_dj[_ed[:,1]]); np.add.at(_ac,_ed[:,1],_dj[_ed[:,0]]); np.add.at(_cn,_ed[:,0],1); np.add.at(_cn,_ed[:,1],1)
                    _dj[_vis]=(_ac/_cn[:,None])[_vis]
                _bc=_bc+_dj
                me.vertices.foreach_set('co',_bc.ravel()); me.update(); bpy.context.view_layer.update(); _dg=bpy.context.evaluated_depsgraph_get(); _dg.update()
                _bvh=BVHTree.FromObject(ob,_dg)
                print('joint: neck skin turned onto the line of the posed head, max move %.2f mm'%(np.linalg.norm(_bc-_b0,axis=1).max()*1000))
            _glue(hc,_hn,w_)
            nm.vertices.foreach_set('co',hc.ravel()); nm.update()
        if not (o.name=='Cabeza' and E('FACEUV',1)>0):
            if not nm.uv_layers: nm.uv_layers.new(name='UVMap')
            u_=np.tile(_cuv,(len(nm.loops),1)); nm.uv_layers[0].data.foreach_set('uv',u_.ravel())
        nm.materials.clear(); nm.materials.append(m)
        for p_ in nm.polygons: p_.use_smooth=True; p_.material_index=0
        if os.environ.get('FACEDBG'):
            _u=np.zeros(len(nm.loops)*2); nm.uv_layers[0].data.foreach_get('uv',_u)
            print('FACEDBG',o.name,'attrs',[a.name for a in nm.attributes],'uv range',_u.min().round(3),_u.max().round(3),'have',sorted(have))
        if o.name=='Cabeza' and E('FACESUB',1)>0:
            s_=o.modifiers.new('sub','SUBSURF'); s_.levels=s_.render_levels=int(E('FACESUB',1))
            if NEWHEAD and E('FACENRM',1)>0 and 'snapw' in nm.attributes:
                # (13-11-2026) along the joint the head takes the NORMALS of the neck skin under it (weight from 'snapw': all
                # on the lowest ~7 mm, none 1.2 cm higher): the light falls the same on both sides of the edge, so no tone step.
                # The subdivision is applied first, so the rest of the head keeps exactly its own normals.
                bpy.context.view_layer.update(); _dg2=bpy.context.evaluated_depsgraph_get(); _dg2.update()
                nm2=bpy.data.meshes.new_from_object(o.evaluated_get(_dg2),preserve_all_data_layers=True,depsgraph=_dg2)
                o.modifiers.clear(); o.data=nm2; n2=len(nm2.vertices)
                c2=np.zeros(n2*3); nm2.vertices.foreach_get('co',c2); c2=c2.reshape(-1,3)
                vn2=np.zeros(n2*3); nm2.vertices.foreach_get('normal',vn2); vn2=vn2.reshape(-1,3)
                w2=np.zeros(n2); nm2.attributes['snapw'].data.foreach_get('value',w2); _bi=np.where(w2>1e-3)[0]
                if _nfk>0 and E('FACEGLUE2',1)>0:
                    # second pass of the glue on the subdivided head: the subdivision rounds the band off the neck skin
                    # by up to a few tenths of mm (edge included); this puts every new vertex back at its exact height
                    _glue(c2,vn2,w2); nm2.vertices.foreach_set('co',c2.ravel()); nm2.update(); nm2.vertices.foreach_get('normal',vn2.reshape(-1))
                _em=ob.evaluated_get(_dg2).data; ne_=len(_em.vertices)
                _ev=np.zeros(ne_*3); _em.vertices.foreach_get('co',_ev); _ev=_ev.reshape(-1,3)
                _lo=c2[_bi].min(0)-0.02; _hi=c2[_bi].max(0)+0.02; _sel=np.where(np.all((_ev>_lo)&(_ev<_hi),1))[0]
                _en=np.zeros(ne_*3); _em.vertices.foreach_get('normal',_en); _en=_en.reshape(-1,3)[_sel]
                from scipy.spatial import cKDTree as _KDn
                _dd,_ii=_KDn(_ev[_sel]).query(c2[_bi],k=4); _wk=1.0/np.maximum(_dd,1e-5)**2
                _nb=(_en[_ii]*_wk[:,:,None]).sum(1); _nb/=np.maximum(np.linalg.norm(_nb,axis=1,keepdims=True),1e-12)
                _wn=np.clip(w2[_bi]*E('FACENRMK',3.0),0,1)[:,None]      # all neck normal on the lowest ~7 mm, none 1.2 cm up
                if _nfk>0:
                    # fitted head: the reference is the VISIBLE neck skin just under the edge of the head (the ring of body
                    # skin 0-2 mm below the cut), not the hidden skin under the band (that one bends in towards the old jaw:
                    # its normals gave a light fringe along the joint). The edge of the head takes exactly the normal of the
                    # neck next to it and turns into its own normals little by little up to FACENH above. With the face
                    # shading (FELT, FCON) 1 deg of difference is ~4 grey levels on the shadow side, and a pose always
                    # leaves 1-2 deg between the two skins: this is what makes the joint hold in any pose.
                    _hda=_em.attributes.get('hd')
                    if _hda is not None:
                        _hdv=np.zeros(ne_); _hda.data.foreach_get('value',_hdv); _rg=np.where((_hdv[_sel]>-E('FACENR',0.002))&(_hdv[_sel]<0.0003))[0]
                        if len(_rg)>50:
                            _dd,_ii=_KDn(_ev[_sel][_rg]).query(c2[_bi],k=4); _wk=1.0/np.maximum(_dd,1e-5)**2
                            _nb=(_en[_rg][_ii]*_wk[:,:,None]).sum(1); _nb/=np.maximum(np.linalg.norm(_nb,axis=1,keepdims=True),1e-12)
                    _wn=np.clip(1-_resth(w2[_bi])/E('FACENH',0.006),0,1); _wn=(_wn*_wn*(3-2*_wn))[:,None]
                _nn=vn2[_bi]*(1-_wn)+_nb*_wn; vn2[_bi]=_nn/np.maximum(np.linalg.norm(_nn,axis=1,keepdims=True),1e-12)
                nm2.normals_split_custom_set_from_vertices([tuple(float(x) for x in v) for v in vn2]); nm2.update()
                print('joint normals: %d band vertices, mean turn %.1f deg'%(len(_bi),float(np.degrees(np.arccos(np.clip((_nb*vn2[_bi]).sum(1),-1,1))).mean())))
                if os.environ.get('JOINTDBG'):
                    # diagnostic: clearance of the band over the neck skin (mm) and angle between the two skins, by sector and height
                    _h2=_resth(w2[_bi])*1000
                    _gn=np.zeros(n2*3); nm2.vertices.foreach_get('normal',_gn); _gn=_gn.reshape(-1,3)[_bi]
                    _s2=np.zeros(len(_bi)); _a2=np.zeros(len(_bi))
                    for k_,i in enumerate(_bi):
                        loc,nrm,_,_=_bvh.find_nearest(c2[i]); _s2[k_]=float((c2[i]-np.array(loc))@np.array(nrm))*1000
                        _a2[k_]=math.degrees(math.acos(max(-1,min(1,float(_gn[k_]@np.array(nrm))))))
                    _cx=c2[_bi][:,0].mean(); _cy=c2[_bi][:,1].mean(); _an=np.abs(np.degrees(np.arctan2(c2[_bi][:,0]-_cx,-(c2[_bi][:,1]-_cy))))
                    print('JOINTDBG centre %.3f %.3f  band verts %d'%(_cx,_cy,len(_bi)))
                    for a0,a1 in ((0,20),(20,60),(60,110),(110,155),(155,181)):
                        for h0,h1 in ((0,0.5),(0.5,2),(2,4),(4,8),(8,12.1)):
                            q_=(_an>=a0)&(_an<a1)&(_h2>=h0)&(_h2<h1)
                            if q_.sum()==0: continue
                            print('JOINTDBG ang %3d-%3d h %4.1f-%4.1f n %4d  clear min %6.3f med %6.3f max %6.3f mm  below %3d%%  angle med %5.1f max %5.1f'%(a0,a1,h0,h1,q_.sum(),_s2[q_].min(),np.median(_s2[q_]),_s2[q_].max(),100*(_s2[q_]<0).mean(),np.median(_a2[q_]),_a2[q_].max()))
                    _he=np.zeros(len(nm2.edges)*2,int); nm2.edges.foreach_get('vertices',_he); _be=np.zeros(len(_em.edges)*2,int); _em.edges.foreach_get('vertices',_be); _be=_be.reshape(-1,2)
                    _zk=(_ev[:,2]>c2[_bi][:,2].min()-0.06)&(_ev[:,2]<c2[_bi][:,2].max()+0.06); _be=_be[_zk[_be[:,0]]&_zk[_be[:,1]]]
                    np.savez(os.environ['JOINTDBG'],c=c2[_bi],s=_s2,a=_a2,h=_h2,an=_an,x=c2[_bi][:,0]-_cx,hv=c2,he=_he.reshape(-1,2),hw=w2,bv=_ev,be=_be)
if os.environ.get('HIDEBODY')=='1': ob.hide_render=True      # debug: head only
if os.environ.get('HIDEHEAD')=='1':                          # debug: body only (the hidden skin under the head band shows)
    for o in _heads: o.hide_render=True
sc.render.filepath=out+'.png'; bpy.ops.render.render(write_still=True)
