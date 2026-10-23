# Muscle atlas compiler: anatomical muscle regions on the rest body, drawn as closed loops of surface landmarks.
#
#   python -I atlas.py OUT.npz SPEC1.py [SPEC2.py ...]        (env ATLAS_REST=<rest.npz>, default ill/rest.npz)
#
# A spec file is plain Python defining two dicts (LEFT side of the body only, +x; the right side is mirrored):
#   LM = { 'name': spec, ... }        surface landmarks; spec forms (metres, degrees):
#        ('F', x, z)        first hit seen from the FRONT   (ray along +y)
#        ('B', x, z)        first hit seen from the BACK    (ray along -y)
#        ('L', y, z)        first hit seen from the LEFT    (ray along -x; body's left = +x)
#        ('R', y, z)        first hit seen from the RIGHT   (ray along +x)
#        ('T', x, y)        first hit seen from the TOP     (ray along -z)
#        ('U', x, y)        first hit seen from BELOW       (ray along +z)
#        ('MX', x0, y, z)   first hit going outwards (+x) from the point (x0,y,z) (inner thigh/arm, armpit)
#        ('V', yaw, pitch, a, b)  oblique view: a,b = horizontal/vertical coordinates in that view's picture plane
#        ('limb', bone, t, ang)   point on a limb: t = 0..1 along the bone, ang around it: 0 front, 90 outer side,
#                                 180 back, -90 inner side (bones: upper_arm.L forearm.L thigh.L shin.L ...)
#        ('P', x, y, z)     nearest surface point
#        ('AT', name, dx, dy, dz)  another landmark moved by (dx,dy,dz), then snapped to the surface
#   MUSCLES = { 'name': dict(loop=[lm, lm, ...], seed=lm-or-spec, origin=(lmA,lmB), insertion=(lmC,lmD),
#                           kind='muscle'|'tendon', sp=6.0, group='lats') }
#        loop: closed border, landmarks in order (either direction). A name ending in '~' makes the segment to the
#              next landmark SOFT (internal division of one muscle, e.g. upper/middle trapezius: faint line only).
#              A name ending in '!' makes that segment STRAIGHT (shortest path, does not follow the mesh grooves).
#        seed: a point surely inside the muscle.  origin/insertion: the two arcs of the loop where the fibres start and
#              end, each given as (first, last) landmark in loop order, with the loop order origin..insertion..
#              (fibres then run from the origin arc to the insertion arc).  sp: fibre line spacing in mm.
# Neighbouring muscles must share the landmarks of their common border so the border is one single line.
# Output npz (per vertex, rest vertex order): mid (muscle index, 0 none), names, bd/bds (mm to nearest hard/soft
# border), fph (fibre phase, lines at integers), fmask (1 fibres, 0 none), plus curves for previews.
import bpy  # noqa: F401  (gives mathutils)
from mathutils.bvhtree import BVHTree
from mathutils import Vector
import numpy as np, scipy.sparse as sp, sys, os, math, runpy, collections, heapq
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from scipy.sparse.linalg import spsolve
E=lambda k,d: float(os.environ.get(k,d))
HERE=os.path.dirname(os.path.abspath(__file__))
REST=os.environ.get('ATLAS_REST',os.path.join(HERE,'rest.npz'))

