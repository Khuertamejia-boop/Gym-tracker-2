# lift the selected weight plates of an already built face-pull frame (same rule as facepull_geo.py)
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
src, dst, q = a[0], a[1], float(a[2])
bpy.ops.wm.open_mainfile(filepath=src)
n, nsel, lift = 15, int(os.environ.get('NSEL', 6)), float(os.environ.get('LIFT', 0.20)) * q
for o in bpy.data.objects:
    if o.name.startswith('Banco_plate') and int(o.name[-2:]) >= n - nsel: o.location.z += lift
    if o.name == 'Banco_stacktop': o.location.z += lift
bpy.ops.wm.save_as_mainfile(filepath=dst)
