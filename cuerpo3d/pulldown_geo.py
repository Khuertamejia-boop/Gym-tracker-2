# Lat pulldown station built around the posed body (style of the reference plates: light-grey frame, black pads and
# weight stack): flat bench under the buttocks, knee roller on top of the thighs, tower in front with the weight stack
# (selected plates rise as the handle comes down), boom with the high pulley on the cable line, cable, and the close-grip
# V-handle (two parallel grips inside the fists, steel triangle up to the clip).
import bpy, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

def _mat(name, col, rough, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m

def _box(name, c, size, mat, R=None, bevel=0.0, seg=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); o = bpy.context.active_object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    o.matrix_world = Matrix.Translation(Vector(c)) @ ((R or Matrix.Identity(3)).to_4x4())
    if bevel > 0: bv = o.modifiers.new('bv', 'BEVEL'); bv.width = bevel; bv.segments = seg
    o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o

def _beam(name, a, b, w, t, mat, bevel=0.006):
    """box beam from a to b (width w along x, thickness t)"""
    a = Vector(a); b = Vector(b); d = b - a; y = d.normalized(); x = Vector((1, 0, 0)); z = x.cross(y).normalized()
    R = Matrix((x, y, z)).transposed()
    return _box(name, (a + b) / 2, (w, d.length, t), mat, R=R, bevel=bevel)

def _cyl(name, a, b, r, mat, verts=32):
    a = Vector(a); b = Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(0, 0, 0))
    o = bpy.context.active_object; o.name = name
    o.matrix_world = Matrix.Translation((a + b) / 2) @ Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    o.data.materials.append(mat); bpy.ops.object.shade_smooth(); return o

def _tube(name, pts, r, mat):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 6
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, P in zip(sp.points, pts): p.co = (P.x, P.y, P.z, 1)
    o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o); cu.materials.append(mat); return o

