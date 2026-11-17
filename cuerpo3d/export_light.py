# Light animation-ready version: rest pose, ~150k triangles, skin weights kept, 50-bone skeleton, vertex colours (grey skin / black shorts).
import bpy,sys,os,numpy as np
from scipy.spatial import cKDTree
src,outdir,name=sys.argv[-3],sys.argv[-2],sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig']; hi=bpy.data.objects['Hi']
for o in list(bpy.data.objects):
    if o.name not in ('Rig','Hi'): bpy.data.objects.remove(o,do_unlink=True)
for pb in rig.pose.bones:
    pb.rotation_mode='QUATERNION'; pb.rotation_quaternion=(1,0,0,0); pb.location=(0,0,0); pb.scale=(1,1,1)
bpy.context.view_layer.update()
me=hi.data; n0=len(me.vertices)
P0=np.zeros(n0*3); me.vertices.foreach_get('co',P0); P0=P0.reshape(-1,3)
sh0=np.zeros(n0,np.float32); me.attributes['shorts'].data.foreach_get('value',sh0)
ntri=sum(len(p.vertices)-2 for p in me.polygons)
ratio=float(os.environ.get('TRIS','150000'))/ntri
print('triangles',ntri,'ratio',round(ratio,4))
for o in bpy.data.objects: o.select_set(False)
hi.select_set(True); bpy.context.view_layer.objects.active=hi
md=hi.modifiers.new('dec','DECIMATE'); md.ratio=ratio; md.use_collapse_triangulate=False
bpy.ops.object.modifier_move_to_index(modifier='dec',index=0)
bpy.ops.object.modifier_apply(modifier='dec')
me=hi.data; n1=len(me.vertices)
P1=np.zeros(n1*3); me.vertices.foreach_get('co',P1); P1=P1.reshape(-1,3)
_,ii=cKDTree(P0).query(P1); sh1=sh0[ii]
# vertex colours
for a in list(me.color_attributes): me.color_attributes.remove(a)
ca=me.color_attributes.new('Col','FLOAT_COLOR','POINT')
skin=np.array([0.80,0.80,0.80,1.0]); dark=np.array([0.035,0.035,0.035,1.0])
# smooth the shorts edge on the light mesh (the source attribute is binary and jagged)
import scipy.sparse as sp0
Ed=np.zeros(len(me.edges)*2,int); me.edges.foreach_get('vertices',Ed); Ed=Ed.reshape(-1,2)
A=sp0.coo_matrix((np.ones(2*len(Ed)),(np.r_[Ed[:,0],Ed[:,1]],np.r_[Ed[:,1],Ed[:,0]])),shape=(n1,n1)).tocsr()
Av=sp0.diags(1/np.maximum(np.asarray(A.sum(1)).ravel(),1))@A
sh1=(sh1>0.5).astype(float)
for _ in range(int(os.environ.get('SHS','14'))): sh1=0.5*sh1+0.5*(Av@sh1)
t=np.clip((sh1-0.5)/0.12+0.5,0,1); t=(t*t*(3-2*t))[:,None]
cols=skin*(1-t)+dark*t
ca.data.foreach_set('color',cols.ravel().astype(np.float32))
# drop the working attributes (not needed by the app)
for nm in ('mu','mdist','groove','mq','ln','hl','mseg','shorts'):
    a=me.attributes.get(nm)
    if a is not None:
        try: me.attributes.remove(a)
        except Exception: pass
# one simple material that shows the vertex colours (the working materials and their textures are not needed)
me.materials.clear()
mt=bpy.data.materials.new('Piel'); mt.use_nodes=True; nt=mt.node_tree; bs=nt.nodes['Principled BSDF']; bs.inputs['Roughness'].default_value=0.6
an=nt.nodes.new('ShaderNodeVertexColor'); an.layer_name='Col'; nt.links.new(an.outputs['Color'],bs.inputs['Base Color'])
me.materials.append(mt)
for img in list(bpy.data.images): bpy.data.images.remove(img)
hi.name='Cuerpo3D'; rig.name='Esqueleto'
tris=sum(len(p.vertices)-2 for p in me.polygons)
print('after decimation: verts',n1,'triangles',tris,'groups',len(hi.vertex_groups))
for p in me.polygons: p.use_smooth=True
os.makedirs(outdir,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir,name+'.blend'),compress=True)
try:
    for o in bpy.data.objects: o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(outdir,name+'.fbx'),object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=False,mesh_smooth_type='FACE')
    print('fbx ok')
except Exception as ex: print('fbx failed',ex)
try:
    bpy.ops.wm.usd_export(filepath=os.path.join(outdir,name+'.usdz'),export_animation=False,export_armatures=True)
    print('usdz ok')
except Exception as ex: print('usdz failed',ex)