class Body:
    def __init__(s,path=REST):
        R=np.load(path,allow_pickle=True)
        s.co=R['co']; s.no=R['no']; s.nv=len(s.co); s.h=R['h_fine']*1000.0
        lt=R['lt']; lv=R['lv']; off=np.r_[0,np.cumsum(lt)]
        s.polys=[lv[off[i]:off[i+1]] for i in range(len(lt))]
        s.ed=R['ed']; s.bones={str(n):(h,t) for n,h,t in zip(R['bn'],R['bh'],R['bt'])}
        s.main=R['main']; s.shorts=R['shorts']
        s.bvh=BVHTree.FromPolygons([tuple(p) for p in s.co],[tuple(int(i) for i in p) for p in s.polys])
        a,b=s.ed[:,0],s.ed[:,1]; s.elen=np.linalg.norm(s.co[a]-s.co[b],axis=1)
        s.adj=sp.coo_matrix((np.ones(2*len(a)),(np.r_[a,b],np.r_[b,a])),shape=(s.nv,s.nv)).tocsr()
        # path cost: prefer the sculpted grooves (valleys of the fine relief)
        hm=np.clip(0.5*(s.h[a]+s.h[b]),-E('HC',2.0),E('HC',2.0))/E('HC',2.0)
        cw=s.elen*np.exp(E('KV',0.0)*hm)
        s.cost_v=sp.coo_matrix((np.r_[cw,cw],(np.r_[a,b],np.r_[b,a])),shape=(s.nv,s.nv)).tocsr()
        s.cost_s=sp.coo_matrix((np.r_[s.elen,s.elen],(np.r_[a,b],np.r_[b,a])),shape=(s.nv,s.nv)).tocsr()
        tris=[]
        for p in s.polys:
            for k in range(1,len(p)-1): tris.append((p[0],p[k],p[k+1]))
        s.tris=np.array(tris)
        s.kd=cKDTree(s.co)
    # ---- surface queries
    def ray(s,o,d):
        loc,n,i,dist=s.bvh.ray_cast(Vector(o),Vector(d))
        return None if loc is None else np.array(loc)
    def nearest(s,p):
        loc,n,i,dist=s.bvh.find_nearest(Vector(tuple(p))); return np.array(loc)
    def limb_frame(s,bone):
        h,t=s.bones[bone]; u=(t-h)/np.linalg.norm(t-h); side=-1.0 if bone.endswith('.R') else 1.0
        ea=np.array((0,-1.0,0)); ea=ea-u*(ea@u); ea/=np.linalg.norm(ea)
        el=np.array((side,0,0.0)); el=el-u*(el@u)-ea*(el@ea); el/=np.linalg.norm(el)
        return h,t,u,ea,el
    @staticmethod
    def view_basis(yaw,pitch):
        y=math.radians(yaw); p=math.radians(pitch)
        back=np.array((math.sin(y)*math.cos(p),-math.cos(y)*math.cos(p),math.sin(p)))   # towards the camera
        f=-back; r=np.cross(f,(0,0,1.0))
        if np.linalg.norm(r)<1e-6: r=np.array((1.0,0,0))
        r/=np.linalg.norm(r); u=np.cross(r,f); return f,r,u
    def resolve(s,spec,lms=None):
        k=spec[0]
        if k=='F': return s.ray((spec[1],-3,spec[2]),(0,1,0))
        if k=='B': return s.ray((spec[1],3,spec[2]),(0,-1,0))
        if k=='L': return s.ray((3,spec[1],spec[2]),(-1,0,0))
        if k=='R': return s.ray((-3,spec[1],spec[2]),(1,0,0))
        if k=='T': return s.ray((spec[1],spec[2],4),(0,0,-1))
        if k=='U': return s.ray((spec[1],spec[2],-1),(0,0,1))
        if k=='MX': return s.ray((spec[1],spec[2],spec[3]),(1,0,0))
        if k=='V':
            f,r,u=s.view_basis(spec[1],spec[2]); o=spec[3]*r+spec[4]*u-4*f; return s.ray(o,f)
        if k=='limb':
            h,t,u,ea,el=s.limb_frame(spec[1]); a=math.radians(spec[3]); d=math.cos(a)*ea+math.sin(a)*el
            p=h+spec[2]*(t-h); hit=s.ray(p,d)
            return hit if hit is not None else s.ray(p+0.5*d,-d)
        if k=='ring':   # ('ring', bone, t, ang): like 'limb' but measured from the centre of the mesh cross-section
            h,t,u,ea,el=s.limb_frame(spec[1]); a=math.radians(spec[3]); d=math.cos(a)*ea+math.sin(a)*el
            c=s.section_centre(spec[1],spec[2]); hit=s.ray(c,d)
            return hit if hit is not None else s.ray(c+0.3*d,-d)
        if k=='P': return s.nearest(spec[1:4])
        if k=='AT':
            base=lms[spec[1]] if lms is not None else None
            return s.nearest(base+np.array(spec[2:5]))
        raise ValueError('unknown landmark spec %r'%(spec,))
    def section_centre(s,bone,t):
        key=(bone,round(t,4))
        if not hasattr(s,'_sc'): s._sc={}
        if key in s._sc: return s._sc[key]
        h,tl,u,ea,el=s.limb_frame(bone); L=np.linalg.norm(tl-h); p0=h+t*(tl-h)
        side=bone.split('.')[-1]; base=bone.split('.')[0]
        fam={'upper_arm':('upper_arm','delt'),'forearm':('forearm','fa_tw'),'thigh':('thigh',),'shin':('shin',)}.get(base,(base,))
        ok=np.array([any(str(m).startswith(f) for f in fam) and str(m).endswith('.'+side) for m in s.main]) if not hasattr(s,'_fam_'+bone) else getattr(s,'_fam_'+bone)
        setattr(s,'_fam_'+bone,ok)
        rel=s.co-p0; along=rel@u
        sel=ok&(np.abs(along)<0.008)
        c=s.co[sel].mean(0) if sel.sum()>10 else p0
        c=c-u*((c-p0)@u)          # stay in the section plane
        s._sc[key]=c; return c
    def vertex_at(s,p):
        return int(s.kd.query(p)[1])
    # ---- paths
    def path(s,a,b,straight=False):
        if a==b: return [a]
        G=s.cost_s if straight else s.cost_v
        lim=4.0*np.linalg.norm(s.co[a]-s.co[b])+0.02
        d,pr=dijkstra(G,indices=a,return_predecessors=True,limit=lim)
        if not np.isfinite(d[b]): d,pr=dijkstra(G,indices=a,return_predecessors=True)
        out=[b]
        while out[-1]!=a: out.append(int(pr[out[-1]]))
        return out[::-1]
    def smooth_curve(s,vs,it=None):
        P=s.co[vs].copy()
        if len(P)<2: return np.vstack([P,P+1e-6])
        if len(P)<3: return P
        P0=P.copy(); cmax=E('CSMAX',0.006)
        for _ in range(int(it if it is not None else E('CSM',25))):
            P[1:-1]=0.5*P[1:-1]+0.25*(P[:-2]+P[2:])
            dv=P-P0; dl=np.linalg.norm(dv,axis=1,keepdims=True)    # never drift far from the mesh path (the label border):
            P=P0+dv*np.minimum(1.0,cmax/np.maximum(dl,1e-12))        # smoothing a path around a skin fold would cut across it
            if _%5==4: P[1:-1]=np.array([s.nearest(p) for p in P[1:-1]])
        P[1:-1]=np.array([s.nearest(p) for p in P[1:-1]])
        # resample ~1 mm
        seg=np.linalg.norm(np.diff(P,axis=0),axis=1); L=np.r_[0,np.cumsum(seg)]
        n=max(2,int(L[-1]/0.001)+1); t=np.linspace(0,L[-1],n)
        return np.stack([np.interp(t,L,P[:,i]) for i in range(3)],1)
    def smooth_chain(s,vs,it=None,ends=(None,None)):
        """smooth a whole border chain (vertex path, ends fixed), keep one point per path vertex"""
        P=s.co[vs].copy()
        if ends[0] is not None: P[0]=ends[0]
        if ends[1] is not None: P[-1]=ends[1]
        if len(P)<3: return P
        P0=P.copy(); cmax=E('CSMAX',0.006)
        for _ in range(int(it if it is not None else E('CCSM',60))):
            P[1:-1]=0.5*P[1:-1]+0.25*(P[:-2]+P[2:])
            dv=P-P0; dl=np.linalg.norm(dv,axis=1,keepdims=True)
            P=P0+dv*np.minimum(1.0,cmax/np.maximum(dl,1e-12))
            if _%5==4: P[1:-1]=np.array([s.nearest(p) for p in P[1:-1]])
        P[1:-1]=np.array([s.nearest(p) for p in P[1:-1]])
        return P
    @staticmethod
    def resample(P,step=0.001):
        if len(P)<2: return np.vstack([P,P+1e-6])
        seg=np.linalg.norm(np.diff(P,axis=0),axis=1); L=np.r_[0,np.cumsum(seg)]
        if L[-1]<=0: return np.vstack([P[:1],P[:1]+1e-6])
        n=max(2,int(L[-1]/step)+1); t=np.linspace(0,L[-1],n)
        return np.stack([np.interp(t,L,P[:,i]) for i in range(3)],1)
    # ---- cotan laplacian
    def cotan(s):
        if hasattr(s,'_Lc'): return s._Lc
        T=s.tris; P=s.co; I=[];J=[];W=[]
        for k in range(3):
            i,j,o=T[:,k],T[:,(k+1)%3],T[:,(k+2)%3]
            u=P[i]-P[o]; v=P[j]-P[o]; c=(u*v).sum(1)/np.maximum(np.linalg.norm(np.cross(u,v),axis=1),1e-12)
            c=np.clip(c,0,10)*0.5; I+= [i,j]; J+=[j,i]; W+=[c,c]
        s._Lc=sp.coo_matrix((np.concatenate(W),(np.concatenate(I),np.concatenate(J))),shape=(s.nv,s.nv)).tocsr()
        return s._Lc

