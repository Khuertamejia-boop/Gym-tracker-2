# Give the mannequin a face: the original detailed head of the Blender "Human Base Meshes" realistic male body (CC0, the
# body our mannequin was made from: same proportions) is added as object 'Cabeza' (+ eyeballs 'Ojo.L', 'Ojo.R'),
# skinned with the body's own weights so it moves exactly like the neck/head. The smooth mannequin head of 'Hi' is pushed
# inside it (topology unchanged, so the muscle atlas and maps stay valid). The renderer snaps the lowest band of the head
# onto the neck (attribute 'snapw') so the joint does not show, and darkens hair / eyebrows / irises with 'tint'.
#   python -I facebuild.py BUNDLE.blend base.blend out.blend     env: CUTZ (1.44), CUTSL (0.32), LEVEL (2), CAPIN (mm, 12)
import bpy, sys, os, math, numpy as np
from mathutils import Vector
from scipy.spatial import cKDTree
E=lambda k,d: float(os.environ.get(k,d))
bun,src,out=sys.argv[-3],sys.argv[-2],sys.argv[-1]
DX=None                                           # the source body sits ~2.26 m to the side in the bundle (exact value from its matrix)
cutz=lambda y: E('CUTZ',1.44)+E('CUTSL',0.32)*(y+0.08)   # tilted cut through the neck (same tilt as headcap.py, 1.5 cm lower)
# ---------------- 1. source head (multires applied) + eyes, from the bundle
bpy.ops.wm.open_mainfile(filepath=bun)
SRCB=os.environ.get('SRCBODY','GEO-body_male_realistic')
o=bpy.data.objects[SRCB]; o.modifiers[0].levels=int(E('LEVEL',2))
dg=bpy.context.evaluated_depsgraph_get(); me=o.evaluated_get(dg).to_mesh()
M=np.array(o.matrix_world); DX=-M[0,3]; print('source offset x %.5f'%DX)
co=np.array([v.co[:] for v in me.vertices]); co=co@M[:3,:3].T+M[:3,3]; co[:,0]+=DX
# ears: face sets of the source mesh (base level) -> per vertex mask, carried to the multires surface by nearest vertex
bm0=o.data; fsv=np.zeros(len(bm0.polygons),int); bm0.attributes['.sculpt_face_set'].data.foreach_get('value',fsv)
b0=np.array([v.co[:] for v in bm0.vertices])@M[:3,:3].T+M[:3,3]; b0[:,0]+=DX
emask0=np.zeros(len(b0))
for p_,f_ in zip(bm0.polygons,fsv):
    if f_ in [int(x) for x in os.environ.get('EARFS','4,5').split(',')]: emask0[list(p_.vertices)]=1.0
from scipy.spatial import cKDTree as _K
earm=emask0[_K(b0).query(co)[1]]
# clean straight cut (bisect along the tilted plane) instead of whole faces: no staircase edge
import bmesh
bm=bmesh.new(); bm.from_mesh(me)
for v,c_ in zip(bm.verts,co): v.co=c_
el_=bm.verts.layers.float.new('earm')
for v,e_ in zip(bm.verts,earm): v[el_]=float(e_)
far=[v for v in bm.verts if v.co.z<cutz(v.co.y)-0.06]; bmesh.ops.delete(bm,geom=far,context='VERTS')
pn=Vector((0,-E('CUTSL',0.32),1.0)).normalized(); pc=Vector((0,-0.08,E('CUTZ',1.44)))
geom=bm.verts[:]+bm.edges[:]+bm.faces[:]
bmesh.ops.bisect_plane(bm,geom=geom,plane_co=pc,plane_no=pn,clear_inner=True)
bm.verts.ensure_lookup_table()
hco=np.array([v.co[:] for v in bm.verts]); idx={v:i for i,v in enumerate(bm.verts)}; hear=np.array([v[el_] for v in bm.verts])
hfaces=[tuple(idx[v] for v in f.verts) for f in bm.faces]
bm.free()
eyes=[]
for n in (SRCB+'.eye.L',SRCB+'.eye.R'):
    e=bpy.data.objects[n]; em=e.evaluated_get(dg).to_mesh(); Me=np.array(e.matrix_world)
    ec=np.array([v.co[:] for v in em.vertices]); ec=ec@Me[:3,:3].T+Me[:3,3]; ec[:,0]+=DX
    eyes.append((n[-1],ec,[tuple(p.vertices) for p in em.polygons]))
print('head verts %d faces %d'%(len(hco),len(hfaces)))
# ---------------- 2. base file: new objects, weights from the body, cap pushed inside
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; rig=bpy.data.objects['Rig']; bme=hi.data; nv=len(bme.vertices)
bco=np.zeros(nv*3); bme.vertices.foreach_get('co',bco); bco=bco.reshape(-1,3)
bno=np.zeros(nv*3); bme.vertices.foreach_get('normal',bno); bno=bno.reshape(-1,3)
gname={g.index:g.name for g in hi.vertex_groups}
def body_weights(idx):
    w={}
    for g in bme.vertices[int(idx)].groups:
        n=gname[g.group]
        if n in rig.data.bones and g.weight>1e-4: w[n]=g.weight
    return w
