import bpy,sys,math,os
from mathutils import Vector,Matrix
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); out=sys.argv[-1]
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']
md=hi.modifiers.new('Armature','ARMATURE'); md.object=rig
import numpy as np
def fixw(ob):
    me=ob.data; gi={g.name:g.index for g in ob.vertex_groups}; gname={g.index:g.name for g in ob.vertex_groups}
    armset=[n for n in gi if n.split('.')[0] in ('upper_arm','forearm','hand') or n[:-3].rstrip('123') in ('thumb','index','middle','ring','pinky')]
    chest=ob.vertex_groups['chest']
    for v in me.vertices:
        ax=abs(v.co.x)
        fa=min(1.0,max(0.0,(ax-float(os.environ.get('FA0','0.10')))/float(os.environ.get('FAW','0.13')))); fa=fa*fa*(3-2*fa); fc=min(1.0,max(0.0,(ax-0.03)/0.12)); fc=fc*fc*(3-2*fc)
        if fa>=1 and fc>=1: continue
        removed=0.0
        for g in v.groups:
            n=gname[g.group]
            if n in armset and fa<1: removed+=g.weight*(1-fa); g.weight*=fa
            elif n.startswith('clavicle') and fc<1: removed+=g.weight*(1-fc); g.weight*=fc
        if removed>1e-4:
            cur=[g.weight for g in v.groups if g.group==chest.index]
            chest.add([v.index],(cur[0] if cur else 0)+removed,'REPLACE')
fixw(hi)
def smoothw(ob,iters=40):
    # smooth the skin weights of the shoulder region (arm / clavicle / chest / spine / neck): removes the faceted look when the arms are raised
    import scipy.sparse as sp0
    me=ob.data; nv=len(me.vertices); gi={g.name:g.index for g in ob.vertex_groups}
    names=[n for n in ('upper_arm.L','upper_arm.R','clavicle.L','clavicle.R','chest','spine','neck') if n in gi]
    co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    ax=np.abs(co[:,0]); z=co[:,2]
    st=lambda a,b,x: (lambda t: t*t*(3-2*t))(np.clip((x-a)/(b-a),0,1))
    reg=st(0.07,0.10,ax)*(1-st(0.30,0.34,ax))*st(1.20,1.26,z)*(1-st(1.50,1.54,z))
    R=np.where(reg>1e-3)[0]
    inv={v:i for i,v in enumerate(R)}
    W=np.zeros((nv,len(names))); idx={gi[n]:k for k,n in enumerate(names)}
    for v in R:
        for g in me.vertices[v].groups:
            k=idx.get(g.group)
            if k is not None: W[v,k]=g.weight
    Ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',Ed); Ed=Ed.reshape(-1,2)
    A=sp0.coo_matrix((np.ones(2*len(Ed)),(np.r_[Ed[:,0],Ed[:,1]],np.r_[Ed[:,1],Ed[:,0]])),shape=(nv,nv)).tocsr()
    Av=(sp0.diags(1/np.maximum(np.asarray(A.sum(1)).ravel(),1))@A).tocsr(); AvR=Av[R,:].tocsr(); w=reg[R][:,None]
    tot0=W[R].sum(1,keepdims=True)
    for _ in range(iters): W[R]=W[R]*(1-w)+w*(AvR@W)
    W[R]*=tot0/np.maximum(W[R].sum(1,keepdims=True),1e-9)
    for v in R:
        for k,n in enumerate(names):
            val=float(W[v,k])
            if val>1e-4: ob.vertex_groups[n].add([int(v)],val,'REPLACE')
            else:
                try: ob.vertex_groups[n].remove([int(v)])
                except Exception: pass
    print('smoothed weights on',len(R),'verts')
