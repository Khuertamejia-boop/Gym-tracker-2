import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
rig=bpy.data.objects['Rig']
B={b.name:(np.array(b.head_local),np.array(b.tail_local)) for b in rig.data.bones}
for n in ('upper_arm.L','forearm.L','hand.L','thumb1.L','thumb3.L','index1.L','pinky1.L'):
    print(n,B[n][0].round(3),B[n][1].round(3))
h,t=B['forearm.L']; a=(t-h)/np.linalg.norm(t-h); f=np.array([0,-1.0,0]); f=f-a*f.dot(a); f/=np.linalg.norm(f); l=np.cross(a,f); l=l if l[2]>0 else -l
for n in ('thumb1.L','pinky1.L','index1.L'):
    r=B[n][0]-h; rr=r-a*r.dot(a); print(n,'theta',round(np.degrees(np.arctan2(rr@l,rr@f)),1))
