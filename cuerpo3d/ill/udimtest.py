import bpy,os,sys
d=sys.argv[-1]
img=bpy.data.images.load(os.path.join(d,'dist.1001.png'))
img.source='TILED'
import re,glob
for f in sorted(glob.glob(os.path.join(d,'dist.*.png'))):
    t=int(f.split('.')[-2])
    if t!=1001 and img.tiles.get(t) is None: img.tiles.new(tile_number=t)
img.filepath=os.path.join(d,'dist.<UDIM>.png'); img.reload()
print('tiles',[t.number for t in img.tiles], img.has_data, img.size[:])