def build(hi, rig, grips, rB, q, HT, HB, cdir, E):
    for o in [o for o in bpy.data.objects if o.name.startswith('Banco')]: bpy.data.objects.remove(o, do_unlink=True)
    frame = _mat('banco_frame', (0.97, 0.97, 0.98), 0.6, 0.0); dark = _mat('banco_dark', (0.035, 0.035, 0.04), 0.5, 0.2)
    pad = _mat('banco_pad', (0.035, 0.035, 0.04), 0.55); steel = _mat('banco_grey', (0.55, 0.55, 0.57), 0.35, 0.6)
    cable = _mat('banco_cable', (0.12, 0.12, 0.13), 0.4, 0.7); grip = _mat('banco_grip', (0.02, 0.02, 0.02), 0.8)
    dg = bpy.context.evaluated_depsgraph_get(); m = hi.evaluated_get(dg).to_mesh()
    P = np.zeros(len(m.vertices) * 3); m.vertices.foreach_get('co', P); P = P.reshape(-1, 3); hi.evaluated_get(dg).to_mesh_clear()
    pb = rig.pose.bones
    hip = (Vector(pb['thigh.L'].head) + Vector(pb['thigh.R'].head)) / 2
    knee = (Vector(pb['shin.L'].head) + Vector(pb['shin.R'].head)) / 2
    # ---- bench: top = lowest skin under the buttocks (a little sink into the pad)
    sel = (np.abs(P[:, 0]) < 0.17) & (P[:, 1] > hip.y - 0.12) & (P[:, 1] < hip.y + 0.16) & (P[:, 2] < hip.z)
    seat = np.percentile(P[sel, 2], 1.0) + E('SINK', 0.006)
    BT, BW = 0.07, 0.28; y0 = knee.y + E('BFRONT', 0.20); y1 = hip.y + E('BBACK', 0.95)
    _box('Banco_pad', (0, (y0 + y1) / 2, seat - BT / 2), (BW, y1 - y0, BT), pad, bevel=0.02, seg=5)
    _box('Banco_base', (0, (y0 + y1) / 2, seat - BT - 0.012), (0.10, y1 - y0 - 0.06, 0.025), frame, bevel=0.004)
    for yl in (y0 + 0.10, y1 - 0.10):
        _box('Banco_leg', (0, yl, (seat - BT) / 2), (0.07, 0.07, seat - BT - 0.02), frame, bevel=0.006)
        _box('Banco_foot', (0, yl, 0.022), (0.42, 0.07, 0.045), frame, bevel=0.006)
    # ---- tower in front of the knees: two uprights, guide rods, weight stack
    yt = knee.y - E('TOWY', 0.48); H = E('TOWH', 2.10); W2 = 0.24
    for sx in (-1, 1):
        _box('Banco_up', (sx * W2, yt, H / 2), (0.075, 0.075, H), frame, bevel=0.008)
        _box('Banco_tfoot', (sx * W2, yt + 0.05, 0.03), (0.09, 0.70, 0.06), dark, bevel=0.01)
        _cyl('Banco_rod', (sx * 0.085, yt, 0.08), (sx * 0.085, yt, H - 0.05), 0.012, frame, 16)
    _box('Banco_ttop', (0, yt, H + 0.03), (2 * W2 + 0.10, 0.16, 0.06), frame, bevel=0.008)
    _box('Banco_tlow', (0, yt, 0.07), (2 * W2, 0.10, 0.05), frame, bevel=0.006)
    travel = (HT - HB).length; lift = (HT - (HT.lerp(HB, q))).length * E('LIFTK', 0.6)
    n = 16; nsel = int(E('NSEL', 6))
    for k in range(n):
        dz = lift if k >= n - nsel else 0.0
        _box('Banco_plate%02d' % k, (0, yt, 0.12 + k * 0.034 + dz), (0.30, 0.15, 0.030), dark, bevel=0.004)
    stz = 0.12 + n * 0.034 + 0.012 + lift
    _box('Banco_stacktop', (0, yt, stz), (0.26, 0.10, 0.035), frame, bevel=0.006)
    # ---- front column (holds the knee roller) and the boom up to the high pulley on the cable line
    Pp = HT + cdir * (E('APEX', 0.10) + E('PULD', 0.24))
    yc = yt + 0.17
    _box('Banco_col', (0, yc, (Pp.z - 0.10) / 2 + 0.03), (0.09, 0.11, Pp.z - 0.10), frame, bevel=0.008)
    _box('Banco_colfoot', (0, (yc + yt) / 2, 0.03), (0.10, yc - yt + 0.12, 0.06), dark, bevel=0.01)
    _beam('Banco_boom', (0, yc, Pp.z - 0.06), (0, Pp.y + 0.03, Pp.z + 0.02), 0.08, 0.08, frame)
    _beam('Banco_topbar', (0, yt, H + 0.03), (0, yc, Pp.z - 0.06), 0.07, 0.06, frame)
    _cyl('Banco_wheel', Pp + Vector((0.016, 0, 0)), Pp - Vector((0.016, 0, 0)), 0.045, dark)
    _box('Banco_housing', Pp + Vector((0, 0.0, 0.03)), (0.05, 0.11, 0.06), frame, bevel=0.006)
    Pt = Vector((0, yt, H + 0.10))
    _cyl('Banco_wheel2', Pt + Vector((0.016, 0, 0)), Pt - Vector((0.016, 0, 0)), 0.045, dark)
    # ---- knee roller on top of the thighs, just behind the knees, on an arm from the front column
    kz = (np.abs(P[:, 0]) > 0.02) & (np.abs(P[:, 0]) < 0.20) & (np.abs(P[:, 1] - (knee.y + 0.09)) < 0.03) & (P[:, 2] > knee.z - 0.02)
    RR = E('ROLLR', 0.055); rc = Vector((0, knee.y + 0.09, np.max(P[kz, 2]) + RR + 0.002))
    _cyl('Banco_roller', (-0.22, rc.y, rc.z), (0.22, rc.y, rc.z), RR, pad, verts=40)
    _cyl('Banco_raxle', (-0.235, rc.y, rc.z), (0.235, rc.y, rc.z), 0.012, steel, 16)
    _beam('Banco_rarm', (0, rc.y - 0.02, rc.z), (0, yc + 0.05, rc.z), 0.05, 0.05, frame)
    # ---- V-handle: grips in the fists, steel triangle up to the clip, cable to the pulley
    cL, aL = grips['L']; cR, aR = grips['R']
    A = (cL + cR) / 2 + cdir * E('APEX', 0.10)
    for Ls, (c, a) in grips.items():
        a = a.normalized()
        e0 = c - a * E('GRIPL', 0.065); e1 = c + a * E('GRIPL', 0.065)
        _cyl('Banco_grip' + Ls, e0, e1, rB, grip)
        _cyl('Banco_gcap' + Ls, e0 - a * 0.006, e0, rB * 1.08, steel, 24); _cyl('Banco_gcap' + Ls, e1, e1 + a * 0.006, rB * 1.08, steel, 24)
        _cyl('Banco_vbar' + Ls, e0 - a * 0.003, A, 0.008, steel, 16); _cyl('Banco_vbar' + Ls, e1 + a * 0.003, A, 0.008, steel, 16)
    _cyl('Banco_clip', A - cdir * 0.005, A + cdir * 0.03, 0.010, steel, 16)
    _tube('Banco_cable', [A + cdir * 0.03, Pp - cdir * 0.045], 0.0035, cable)
    _tube('Banco_cable2', [Pp + Vector((0, 0, 0.045)), Pt + Vector((0, 0, 0.045))], 0.0035, cable)
    _tube('Banco_cable3', [Pt + Vector((0, 0.045, 0)), Vector((0, yt + 0.045, stz + 0.02))], 0.0035, cable)
    # ---- checks: how close the handle and the fists come to the face
    cab = bpy.data.objects.get('Cabeza')
    if cab is not None:
        bv = BVHTree.FromObject(cab, dg)
        pts = [A, cL, cR] + [c + a * k for (c, a) in grips.values() for k in (-0.07, 0.07)]
        dmin = min((p - bv.find_nearest(p)[0]).length for p in pts)
        print('handle-to-head min %.1f mm  seat %.3f roller %s pulley %s travel %.2f m' % (dmin * 1000, seat, tuple(round(v, 3) for v in rc), tuple(round(v, 3) for v in Pp), travel))
