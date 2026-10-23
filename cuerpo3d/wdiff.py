import bpy,sys,numpy as np
def load(f):
    bpy.ops.wm.open_mainfile(filepath=f); ob=bpy.data.objects['Hi']; me=ob.data
    gi={g.name:g.index for g in ob.vertex_groups}; k=gi['upper_arm.L']
    nv=len(me.vertices); co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    sel=np.where((co[:,0]>0.10)&(co[:,0]<0.22)&(co[:,2]>1.30)&(co[:,2]<1.42))[0][::40]
    w=[]
    for v in sel:
        t=0.0
        for g in me.vertices[v].groups:
            if g.group==k: t=g.weight
        w.append(t)
    return np.array(w), len(ob.modifiers)
a,ma=load(sys.argv[-2]); b,mb=load(sys.argv[-1])
print('WDIFF mean abs',float(np.abs(a-b).mean()),'n',len(a),'mods',ma,mb)