if os.environ.get('SMW','0')=='1': smoothw(hi,int(os.environ.get('SMWIT','40')))
def ballw(ob,r0,r1):
    # shoulder as a ball joint: the arm weight blends smoothly with the distance to the shoulder joint (instead of a hard |x| band)
    me=ob.data; nv=len(me.vertices); gi={g.name:g.index for g in ob.vertex_groups}
    co=np.zeros(nv*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    n=0
    for s_,L in ((1,'L'),(-1,'R')):
        J=np.array(rig.data.bones['upper_arm.'+L].head_local)
        d=np.linalg.norm(co-J,axis=1); w=np.clip((r1-d)/(r1-r0),0,1); w=w*w*(3-2*w)
        reg=np.where((w>1e-3)&(co[:,0]*s_>0.0)&(co[:,2]>1.15))[0]
        gU=ob.vertex_groups['upper_arm.'+L]; gC=ob.vertex_groups['chest']
        for v in reg:
            cur=0.0; cc=0.0
            for g in me.vertices[v].groups:
                if g.group==gU.index: cur=g.weight
                if g.group==gC.index: cc=g.weight
            tgt=max(cur,float(w[v]))
            gU.add([int(v)],tgt,'REPLACE')
            # keep the total roughly 1: take what the arm gained from the chest
            gC.add([int(v)],max(cc-(tgt-cur),0.0),'REPLACE')
        n+=len(reg)
    print('ball-joint weights on',n,'verts')
if os.environ.get('BALL'):
    r_=[float(v) for v in os.environ['BALL'].split(',')]; ballw(hi,r_[0],r_[1])
def aim(bn,target,roll=0.0):
    pb=rig.pose.bones[bn]; b=rig.data.bones[bn]
    bpy.context.view_layer.update()
    cur=(pb.tail-pb.head).normalized()           # current pose direction (armature space)
    tv=Vector(target).normalized(); R=Matrix.Rotation(math.radians(roll),3,tv)@cur.rotation_difference(tv).to_matrix()
    # world-space rotation -> local pose rotation
    M=pb.matrix.to_3x3()
    newM=R@M
    par=pb.parent.matrix.to_3x3() if pb.parent else Matrix.Identity(3)
    rest=b.matrix_local.to_3x3(); prest=b.parent.matrix_local.to_3x3() if b.parent else Matrix.Identity(3)
    local=(prest.inverted()@rest).inverted()@par.inverted()@newM
    pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=local.to_quaternion()
    bpy.context.view_layer.update()
if os.environ.get('CLAV'):
    # the shoulder girdle follows when the arm is raised: lift the clavicle (scapulo-humeral rhythm)
    lift=float(os.environ.get('CLAV'))
    for s_,L in ((1,'L'),(-1,'R')):
        bn=rig.data.bones['clavicle.'+L]; d_=(bn.tail_local-bn.head_local); n_=d_.length
        aim('clavicle.'+L,(d_.x,d_.y,d_.z+lift*n_))
ua=[float(v) for v in os.environ.get('UA','0.16,0.02,-1').split(',')]
fa=[float(v) for v in os.environ.get('FA','0.10,-0.18,-1').split(',')]
for s,L in ((1,'L'),(-1,'R')):
    aim('upper_arm.'+L,(s*ua[0],ua[1],ua[2]),s*float(os.environ.get('ROLL','70')))
    aim('forearm.'+L,(s*fa[0],fa[1],fa[2]),s*float(os.environ.get('FROLL','0')))
if os.environ.get('TH'):
    th=[float(v) for v in os.environ.get('TH').split(',')]; sh=[float(v) for v in os.environ.get('SH','0.02,0,-1').split(',')]
    for s_,L in ((1,'L'),(-1,'R')):
        aim('thigh.'+L,(s_*th[0],th[1],-1)); aim('shin.'+L,(s_*sh[0],sh[1],-1))
if os.environ.get('GIK'):
    # fingers wrap the bar: each phalanx bends about the WORLD x axis (the bar axis), whatever its own bone roll is
    from mathutils import Quaternion
    A=[float(v) for v in os.environ.get('GA','55,50,40').split(',')]; sc=[float(v) for v in os.environ.get('GSC','1,1,1,1').split(',')]
    TA=[float(v) for v in os.environ.get('GTA','20,25,25').split(',')]
    bpy.context.view_layer.update()
    X_=Vector((1,0,0)); pts=[]
    for L in 'LR':
        hp=rig.pose.bones['hand.'+L].matrix.copy()
        for f_,scf in (('index',sc[0]),('middle',sc[1]),('ring',sc[2]),('pinky',sc[3]),('thumb',1.0)):
            par=hp; parent_rest=rig.data.bones['hand.'+L].matrix_local
            angs=TA if f_=='thumb' else A
            for k in (1,2,3):
                bn=rig.data.bones[f'{f_}{k}.{L}']; pb=rig.pose.bones[f'{f_}{k}.{L}']
                M=par@(parent_rest.inverted()@bn.matrix_local)
                ax_=M.to_3x3().inverted()@X_
                q=Quaternion(ax_.normalized(),math.radians(angs[k-1]*scf))
                pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=q
                par=M@q.to_matrix().to_4x4(); parent_rest=bn.matrix_local
                if f_=='middle' and k>=2: pts.append(par.translation.copy())
                if f_=='middle' and k==3: pts.append(par@Vector((0,bn.length,0)))
    bpy.context.view_layer.update()
    g=sum(pts,Vector())/len(pts)
    off=g-Vector((0,-0.2962,0.9366))+Vector((0,float(os.environ.get('GDY','0')),float(os.environ.get('GDZ','0'))))
    if os.environ.get('BARR'):
        k_=float(os.environ['BARR'])/0.025; bm_=bpy.data.objects['Barra'].data
        for v_ in bm_.vertices: v_.co.y=-0.2962+(v_.co.y+0.2962)*k_; v_.co.z=0.9366+(v_.co.z-0.9366)*k_
        bm_.update()
    for n in ('Barra','Discos'):
        o=bpy.data.objects[n]; o.parent=None; o.location=off; o.hide_render=False
    print('GIK bar centre',tuple(g))
if os.environ.get('GRIP'):
    # hands close around the bar: curl the fingers and thumb, then move the bar to the hands
    cu=float(os.environ.get('GRIP'))
    for L in 'LR':
        for f_,ang in (('index',(1.0,1.2,0.9)),('middle',(1.0,1.25,0.95)),('ring',(1.05,1.25,0.95)),('pinky',(1.1,1.25,0.95)),('thumb',(0.35,0.5,0.4))):
            for k in (1,2,3):
                pb=rig.pose.bones[f'{f_}{k}.{L}']; pb.rotation_mode='XYZ'
                ax_=os.environ.get('GAX','x'); sg=float(os.environ.get('GSG','1'))
                e=[0,0,0]; e['xyz'.index(ax_)]=sg*cu*ang[k-1]*(1 if L=='L' else float(os.environ.get('GRS','1')))
                pb.rotation_euler=e
    bpy.context.view_layer.update()
    if os.environ.get('GPT')=='mid2':
        gp=[ rig.matrix_world@((rig.pose.bones['index2.'+L].head+rig.pose.bones['middle2.'+L].head+rig.pose.bones['ring2.'+L].head)/3) for L in 'LR']
    else:
        gp=[ (rig.matrix_world@(rig.pose.bones['index1.'+L].head+rig.pose.bones['pinky1.'+L].head)/2) for L in 'LR']
    g=(gp[0]+gp[1])/2; off=g-Vector((0,-0.296,0.937))+Vector((0,float(os.environ.get('GDY','-0.02')),float(os.environ.get('GDZ','-0.02'))))
    for n in ('Barra','Discos'):
        o=bpy.data.objects[n]; o.parent=None; o.location=off; o.hide_render=False
    if os.environ.get('BARR'):
        # real bar: the model's shaft is 50 mm thick, a men's Olympic shaft is 28 mm
        k_=float(os.environ['BARR'])/0.025; bm_=bpy.data.objects['Barra'].data
        for v_ in bm_.vertices: v_.co.y=-0.2962+(v_.co.y+0.2962)*k_; v_.co.z=0.9366+(v_.co.z-0.9366)*k_
        bm_.update()
    print('grip',tuple(g),'bar offset',tuple(off))
bpy.ops.wm.save_as_mainfile(filepath=out)
