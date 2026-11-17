# Pull-up station for the pull-up frames (15-11-2026): two uprights (light frame, like the other machines), a beam on top,
# dark feet, and the bar between the uprights (the long barbell 'Barra' of the base is replaced by a bar of that length,
# same radius, same place: the hands were wrapped round it by pullup6.py).
#   python -I dominadas_geo.py in.blend out.blend        env: BARY BARZ BARR (as pullup6.py), DGW half width, DGH height
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pulldown_geo import _mat, _box, _cyl
E = lambda k, d: float(os.environ.get(k, d))
src, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
BY = E('BARY', -0.03); BZ = E('BARZ', 2.15); rB = E('BARR', 0.0145); W = E('DGW', 0.62); H = E('DGH', 2.75)
for n in ('Barra', 'Discos'):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
for o in [o for o in bpy.data.objects if o.name.startswith('Banco')]: bpy.data.objects.remove(o, do_unlink=True)
frame = _mat('banco_frame', (0.97, 0.97, 0.98), 0.6, 0.0); dark = _mat('banco_dark', (0.035, 0.035, 0.04), 0.5, 0.2)
bar = _cyl('Barra', (-W, BY, BZ), (W, BY, BZ), rB, frame, 48)          # the renderer gives 'Barra' its steel material
for sx in (1, -1):
    _box('Banco_up', (sx * W, BY, H / 2), (0.07, 0.07, H), frame, bevel=0.008)
    _box('Banco_foot', (sx * W, BY, 0.03), (0.09, 0.80, 0.06), dark, bevel=0.01)
    _box('Banco_cap', (sx * W, BY, BZ), (0.10, 0.10, 0.08), dark, bevel=0.01)     # bar clamp on each upright
_box('Banco_top', (0, BY, H + 0.03), (2 * W + 0.07, 0.07, 0.06), frame, bevel=0.008)
bpy.ops.wm.save_as_mainfile(filepath=out)
print('pull-up station: bar %.2f m at z %.2f, uprights at x = +-%.2f' % (2 * W, BZ, W))
