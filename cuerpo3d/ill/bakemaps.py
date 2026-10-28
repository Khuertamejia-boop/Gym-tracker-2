# Bake the muscle atlas into UDIM textures (exact per texel, independent of the mesh density):
#   <out>/dist.<tile>.png  R = distance to the nearest HARD border (0.1 mm units, 0..25.5 mm)
#                          G = distance to the nearest SOFT border, B = 255 on tendons
#   <out>/lab.<tile>.png   R = muscle index (atlas 'names' order), for per-exercise red maps (redmap.py)
#   python -I bakemaps.py ATLAS.npz OUTDIR [RES=1024]
import sys, os, collections, numpy as np
from scipy.spatial import cKDTree
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__))
E=lambda k,d: float(os.environ.get(k,d))
atl=np.load(sys.argv[1],allow_pickle=True); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
R=int(E('RES',1024))
rest=np.load(os.path.join(HERE,'rest.npz'),allow_pickle=True); co=rest['co']; no=rest['no']
uvt=np.load(os.path.join(HERE,'uvtri.npz')); tv=uvt['tv']; tuv=uvt['tuv']
mid=atl['mid'].astype(int); names=[str(n) for n in atl['names']]
kinds=['none']+[str(k) for k in atl['kinds']]
tendon_id=np.array([k=='tendon' for k in kinds])
kdv=cKDTree(co)
# ---- curves: dense resampling (0.25 mm), tangents, and the muscle on each side
cp=atl['curve_pts']; cid=atl['curve_id'].astype(int); csoft=atl['curve_soft']
def resample(c,step=0.00025):
    seg=np.linalg.norm(np.diff(c,axis=0),axis=1); L=np.r_[0,np.cumsum(seg)]
    if L[-1]<=0: return c[:1]
    t=np.linspace(0,L[-1],max(2,int(L[-1]/step)+1)); return np.stack([np.interp(t,L,c[:,i]) for i in range(3)],1)
H=[];S=[];HS=[];SS=[];Hid=[];Sid=[];HN=[];SN=[]
side_lab={}
for k in range(int(cid.max())+1 if len(cid) else 0):
    c=cp[cid==k]
    if len(c)<2: continue
    c=resample(c); tg=np.gradient(c,axis=0); tg/=np.maximum(np.linalg.norm(tg,axis=1,keepdims=True),1e-12)
    nn=no[kdv.query(c)[1]]; sv=np.cross(tg,nn); sv/=np.maximum(np.linalg.norm(sv,axis=1,keepdims=True),1e-12)
    m1=int(atl['curve_m1'][k]) if 'curve_m1' in atl.files else 0; m2=int(atl['curve_m2'][k]) if 'curve_m2' in atl.files else 0
    votes_p=collections.Counter(); votes_m=collections.Counter()
    for o_ in (0.003,0.006,0.009,0.013,0.018):
        for lab_ in mid[kdv.query(c+o_*sv)[1]]: votes_p[int(lab_)]+=1.0/o_
        for lab_ in mid[kdv.query(c-o_*sv)[1]]: votes_m[int(lab_)]+=1.0/o_
    if m1 and m2 and m1!=m2:
        # the atlas knows the two muscles of this border: only decide which one is on the + side
        sc=(votes_p[m1]-votes_m[m1])-(votes_p[m2]-votes_m[m2])
        vp,vm=(m1,m2) if sc>=0 else (m2,m1)
    else:
        vp=max((v for v in votes_p if v>0),key=lambda v:votes_p[v],default=0)
        vm=max((v for v in votes_m if v>0 and v!=vp),key=lambda v:votes_m[v],default=0)
    if csoft[k]: S.append(c); SS.append(sv); Sid.append(np.full(len(c),k)); SN.append(nn)
    else: H.append(c); HS.append(sv); Hid.append(np.full(len(c),k)); HN.append(nn)
    side_lab[k]=(vp,vm)
