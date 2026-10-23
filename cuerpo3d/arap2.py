# Shoulder skin after posing, "as-rigid-as-possible": inside a ball around each shoulder joint the skin finds the
# position where every small patch keeps its rest shape as well as possible (only turning), between the torso and
# the arm, which stay where the skinning put them. Removes pinches, folds and the stretched/flared armpit.
# Bakes the mesh.  usage: RESTBLEND=NB_s.blend python arap2.py posed.blend out.blend   env RAD, IT (iterations)
# arap2: for frames whose skinning was already baked (pullup6 / CoR): the rest shape is read from RESTBLEND.
import bpy,sys,os,time
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
src,out=sys.argv[-2],sys.argv[-1]
E=lambda k,d: float(os.environ.get(k,d))
t0=time.time()
bpy.ops.wm.open_mainfile(filepath=src)
hi=bpy.data.objects['Hi']; rig=bpy.data.objects['Rig']; me=hi.data; nv=len(me.vertices)
for m in hi.modifiers:
    if m.name=='CorrectiveSmooth2' and E('KEEPCS2',0)==0: m.show_viewport=False
dg=bpy.context.evaluated_depsgraph_get(); ev=hi.evaluated_get(dg)
newme=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=dg)
X=np.zeros(nv*3); newme.vertices.foreach_get('co',X); X=X.reshape(-1,3)
if os.environ.get('RESTBLEND'):
    _lib=bpy.data.libraries.load(os.environ['RESTBLEND'])
    with _lib as (src_,dst_): dst_.meshes=[n for n in src_.meshes]
    _rm=[m for m in dst_.meshes if m and len(m.vertices)==nv][0]
    P=np.zeros(nv*3); _rm.vertices.foreach_get('co',P); P=P.reshape(-1,3)
else:
    P=np.zeros(nv*3); me.vertices.foreach_get('co',P); P=P.reshape(-1,3)
ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
gname={g.index:g.name for g in hi.vertex_groups}
RAD=E('RAD',0.22)
d=np.min([np.linalg.norm(P-np.array(rig.data.bones['upper_arm.'+L].head_local),axis=1) for L in 'LR'],axis=0)
cand=np.where(d<RAD)[0]
fixw=np.zeros(nv)
for i in cand:
    for g in me.vertices[int(i)].groups:
        n=gname.get(g.group,'')
        if n in ('neck','head') or n.startswith(('forearm','hand')): fixw[i]+=g.weight
free=np.zeros(nv,bool); free[cand]=fixw[cand]<E('NECKFIX',0.3)
idx=np.where(free)[0]; nf=len(idx); pos=-np.ones(nv,int); pos[idx]=np.arange(nf)
print('free verts',nf)
# triangles near the region -> edges with cotangent weights (more even than uniform weights)
near=np.zeros(nv,bool); near[cand]=True
lt=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_total',lt)
ls=np.zeros(len(me.polygons),int); me.polygons.foreach_get('loop_start',ls)
lv=np.zeros(len(me.loops),int); me.loops.foreach_get('vertex_index',lv)
tris=[]
for n_ in (3,4):
    sel=np.where(lt==n_)[0]; vv=lv[ls[sel][:,None]+np.arange(n_)]
    ok=near[vv].any(1); vv=vv[ok]
    tris.append(vv[:,[0,1,2]])
    if n_==4: tris.append(vv[:,[0,2,3]])
