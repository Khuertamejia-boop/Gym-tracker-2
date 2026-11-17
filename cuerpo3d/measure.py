# Body proportions at rest (cm): shoulder width (deltoids), back width under the armpit, waist, chest depth, traps.
import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices)
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
if me.shape_keys:
    k=np.zeros(nv*3); me.shape_keys.key_blocks['Basis'].data.foreach_get('co',k); co=k.reshape(-1,3)
names=[m.name for m in me.materials]; mi=np.zeros(len(me.polygons),int); me.polygons.foreach_get('material_index',mi)
lt=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_total',lt); lv=np.zeros(len(me.loops),int); me.loops.foreach_get('vertex_index',lv)
pv=np.repeat(np.arange(len(me.polygons)),lt)
def mv(mat): return np.unique(lv[mi[pv]==names.index(mat)])
gi={g.index:g.name for g in hi.vertex_groups}; arm=np.zeros(nv)
for v in me.vertices:
    for g in v.groups:
        n=gi.get(g.group,'')
        if n.startswith(('upper_arm','forearm','hand','thumb','index','middle','ring','pinky')): arm[v.index]+=g.weight
        elif n.startswith('delt'): arm[v.index]+=0.5*g.weight
d=mv('mus_mat_deltoid'); print('shoulder width (deltoids) %.1f'%(2*np.abs(co[d,0]).max()*100))
for z in (1.10,1.20,1.25,1.30):
    m=(np.abs(co[:,2]-z)<0.004)&(arm<0.3); print('torso width z=%.2f: %.1f   depth %.1f'%(z,2*np.abs(co[m,0]).max()*100,(co[m,1].max()-co[m,1].min())*100))
t=mv('mus_mat_traps'); print('traps top z %.3f (at x=%.3f)'%(co[t,2].max(),abs(co[t][np.argmax(co[t,2]),0])))
# trap height at x=0.10 (between neck and shoulder)
m=(np.abs(np.abs(co[:,0])-0.10)<0.004)&(np.abs(co[:,1]-0.02)<0.05)&(co[:,2]>1.35)&(co[:,2]<1.6); print('top of shoulder line at x=10cm: z %.3f'%co[m,2].max())
p=mv('mus_mat_pectoral'); print('pec front y %.3f'%co[p,1].min())
b=mv('mus_mat_biceps'); print('upper arm: biceps x max %.3f'%np.abs(co[b,0]).max())