H=np.concatenate(H) if H else np.zeros((1,3))+9; HS=np.concatenate(HS) if HS else np.zeros((1,3)); Hid=np.concatenate(Hid) if Hid else np.zeros(1,int)
S=np.concatenate(S) if S else np.zeros((1,3))+9; SS=np.concatenate(SS) if SS else np.zeros((1,3)); Sid=np.concatenate(Sid) if Sid else np.zeros(1,int)
HN=np.concatenate(HN) if HN else np.zeros((1,3)); SN=np.concatenate(SN) if SN else np.zeros((1,3))
kdH=cKDTree(H); kdS=cKDTree(S)
# REDSEL (worked-muscle list, as redmap.py): distance to the OUTER border of the red area (hard lines with red on one
# side only) -> redd16.<tile>.png, used by the renderer to fade the red in softly from that border
REDSEL=os.environ.get('REDSEL','')
kdRB=None
if REDSEL:
    _base=[n.rsplit('.',1)[0] for n in names]; _groups=['none']+[str(g) for g in atl['groups']]
    def _m(i,key):
        if key[-2:] in ('.L','.R'):
            k=key[:-2]; return names[i].endswith(key[-2:]) and (_base[i]==k or _groups[i]==k)
        return _base[i]==key or _groups[i]==key
    _red=np.zeros(len(names),bool)
    for it in [x for x in REDSEL.split(',') if x.strip()]:
        key=it.strip().rsplit(':',1)[0]
        for i in range(1,len(names)):
            if _m(i,key) and not tendon_id[i]: _red[i]=True
    rb=np.array([_red[side_lab[k][0]]!=_red[side_lab[k][1]] for k in Hid]) if len(Hid) else np.zeros(0,bool)
    if rb.any(): kdRB=cKDTree(H[rb])
    print('red outer border points',int(rb.sum()))
DOME=os.environ.get('DOME','')
if DOME:
    dz=np.load(DOME); dome_v=dz['dome'].astype(float); damp_v=dz['damp'].astype(float); halfw_v=dz['halfw'].astype(float) if 'halfw' in dz.files else damp_v*0+10; draw_v=dz['domeraw'].astype(float) if 'domeraw' in dz.files else dome_v
print('curve points hard %d soft %d'%(len(H),len(S)))
# ---- rasterise each UDIM tile
cen=tuv.mean(1); tile=(np.floor(cen[:,0])+10*np.floor(cen[:,1])).astype(int)
np.savez(os.path.join(out,'curves.npz'),ids=np.array(sorted(side_lab.keys())),vp=np.array([side_lab[k][0] for k in sorted(side_lab.keys())]),
         vm=np.array([side_lab[k][1] for k in sorted(side_lab.keys())]),soft=np.array([bool(csoft[k]) for k in sorted(side_lab.keys())]))
