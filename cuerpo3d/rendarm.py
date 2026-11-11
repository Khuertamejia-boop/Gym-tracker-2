import bpy,sys,math,os
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Hi' and not o.name.startswith('Banco') and not (os.environ.get('SHOWBAR') and o.name in (('Barra',) if os.environ.get('NODISC') else ('Barra','Discos'))): o.hide_render=True
ob=bpy.data.objects['Hi']
m=bpy.data.materials.new('armv'); nt=m.node_tree; b=nt.nodes['Principled BSDF']; b.inputs['Roughness'].default_value=0.5
at=nt.nodes.new('ShaderNodeAttribute'); at.attribute_name='mseg'; at.attribute_type='GEOMETRY'
red=[float(v) for v in os.environ.get('REDIDS','4,5').split(',')]
mask=None
for r_ in red:
    c1=nt.nodes.new('ShaderNodeMath'); c1.operation='COMPARE'; c1.inputs[1].default_value=r_; c1.inputs[2].default_value=0.4
    nt.links.new(at.outputs['Fac'],c1.inputs[0])
    if mask is None: mask=c1.outputs[0]
    else:
        mx=nt.nodes.new('ShaderNodeMath'); mx.operation='MAXIMUM'; nt.links.new(mask,mx.inputs[0]); nt.links.new(c1.outputs[0],mx.inputs[1]); mask=mx.outputs[0]
if os.environ.get('HL'):
    ah=nt.nodes.new('ShaderNodeAttribute'); ah.attribute_name='hl'; ah.attribute_type='GEOMETRY'; mask=ah.outputs['Fac']
