# rasterise the rest body's UV layout coloured by the mid relief (to see if UV space is a usable atlas chart)
import bpy,sys,numpy as np
from PIL import Image,ImageDraw
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
me=bpy.data.objects['Hi'].data; nv=len(me.vertices)
uv=np.zeros(len(me.loops)*2); me.uv_layers.active.data.foreach_get('uv',uv); uv=uv.reshape(-1,2)
lv=np.zeros(len(me.loops),int); me.loops.foreach_get('vertex_index',lv)
lt=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_total',lt); ls=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_start',ls)
print('uv range',uv.min(0),uv.max(0),'loop_total',np.unique(lt,return_counts=True))
d=np.load(sys.argv[-3]); h=d['h_mid']
R=400; im=Image.new('RGB',(R*9,R*4),(255,255,255)); dr=ImageDraw.Draw(im)
for f in range(len(me.polygons)):
    idx=range(ls[f],ls[f]+lt[f]); pts=[(uv[i,0]*R,(4-uv[i,1])*R) for i in idx]
    v=np.mean([h[lv[i]] for i in idx]); g=int(np.clip(128+v*1000*14,0,255))
    dr.polygon(pts,fill=(g,g,g))
[dr.line([(k*R,0),(k*R,4*R)],fill=(255,0,0)) for k in range(10)]; [dr.line([(0,k*R),(9*R,k*R)],fill=(255,0,0)) for k in range(5)]; im.save(out)
tile=(np.floor(uv[:,0])+10*np.floor(uv[:,1])).astype(int); import collections; print(collections.Counter(tile))
# per-vertex: count distinct uvs (seams)
from collections import defaultdict
