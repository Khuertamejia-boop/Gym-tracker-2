# Lying leg curl machine (like the owner's example): angled hip/thigh pad (hips highest), separate lower chest pad,
# light-grey steel frame, weight-stack tower behind, knee pivot with lever and roller behind the ankles, front handles.
import bpy, math, numpy as np
from mathutils import Vector, Matrix
def _mat(name,col,rough,metal=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
    b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(*col,1); b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
    return m
def _box(name,c,size,mat,R=None,bevel=0.0,seg=3):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,0)); o=bpy.context.active_object; o.name=name; o.scale=size
    bpy.ops.object.transform_apply(scale=True)
    o.matrix_world=Matrix.Translation(Vector(c))@((R or Matrix.Identity(3)).to_4x4())
    if bevel>0: bv=o.modifiers.new('bv','BEVEL'); bv.width=bevel; bv.segments=seg
    o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o
def _cyl(name,a,b,r,mat,verts=32):
    a=Vector(a); b=Vector(b); d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d.length,location=(0,0,0)); o=bpy.context.active_object; o.name=name
    o.matrix_world=Matrix.Translation((a+b)/2)@Vector((0,0,1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o
def _pad_on(P,name,y0,y1,u,width,thick,pad,sink,xmax=0.17):
    """pad aligned with direction u (in the YZ plane) under the body points with y in [y0,y1]; its top touches them"""
    u=np.array(u)/np.linalg.norm(u); nu=np.array((0,-u[2],u[1])); nu=nu if nu[2]>0 else -nu     # up-normal of the pad top
    sel=(P[:,1]>y0)&(P[:,1]<y1)&(np.abs(P[:,0])<xmax)
    top=(P[sel]@nu).min()+sink
    a=P[sel]@u; s0,s1=a.min(),a.max()
    c=u*(s0+s1)/2+nu*(top-thick/2)
    R=Matrix((Vector((1,0,0)),Vector(u),Vector(nu))).transposed()
    _box(name,c,(width,s1-s0,thick),pad,R=R,bevel=0.022,seg=5)
    return Vector(c),Vector(u),Vector(nu),top
def build(hi,rig,KNEE,SHIN,HANDLE,Rb,TH,E):
    for o in [o for o in bpy.data.objects if o.name.startswith('Banco')]: bpy.data.objects.remove(o,do_unlink=True)
    pad=_mat('banco_pad',(0.03,0.03,0.035),0.55); steel=_mat('banco_grey',(0.55,0.55,0.57),0.35,0.6)
    stack=_mat('banco_stack',(0.03,0.03,0.03),0.45,0.3); grip=_mat('banco_grip',(0.02,0.02,0.02),0.8)
    dg=bpy.context.evaluated_depsgraph_get(); m=hi.evaluated_get(dg).to_mesh()
    P=np.zeros(len(m.vertices)*3); m.vertices.foreach_get('co',P); P=P.reshape(-1,3); hi.evaluated_get(dg).to_mesh_clear()
    bb=rig.data.bones; pbn=rig.pose.bones
    hipj=(Vector(pbn['thigh.L'].head)+Vector(pbn['thigh.R'].head))/2; kn=(KNEE[1]+KNEE[-1])/2
    # hip / thigh pad: along the thigh line, from the lower belly to just above the knees
    ut=(kn-hipj).normalized(); ut=Vector((0,ut.y,ut.z)).normalized()
    s_h=np.array(hipj)@np.array(ut); s_k=np.array(kn)@np.array(ut)
    cT,uT,nT,topT=_pad_on(P,'Banco_thighpad',hipj.y-E('PADB',0.16),kn.y-E('PADK',0.06),ut,0.32,0.08,pad,E('SINK',0.007))
    # chest pad: along the torso, under the chest (lower, separate)
    sh=(Vector(pbn['upper_arm.L'].head)+Vector(pbn['upper_arm.R'].head))/2
    uc=(hipj-sh).normalized(); uc=Vector((0,uc.y,uc.z)).normalized()
    s_s=np.array(sh)@np.array(uc)
    cC,uC,nC,topC=_pad_on(P,'Banco_chestpad',sh.y-E('CPF',0.04),sh.y+E('CPB',0.22),uc,0.32,0.08,pad,E('SINK',0.007),xmax=0.12)
    # frame under the pads, down to the floor
    for c,u,n,L in ((cT,uT,nT,0.0),(cC,uC,nC,0.0)):
        under=c-n*0.06
        _box('Banco_padbase',under,(0.20,0.9*((E('PADB',0.20)+0.3) if c is cT else 0.3),0.03),steel,R=Matrix((Vector((1,0,0)),u,n)).transposed(),bevel=0.004)
    yt=cT.y; yc=cC.y
    _cyl('Banco_postT',(0,yt,cT.z-0.10),(0,yt,0.05),0.04,steel)
    _cyl('Banco_postC',(0,yc,cC.z-0.10),(0,yc,0.05),0.04,steel)
    _box('Banco_rail',(0,(yt+yc)/2,0.03),(0.09,abs(yt-yc)+0.9,0.06),steel,bevel=0.008)
    for yy in (yc-0.30,yt+0.45):
        _box('Banco_foot',(0,yy,0.03),(0.70,0.08,0.06),steel,bevel=0.008)
    # knee pivot, lever and roller behind the ankles (calf side)
    PX=E('PIVX',0.25); Ls=bb['shin.L'].length; sd=SHIN[1]
    up=Vector((0,0,1)); t=(kn-hipj).normalized(); post=(up-t*(up@t)).normalized()
    f=math.acos(max(-1,min(1,sd@t))); ps=(post*math.cos(f)-t*math.sin(f)).normalized()
    rc=kn+sd*(E('ROLLKB',0.86)*Ls)+ps*(E('SHINB',0.045)+E('ROLLR',0.045)); rc.x=0
    for s in (1,-1):
        _cyl('Banco_pivot',(s*(PX-0.03),kn.y,kn.z),(s*(PX+0.03),kn.y,kn.z),0.05,steel)
        _cyl('Banco_pivarm',(s*PX,kn.y,kn.z),(s*0.06,yt+0.10,cT.z-0.12),0.022,steel)
        _cyl('Banco_lever',(s*PX,kn.y,kn.z),(s*(PX-0.02),rc.y,rc.z),0.02,steel)
        _cyl('Banco_axle',(s*(PX-0.02),rc.y,rc.z),(s*0.20,rc.y,rc.z),0.012,steel)
        _cyl('Banco_roller',(s*0.02,rc.y,rc.z),(s*0.20,rc.y,rc.z),E('ROLLR',0.045),pad,verts=40)
        h=HANDLE[s]
        _cyl('Banco_handle',(h.x-0.065,h.y,h.z),(h.x+0.065,h.y,h.z),0.017,grip)
        _cyl('Banco_hsup',(h.x-s*0.065,h.y,h.z),(s*0.06,cC.y-0.05,cC.z-0.10),0.014,steel)
    # weight-stack tower behind the bench (far side, -X), centred on the hips
    TXp=E('TOWX',-0.62); y0=hipj.y-0.28; y1=hipj.y+0.28; H=E('TOWH',1.95)
    for yy in (y0,y1): _box('Banco_upright',(TXp,yy,H/2),(0.07,0.07,H),steel,bevel=0.01)
    _box('Banco_top',(TXp,(y0+y1)/2,H-0.035),(0.07,y1-y0+0.07,0.07),steel,bevel=0.01)
    for yy in ((y0+y1)/2-0.08,(y0+y1)/2+0.08): _cyl('Banco_rod',(TXp,yy,0.10),(TXp,yy,H-0.07),0.009,steel)
    _box('Banco_stack',(TXp,(y0+y1)/2,0.36),(0.10,0.34,0.46),stack,bevel=0.008)
    _box('Banco_stacktop',(TXp,(y0+y1)/2,0.62),(0.08,0.28,0.05),stack,bevel=0.006)
    _box('Banco_towbase',(TXp,(y0+y1)/2,0.03),(0.16,y1-y0+0.25,0.06),steel,bevel=0.008)
    _box('Banco_towlink',((TXp+0)/2,hipj.y,0.03),(abs(TXp)+0.05,0.08,0.06),steel,bevel=0.008)
    print('machine: thigh pad top %.3f chest pad top %.3f roller'%(topT,topC),tuple(round(x,3) for x in rc))
