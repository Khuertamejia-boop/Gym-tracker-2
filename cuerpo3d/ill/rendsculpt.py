# Anatomy-plate look by SCULPTING, not drawing: the muscle map is turned into real relief at render time
# (subdivided mesh + material displacement): every muscle is a rounded pillow, its border a deep soft groove, so the
# light itself makes the gradients; fibres are a fine relief + light/dark streaks; worked muscles coral red.
#   python -I rendsculpt.py posed.blend OUTPREFIX      env: MAPS=<bakemaps dir> NPZ=<stylefields npz>, camera env
import bpy, sys, math, os, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
C=lambda k,d: tuple(float(x) for x in os.environ.get(k,d).split(','))+(1.0,)
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Hi' and not (os.environ.get('SHOWBAR','1')=='1' and o.name in ('Barra','Discos')) and not (o.name.startswith('Banco') and os.environ.get('HIDEBANCO','0')!='1'): o.hide_render=True
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
_rest=np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rest.npz'),allow_pickle=True)
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
if E('SHORTZ',0)>0:
    # shorter shorts: cut the existing shorts mask at a higher hem (rest-pose height), a little higher on the outside
    _sh=np.zeros(nv,np.float32); me.attributes['shorts'].data.foreach_get('value',_sh)
    _ax=np.abs(_co[:,0])
    _zh=E('SHORTZ',0.74)+E('SHSL',0.25)*np.clip(_ax-E('SHX0',0.10),0,0.08)-E('SHBK',0.0)*np.clip(_co[:,1]/0.10,0,1)
    _t=np.clip((_co[:,2]-_zh)/E('SHBAND',0.008)+0.5,0,1); _t=_t*_t*(3-2*_t)
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
gh=pillow(d,E('W',7.0),E('P',1.5)); gs=pillow(ds,E('WS',5.0),E('P',1.5))
# fibres: phase field from the atlas, broken into bundles by noise (fixed to the body via its rest position)
tc=A('restco').outputs['Vector'] if 'restco' in have else N.new('ShaderNodeTexCoord').outputs['Object']
nz=N.new('ShaderNodeTexNoise'); L.new(tc,nz.inputs['Vector']); nz.inputs['Scale'].default_value=E('NZS',35.0); nz.inputs['Detail'].default_value=4.0
noise=nz.outputs['Fac']
nz2=N.new('ShaderNodeTexNoise'); L.new(tc,nz2.inputs['Vector']); nz2.inputs['Scale'].default_value=E('NZS2',120.0); nz2.inputs['Detail'].default_value=2.0
fine=nz2.outputs['Fac']
ph=M('ADD',M('MULTIPLY',F('fph'),E('FSC',0.7)),M('MULTIPLY',noise,E('FJIT',0.8)))
if os.environ.get('FMODE','streak')=='streak':
    # painterly streaks: random brightness per thin band across the fibres (1D noise of the fibre phase)
    n1=N.new('ShaderNodeTexNoise'); n1.noise_dimensions='1D'; n1.inputs['Scale'].default_value=E('FSTS',1.0); n1.inputs['Detail'].default_value=E('FSTD',2.0)
    L.new(M('ADD',M('MULTIPLY',F('fph'),E('FSTR',3.0)),M('MULTIPLY',noise,E('FSTJ',0.6))),n1.inputs['W'])
    wave=SS(n1.outputs['Fac'],E('FS0',0.35),E('FS1',0.70))
else:
    wave=M('MULTIPLY',M('ADD',M('SINE',M('MULTIPLY',ph,2*math.pi)),1.0),0.5)          # 0..1 across each fibre bundle