ao=nt.nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value=float(os.environ.get('AOD','0.02')); ao.samples=16
mix=nt.nodes.new('ShaderNodeMix'); mix.data_type='RGBA'; mix.inputs['A'].default_value=(0.80,0.80,0.80,1); mix.inputs['B'].default_value=tuple(float(v) for v in os.environ.get('REDC','0.85,0.20,0.10').split(','))+(1,)
nt.links.new(mask,mix.inputs['Factor'])
mul=nt.nodes.new('ShaderNodeMix'); mul.data_type='RGBA'; mul.blend_type='MULTIPLY'; mul.inputs['Factor'].default_value=1.0
pw=nt.nodes.new('ShaderNodeMath'); pw.operation='POWER'; pw.inputs[1].default_value=float(os.environ.get('AOP','1.5'))
nt.links.new(ao.outputs['AO'],pw.inputs[0])
cr=nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(pw.outputs[0],cr.inputs[i]) for i in range(3)]
aq=nt.nodes.new('ShaderNodeAttribute'); aq.attribute_name='mq'; aq.attribute_type='GEOMETRY'
# edge gradient: 1 - G*(1-q)^P  (q=1 centre of muscle, 0 at its border)
om=nt.nodes.new('ShaderNodeMath'); om.operation='SUBTRACT'; om.inputs[0].default_value=1.0; nt.links.new(aq.outputs['Fac'],om.inputs[1])
pq=nt.nodes.new('ShaderNodeMath'); pq.operation='POWER'; pq.inputs[1].default_value=float(os.environ.get('GP','1.6')); nt.links.new(om.outputs[0],pq.inputs[0])
gq=nt.nodes.new('ShaderNodeMath'); gq.operation='MULTIPLY'; gq.inputs[1].default_value=float(os.environ.get('GG','0.45')); nt.links.new(pq.outputs[0],gq.inputs[0])
iq=nt.nodes.new('ShaderNodeMath'); iq.operation='SUBTRACT'; iq.inputs[0].default_value=1.0; nt.links.new(gq.outputs[0],iq.inputs[1])
m2=nt.nodes.new('ShaderNodeMath'); m2.operation='MULTIPLY'; nt.links.new(pw.outputs[0],m2.inputs[0]); nt.links.new(iq.outputs[0],m2.inputs[1])
cr2=nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(m2.outputs[0],cr2.inputs[i]) for i in range(3)]
nt.links.new(cr2.outputs[0],mul.inputs['B'])
nt.links.new(mix.outputs['Result'],mul.inputs['A'])
# dark shorts
ash=nt.nodes.new('ShaderNodeAttribute'); ash.attribute_name='shorts'; ash.attribute_type='GEOMETRY'
mr=nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value=0.45; mr.inputs['From Max'].default_value=0.55; nt.links.new(ash.outputs['Fac'],mr.inputs['Value'])
dk=nt.nodes.new('ShaderNodeMix'); dk.data_type='RGBA'; dk.blend_type='MULTIPLY'; dk.inputs['Factor'].default_value=1.0
sv=float(os.environ.get('SHV','0.10')); dk.inputs['A'].default_value=(sv,sv,sv,1); nt.links.new(cr.outputs[0],dk.inputs['B'])
fin=nt.nodes.new('ShaderNodeMix'); fin.data_type='RGBA'; nt.links.new(mr.outputs['Result'],fin.inputs['Factor'])
nt.links.new(mul.outputs['Result'],fin.inputs['A']); nt.links.new(dk.outputs['Result'],fin.inputs['B'])
finout=fin.outputs['Result']
if os.environ.get('WORK'):
    # worked muscles: natural red gradient (light warm red at the borders -> deep red in the belly), also over the shorts
    aw=nt.nodes.new('ShaderNodeAttribute'); aw.attribute_name='work'; aw.attribute_type='GEOMETRY'
    rp=nt.nodes.new('ShaderNodeValToRGB'); el=rp.color_ramp.elements
    el[0].position=0.0; el[0].color=(0.80,0.80,0.80,1); el[1].position=1.0; el[1].color=tuple(float(v) for v in os.environ.get('WC1','0.74,0.11,0.07').split(','))+(1,)
    e_=el.new(float(os.environ.get('WMP','0.38'))); e_.color=tuple(float(v) for v in os.environ.get('WC0','0.90,0.52,0.44').split(','))+(1,)
    nt.links.new(aw.outputs['Fac'],rp.inputs['Fac']); nt.links.new(rp.outputs['Color'],mul.inputs['A'])
    dr=nt.nodes.new('ShaderNodeMix'); dr.data_type='RGBA'; dr.blend_type='MULTIPLY'; dr.inputs['Factor'].default_value=1.0
    nt.links.new(mul.outputs['Result'],dr.inputs['A']); k_=float(os.environ.get('WSD','0.80')); dr.inputs['B'].default_value=(k_,k_,k_,1)
    wf=nt.nodes.new('ShaderNodeMath'); wf.operation='MULTIPLY'; nt.links.new(aw.outputs['Fac'],wf.inputs[0]); nt.links.new(mr.outputs['Result'],wf.inputs[1])
    wf2=nt.nodes.new('ShaderNodeMath'); wf2.operation='MULTIPLY'; wf2.use_clamp=True; wf2.inputs[1].default_value=float(os.environ.get('WSK','1.3')); nt.links.new(wf.outputs[0],wf2.inputs[0])
    fw=nt.nodes.new('ShaderNodeMix'); fw.data_type='RGBA'; nt.links.new(wf2.outputs[0],fw.inputs['Factor'])
    nt.links.new(fin.outputs['Result'],fw.inputs['A']); nt.links.new(dr.outputs['Result'],fw.inputs['B']); finout=fw.outputs['Result']