T=np.vstack(tris)
def cot(u,v): return np.einsum('ij,ij->i',u,v)/np.maximum(np.linalg.norm(np.cross(u,v),axis=1),1e-12)
I,J,K=T[:,0],T[:,1],T[:,2]
cK=cot(P[I]-P[K],P[J]-P[K]); cI=cot(P[J]-P[I],P[K]-P[I]); cJ=cot(P[K]-P[J],P[I]-P[J])
ea=np.r_[I,J,K]; eb=np.r_[J,K,I]; ew=0.5*np.r_[cK,cI,cJ]
lo=np.minimum(ea,eb); hi_=np.maximum(ea,eb); key=lo.astype(np.int64)*nv+hi_
uk,inv_=np.unique(key,return_inverse=True); w=np.bincount(inv_,ew)
a=(uk//nv).astype(int); b=(uk%nv).astype(int)
w=np.maximum(w,E('WMIN',0.05))
if E('WUNI',0)>0: w=np.ones_like(w)
ek=free[a]|free[b]; a,b,w=a[ek],b[ek],w[ek]
print('edges',len(a),'weight mean %.3f'%w.mean())
ep=P[a]-P[b]
inv=np.unique(np.r_[a,b]); vpos=-np.ones(nv,int); vpos[inv]=np.arange(len(inv))
fa,fb=free[a],free[b]; ff=fa&fb
degw=np.bincount(np.r_[a,b],np.r_[w,w],minlength=nv)
L=sp.coo_matrix((np.r_[-w[ff],-w[ff]],(np.r_[pos[a[ff]],pos[b[ff]]],np.r_[pos[b[ff]],pos[a[ff]]])),shape=(nf,nf)).tocsr()
L=L+sp.diags(degw[idx])
lu=sla.splu(L.tocsc(),permc_spec='COLAMD')
def rotations(X):
    ex=X[a]-X[b]; O=(w[:,None,None]*np.einsum('ni,nj->nij',ep,ex)).reshape(-1,9)
    S=np.zeros((len(inv),9))
    for k in range(9):
        S[:,k]=np.bincount(vpos[a],O[:,k],len(inv))+np.bincount(vpos[b],O[:,k],len(inv))
    S=S.reshape(-1,3,3); U,s,Vt=np.linalg.svd(S)
    R=np.einsum('nji,nkj->nik',Vt,U)          # R = V U^T
    bad=np.linalg.det(R)<0
    if bad.any():
        Vt[bad,2,:]*=-1; s[bad,2]*=-1; R[bad]=np.einsum('nji,nkj->nik',Vt[bad],U[bad])
    if E('SCALE',0)>0:
        # allow the skin to shrink/grow a little where it is squeezed/stretched (no buckling)
        den=np.zeros(len(inv)); pl=w*np.einsum('ij,ij->i',ep,ep)
        den=np.bincount(vpos[a],pl,len(inv))+np.bincount(vpos[b],pl,len(inv))
        sc=np.clip(s.sum(1)/np.maximum(den,1e-15),E('SMIN',0.6),E('SMAX',1.25))
        R=R*sc[:,None,None]
    return R
# blended bone rotation per vertex (smooth starting guess, no folds)
mwi=hi.matrix_world.inverted(); quats={}
for pb in rig.pose.bones:
    M=(mwi@rig.matrix_world@pb.matrix@pb.bone.matrix_local.inverted()@rig.matrix_world.inverted()@hi.matrix_world).to_3x3()
    quats[pb.name]=np.array(M.to_quaternion().normalized())
ref=quats['chest']; Q=np.zeros((len(inv),4))
for n_,i in enumerate(inv):
    acc=np.zeros(4)
    for g in me.vertices[int(i)].groups:
        bn=gname.get(g.group)
        if bn in quats and g.weight>0:
            q=quats[bn]; acc+=g.weight*(q if q@ref>=0 else -q)
    nq=np.linalg.norm(acc); Q[n_]=acc/nq if nq>0 else ref
qw,qx,qy,qz=Q.T
R0=np.stack([np.c_[1-2*(qy*qy+qz*qz),2*(qx*qy-qz*qw),2*(qx*qz+qy*qw)],
             np.c_[2*(qx*qy+qz*qw),1-2*(qx*qx+qz*qz),2*(qy*qz-qx*qw)],
             np.c_[2*(qx*qz-qy*qw),2*(qy*qz+qx*qw),1-2*(qx*qx+qy*qy)]],axis=1)
Xc=X.copy()
for it in range(int(E('IT',25))):
    R=R0 if (it==0 and E('INITQ',1)>0) else rotations(Xc)
    Re=0.5*(R[vpos[a]]+R[vpos[b]]); be=w[:,None]*np.einsum('nij,nj->ni',Re,ep)
    rhs=np.zeros((nf,3))
    for k in range(3):
        rhs[:,k]+=np.bincount(pos[a[fa]],be[fa,k],nf)-np.bincount(pos[b[fb]],be[fb,k],nf)
        # fixed neighbours go to the right-hand side
        m1=fa&~fb; rhs[:,k]+=np.bincount(pos[a[m1]],w[m1]*Xc[b[m1],k],nf)
        m2=fb&~fa; rhs[:,k]+=np.bincount(pos[b[m2]],w[m2]*Xc[a[m2],k],nf)
    new=np.column_stack([lu.solve(rhs[:,k]) for k in range(3)])
    ch=np.linalg.norm(new-Xc[idx],axis=1).max(); Xc[idx]=new
    if it%5==0 or it==int(E('IT',25))-1: print('iter',it,'max change mm %.2f'%(ch*1000))
if E('POSTSM',0)>0:
    # remove the fine wrinkles (short waves) without flattening the muscles (Taubin: no shrinking)
    Ad=sp.coo_matrix((np.ones(len(ed)*2),(np.r_[ed[:,0],ed[:,1]],np.r_[ed[:,1],ed[:,0]])),shape=(nv,nv)).tocsr()
    dg_=np.asarray(Ad.sum(1)).ravel(); dg_[dg_==0]=1
    mk=np.zeros(nv); mk[idx]=np.clip((RAD-d[idx])/E('POSTFADE',0.05),0,1)
    mk=mk[:,None]
    for _ in range(int(E('POSTSM',0))):
        for f_ in (0.5,-0.53): Xc=Xc+mk*f_*((Ad@Xc)/dg_[:,None]-Xc)
if E('RIN',0)>0:
    # full effect inside RIN, fading smoothly to the skinned result at RAD (no seam at the edge of the region)
    sfade=np.clip((RAD-d[idx])/(RAD-E('RIN',0)),0,1); sfade=sfade*sfade*(3-2*sfade)
    Xc[idx]=X[idx]+sfade[:,None]*(Xc[idx]-X[idx])
mv=np.linalg.norm(Xc[idx]-X[idx],axis=1); print('moved mm: mean %.1f p95 %.1f max %.1f'%(mv.mean()*1000,np.percentile(mv,95)*1000,mv.max()*1000))
newme.vertices.foreach_set('co',Xc.ravel()); newme.update()
hi.modifiers.clear(); hi.data=newme
bpy.ops.wm.save_as_mainfile(filepath=out); print('done in %.0fs'%(time.time()-t0))