bund=SS(noise,E('FB0',0.30),E('FB1',0.70),E('FBMIN',0.2),1.0)                    # some bundles stronger than others
fib=M('MULTIPLY',M('MULTIPLY',wave,bund),M('MULTIPLY',F('fmask'),SS(d,0.5,4.0)))   # 0 on grooves / tendons
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
dn=N.new('ShaderNodeDisplacement'); dn.space='OBJECT'
L.new(M('DIVIDE',h,1000.0),dn.inputs['Height']); dn.inputs['Midlevel'].default_value=0.0; dn.inputs['Scale'].default_value=E('DSC',1.0)
L.new(dn.outputs['Displacement'],N['Material Output'].inputs['Displacement'])
# ---- colour: white clay, slightly darker in the grooves; red with deeper red grooves and visible fibre streaks
cav=M('MULTIPLY',M('SUBTRACT',1.0,gh),E('CAVK',0.35))
white=MIX(cav,G(E('SKC',0.88)),G(E('SKG',0.45)))
wst=M('MULTIPLY',M('MULTIPLY',M('SUBTRACT',1.0,wave),SS(d,0.5,4.0)),M('SUBTRACT',1.0,tend))   # faint grey streaks on white muscles too
white=MIX(M('MULTIPLY',wst,E('FIBW',0.06)),white,G(E('FIBWC',0.45)))
rc=C('REDC','0.86,0.26,0.15'); rg=C('REDG','0.42,0.06,0.03'); rl=C('REDL','1.0,0.62,0.48')
redb=MIX(M('MULTIPLY',M('SUBTRACT',1.0,gh),E('CAVR',0.75)),rc,rg)
redb=MIX(M('MULTIPLY',fib,E('FIBR',0.45)),redb,C('FIBRC','0.55,0.08,0.04'))
redb=MIX(M('MULTIPLY',M('MULTIPLY',M('SUBTRACT',1.0,wave),bund),M('MULTIPLY',F('fmask'),E('FIBL',0.25))),redb,rl)
core=M('MULTIPLY',M('MULTIPLY',SS(d,E('LW0',0.3),E('LW1',1.4),1.0,0.0),E('LINEK',0.45)),M('SUBTRACT',1.0,M('MULTIPLY',F('tfade'),E('TFL',0.5))))      # thin dark core at the bottom of each groove
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
            hb=M('MULTIPLY',hb,M('ADD',E('GBUMP',1.0),M('MULTIPLY',red,1.0-E('GBUMP',1.0))))   # GBUMP<1: softer roundness on grey muscles
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
    if E('EDGEK',0)>0:
        # per-muscle shading like a drawn plate: every muscle is darker/more intense along its border and fades to
        # light towards its middle; the band width follows the muscle's own width so it reads at any distance
        def _tex16(name,scale):
            tx_=udim(name,'Cubic'); sp__=N.new('ShaderNodeSeparateColor'); L.new(tx_.outputs['Color'],sp__.inputs[0]); return M('MULTIPLY',sp__.outputs[0],scale)
        ew=M('MAXIMUM',M('MULTIPLY',_tex16('halfw',64.0),M('ADD',E('EWF',0.75),M('MULTIPLY',red,E('EWFR',0.75)-E('EWF',0.75)))),E('EMM',5.0))
        eg=SS(M('MINIMUM',M('DIVIDE',M('ADD',_tex16('dh16',64.0),ladd),ew),1.0),0.0,1.0)
        eg=M('POWER',eg,E('EGP',0.8))
        egs=SS(M('MINIMUM',M('DIVIDE',_tex16('ds16',64.0),E('ESW',6.0)),1.0),0.0,1.0,E('ESOFT',0.7),1.0)
        eg=M('MULTIPLY',eg,egs)
        emin=M('ADD',E('EMIN',0.35),M('MULTIPLY',tend,E('ETMIN',0.75)-E('EMIN',0.35)))   # tendons: same gradient, softer
        emin=M('ADD',emin,M('MULTIPLY',red,E('ERMIN',0.35)-E('EMIN',0.35)))              # worked (red) muscles: own border depth
        ef=M('ADD',emin,M('MULTIPLY',eg,M('SUBTRACT',1.0,emin)))            # 1 in the middle, emin at the border
        ef=M('ADD',ef,M('MULTIPLY',SS(A('shorts').outputs['Fac'],0.3,0.6),M('SUBTRACT',1.0,ef)))   # not on the shorts
        ef=M('ADD',ef,M('MULTIPLY',M('MULTIPLY',F('tfade'),E('TFE',0.6)),M('SUBTRACT',1.0,ef)))       # lower forearm: tendons, lighter
        # border darkening mostly on the shadow (lower) side of each muscle: lit borders stay light, like the plates
        tl_=t
        sidew=SS(tl_,E('SIDEHI',0.75),E('SIDELO',0.35),1.0,0.0)                    # 1 in shadow, 0 in light
        smin=M('ADD',E('SIDEMIN',1.0),M('MULTIPLY',red,E('SIDEMINR',1.0)-E('SIDEMIN',1.0)))   # weight kept on the lit side
        sidew=M('ADD',smin,M('MULTIPLY',sidew,M('SUBTRACT',1.0,smin)))
        ef=M('SUBTRACT',1.0,M('MULTIPLY',M('SUBTRACT',1.0,ef),sidew))
        t=M('MULTIPLY',M('ADD',M('MULTIPLY',t,E('ELT',1.0)),1.0-E('ELT',1.0)),ef)   # ELT<1 = less light, more drawing
        if os.environ.get('MDEBUG')=='eg': outdbg=eg
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
        outc=MIX(M('MULTIPLY',red,M('SUBTRACT',1.0,sh)),outc,rsh)
    outc=MIX(1.0,outc,G(spec),'ADD')
    if os.environ.get('MDEBUG')=='n':
        mp=N.new('ShaderNodeVectorMath'); mp.operation='MULTIPLY_ADD'; L.new(vt.outputs['Vector'],mp.inputs[0]); mp.inputs[1].default_value=(0.5,0.5,0.5); mp.inputs[2].default_value=(0.5,0.5,0.5)
        outc=mp.outputs['Vector']
    if os.environ.get('MDEBUG')=='t': outc=G(t)
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
sc.render.filepath=out+'.png'; bpy.ops.render.render(write_still=True)
