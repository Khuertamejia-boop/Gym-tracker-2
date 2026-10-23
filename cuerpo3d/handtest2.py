# Test: re-skin the hands in the rest pose, close them, put a bar in the fist.  usage: handtest2.py -- in.blend out.blend
import bpy,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import handrig
from mathutils import Vector
E=lambda k,d: float(os.environ.get(k,d))
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']
for m in list(hi.modifiers):
    if m.type=='ARMATURE': hi.modifiers.remove(m)
md=hi.modifiers.new('Armature','ARMATURE'); md.object=rig; md.use_deform_preserve_volume=bool(int(E('DQS',1)))
for L in 'LR': handrig.reweight(hi,rig,L)
A=[float(v) for v in os.environ.get('GA','75,70,55').split(',')]; TA=[float(v) for v in os.environ.get('GTA','15,25,30').split(',')]
ax,c=handrig.fist(rig,'L',A,TA)
handrig.fist(rig,'R',A,TA)
off=Vector((0,E('BDY',0.0),E('BDZ',0.0)))
handrig.place_bar(c+off,ax,E('BARR',0.0145))
print('bar centre',tuple(round(x,3) for x in c),'axis',tuple(round(x,3) for x in ax))
bpy.ops.wm.save_as_mainfile(filepath=out)
