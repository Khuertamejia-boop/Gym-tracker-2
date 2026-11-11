# Leg extension machine built around the posed body: seat and backrest pads touching the body, pivot at the knee,
# lever + double roller on the front of the lower shins, side handles, steel frame on the floor.
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
def build(hi,rig,KNEE,HANDLE,RECL,FLEX,E):
    for o in [o for o in bpy.data.objects if o.name.startswith('Banco')]: bpy.data.objects.remove(o,do_unlink=True)
    pad=_mat('banco_pad',(0.035,0.035,0.04),0.55); steel=_mat('banco_steel',(0.12,0.12,0.13),0.35,0.8); grip=_mat('banco_grip',(0.02,0.02,0.02),0.8)
    dg=bpy.context.evaluated_depsgraph_get(); m=hi.evaluated_get(dg).to_mesh()
    P=np.zeros(len(m.vertices)*3); m.vertices.foreach_get('co',P); P=P.reshape(-1,3); hi.evaluated_get(dg).to_mesh_clear()
    ky=KNEE[1].y; kz=KNEE[1].z
    # seat: top = lowest skin under the buttocks/thighs (a little sink)
    sel=(np.abs(P[:,0])<0.20)&(P[:,1]>ky+0.16)&(P[:,1]<ky+0.55)&(P[:,2]<kz+0.10)&(P[:,2]>kz-0.15)
    seat_top=np.percentile(P[sel,2],1.5)+E('SINK',0.006)
    yb=P[sel,1].max()                                         # back end of the buttocks
    SW,ST=0.36,0.075; sy0=ky+0.07; sy1=yb+0.02
    _box('Banco_seat',(0,(sy0+sy1)/2,seat_top-ST/2),(SW,sy1-sy0,ST),pad,bevel=0.022,seg=5)
    # backrest: plane tangent to the back, reclined
    Rr=Matrix.Rotation(math.radians(-RECL),3,'X'); nb=Rr@Vector((0,1,0)); up=Rr@Vector((0,0,1))
    zb=(P[:,2]>seat_top+0.12)&(P[:,2]<seat_top+0.62)&(np.abs(P[:,0])<0.16)
    off=(P[zb]@np.array(nb)).max()-E('SINK',0.006)
    BH,BT=0.62,0.075; base=Vector((0,sy1,seat_top+0.03))
    c=base+up*(BH/2+0.02); c=c+nb*((off-(c@nb))+BT/2)
    _box('Banco_back',c,(SW,BT,BH),pad,R=Rr,bevel=0.022,seg=5)
    # frame
    _box('Banco_seatbase',(0,(sy0+sy1)/2,seat_top-ST-0.015),(SW*0.8,sy1-sy0,0.03),steel,bevel=0.004)
    _box('Banco_post',(0,(sy0+sy1)/2+0.05,(seat_top-ST)/2),(0.07,0.07,seat_top-ST-0.03),steel,bevel=0.006)
    _box('Banco_rail',(0,ky+0.15,0.025),(0.08,1.05,0.05),steel,bevel=0.006)
    _box('Banco_railx',(0,sy1+0.10,0.025),(0.62,0.07,0.05),steel,bevel=0.006)
    _box('Banco_railx2',(0,ky-0.15,0.025),(0.62,0.07,0.05),steel,bevel=0.006)
    bk=c-nb*(BT/2+0.04); _box('Banco_backpost',bk-up*0.05,(0.07,0.06,BH*0.8),steel,R=Rr,bevel=0.006)
    # pivot housings at the knee axis (both sides), lever arms and roller
    PX=E('PIVX',0.27)
    shin=Matrix.Rotation(math.radians(FLEX),3,'X')@Vector((0,-1,0)); front=Matrix.Rotation(math.radians(-90),3,'X')@shin
    sb=rig.data.bones['shin.L']; Ls=sb.length
    pk=Vector((0,ky,kz))
    if E('ROLLSIDE',1)>0: rc=pk+shin*(E('ROLLK',0.80)*Ls)+front*(E('SHINF',0.030)+E('ROLLR',0.045))
    else: rc=pk+shin*(E('ROLLKB',0.86)*Ls)-front*(E('SHINB',0.045)+E('ROLLR',0.045))   # leg curl: behind the ankles
    for s in (1,-1):
        _cyl('Banco_pivot',(s*(PX-0.03),ky,kz),(s*(PX+0.03),ky,kz),0.055,steel)
        _cyl('Banco_pivpost',(s*PX,ky,kz-0.03),(s*PX,ky,0.05),0.025,steel)
        a=Vector((s*PX,ky,kz)); b=Vector((s*(PX-0.02),rc.y,rc.z))
        _cyl('Banco_lever',a,b,0.018,steel)
        _cyl('Banco_axle',(s*(PX-0.02),rc.y,rc.z),(s*0.205,rc.y,rc.z),0.012,steel)
        _cyl('Banco_roller',(s*0.02,rc.y,rc.z),(s*0.20,rc.y,rc.z),E('ROLLR',0.045),pad,verts=40)
        # side handle (grip along Y) and its support down to the seat frame
        h=HANDLE[s]
        _cyl('Banco_handle',(h.x,h.y-0.075,h.z),(h.x,h.y+0.075,h.z),0.017,grip)
        _cyl('Banco_hsup',(h.x,h.y+0.07,h.z),(h.x,h.y+0.07,seat_top-ST-0.01),0.012,steel)
        _cyl('Banco_hsup2',(h.x,h.y+0.07,seat_top-ST-0.01),(s*SW*0.35,h.y+0.07,seat_top-ST-0.01),0.012,steel)
    if E('LAP',0)>0:
        # thigh hold-down pad (leg curl): roller across the lower thighs, resting on them, held from the pivot housings
        LY=ky+E('LAPY',0.12); RL=E('LAPR',0.045)
        tsel=(np.abs(P[:,1]-LY)<0.012)&(np.abs(P[:,0])<0.20)&(P[:,2]>kz-0.05)&(P[:,2]<kz+0.20)
        zt=P[tsel,2].max(); zc=zt+RL-E('SINK',0.006)
        _cyl('Banco_lap',(-0.20,LY,zc),(0.20,LY,zc),RL,pad,verts=40)
        for s in (1,-1):
            _cyl('Banco_lapaxle',(s*0.20,LY,zc),(s*(PX-0.03),LY,zc),0.012,steel)
            _cyl('Banco_lapstrut',(s*(PX-0.03),LY,zc),(s*(PX-0.03),ky,kz+0.04),0.016,steel)
        print('lap pad z %.3f'%zc)
    print('machine: seat top %.3f, roller centre'%seat_top,tuple(round(x,3) for x in rc))
