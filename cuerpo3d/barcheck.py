# usage: cd $GT3D/w && ../venv/bin/python -I ../barcheck.py -- DLf00.blend ...
# distance from the bar surface to the leg skin in each posed frame (negative = the bar is inside the leg)
import bpy, sys, os, numpy as np
R=np.load(os.path.join(os.environ.get('GT3D','.'),'ill','rest.npz'),allow_pickle=True); main=np.array([str(m) for m in R['main']])
legs=np.isin(main,['thigh.L','thigh.R','shin.L','shin.R','hips','foot.L','foot.R'])
for f in sys.argv[sys.argv.index('--')+1:]:
    bpy.ops.wm.open_mainfile(filepath=f)
    hi=bpy.data.objects['Hi']; dg=bpy.context.evaluated_depsgraph_get(); me=hi.evaluated_get(dg).to_mesh()
    co=np.array([v.co[:] for v in me.vertices]); M=np.array(hi.matrix_world)
    co=co@M[:3,:3].T+M[:3,3]
    if len(co)!=len(main): print('vert count differs',len(co),len(main)); continue
    b=bpy.data.objects['Barra']; Mb=np.array(b.matrix_world); C0=np.array((0,-0.2962,0.9366)); c=Mb[:3,:3]@C0+Mb[:3,3]
    sel=legs&(np.abs(co[:,0])<0.30)
    d=np.hypot(co[sel,1]-c[1],co[sel,2]-c[2])-0.0145
    i=np.argmin(d); p=co[sel][i]
    print('%s bar y %.3f z %.3f  min gap %+.1f mm at %s (%s)'%(f,c[1],c[2],d[i]*1000,np.round(p,3),main[sel][i]))