R=np.load(os.environ.get('RESTNPZ',os.path.join(os.environ.get('GT3D','.'),'ill','rest.npz')),allow_pickle=True); main=np.array([str(m) for m in R['main']])
upper=np.isin(main,['head','neck','chest','clavicle.L','clavicle.R'])
kd=cKDTree(bco[upper]); upid=np.where(upper)[0]
def make(name,verts,faces):
    m=bpy.data.meshes.new(name); m.from_pydata([tuple(v) for v in verts],[],faces); m.update()
    ob=bpy.data.objects.new(name,m); bpy.context.scene.collection.objects.link(ob)
    for p in m.polygons: p.use_smooth=True
    return ob
FEM=os.environ.get('HAIRSTYLE','')=='bun' and E('FEMFACE',1)>0
if FEM:
    # feminine face (femface.py): narrower jaw and chin, shorter chin, fuller cheeks and lips, softer brow ridge, smaller
    # nose, eyes a little larger; slimmer neck (the same function is applied to the body's neck below)
    sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import femface
    ss_f=femface.ss
    # the face edits fade out before the band that is glued to the neck (1.2 cm): no crease at the joint
    hco,eyes=femface.deform(hco,hfaces,eyes,prot=ss_f((hco[:,2]-cutz(hco[:,1])-E('SNAPH',0.012))/0.02))
    hco=femface.neck_scale(hco,femface.neck_mask(hco))
if E('MANSHAPE',0)>0:
    # masculine athletic face (manface.py, 12-11-2026): squarer jaw and chin, cheekbones, brow ridge, deeper-set eyes
    sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import manface
    hco,eyes=manface.deform(hco,hfaces,eyes,prot=manface.ss((hco[:,2]-cutz(hco[:,1])-E('SNAPH',0.012))/0.02))
if E('EARPIN',0)>0:
    # ears closer to the head: what sticks out beyond EARX0 from the midline is reduced by EARPIN (0..1)
    _dx=np.maximum(np.abs(hco[:,0])-E('EARX0',0.072),0)*np.clip(hear,0,1)*E('EARPIN',0)
    hco[:,0]-=np.sign(hco[:,0])*_dx; hco[:,1]+=0.35*_dx
if E('SMILE',0)>0:
    # slight smile (owner 10-11-2026): the mouth corners rise SMILE m (and go a little back / out), with a smooth
    # gaussian falloff (SMX x SMZ) in the front plane; the cheek just above the corner lifts a little too (SMCH)
    zm_=E('LIPZ',1.5073); xc_=E('LIPW',0.0235)*0.95; ss_s=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
    front_=ss_s((-0.10-hco[:,1])/0.03)
    for sg_ in (1,-1):
        g_=np.exp(-((hco[:,0]-sg_*xc_)/E('SMX',0.010))**2-((hco[:,2]-zm_)/E('SMZ',0.008))**2)*front_
        hco=hco+np.stack([sg_*E('SMILE',0)*0.35*g_, E('SMILE',0)*0.5*g_, E('SMILE',0)*g_],1)
        gc_=np.exp(-((hco[:,0]-sg_*(xc_+0.008))/0.014)**2-((hco[:,2]-zm_-0.016)/0.012)**2)*front_
        hco=hco+np.stack([0*gc_, -E('SMCH',0.0012)*gc_, 0.4*E('SMCH',0.0012)*gc_],1)
    print('smile: corners up %.1f mm'%(E('SMILE',0)*1000))