def load_specs(files):
    LM={}; MU={}
    for f in files:
        g=runpy.run_path(f)
        for k,v in g.get('LM',{}).items():
            if k in LM and LM[k]!=v: print('WARNING landmark %s redefined in %s'%(k,f))
            LM[k]=v
        for k,v in g.get('MUSCLES',{}).items():
            if k in MU: print('WARNING muscle %s redefined in %s'%(k,f))
            v=dict(v); v['_file']=os.path.basename(f); MU[k]=v
    return LM,MU

def resolve_landmarks(B,LM):
    pos={}; todo=dict(LM); guard=0
    while todo and guard<10:
        guard+=1
        for k,v in list(todo.items()):
            if v[0]=='AT' and v[1] not in pos: continue
            p=B.resolve(v,pos)
            if p is None: print('ERROR landmark %s %r: ray missed the body'%(k,v)); p=np.array((0,0,0.0))
            pos[k]=p; del todo[k]
    for k in todo: print('ERROR landmark %s: unresolved reference'%k)
    return pos

def compile_atlas(files,out=None,verbose=True):
    B=Body(); LM,MU=load_specs(files)
    posL=resolve_landmarks(B,LM)
    # mirrored landmarks
    P={}; V={}
    for k,p in posL.items():
        P[k+'@L']=p
        if abs(p[0])<E('MIDX',0.004): P[k+'@R']=p
        else: P[k+'@R']=B.nearest(p*np.array((-1,1,1)))
    for k,p in P.items(): V[k]=B.vertex_at(p)
    names=['none']; mid=np.zeros(B.nv,np.int32); owner_size=np.zeros(B.nv)+1e18
    segs={}; segflags={}; problems=[]
    muscles=[]
    seg_mus={}
    MIR=os.environ.get('MIRROR','1')=='1'   # build the left side only and mirror the result (exactly symmetric)
    for side in (('L',) if MIR else ('L','R')):
        for mn,m in MU.items():
            loop=[]; flags=[]
            for it in m['loop']:
                nm=it.rstrip('~!'); fl=it[len(nm):]
                if nm not in posL: problems.append('%s: unknown landmark %s'%(mn,nm)); continue
                loop.append(nm+'@'+side); flags.append(fl)
            muscles.append((mn+'.'+side,mn,side,m,loop,flags))
            for i_ in range(len(loop)):
                kk=tuple(sorted((loop[i_],loop[(i_+1)%len(loop)])))
                seg_mus.setdefault(kk,[]).append(mn)
            for i in range(len(loop)):
                a,b=loop[i],loop[(i+1)%len(loop)]; key=tuple(sorted((a,b)))
                f=segflags.setdefault(key,set()); f.update(flags[i])
    # paths per unique segment
    for key,fl in segflags.items():
        a,b=key; pv=B.path(V[a],V[b],straight=('!' in fl)); segs[key]=pv
        if V[a]==V[b]: problems.append('landmarks %s and %s land on the same vertex'%(a,b))
    # region fill per muscle
    info={}
    fib=np.zeros(B.nv); fmask=np.zeros(B.nv,np.float32); Lc=B.cotan()
    for full,mn,side,m,loop,flags in muscles:
        cyc=[]; lmidx={}
        for i in range(len(loop)):
            a,b=loop[i],loop[(i+1)%len(loop)]; key=tuple(sorted((a,b))); pv=segs[key]
            if key[0]!=a: pv=pv[::-1]
            lmidx[loop[i].split('@')[0]]=len(cyc); cyc+=pv[:-1]
        blocked=set(cyc)
        sd=m.get('seed'); sp_=posL[sd] if isinstance(sd,str) else B.resolve(sd,posL)
        if sp_ is None: problems.append('%s: seed missed'%full); continue
        if side=='R': sp_=B.nearest(sp_*np.array((-1,1,1)))
        s0=B.vertex_at(sp_)
        if s0 in blocked:
            nb=[j for j in B.adj[s0].indices if j not in blocked]
            if not nb: problems.append('%s: seed on the border'%full); continue
            s0=nb[0]
        seen={s0}; q=collections.deque([s0]); lim=int(E('LEAK',0.06)*B.nv)
        while q and len(seen)<=lim:
            i=q.popleft()
            for j in B.adj.indices[B.adj.indptr[i]:B.adj.indptr[i+1]]:
                if j not in seen and j not in blocked: seen.add(j); q.append(j)
        if len(seen)>lim:
            problems.append('%s: LEAK (border not closed or seed outside); region > %d verts'%(full,lim)); continue
        reg=np.array(sorted(seen)); idx=len(names); names.append(full)
        area=len(reg)
        # smaller muscles win overlaps
        ov=reg[owner_size[reg]<1e17]
        if len(ov)>3 and area>=owner_size[ov].min():
            others=collections.Counter(names[mid[i]] for i in ov); problems.append('%s overlaps %s'%(full,dict(others)))
        take=reg[area<owner_size[reg]]; mid[take]=idx; owner_size[take]=area
        # border vertices of this loop: give to this muscle if not owned
        cy=np.array(cyc); free=cy[owner_size[cy]>1e17]
        info[full]=dict(idx=idx,reg=reg,cyc=cyc,lmidx=lmidx,m=m)
    # fibres: harmonic field across the muscle (0 on one side arc, 1 on the other), stripes along the fibres
    for full,d in info.items():
        m=d['m']
        if m.get('kind','muscle')!='muscle' or 'origin' not in m or 'insertion' not in m: continue
        cyc=d['cyc']; n=len(cyc); li=d['lmidx']
        try: a,b=[li[x] for x in m['origin']]; c,e=[li[x] for x in m['insertion']]
        except KeyError as ex: problems.append('%s: origin/insertion landmark %s not in loop'%(full,ex)); continue
        def arc(i,j):
            out=[]; k=i
            while True:
                out.append(k)
                if k==j: break
                k=(k+1)%n
            return out
        # loop may run origin..insertion in either direction
        o1=arc(a,b); i1=arc(c,e)
        if len(set(o1)&set(i1))>2: problems.append('%s: origin and insertion arcs overlap (check order)'%full); continue
        s1=arc(b,c); s2=arc(e,a)
        reg=np.union1d(d['reg'],np.array(cyc)); ri={v:k for k,v in enumerate(reg)}
        fix={}
        for k in s1: fix[cyc[k]]=0.0
        for k in s2: fix[cyc[k]]=1.0
        Ls=Lc[reg][:,reg].tocsr(); Ds=np.asarray(Ls.sum(1)).ravel(); Lr=(sp.diags(Ds)-Ls).tocsr()
        fx=np.array([ri[v] for v in fix]); fv=np.array(list(fix.values()))
        free=np.setdiff1d(np.arange(len(reg)),fx)
        x=np.zeros(len(reg)); x[fx]=fv
        A=Lr[free][:,free]; rhs=-Lr[free][:,fx]@fv
        try: x[free]=spsolve(A.tocsc(),rhs)
        except Exception as ex: problems.append('%s: fibre solve failed %s'%(full,ex)); continue
        # stripe count from the median gradient
        own=d['reg'][mid[d['reg']]==d['idx']]
        sub=B.ed[np.isin(B.ed[:,0],reg)&np.isin(B.ed[:,1],reg)]
        g=np.abs(x[[ri[v] for v in sub[:,0]]]-x[[ri[v] for v in sub[:,1]]])/np.maximum(np.linalg.norm(B.co[sub[:,0]]-B.co[sub[:,1]],axis=1),1e-6)
        gm=np.median(g[g>0]) if (g>0).any() else 1.0
        nst=max(2.0,1.0/(gm*m.get('sp',E('FSP',6.0))/1000.0))
        fib[own]=x[[ri[v] for v in own]]*nst; fmask[own]=1.0
        d['nst']=nst
    # border distances
    hard=[];soft=[];curves=[]
    issoft={k:('~' in segflags[k]) for k in segs}
    inc=collections.defaultdict(list)
    for k in segs:
        inc[k[0]].append(k); inc[k[1]].append(k)
    def leave_dir(k,n):
        pv=segs[k] if k[0]==n else segs[k][::-1]
        P=B.co[pv]; L_=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
        j=int(np.searchsorted(L_,E('DIRL',0.01))); j=min(max(j,1),len(P)-1)
        d_=P[j]-P[0]; return d_/max(np.linalg.norm(d_),1e-9)
    # pair the segments at each landmark into straight continuations (mutual best, small turn, same softness)
    pair={}
    for n,ks in inc.items():
        if len(ks)<2: continue
        cand=[]
        for i in range(len(ks)):
            for j in range(i+1,len(ks)):
                if issoft[ks[i]]!=issoft[ks[j]]: continue
                c_=-(leave_dir(ks[i],n)@leave_dir(ks[j],n))      # 1 = straight through
                cand.append((c_,ks[i],ks[j]))
        cand.sort(reverse=True); used=set()
        for c_,ki,kj in cand:
            if ki in used or kj in used: continue
            if len(ks)>2 and c_<math.cos(math.radians(E('TURN',60)))*1.0: continue
            pair[(ki,n)]=kj; pair[(kj,n)]=ki; used|={ki,kj}
    done=set(); chains=[]
    for k0 in segs:
        if k0 in done: continue
        cur=k0; node=k0[0]; seen_={k0}
        while (cur,node) in pair:
            nxt=pair[(cur,node)]
            if nxt in seen_: break
            seen_.add(nxt); cur=nxt; node=cur[0] if cur[1]==node else cur[1]
        chain=[]; start=node; k=cur
        while True:
            b_=k[1] if k[0]==start else k[0]
            chain.append((k,start,b_)); done.add(k)
            if (k,b_) not in pair: break
            nk=pair[(k,b_)]
            if nk in done: break
            k=nk; start=b_
        chains.append(chain)
    def chain_len(ch): return sum(len(segs[k]) for k,_,_ in ch)
    chains.sort(key=chain_len,reverse=True)
    placed={}; smoothed={}
    for chain in chains:
        vs=[]; bounds=[]; nodes=[]
        for k,a_,b_ in chain:
            pv=segs[k] if k[0]==a_ else segs[k][::-1]
            if vs and vs[-1]==pv[0]: pv=pv[1:]
            st=max(len(vs)-1,0); vs+=list(pv); bounds.append((k,st,len(vs)-1,a_,b_))
        first=chain[0][1]; last=chain[-1][2]
        Pc=B.smooth_chain(vs,ends=(placed.get(first),placed.get(last)))
        for k,i0,i1,a_,b_ in bounds:
            placed.setdefault(a_,Pc[i0]); placed.setdefault(b_,Pc[i1])
            seg_=Pc[i0:i1+1]
            smoothed[k]=B.resample(seg_)
    for key in segs:
        c=smoothed[key]
        (soft if issoft[key] else hard).append(c); curves.append((key,issoft[key],c))
    if MIR:
        # right side = mirror image of the left: labels and fibres through the vertex mirror map, curves mirrored exactly
        mi=B.kd.query(B.co*np.array((-1.0,1,1)))[1]
        right=B.co[:,0]<-E('MIRX',0.0005)
        mapR={0:0}
        for full in list(info.keys()):
            j=len(names); names.append(full[:-2]+'.R'); mapR[info[full]['idx']]=j
            info[full[:-2]+'.R']=dict(info[full]); info[full[:-2]+'.R']['idx']=j
        src=mi[right]
        mid[right]=np.array([mapR.get(int(m),0) for m in mid[src]]); fib[right]=fib[src]; fmask[right]=fmask[src]
        for key,soft_,c in list(curves):
            cm=c*np.array((-1.0,1,1))
            if np.abs(c[:,0]).max()<0.002: continue
            (soft if soft_ else hard).append(cm); curves.append(((key[0].replace('@L','@R'),key[1].replace('@L','@R')),soft_,cm))
    # orient every curve the same way relative to its two muscles (the higher muscle id on the + side), so the signed
    # distance keeps one sign along a whole border (no false ticks where two border segments meet)
    def orient(cs):
        out=[]
        for c in cs:
            tg=np.gradient(c,axis=0); tg/=np.maximum(np.linalg.norm(tg,axis=1,keepdims=True),1e-12)
            nn=B.no[B.kd.query(c)[1]]; sv=np.cross(tg,nn); sv/=np.maximum(np.linalg.norm(sv,axis=1,keepdims=True),1e-12)
            lp=mid[B.kd.query(c+0.004*sv)[1]]; lm=mid[B.kd.query(c-0.004*sv)[1]]
            vote=np.sign(lp.astype(int)-lm.astype(int)).sum()
            out.append(c[::-1].copy() if vote<0 else c)
        return out
    hard=orient(hard); soft=orient(soft)
    def dist(cs):
        if not cs: return np.full(B.nv,60.0),np.full(B.nv,60.0)
        pts=np.concatenate(cs); tg=np.concatenate([np.gradient(c,axis=0) for c in cs])
        tg/=np.maximum(np.linalg.norm(tg,axis=1,keepdims=True),1e-12)
        nn=B.no[B.kd.query(pts)[1]]; side=np.cross(tg,nn)
        dd,ii=cKDTree(pts).query(B.co,distance_upper_bound=0.06); far=~np.isfinite(dd); ii[far]=0; dd[far]=0.06
        sg=np.sign(((B.co-pts[ii])*side[ii]).sum(1)); sg[sg==0]=1
        return dd*1000,(dd*sg)*1000
    bd,sd=dist(hard); bds,sds=dist(soft)
    # border-path vertices were left unlabelled by the fill: give each one the label (and fibre phase) of the
    # neighbouring muscle lying on the same side of the smooth border line
    border=np.zeros(B.nv,bool)
    for d_ in info.values(): border[np.array(d_['cyc'],int)]=True
    if MIR: border|=border[mi]
    for _ in range(2):
        todo=np.where((mid==0)&border)[0]; new_mid={}; new_f={}
        for v in todo:
            nb=B.adj.indices[B.adj.indptr[v]:B.adj.indptr[v+1]]; nb=nb[(~border[nb])|(mid[nb]>0)]
            if not len(nb): continue
            same=nb[np.sign(sd[nb])==np.sign(sd[v])]
            pick=same if len(same) else nb
            lab=collections.Counter(mid[pick]).most_common(1)[0][0]
            if lab==0: continue
            new_mid[v]=lab; ff=pick[mid[pick]==lab]; new_f[v]=(fib[ff].mean(),fmask[ff].max())
        for v,lab in new_mid.items(): mid[v]=lab; fib[v],fmask[v]=new_f[v]
    # detour check: path length vs straight distance
    for key,pv in segs.items():
        Lp=np.linalg.norm(np.diff(B.co[pv],axis=0),axis=1).sum(); Ls=np.linalg.norm(B.co[pv[0]]-B.co[pv[-1]])
        if Ls>0.02 and Lp>E('DETOUR',1.2)*Ls: problems.append('segment %s-%s: path %.0f mm for a %.0f mm gap (detour; add a landmark in between or mark it straight with !)'%(key[0],key[1],Lp*1000,Ls*1000))
    if verbose:
        for p in problems: print('PROBLEM',p)
        print('muscles',len(names)-1,'labelled verts',int((mid>0).sum()),'segments',len(segs))
        va=np.zeros(B.nv)
        for p in B.polys:
            pass
        for full,d in info.items():
            if not full.endswith('.L') and os.environ.get('BOTH')!='1': continue
            print('  %-24s verts %6d  stripes %s'%(full,int((mid==d['idx']).sum()),('%.0f'%d['nst']) if 'nst' in d else '-'))
    nidx={n:i for i,n in enumerate(names)}
    def _mus_of(k_,j):
        side=k_[0].split('@')[1]; kl=tuple(sorted((k_[0].replace('@R','@L'),k_[1].replace('@R','@L'))))
        ms=seg_mus.get(kl,[])
        return nidx.get(ms[j]+'.'+side,0) if len(ms)>j else 0
    res=dict(mid=mid,names=np.array(names),bd=bd.astype(np.float32),bds=bds.astype(np.float32),sd=sd.astype(np.float32),sds=sds.astype(np.float32),fph=fib.astype(np.float32),fmask=fmask,
             lm_names=np.array(list(P.keys())),lm_pos=np.array(list(P.values())),
             curve_pts=np.concatenate([c for _,_,c in curves]) if curves else np.zeros((0,3)),
             curve_id=np.concatenate([np.full(len(c),i) for i,(_,_,c) in enumerate(curves)]) if curves else np.zeros(0),
             curve_soft=np.array([s_ for _,s_,_ in curves]),
             curve_m1=np.array([_mus_of(k_,0) for k_,_,_ in curves]),curve_m2=np.array([_mus_of(k_,1) for k_,_,_ in curves]),
             kinds=np.array(['tendon' if info[n]['m'].get('kind','muscle')=='tendon' else 'muscle' for n in names[1:]]) if len(names)>1 else np.array([]),
             groups=np.array([info[n]['m'].get('group',n.rsplit('.',1)[0]) for n in names[1:]]) if len(names)>1 else np.array([]),
             problems=np.array(problems))
    if out: np.savez(out,**res)
    return res

if __name__=='__main__':
    if sys.argv[1]=='--print':     # print where each landmark lands (3D and per-view coordinates)
        B=Body(); LM,MU=load_specs(sys.argv[2:]); pos=resolve_landmarks(B,LM)
        for k,p in pos.items():
            print('%-16s xyz (%.3f, %.3f, %.3f)   F/B: x=%.3f z=%.3f   L: y=%.3f z=%.3f   spec %r'%(k,p[0],p[1],p[2],p[0],p[2],p[1],p[2],LM[k]))
    else:
        out=sys.argv[1]; files=sys.argv[2:]
        compile_atlas(files,out)