for t in sorted(set(tile.tolist())):
    T=np.where(tile==t)[0]; ox,oy=t%10,t//10
    U=(tuv[T]-np.array((ox,oy)))*R                     # texel coords (x right, y up)
    tri_of=np.full(R*R,-1); bary=np.zeros((R*R,3),np.float32)
    lo=np.floor(U.min(1)-0.5).astype(int); hi=np.ceil(U.max(1)+0.5).astype(int)
    size=(hi-lo).max(1)
    order=np.argsort(size)
    for s0 in range(0,len(T),3000):
        idx=order[s0:s0+3000]; W=int(size[idx].max())+1
        gx,gy=np.meshgrid(np.arange(W),np.arange(W)); gx=gx.ravel(); gy=gy.ravel()
        px=lo[idx,0][:,None]+gx[None]; py=lo[idx,1][:,None]+gy[None]
        cx=px+0.5; cy=py+0.5
        a=U[idx,0]; b=U[idx,1]; c=U[idx,2]
        d=(b[:,1]-c[:,1])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,1]-c[:,1]); d=np.where(np.abs(d)<1e-12,1e-12,d)
        w0=((b[:,1]-c[:,1])[:,None]*(cx-c[:,0][:,None])+(c[:,0]-b[:,0])[:,None]*(cy-c[:,1][:,None]))/d[:,None]
        w1=((c[:,1]-a[:,1])[:,None]*(cx-c[:,0][:,None])+(a[:,0]-c[:,0])[:,None]*(cy-c[:,1][:,None]))/d[:,None]
        w2=1-w0-w1
        ins=(w0>=-1e-4)&(w1>=-1e-4)&(w2>=-1e-4)&(px>=0)&(px<R)&(py>=0)&(py<R)
        ii,jj=np.nonzero(ins)
        pix=py[ii,jj]*R+px[ii,jj]
        tri_of[pix]=T[idx[ii]]; bary[pix]=np.stack([w0[ii,jj],w1[ii,jj],w2[ii,jj]],1)
    cov=np.where(tri_of>=0)[0]
    P=(bary[cov][:,:,None]*co[tv[tri_of[cov]]]).sum(1)
    PN=(bary[cov][:,:,None]*no[tv[tri_of[cov]]]).sum(1); PN/=np.maximum(np.linalg.norm(PN,axis=1,keepdims=True),1e-9)
    dh,ih=kdH.query(P,distance_upper_bound=0.064,workers=-1); dh=np.where(np.isfinite(dh),dh,0.064)
    ds,is_=kdS.query(P,distance_upper_bound=0.064,workers=-1); ds=np.where(np.isfinite(ds),ds,0.064)
    # label: nearest vertex, corrected next to a border by the side of the border line the texel lies on
    LUTF=os.environ.get('LSTR','')
    if LUTF:
        # per-border strength: effective distance = min over nearby lines of (distance + (1-strength)*LDW). A min of
        # continuous functions is continuous, so weak borders fade out without seams where two borders meet
        slut=np.load(LUTF); LDW=E('LDW',25.0)/1000.0
        dd_,ii_=kdH.query(P,k=int(E('LK_',24)),distance_upper_bound=0.064,workers=-1)
        okk=np.isfinite(dd_); ii_=np.where(okk,ii_,0)
        off=(1.0-slut[np.clip(Hid[ii_],0,len(slut)-1)])*LDW
        eff=np.where(okk,dd_+off,0.064).min(1)
        dh_eff=np.minimum(eff,0.064)
    else:
        dh_eff=dh
    L3=mid[tv[tri_of[cov]]]                                   # labels of the texel's own triangle (never across a fold)
    lab=L3[np.arange(len(cov)),np.argmax(bary[cov],1)]
    # nearest border line (hard or soft) decides: the texel takes the muscle on its side of that line
    useS=ds<dh
    dmin=np.where(useS,ds,dh); band=np.where(dmin<E('LBAND',0.0254))[0]
    for C_,SV,ID,j_,sel_,CN in ((H,HS,Hid,ih,~useS[band],HN),(S,SS,Sid,is_,useS[band],SN)):
        nb=band[sel_]
        if not len(nb): continue
        nb=nb[(PN[nb]*CN[j_[nb]]).sum(1)>E('NDOT',0.5)]     # same surface as the line (not the arm next to the torso)
        j=j_[nb]; sgn=((P[nb]-C_[j])*SV[j]).sum(1)>0
        k=ID[j]; vp=np.array([side_lab[x][0] for x in k]); vm=np.array([side_lab[x][1] for x in k])
        cand=np.where(sgn,vp,vm)
        # only lines that belong to this triangle's muscles may relabel it (a line across a skin fold may not)
        ok_=((L3[nb]==vp[:,None])|(L3[nb]==vm[:,None])).any(1)
        # a label the triangle does not have is taken only right next to the line (not from far, unreliable sides)
        ok_&=(L3[nb]==cand[:,None]).any(1)|(dmin[nb]<E('LNEAR',0.006))
        if E('NONEFIX',0)>0:
            # NONEFIX=1: a triangle that is all one muscle never turns into plain skin ('none'): at tight curves of a
            # border (e.g. the tip of the biceps) the side test can flip and leave a plain band inside the muscle
            uni=(L3[nb]==L3[nb][:,:1]).all(1)
            ok_&=~(uni&(cand==0)&(L3[nb][:,0]!=0))
        lab[nb[ok_]]=cand[ok_]
    img=np.zeros((R*R,3),np.uint8); li=np.zeros(R*R,np.uint8)
    img[cov,0]=np.clip(np.round(dh_eff*10000),0,255); img[cov,1]=np.clip(np.round(ds*10000),0,255); img[cov,2]=np.where(tendon_id[lab],255,0)
    li[cov]=np.clip(lab,0,255)
    # dilate a few texels into the empty space so filtering at UV seams does not pull in black
    filled=np.zeros(R*R,bool); filled[cov]=True
    img=img.reshape(R,R,3); li=li.reshape(R,R); filled=filled.reshape(R,R)
    for _ in range(int(E('DIL',6))):
        ys,xs=np.nonzero(~filled)
        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
            yy=np.clip(ys+dy,0,R-1); xx=np.clip(xs+dx,0,R-1); ok=filled[yy,xx]&~filled[ys,xs]
            img[ys[ok],xs[ok]]=img[yy[ok],xx[ok]]; li[ys[ok],xs[ok]]=li[yy[ok],xx[ok]]; filled[ys[ok],xs[ok]]=True
    if DOME:
        # exact (barycentric) interpolation per texel, then a normalised Gaussian blur in texture space: smooth, no
        # ripples between sparse vertex rows and no k-nearest truncation artefacts
        from scipy.ndimage import gaussian_filter
        tv_c=tv[tri_of[cov]]; bw=bary[cov]
        def bake_field(vals):
            img_=np.zeros(R*R); img_[cov]=(bw*vals[tv_c]).sum(1); msk=np.zeros(R*R); msk[cov]=1
            sp=E('TBLURPX',10.0)
            num=gaussian_filter(img_.reshape(R,R),sp,mode='nearest'); den=gaussian_filter(msk.reshape(R,R),sp,mode='nearest')
            out_=num/np.maximum(den,1e-6); return out_.ravel()[cov]
        dm=bake_field(dome_v); da=bake_field(damp_v); hw=bake_field(halfw_v); drw=bake_field(draw_v)
        dimg=np.zeros(R*R,np.uint16); aimg=np.zeros(R*R,np.uint16); wimg=np.zeros(R*R,np.uint16)
        wimg[cov]=np.clip(hw/64.0*65535,0,65535); rimg=np.zeros(R*R,np.uint16); rimg[cov]=np.clip(drw*65535,0,65535)
        dimg[cov]=np.clip(dm*65535,0,65535); aimg[cov]=np.clip(da/16.0*65535,0,65535)
        fl=np.zeros(R*R,bool); fl[cov]=True; dimg=dimg.reshape(R,R); aimg=aimg.reshape(R,R); wimg=wimg.reshape(R,R); rimg=rimg.reshape(R,R); fl=fl.reshape(R,R)
        for _ in range(int(E('DIL',6))):
            ys,xs=np.nonzero(~fl)
            for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
                yy=np.clip(ys+dy,0,R-1); xx=np.clip(xs+dx,0,R-1); ok2=fl[yy,xx]&~fl[ys,xs]
                dimg[ys[ok2],xs[ok2]]=dimg[yy[ok2],xx[ok2]]; aimg[ys[ok2],xs[ok2]]=aimg[yy[ok2],xx[ok2]]; wimg[ys[ok2],xs[ok2]]=wimg[yy[ok2],xx[ok2]]; rimg[ys[ok2],xs[ok2]]=rimg[yy[ok2],xx[ok2]]; fl[ys[ok2],xs[ok2]]=True
        Image.fromarray(dimg[::-1].copy(),mode='I;16').save(os.path.join(out,'dome.%d.png'%(1001+t)))
        Image.fromarray(aimg[::-1].copy(),mode='I;16').save(os.path.join(out,'damp.%d.png'%(1001+t)))
        Image.fromarray(wimg[::-1].copy(),mode='I;16').save(os.path.join(out,'halfw.%d.png'%(1001+t)))
        Image.fromarray(rimg[::-1].copy(),mode='I;16').save(os.path.join(out,'domeraw.%d.png'%(1001+t)))
    fields=[('dh16',dh_eff),('ds16',ds)]
    if kdRB is not None:
        dr,_=kdRB.query(P,distance_upper_bound=0.064,workers=-1); fields.append(('redd16',np.where(np.isfinite(dr),dr,0.064)))
    for nm_,val in fields:
        a16=np.zeros(R*R,np.uint16); a16[cov]=np.clip(val/0.064*65535,0,65535); a16=a16.reshape(R,R); fl=np.zeros(R*R,bool); fl[cov]=True; fl=fl.reshape(R,R)
        for _ in range(int(E('DIL',6))):
            ys,xs=np.nonzero(~fl)
            for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
                yy=np.clip(ys+dy,0,R-1); xx=np.clip(xs+dx,0,R-1); ok2=fl[yy,xx]&~fl[ys,xs]
                a16[ys[ok2],xs[ok2]]=a16[yy[ok2],xx[ok2]]; fl[ys[ok2],xs[ok2]]=True
        Image.fromarray(a16[::-1].copy(),mode='I;16').save(os.path.join(out,'%s.%d.png'%(nm_,1001+t)))
    # id of the nearest hard line (+1; 0 = none) and of the nearest soft line, for per-border strength maps
    for nm_,dd_,ii_,ID_ in (('cidh',dh,ih,Hid),('cids',ds,is_,Sid)):
        c16=np.zeros(R*R,np.uint16); c16[cov]=np.where(dd_<0.0635,ID_[np.minimum(ii_,len(ID_)-1)]+1,0); c16=c16.reshape(R,R)
        fl=np.zeros(R*R,bool); fl[cov]=True; fl=fl.reshape(R,R)
        for _ in range(int(E('DIL',6))):
            ys,xs=np.nonzero(~fl)
            for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
                yy=np.clip(ys+dy,0,R-1); xx=np.clip(xs+dx,0,R-1); ok2=fl[yy,xx]&~fl[ys,xs]
                c16[ys[ok2],xs[ok2]]=c16[yy[ok2],xx[ok2]]; fl[ys[ok2],xs[ok2]]=True
        Image.fromarray(c16[::-1].copy(),mode='I;16').save(os.path.join(out,'%s.%d.png'%(nm_,1001+t)))
    Image.fromarray(img[::-1]).save(os.path.join(out,'dist.%d.png'%(1001+t)))
    Image.fromarray(li[::-1]).save(os.path.join(out,'lab.%d.png'%(1001+t)))
    print('tile',1001+t,'covered',len(cov))
