import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2])
me=bpy.data.objects['Hi'].data
me.calc_loop_triangles()
nt=len(me.loop_triangles)
tv=np.zeros(nt*3,int); me.loop_triangles.foreach_get('vertices',tv)
tl=np.zeros(nt*3,int); me.loop_triangles.foreach_get('loops',tl)
uv=np.zeros(len(me.loops)*2); me.uv_layers.active.data.foreach_get('uv',uv); uv=uv.reshape(-1,2)
np.savez(sys.argv[-1],tv=tv.reshape(-1,3),tuv=uv[tl].reshape(-1,3,2))
print('tris',nt)
