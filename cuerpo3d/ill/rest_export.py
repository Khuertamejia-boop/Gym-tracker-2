# export the rest body (vertex order shared by all posed frames) to ill/rest.npz for the atlas compiler
import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-3]); out=sys.argv[-1]; rel=np.load(sys.argv[-2])
hi=bpy.data.objects['Hi']; me=hi.data; nv=len(me.vertices); rig=bpy.data.objects['Rig']
co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
no=np.zeros(nv*3); me.vertices.foreach_get('normal',no); no=no.reshape(-1,3)
lt=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_total',lt)
lv=np.zeros(len(me.loops),int); me.loops.foreach_get('vertex_index',lv)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed)
sh=np.zeros(nv,np.float32); me.attributes['shorts'].data.foreach_get('value',sh)
gi={g.index:g.name for g in hi.vertex_groups}
main=['']*nv; mw=np.zeros(nv)
for v in me.vertices:
    for g in v.groups:
        if g.weight>mw[v.index]: mw[v.index]=g.weight; main[v.index]=gi[g.group]
bn=[b.name for b in rig.data.bones]
bh=np.array([b.head_local for b in rig.data.bones]); bt=np.array([b.tail_local for b in rig.data.bones])
np.savez(out,co=co,no=no,lt=lt,lv=lv,ed=ed.reshape(-1,2),shorts=sh,main=np.array(main),bn=np.array(bn),bh=bh,bt=bt,h_fine=rel['h_fine'],h_mid=rel['h_mid'])
print('ok',nv)
