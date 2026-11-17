import os
import bpy,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2])
for i in bpy.data.images:
    if i.filepath: print(i.filepath); i.filepath=i.filepath.replace('/tmp/w/',os.environ.get('GT3D','/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad')+'/w/'); i.reload()
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])