aln=nt.nodes.new('ShaderNodeAttribute'); aln.attribute_name='ln'; aln.attribute_type='GEOMETRY'
lk=nt.nodes.new('ShaderNodeMath'); lk.operation='MULTIPLY'; lk.inputs[1].default_value=float(os.environ.get('LNK','0.75')); nt.links.new(aln.outputs['Fac'],lk.inputs[0])
li=nt.nodes.new('ShaderNodeMath'); li.operation='SUBTRACT'; li.inputs[0].default_value=1.0; nt.links.new(lk.outputs[0],li.inputs[1])
lc_=nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(li.outputs[0],lc_.inputs[i]) for i in range(3)]
lm=nt.nodes.new('ShaderNodeMix'); lm.data_type='RGBA'; lm.blend_type='MULTIPLY'; lm.inputs['Factor'].default_value=1.0
nt.links.new(finout,lm.inputs['A']); nt.links.new(lc_.outputs[0],lm.inputs['B'])
nt.links.new(lm.outputs['Result'],b.inputs['Base Color'])
if os.environ.get('MASKONLY'):
    # flat mask pass: white where the worked muscles are, black elsewhere (for compositing)
    em=nt.nodes.new('ShaderNodeEmission'); nt.links.new(mask,em.inputs['Strength']); em.inputs['Color'].default_value=(1,1,1,1)
    nt.links.new(em.outputs[0],nt.nodes['Material Output'].inputs['Surface'])
for i in range(len(ob.data.materials)): ob.data.materials[i]=m
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=int(os.environ.get('SMP','24')); sc.cycles.device='CPU'; sc.view_settings.view_transform='Standard'
sc.cycles.use_denoising=(os.environ.get('DENOISE','1')=='1')
w=bpy.data.worlds.new('w'); w.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1); w.node_tree.nodes['Background'].inputs['Strength'].default_value=float(os.environ.get('AMB','0.2')); sc.world=w
def light(loc,e,sz=2.5):
    l=bpy.data.lights.new('L','AREA'); l.energy=e; l.size=sz; o=bpy.data.objects.new('L',l); o.location=loc; sc.collection.objects.link(o)
    from mathutils import Vector; d=Vector((0.35,-0.1,1.2))-o.location; o.rotation_euler=(-d).to_track_quat('Z','Y').to_euler()
K=float(os.environ.get('LK','0.3'))
_y=math.radians(float(os.environ.get('YAW','0')))
def rot(x,y,z): return (x*math.cos(_y)-y*math.sin(_y), x*math.sin(_y)+y*math.cos(_y), z)
light(rot(-2.2,-3.0,3.2),240*K); light(rot(3,-2,1.2),45*K); light(rot(0.5,3,2.5),90*K)
cam=bpy.data.objects.new('cam',bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
V={'full':((-1.6,-5.2,0.95),(90,0,-17),2.05),'upper':((-1.0,-5.2,1.25),(90,0,-17),0.95),'af':((0.36,-6.5,1.2),(90,0,0),0.62),'ab':((0.36,6.5,1.2),(90,0,180),0.62),'aq':((3.0,-4.0,1.25),(90,0,37),0.62),'al':((4.6,-1.0,1.35),(75,0,78),0.62)}
import math as _m
def look(target,yaw,pitch,dist=6.0):
    y=_m.radians(yaw); p=_m.radians(pitch)
    loc=(target[0]+dist*_m.sin(y)*_m.cos(p), target[1]-dist*_m.cos(y)*_m.cos(p), target[2]+dist*_m.sin(p))
    return loc,(90-pitch,0,yaw)
YAW=float(os.environ.get('YAW','-25')); PIT=float(os.environ.get('PIT','6'))
V['full']=look((0,-0.02,0.90),YAW,PIT)+(2.0,)
V['upper']=look((0,-0.02,1.18),YAW,PIT)+(0.95,)
V['chest']=look((0.0,-0.02,1.30),YAW,PIT)+(0.45,)
V['cus']=look((float(os.environ.get('TX','0')),float(os.environ.get('TY','-0.02')),float(os.environ.get('TZ','1.2'))),YAW,PIT)+(float(os.environ.get('OSC','0.9')),)
sc.render.film_transparent=True
for vn in os.environ.get('VIEWS','af,ab,aq').split(','):
    loc,rot,s=V[vn]; cam.location=loc; cam.rotation_euler=[math.radians(a) for a in rot]; cam.data.type='ORTHO'; cam.data.ortho_scale=s
    r_=int(os.environ.get('RES','700')); sc.render.resolution_x,sc.render.resolution_y=((int(r_*0.62),r_) if vn=='full' else (r_,r_))
    sc.render.filepath=f'{out}_{vn}.png'; bpy.ops.render.render(write_still=True)
