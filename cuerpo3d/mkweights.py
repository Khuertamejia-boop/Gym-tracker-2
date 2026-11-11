# SMH_f (fitted finger bones) -> SMH_w (clean hand weights, no drawn line on the hands)
import bpy,sys,os,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import handrig
src,out=sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']
for L in 'LR': handrig.reweight(hi,rig,L)
# corrective-smooth group: every finger (joints included), fading into the palm
g=hi.vertex_groups.get('CS') or hi.vertex_groups.new(name='CS')
names=set(f'{f}{k}.{L}' for f in ('index','middle','ring','pinky','thumb') for k in (1,2,3) for L in 'LR')
gi={hi.vertex_groups[n].index for n in names}
acc={}
for v in hi.data.vertices:
    w=sum(x.weight for x in v.groups if x.group in gi)
    if w>0.02: acc.setdefault(round(min(1.0,w*1.3)*20)/20,[]).append(v.index)
for w,ids in acc.items(): g.add(ids,w,'REPLACE')
me=hi.data; nv=len(me.vertices); co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
m=(np.abs(co[:,0])>0.40)&(co[:,2]<1.12); a=me.attributes.get('ln')
if a is not None and a.domain=='POINT':
    x=np.zeros(len(a.data),np.float32); a.data.foreach_get('value',x); x[m]=0; a.data.foreach_set('value',x)
bpy.ops.wm.save_as_mainfile(filepath=out)
