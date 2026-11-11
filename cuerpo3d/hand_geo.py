# Procedural mannequin hand already closed around a bar (Skin modifier on a skeleton graph, then subdivided).
# Local frame: origin = bar centre, X = bar axis (thumb on -X), s = finger direction (towards the finger tips), t = palm normal (towards the bar).
import bpy,math,os
import numpy as np
E=lambda k,d: float(os.environ.get(k,d))

def skeleton():
    RB=E('BARR',0.0145); FR=E('FRAD',0.0105); rc=RB+FR          # fingers wrap on a circle around the bar (radius rc)
    V=[]; R=[]; Ed=[]
    def add(p,r): V.append(tuple(p)); R.append(r); return len(V)-1
    # palm and wrist
    W2=add((0.0,-0.150,-0.030),E('W2R',0.0430))     # inside the forearm (hidden)
    W =add((0.0,-0.095,-0.030),E('WR',0.0430))
    P0=add((0.0,-0.052,-0.027),E('P0R',0.0245))
    PL=add((-0.024,-0.020,-0.024),E('PSR',0.0150)); PR=add((0.024,-0.020,-0.024),E('PSR',0.0150))   # palm widens towards the knuckles
    Ed+= [(W2,W),(W,P0),(P0,PL),(P0,PR)]
    sp=E('FSP',0.0205); xs=[-1.5*sp,-0.5*sp,0.5*sp,1.5*sp]; lam=[0.93,1.0,0.94,0.80]; lens=[0.042*E('LS',0.95),0.026*E('LS',0.95),0.021*E('LS',0.95)]
    phi0=math.radians(E('PHI0',-35))
    K=[]
    for x,l in zip(xs,lam):
        # knuckle (MCP) just behind the circle start, lower in the hand
        kp=(x,0.0165,-0.0205); k=add(kp,E('KR',0.0130)); K.append(k); Ed.append((PL if x<0 else PR,k))
        phi=phi0; prev=k
        for j,L in enumerate(lens):
            L*=l; dphi=2*math.asin(min(L/(2*rc),0.999)); phi+=dphi if j>0 else dphi*E('D1',1.0)
            r=[0.0108,0.0100,0.0090][j]*E('FS',1.0)*(0.92 if l<0.9 else 1.0)
            p=(x+0.0,rc*math.cos(phi),rc*math.sin(phi))
            prev=(add((p[0],p[1],p[2]),r) if True else 0)
            if j==0: Ed.append((k,prev))
            else: Ed.append((last,prev))
            last=prev
        # fingertip cap
    # thumb: base on the palm, crosses over the fingers on a bigger circle
    rt=rc+FR+0.0105
    T0=add((-0.043,-0.052,-0.022),0.0128); Ed.append((P0,T0))
    prev=T0
    for ang,x,r in ((195,-0.043,0.0130),(155,-0.036,0.0120),(120,-0.027,0.0112),(96,-0.020,0.0102)):
        p=(x,rt*math.cos(math.radians(ang)),rt*math.sin(math.radians(ang)))
        n=add(p,r); Ed.append((prev,n)); prev=n
    return V,R,Ed

def build(name='Hand',subsurf=2):
    V,R,Ed=skeleton()
    me=bpy.data.meshes.new(name); me.from_pydata(V,Ed,[]); ob=bpy.data.objects.new(name,me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active=ob
    sk=ob.modifiers.new('Skin','SKIN'); sk.branch_smoothing=E('BSM',0.9); sk.use_smooth_shade=True
    for i,r in enumerate(R): me.skin_vertices[0].data[i].radius=(r,r)
    me.skin_vertices[0].data[0].use_root=True
    ss=ob.modifiers.new('Sub','SUBSURF'); ss.levels=subsurf; ss.render_levels=subsurf
    dg=bpy.context.evaluated_depsgraph_get(); ev=ob.evaluated_get(dg); em=bpy.data.meshes.new_from_object(ev)
    nob=bpy.data.objects.new(name+'_mesh',em); bpy.context.scene.collection.objects.link(nob)
    bpy.data.objects.remove(ob,do_unlink=True)
    import bmesh
    bmx=bmesh.new(); bmx.from_mesh(em)
    bmesh.ops.delete(bmx,geom=[v for v in bmx.verts if not v.link_faces],context='VERTS')   # loose specks left by the skin modifier
    bmx.to_mesh(em); bmx.free()
    for p in em.polygons: p.use_smooth=True
    return nob
