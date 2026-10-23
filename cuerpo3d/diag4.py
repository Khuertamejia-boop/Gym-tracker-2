import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
me=bpy.data.objects['Cuerpo'].data
co=np.array([v.co[:] for v in me.vertices]); nv=len(co)
nb=[[] for _ in range(nv)]
for e in me.edges: a,b=e.vertices; nb[a].append(b); nb[b].append(a)
n=np.array([v.normal[:] for v in me.vertices])
lap=np.array([co[x].mean(0)-co[i] if x else np.zeros(3) for i,x in enumerate(nb)])
s=(lap*n).sum(1)
m=(co[:,0]>0.1)&(co[:,0]<0.25)&(co[:,1]<-0.05)&(co[:,2]>0.40)&(co[:,2]<0.70)
idx=np.where(m)[0]; o=idx[np.argsort(-np.abs(s[idx]))][:15]
for i in o: print(co[i].round(3), round(s[i]*1000,2),'mm', 'val',len(nb[i]))
# shading normal check: angle between vertex normal and neighbors