HREL=None
if E('NECKFIT',0)>0:
    # (13-11-2026, owner: «todavía se ve la unión del cuello y la cabeza: una línea marcada») The stump of this head is
    # 3-13 mm wider than the neck of the mannequin all round the cut AND leaves it at another angle (measured: under the
    # chin it opens 25 deg away from the line of the throat, at the sides 20 deg, on the nape 45 deg). The renderer had to
    # pull its lowest 12 mm onto the neck: a step like the collar of a shirt and, once that was gone, a sharp fold along
    # the joint. Now the stump is fitted onto the neck in the rest pose. Everything is measured and moved along the
    # horizontal-radial direction tilted so that the height h over the (tilted) cut plane never changes:
    #   off(angle, h) = how far the head skin is outside the ORIGINAL neck skin of the mannequin (ray from each head
    #       vertex of the lowest NFS m), fitted per angle round the neck (72 bins, mirrored, smoothed) with a line, or
    #       a parabola when it levels off (nape, sides); above the fitted heights the line goes on straight (under the
    #       chin: the line of the throat, not the old chin of the mannequin) and the parabola stays at its top;
    #   move = (off - NFK.h).w(h),  w = 1 at the cut -> 0 at NFH (NFHB on the nape), no slope at either end.
    # So at the cut the head lies ON the neck skin and goes on with the SAME slope (no step, no fold), lifting off it by
    # NFK (0.06 mm per mm, a 3 deg wedge: the two skins never interleave), and it turns little by little into its own
    # shape up to NFH higher (under the jaw, behind the ear, at the base of the skull).
    from mathutils.bvhtree import BVHTree as _BVn
    _ssn=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
    if E('NFSM',10)>0:
        # the neck skin of the mannequin itself has a small ledge at this very height on both sides of the nape (its
        # profile turns 35 deg within 1 mm): under the old head it was one of the «two small folds of the nape», now it
        # showed as a hair-thin line right along the joint. The skin of the neck is smoothed (no shrinking: Taubin)
        # in a ring NFSMH above and below the cut plane, full at the cut -> nothing at the borders of the ring.
        from scipy.sparse import coo_matrix as _coo
        _ed=np.zeros(len(bme.edges)*2,int); bme.edges.foreach_get('vertices',_ed); _ed=_ed.reshape(-1,2)
        _Am=_coo((np.ones(len(_ed)*2),(np.r_[_ed[:,0],_ed[:,1]],np.r_[_ed[:,1],_ed[:,0]])),shape=(nv,nv)).tocsr(); _dg=np.maximum(np.asarray(_Am.sum(1)).ravel(),1)
        _wsm=_ssn(1-np.abs(bco[:,2]-cutz(bco[:,1]))/E('NFSMH',0.009))*_ssn((0.10-np.hypot(bco[:,0],bco[:,1]-E('NFYC',-0.03)))/0.02)
        _b0=bco.copy()
        for _ in range(int(E('NFSM',10))):
            for lam_ in (0.5,-0.53): bco=bco+((_Am@bco)/_dg[:,None]-bco)*(lam_*_wsm[:,None])
        print('neck fit: neck skin smoothed round the cut, %d verts, max move %.2f mm'%(int((_wsm>0).sum()),np.linalg.norm(bco-_b0,axis=1).max()*1000))
    bme.calc_loop_triangles(); _bt=np.array([t.vertices[:] for t in bme.loop_triangles])
    _bb=_BVn.FromPolygons([tuple(v) for v in bco],[tuple(int(i) for i in t) for t in _bt])
    h0_=hco[:,2]-cutz(hco[:,1]); HREL=h0_.copy(); NFH=E('NFH',0.026); yc_=E('NFYC',-0.03); NB_=72; _cs=E('CUTSL',0.32)
    ang_=lambda P: np.arctan2(P[:,0],-(P[:,1]-yc_))                    # 0 = front, +-pi/2 = sides, pi = nape
    def dir_(th):                                                      # unit direction "outwards at constant h"
        e_=np.stack([np.sin(th),-np.cos(th),-_cs*np.cos(th)],1); return e_/np.linalg.norm(e_,axis=1,keepdims=True)
    ids_=np.where(h0_<E('NFS',0.013))[0]; th0_=ang_(hco[ids_]); e0_=dir_(th0_); off_=np.full(len(ids_),np.nan)
    for k_,i_ in enumerate(ids_):
        hit_=_bb.ray_cast(Vector(hco[i_]+e0_[k_]*0.03),Vector(-e0_[k_]),0.06)
        if hit_[0] is None or float(np.array(hit_[1])@e0_[k_])<0.5 or abs(hit_[3]-0.03)>0.02: continue   # outer neck skin only
        off_[k_]=hit_[3]-0.03
    # in front the old chin of the mannequin starts ~8 mm above the cut: only the throat below it counts there
    hs_=h0_[ids_]; dg_=np.abs(np.degrees(th0_)); ok_=np.isfinite(off_)&(hs_<np.where(dg_<E('NFFR',55.0),E('NFSF',0.007),1.0))
    bin_=np.floor((th0_+math.pi)/(2*math.pi)*NB_).astype(int)%NB_
    # two lines per angle: B,C = the head against the neck skin as it goes on above the cut (the old neck of the
    # mannequin), Bt = against the TANGENT of the neck skin at the cut (samples of the lowest NFST m only). Above the cut
    # the old skin bends in towards the old jaw at the front and sides: a head that follows that bend and then opens out
    # to its own jaw makes an S (a light fringe over a dark one along the joint, on the shadow side); on the nape the
    # old skin bends out and must be followed. The head takes whichever keeps it further OUT: min(tangent, old skin).
    B_=np.zeros(NB_); C_=np.zeros(NB_); Bt_=np.zeros(NB_); has_=np.zeros(NB_,bool); hast_=np.zeros(NB_,bool)
    for b_ in range(NB_):
        d_=(bin_-b_+NB_//2)%NB_-NB_//2; m_=ok_&(np.abs(d_)<=2)
        if m_.sum()>=8 and np.ptp(hs_[m_])>=0.004:
            wt_=np.array([1.0,0.6,0.3])[np.abs(d_[m_])]; x_=hs_[m_]; y_=off_[m_]; sw_=np.sqrt(wt_)
            q_=np.linalg.lstsq(np.stack([np.ones(len(x_)),x_,x_*x_],1)*sw_[:,None],y_*sw_,rcond=None)[0]
            if q_[2]<0 and np.ptp(x_)>0.008: B_[b_],C_[b_]=q_[1],q_[2]
            else: B_[b_]=np.linalg.lstsq(np.stack([np.ones(len(x_)),x_],1)*sw_[:,None],y_*sw_,rcond=None)[0][1]; C_[b_]=0.0
            has_[b_]=True
        m_=m_&(hs_<E('NFST',0.0036))
        if m_.sum()>=6 and np.ptp(hs_[m_])>=0.0015:
            wt_=np.array([1.0,0.6,0.3])[np.abs(d_[m_])]; x_=hs_[m_]; y_=off_[m_]; sw_=np.sqrt(wt_)
            Bt_[b_]=np.linalg.lstsq(np.stack([np.ones(len(x_)),x_],1)*sw_[:,None],y_*sw_,rcond=None)[0][1]; hast_[b_]=True
    assert has_.sum()>NB_*0.8 and hast_.sum()>NB_*0.8, 'neck fit: too few samples round the cut'
    for arr_,hz_ in ((B_,has_),(C_,has_),(Bt_,hast_)): arr_[~hz_]=np.interp(np.where(~hz_)[0],np.where(hz_)[0],arr_[hz_],period=NB_)
    mir_=lambda a_: 0.5*(a_+a_[::-1])                                  # bins are symmetric about x = 0 (bin b <-> NB-1-b)
    def _smc(a_,n_=2):                                                 # circular smoothing
        for _ in range(n_): a_=0.25*np.roll(a_,1,0)+0.5*a_+0.25*np.roll(a_,-1,0)
        return a_
    B_=_smc(mir_(B_)); C_=np.minimum(_smc(mir_(C_)),0.0); Bt_=_smc(mir_(Bt_))
    # A = how far the head is outside the neck AT the cut: not per bin (the smoothing left the edge up to 1.3 mm off
    # the skin where it changes fast, e.g. the groove of the nape) but from the edge vertices themselves, by angle
    lp_=np.where(np.isfinite(off_)&(hs_<0.0004))[0]; lp_=lp_[np.argsort(th0_[lp_])]; thL_=th0_[lp_]; aL_=off_[lp_]
    aL_=0.25*np.roll(aL_,1)+0.5*aL_+0.25*np.roll(aL_,-1)
    Af_=lambda th: np.interp(th,thL_,aL_,period=2*math.pi)
    # the fit is longer on the nape (NFHB: there is room up to the base of the skull) than in front and at the sides
    # (NFH: the chin and the angle of the jaw are close)
    NFHB=E('NFHB',0.045); sel_=np.where(h0_<max(NFH,NFHB))[0]; th_=ang_(hco[sel_])
    Hs_=NFH+(NFHB-NFH)*_ssn((np.abs(np.degrees(th_))-E('NFB0',80.0))/(E('NFB1',150.0)-E('NFB0',80.0)))
    a_=(th_+math.pi)/(2*math.pi)*NB_-0.5; i0_=np.floor(a_).astype(int); f_=a_-i0_
    lerp_=lambda arr_: arr_[i0_%NB_]*(1-f_)+arr_[(i0_+1)%NB_]*f_
    hh_=np.maximum(h0_[sel_],0.0); w_=1.0-_ssn(hh_/Hs_); a2_=Af_(th_); b2_=lerp_(B_); c2_=lerp_(C_); bt_=lerp_(Bt_)
    hv_=np.where(c2_<-1e-9,np.clip(-b2_/np.minimum(2*c2_,-1e-9),0.0,None),1e9); hq_=np.minimum(hh_,hv_)   # parabola: held at its top
    bt_=bt_+_ssn((np.abs(np.degrees(th_))-E('NFT0',105.0))/(E('NFT1',125.0)-E('NFT0',105.0)))     # nape: the old skin only (the tangent never wins)
    g_=np.clip(a2_+np.minimum(b2_*hq_+c2_*hq_*hq_,bt_*hh_),-E('NFMAX',0.016),E('NFMAX',0.016))
    dl_=(g_-E('NFK',0.06)*hh_)*w_*E('NECKFIT',0)
    hco[sel_]=hco[sel_]-dir_(th_)*dl_[:,None]
    print('neck fit: outside the neck at the cut %.1f..%.1f mm (mean %.1f), slope %.2f..%.2f (tangent %.2f..%.2f), max move %.1f mm, %d verts, %d samples'%(
        aL_.min()*1000,aL_.max()*1000,aL_.mean()*1000,B_.min(),B_.max(),Bt_.min(),Bt_.max(),np.abs(dl_).max()*1000,len(sel_),int(ok_.sum())))
    if os.environ.get('NFDBG'):
        for b_ in range(NB_//2,NB_,4): print('  bin %2d ang %4.0f  A %5.1f mm  B %5.2f  C %7.1f  Bt %5.2f'%(b_,(b_+0.5)/NB_*360-180,float(Af_(np.array([(b_+0.5)/NB_*2*math.pi-math.pi]))[0])*1000,B_[b_],C_[b_],Bt_[b_]))
cab=make('Cabeza',hco,hfaces)
cab['cutz']=E('CUTZ',1.44); cab['cutsl']=E('CUTSL',0.32)          # the cut plane (rest pose), for the renderer
cab['snaph']=E('SNAPH',0.012); cab['nfk']=E('NFK',0.06) if E('NECKFIT',0)>0 else 0.0   # height of the 'snapw' band; wedge of the neck fit (0 = no fit)
# ---- hair (short, buzz cut) and eyebrows: darkness 'tint' for the renderer
ss_=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
hn=np.zeros(len(hco)*3); cab.data.vertices.foreach_get('normal',hn); hn=hn.reshape(-1,3)
# skin (no hair) region seen from the side, (y, z): forehead, temple, sideburn, around the ear, behind the ear, nape
SKIN=np.array([(-0.30,1.30),(-0.30,1.646),(-0.112,1.646),(-0.104,1.632),(-0.096,1.612),(-0.088,1.595),(-0.082,1.578),
               (-0.078,1.566),(-0.072,1.560),(-0.064,1.565),(-0.061,1.585),(-0.052,1.597),(-0.038,1.600),(-0.024,1.596),
               (-0.015,1.585),(-0.010,1.565),(-0.006,1.545),(0.002,1.525),(0.012,1.512),(0.030,1.506),(0.20,1.504),(0.20,1.30)])
# (measured on the head: ear y -0.058..-0.016, z 1.52..1.59; the hair comes down to ~5 mm from the ear)
def sdist(px,py,poly):
    """signed distance of points to a closed polygon (negative inside)"""
    x0,y0=poly[:,0],poly[:,1]; x1,y1=np.roll(x0,-1),np.roll(y0,-1)
    dmin=np.full(len(px),9.0); inside=np.zeros(len(px),bool)
    for i in range(len(poly)):
        ex,ey=x1[i]-x0[i],y1[i]-y0[i]; t=np.clip(((px-x0[i])*ex+(py-y0[i])*ey)/max(ex*ex+ey*ey,1e-12),0,1)
        dmin=np.minimum(dmin,np.hypot(px-(x0[i]+t*ex),py-(y0[i]+t*ey)))
        cr=((y0[i]>py)!=(y1[i]>py))&(px<(x1[i]-x0[i])*(py-y0[i])/np.where(y1[i]-y0[i]==0,1e-12,y1[i]-y0[i])+x0[i]); inside^=cr
    return np.where(inside,-dmin,dmin)
ax0=np.abs(hco[:,0])
FADE=os.environ.get('HAIRSTYLE','')=='fade'
rec=E('HREC',0.0 if FADE else 0.009)*ss_((ax0-0.018)/0.032)*(hco[:,1]<-0.10)          # temples recede a little (soft M shape)
ZO=E('ZOFF',0.0)
if os.environ.get('HAIRSTYLE','')=='bun':
    SKIN=np.array([(-0.30,1.30),(-0.30,1.641),(-0.114,1.641),(-0.106,1.630),(-0.097,1.613),(-0.089,1.596),(-0.082,1.582),
                   (-0.074,1.574),(-0.066,1.582),(-0.062,1.598),(-0.052,1.606),(-0.036,1.608),(-0.022,1.602),(-0.012,1.588),
                   (-0.006,1.565),(0.000,1.540),(0.010,1.520),(0.030,1.508),(0.20,1.504),(0.20,1.30)])
if FADE:
    # skin fade with a lined-up front (owner's photo, 12-11-2026): straight front hairline at HLZ with a squared temple
    # corner (the temple edge is a vertical line at y = HTY in the side view), short sideburn, around the ear, nape
    HLZ=E('HLZ',1.648); TY_=E('HTY',-0.091)
    SKIN=np.array([(-0.30,1.30),(-0.30,HLZ),(TY_-0.004,HLZ),(TY_,HLZ-0.004),(TY_+0.001,1.615),(TY_+0.004,1.590),(-0.082,1.572),
                   (-0.077,1.560),(-0.071,1.556),(-0.064,1.562),(-0.061,1.585),(-0.052,1.597),(-0.038,1.600),(-0.024,1.596),
                   (-0.015,1.585),(-0.010,1.565),(-0.006,1.545),(0.002,1.525),(0.012,1.512),(0.030,1.506),(0.20,1.504),(0.20,1.30)])
sd=sdist(hco[:,1],hco[:,2]-ZO-rec,SKIN)
hair=ss_((sd+E('HSOFT',0.0035))/(2*E('HSOFT',0.0035)))
dens=hair
if FADE:
    hs_=E('HSOFT',0.0012); hair=np.clip((sd+hs_)/(2*hs_),0,1)         # crisp line-up: linear ramp ~2.4 mm (wider than the mesh)
    # the fade: hair darkness by height. Middle of the gradient at FZT over the temple, FZE over the ear, FZB at the
    # back of the head; FW = half height of the gradient; FMIN = faint shadow of the shaved part (never bare 'skin')
    yb_=hco[:,1]; u_=ss_((yb_+0.090)/0.050); v_=ss_((yb_+0.020)/0.070)
    zf_=E('FZT',1.628)+(E('FZE',1.622)-E('FZT',1.628))*u_+(E('FZB',1.585)-E('FZE',1.622))*v_
    fd_=ss_((hco[:,2]-ZO-zf_)/(2*E('FW',0.026))+0.5)**E('FP',1.3)
    dens=hair*(E('FMIN',0.06)+(1-E('FMIN',0.06))*fd_)
    densv=ss_(sd/E('HVR',0.014))*fd_*(1.0-np.clip(hear*1.5,0,1))       # for the volume: grows inside the hair, 0 at the hairline (no ledge)
hair=hair*(1.0-np.clip(hear*1.5,0,1)); dens=dens*(1.0-np.clip(hear*1.5,0,1))     # never on the ear itself
# eyebrows (owner's reference photo, 28-10-2026): thick, dense, almost straight, soft arch at the outer third, tail
# thinning and dropping a little; the head (next to the nose) lighter and fuzzy with hairs pointing up.
# 'bw' = coordinate across the hairs (mm) for the renderer's hair strokes; 'bmask' = brow amount
brow=np.zeros(len(hco)); bw=np.zeros(len(hco))
for sg in (1,-1):
    xs=sg*hco[:,0]
    u=(xs-E('BX0',0.011))/(E('BX1',0.062)-E('BX0',0.011)); uc=np.clip(u,0,1)
    if os.environ.get('HAIRSTYLE','')=='bun':      # female: thinner, more arched
        bot=E('BZB',1.5885)+ZO-E('BDROP',0.0003)+0.0026*ss_(uc/0.62)-0.0068*ss_((uc-0.62)/0.38)   # soft arch, head not low (no frown)
        top=bot+E('BTH',0.0060)*(1-0.50*uc)+0.001*ss_(uc/0.5)
    else:
        bot=E('BZB',1.5885)+ZO+0.003*uc-0.005*ss_((uc-0.7)/0.3)
        top=E('BZT',1.5965)+ZO+0.0025*ss_(uc/0.6)-0.0075*ss_((uc-0.6)/0.4)
    mid=0.5*(bot+top); half=0.5*(top-bot)*(0.55+0.45*ss_((1-uc)/0.15))     # rounded thin end of the tail
    inn=ss_((half-np.abs(hco[:,2]-mid))/E('BSOFT',0.0016)+0.5)
    inn*=ss_(u/0.16+0.35)*ss_((1-u)/0.05+0.2)                                 # fuzzy start, thin tail
    inn*=(0.72+0.28*ss_(uc/0.22))*(1-0.12*ss_((uc-0.8)/0.2))                 # lighter head, dense body
    inn*=(xs>0)*(hn[:,1]<-0.25)*(hco[:,1]<-0.09)
    ang=np.radians(80-55*ss_(uc/0.3)-12*ss_((uc-0.5)/0.5))                   # hair direction: up at the head, outwards
    w_=(-np.sin(ang)*(xs-0.035)+np.cos(ang)*(hco[:,2]-1.592-ZO))*1000.0      # small, continuous on each side (no jumps)
    bw[xs>0]=w_[xs>0]; brow=np.maximum(brow,inn)
a_=cab.data.attributes.new('bmask','FLOAT','POINT'); a_.data.foreach_set('value',brow.astype(np.float32))
a_=cab.data.attributes.new('bw','FLOAT','POINT'); a_.data.foreach_set('value',bw.astype(np.float32))
tint=np.maximum(dens*E('HAIRT',0.51),brow*E('BROWT',0.95))
if (os.environ.get('HAIRSTYLE','')=='bun' and E('FEMFACE',1)>0) or E('MANFACE',0)>0:   # MANFACE=1: lips / mouth line / lashes on the man too
    ss1=lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
    # lips: a little darker (natural lip colour in a grey plate), upper lip thinner than the lower one
    # (28-10 v3) real lip shape: mouth line measured on the head (corners a little lower), upper lip with the cupid's bow
    # (two peaks, dip in the middle), fuller rounded lower lip, soft 0.8 mm edge; a thin darker mouth line
    W_=E('LIPW',0.0235); ax_=np.abs(hco[:,0])/W_; Zh=hco[:,2]
    zm=E('LIPZ',1.4673)-E('LIPDN',0.0015)*np.clip(np.abs(hco[:,0])/0.022,0,1.2)**2     # corners only a little lower (not sad)
    hu=(0.0088+0.0017*np.exp(-((np.abs(hco[:,0])-0.0058)/0.0030)**2))*np.clip(1-ax_**2.2,0,1)**0.65
    hl=0.0102*np.clip(1-ax_**2,0,1)**0.6
    lin=lambda t: np.clip(t,0,1)                      # linear ramps ~2 mm (wider than the mesh): smooth edge, no staircase
    lip=lin((zm+hu-Zh)/E('LIPS',0.0022)+0.5)*lin((Zh-zm+hl)/E('LIPS',0.0022)+0.5)*ss1((1-ax_)/0.10)
    lip=lip*(1+0.12*(Zh>zm))*(hn[:,1]<-0.3)*(hco[:,1]<-0.13)
    mline=np.exp(-((Zh-zm)/0.0011)**2)*ss1((1-ax_)/0.15)*(hn[:,1]<-0.1)*(hco[:,1]<-0.13)
    # lash line: dark along the upper lid margin (thicker towards the outer corner), lighter below
    lash=np.zeros(len(hco))
    for L_,ec_,ef_ in eyes:
        c_=ec_.mean(0); r_=np.linalg.norm(ec_-c_,axis=1).mean(); v_=hco-c_; d_=np.linalg.norm(v_,axis=1)
        near=ss1((r_+E('LASHD',0.0032)-d_)/0.0012)*(v_[:,1]<0)
        up=ss1(v_[:,2]/0.002); outer=0.75+0.25*ss1((np.sign(c_[0])*v_[:,0])/0.008)
        lash=np.maximum(lash,near*(up*outer*E('LASHT',0.92)+(1-up)*E('LASHB',0.35)))
    tint=np.maximum.reduce([tint,lip*E('LIPT',0.36),mline*E('MLINE',0.55),lash])
    print('lips verts',int((lip>0.5).sum()),'lash verts',int((lash>0.5).sum()))
# hair volume: pulled-back hair lies a few mm over the skull (fuller head, soft step at the hairline)
if FADE and E('HVOL',0)>0:
    # short hair has thickness: HVOL mm where it is dark (0 on the shaved part), + HTOPV mm on the top of the head
    hv=(E('HVOL',0)+E('HTOPV',0)*ss_((hco[:,2]-ZO-E('HTOPZ',1.628))/0.030))/1000.0*np.clip(densv,0,1)**0.8
    hco=hco+hn*hv[:,None]; cab.data.vertices.foreach_set('co',hco.astype(np.float32).ravel()); cab.data.update()
elif E('HVOL',0)>0:
    hv=E('HVOL',0)/1000.0*hair*(0.6+0.4*np.clip((hco[:,2]-hco[:,2].min())/(hco[:,2].max()-hco[:,2].min()),0,1))
    hco=hco+hn*hv[:,None]; cab.data.vertices.foreach_set('co',hco.astype(np.float32).ravel()); cab.data.update()
# hair strands: across-strand coordinate 'hw' (mm) = angle around the axis head centre -> bun (strands run to the bun)
if os.environ.get('HAIRSTYLE','')=='bun':
    BC=np.array((0.0,E('BUNY',0.018),E('BUNZ',1.612)))         # bun centre (female head)
    HC=np.array((0.0,-0.045,1.53))
    ax=(BC-HC)/np.linalg.norm(BC-HC); e1=np.cross(ax,(1.0,0,0)); e1/=np.linalg.norm(e1); e2=np.cross(ax,e1)
    rv=hco-HC; phi=np.arctan2(rv@e2,rv@e1)
    hw=phi*90.0
    a_=cab.data.attributes.new('hmask','FLOAT','POINT'); a_.data.foreach_set('value',hair.astype(np.float32))
    a_=cab.data.attributes.new('hw','FLOAT','POINT'); a_.data.foreach_set('value',hw.astype(np.float32))
    # the bun: a slightly flattened ball of hair, twisted strands ('hw' around its own axis), on the head bone
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=E('BUNR',0.034),location=tuple(BC))
    bun=bpy.context.active_object; bun.name='Ojo.Mono'
    bc=np.array([v.co[:] for v in bun.data.vertices]); M_=np.array(bun.matrix_world); bc=bc@M_[:3,:3].T+M_[:3,3]
    rel=bc-BC; rel=rel-np.outer(rel@ax,ax)*(1-E('BUNFLAT',0.72))          # flattened along the axis
    bc=BC+rel; bun.matrix_world.identity()
    bun.data.vertices.foreach_set('co',bc.astype(np.float32).ravel()); bun.data.update()
    for p_ in bun.data.polygons: p_.use_smooth=True
    rv=bc-BC; ang_=np.arctan2(rv@e2,rv@e1); tw=(rv@ax)/E('BUNR',0.034)
    a_=bun.data.attributes.new('tint','FLOAT','POINT'); a_.data.foreach_set('value',np.full(len(bc),E('HAIRT',0.51),np.float32))
    a_=bun.data.attributes.new('hmask','FLOAT','POINT'); a_.data.foreach_set('value',np.ones(len(bc),np.float32))
    a_=bun.data.attributes.new('hw','FLOAT','POINT'); a_.data.foreach_set('value',((ang_+1.2*tw)*40.0).astype(np.float32))
    g=bun.vertex_groups.new(name='head'); g.add(list(range(len(bc))),1.0,'REPLACE')
    mb=bun.modifiers.new('Armature','ARMATURE'); mb.object=rig
a=cab.data.attributes.new('tint','FLOAT','POINT'); a.data.foreach_set('value',tint.astype(np.float32))
if E('FACEATTR',0)>0:
    # 'face' = how much of the face shading (rendsculpt.py FELT / FAOP / FCON) applies: the same function of the rest
    # height that the renderer gives to the neck of the body (0 at the base of the neck -> 1 under the jaw): no joint
    zn_=float(rig.data.bones['neck'].head_local[2]); fa_=ss_((hco[:,2]-(zn_-E('FNZ0',0.012)))/E('FNZH',0.070))
    a=cab.data.attributes.new('face','FLOAT','POINT'); a.data.foreach_set('value',fa_.astype(np.float32))
    a=cab.data.attributes.new('hstip','FLOAT','POINT'); a.data.foreach_set('value',(hair if FADE else 0*hair).astype(np.float32))
    a=cab.data.attributes.new('hrest','FLOAT_VECTOR','POINT'); a.data.foreach_set('vector',hco.astype(np.float32).ravel())
print('hair verts',int((hair>0.5).sum()),'brow verts',int((brow>0.5).sum()))
# weights: nearest body vertex of the ORIGINAL surface (neck band) / head bone for the face
d,ii=kd.query(hco); src_ids=upid[ii]
grp={}
for vi,bi in enumerate(src_ids):
    for n,wv in body_weights(bi).items():
        g=grp.get(n) or cab.vertex_groups.new(name=n); grp[n]=g; g.add([vi],wv,'REPLACE')
am=cab.modifiers.new('Armature','ARMATURE'); am.object=rig
# snap band: 1 at the cut edge -> 0 at 1.2 cm above it
h=HREL if HREL is not None else hco[:,2]-cutz(hco[:,1])      # NECKFIT: height above the cut BEFORE the taper
snapw=np.clip(1-h/E('SNAPH',0.012),0,1); snapw=snapw*snapw*(3-2*snapw)
a=cab.data.attributes.new('snapw','FLOAT','POINT'); a.data.foreach_set('value',snapw.astype(np.float32))
for L,ec,ef in eyes:
    ob=make('Ojo.'+L,ec,ef)
    bpy.context.view_layer.objects.active=ob; sm=ob.modifiers.new('s','SUBSURF'); sm.levels=int(E('EYESUB',3))
    bpy.ops.object.modifier_apply(modifier='s'); ec=np.array([v.co[:] for v in ob.data.vertices])
    g=ob.vertex_groups.new(name='head'); g.add(list(range(len(ec))),1.0,'REPLACE')
    m2=ob.modifiers.new('Armature','ARMATURE'); m2.object=rig
    c=ec.mean(0); r=np.linalg.norm(ec-c,axis=1).mean(); fwd=np.array((0,-1.0,0))
    cosang=((ec-c)@fwd)/np.maximum(np.linalg.norm(ec-c,axis=1),1e-9)
    ang=np.degrees(np.arccos(np.clip(cosang,-1,1)))
    # iris (~11 mm wide on a 24 mm eye ~ 27 deg) and pupil (~10 deg): darkness for the renderer's 'tint'
    sm_=lambda a,b,x: np.clip((x-a)/(b-a),0,1)**2*(3-2*np.clip((x-a)/(b-a),0,1))
    t=0.45*(1-sm_(E('IRISA',27)-1.5,E('IRISA',27)+1.0,ang))+0.42*(1-sm_(E('PUPA',10)-1.0,E('PUPA',10)+1.0,ang))
    if E('EYEV2',0)>0:
        # (12-11-2026) living eye: iris darker towards its rim (limbal ring) and a little lighter around the pupil, black
        # pupil, a small catchlight up and to the viewer's left (where the key light is), white of the eye a little brighter
        ir_=E('IRISA',27); pu_=E('PUPA',10)
        iris_=1-sm_(ir_-0.5,ir_+1.2,ang); rad_=np.clip((ang-pu_)/(ir_-pu_),0,1)
        t=iris_*(E('IRIST',0.58)+E('LIMT',0.26)*sm_(0.55,1.0,rad_)+E('IRISG',0.08)*(1-sm_(0.0,0.5,rad_)))
        # iris fibres: fine radial streaks (a smooth pseudo-random function of the angle around the eye axis)
        az_=np.arctan2((ec-c)[:,2],(ec-c)[:,0])
        fib_=0.5*np.sin(37*az_+1.3*np.sin(11*az_))+0.5*np.sin(23*az_+2.1+0.8*np.sin(5*az_))
        t=t+E('IRISF',0.07)*fib_*iris_*sm_(0.08,0.30,rad_)*(1-sm_(0.80,1.0,rad_))
        t=np.clip(np.maximum(t,(1-sm_(pu_-1.0,pu_+1.0,ang))*E('PUPT',0.97)),0,1)
        gd_=np.array((E('GLX',-0.26),-1.0,E('GLZ',0.24))); gd_/=np.linalg.norm(gd_)
        ga_=np.degrees(np.arccos(np.clip(((ec-c)@gd_)/np.maximum(np.linalg.norm(ec-c,axis=1),1e-9),-1,1)))
        gl_=1-sm_(E('GLR',4.2)-1.0,E('GLR',4.2)+1.0,ga_)
        gl_=np.maximum(gl_,E('EYEW',0.20)*(1-iris_)*(cosang>0.2))
        t=t*(1-gl_*(gl_>0.5))
        a=ob.data.attributes.new('glint','FLOAT','POINT'); a.data.foreach_set('value',gl_.astype(np.float32))
        a=ob.data.attributes.new('face','FLOAT','POINT'); a.data.foreach_set('value',np.full(len(ec),E('EYEFACE',0.3),np.float32))
    a=ob.data.attributes.new('tint','FLOAT','POINT'); a.data.foreach_set('value',t.astype(np.float32))
    print('eye',L,'centre',np.round(c,3),'r %.4f'%r)
# body cap pushed inside the new head: from 0.8 cm above the cut, up to CAPIN mm (smooth), only the head region
hb=np.isin(main,['head','neck'])
hh=bco[:,2]-cutz(bco[:,1])
push=np.clip((hh-E('CAP0',0.008))/(E('CAP1',0.03)-E('CAP0',0.008)),0,1); push=push*push*(3-2*push)*hb
bco=bco-bno*(push[:,None]*E('CAPIN',12)/1000.0)
if FEM: bco=femface.neck_scale(bco,femface.neck_mask(bco))
# guarantee: no vertex of the old cap pokes through the new head (keep it >= CAPMIN mm inside)
from mathutils.bvhtree import BVHTree
_bv=BVHTree.FromPolygons([tuple(v) for v in hco],[tuple(f) for f in hfaces])
moved_=0
for i in np.where(hb&(hh>E('CAP0',0.008)))[0]:
    loc,nrm,_,dist=_bv.find_nearest(Vector(bco[i]))
    if loc is None: continue
    sdist_=(bco[i]-np.array(loc))@np.array(nrm)
    if sdist_>-E('CAPMIN',3)/1000.0: bco[i]=np.array(loc)-np.array(nrm)*E('CAPMIN',3)/1000.0; moved_+=1
print('cap verts clamped inside',moved_)
if E('NECKFIT',0)>0 and not FEM:
    # with the neck fit the new head follows the line of the throat higher up, and the lowest lip of the OLD chin of the
    # mannequin (it dips below CAP0, so the cap above did not take it) stuck out under the new chin: a small dark spot
    # in front, a tiny spike in profile. The skin of the old head that faces down (old chin and jaw, not the neck skin,
    # which the head band lies on) between CAPL and CAP0 above the cut goes CAPMIN inside the new head too.
    _th=np.abs(np.degrees(np.arctan2(bco[:,0],-(bco[:,1]-E('NFYC',-0.03))))); lip_=0
    for i in np.where(hb&(hh>E('CAPL',0.001))&(hh<=E('CAP0',0.008))&(bno[:,2]<-E('CAPNZ',0.5))&(_th<E('CAPTH',110.0)))[0]:
        loc,nrm,_,dist=_bv.find_nearest(Vector(bco[i]))
        if loc is None: continue
        if (bco[i]-np.array(loc))@np.array(nrm)>-E('CAPMIN',3)/1000.0: bco[i]=np.array(loc)-np.array(nrm)*E('CAPMIN',3)/1000.0; lip_+=1
    print('neck fit: old chin lip, %d verts put inside the head'%lip_)
bme.vertices.foreach_set('co',bco.ravel()); bme.update()
print('cap verts pushed',int((push>0.01).sum()))
bpy.ops.wm.save_as_mainfile(filepath=out)
