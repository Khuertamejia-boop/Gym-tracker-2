# Ray-cast pixels of a rendarm 'cus' view to find which skin they are (rest position + bone weights).
# usage: blender -b -P pick.py -- posed.blend   env TX TY TZ YAW PIT OSC RES PIX="x,y;x,y" REST=rest.blend (for rest coords)
import bpy,sys,os,math, numpy as np
from mathutils import Vector, Euler
E=lambda k,d: float(os.environ.get(k,d))
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
hi=bpy.data.objects['Hi']
for o in bpy.data.objects:
    if o.type=='MESH' and o.name!='Hi': o.hide_viewport=True
dg=bpy.context.evaluated_depsgraph_get(); sc=bpy.context.scene
tx,ty,tz=E('TX',0),E('TY',0),E('TZ',1.5); yaw=math.radians(E('YAW',0)); pit=math.radians(E('PIT',0)); d=6
loc=Vector((tx+d*math.sin(yaw)*math.cos(pit), ty-d*math.cos(yaw)*math.cos(pit), tz+d*math.sin(pit)))
R=Euler((math.radians(90-E('PIT',0)),0,yaw)).to_matrix(); fwd=R@Vector((0,0,-1)); right=R@Vector((1,0,0)); up=R@Vector((0,1,0))
osc=E('OSC',1); res=E('RES',700)
rest=None
if os.environ.get('REST'):
    import bpy as _b
pts=[tuple(map(float,p.split(','))) for p in os.environ['PIX'].split(';')]
hits=[]
for (px,py) in pts:
    o=loc+right*((px/res-0.5)*osc)+up*((0.5-py/res)*osc)
    hit,pos,nrm,fi,ob,mat=sc.ray_cast(dg,o,fwd)
    if not hit: print(px,py,'no hit'); continue
    vs=list(ob.evaluated_get(dg).data.polygons[fi].vertices); hits.append((px,py,vs))
gi={g.index:g.name for g in hi.vertex_groups}
me=hi.data
bpy.ops.wm.open_mainfile(filepath=os.environ['REST']); hr=bpy.data.objects['Hi']; mr=hr.data
kb=mr.shape_keys.key_blocks['Basis'] if mr.shape_keys else None
gr={g.index:g.name for g in hr.vertex_groups}
for px,py,vs in hits:
    P=np.mean([ (kb.data[i].co if kb else mr.vertices[i].co) for i in vs],axis=0)
    ws={}
    for i in vs:
        for g in mr.vertices[i].groups:
            n=gr[g.group]
            if n not in ('CS','CS2','AX'): ws[n]=ws.get(n,0)+g.weight/len(vs)
    print(px,py,'rest',np.round(P,3),{k:round(v,2) for k,v in ws.items() if v>0.04})
