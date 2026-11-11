# Skinning / deformer stack for the pull-up poses (replaces the modifier part of pullup5.py).
import bpy, os, math
import numpy as np

def set_group(hi, name, w, q=1024):
    if name in hi.vertex_groups: hi.vertex_groups.remove(hi.vertex_groups[name])
    g = hi.vertex_groups.new(name=name); qq = np.round(np.clip(w, 0, 1) * q).astype(int)
    for val in np.unique(qq[qq > 0]): g.add([int(i) for i in np.where(qq == val)[0]], val / q, 'REPLACE')
    return g

def read_weights(hi, names):
    me = hi.data; nv = len(me.vertices); gi = {hi.vertex_groups[n].index: k for k, n in enumerate(names) if n in hi.vertex_groups}
    W = np.zeros((nv, len(names)), np.float32)
    for v in me.vertices:
        for g in v.groups:
            k = gi.get(g.group)
            if k is not None: W[v.index, k] = g.weight
    return W

def rest_co(hi):
    me = hi.data; co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); return co.reshape(-1, 3)

def dq_mask(hi, rig, E):
    """smooth mask: 1 around the shoulder joint / deltoid / upper arm, 0 on the chest middle, neck, lats far below"""
    bb = rig.data.bones; co = rest_co(hi); nv = len(co)
    W = read_weights(hi, ['neck', 'head', 'forearm.L', 'forearm.R', 'hand.L', 'hand.R'])
    nh = W[:, 0] + W[:, 1]
    m = np.zeros(nv)
    for L in 'LR':
        j = np.array(bb['upper_arm.' + L].head_local); t = np.array(bb['upper_arm.' + L].tail_local)
        a = (t - j); la = np.linalg.norm(a); a /= la
        rel = co - j; s = rel @ a                        # along the arm
        dseg = np.linalg.norm(rel - np.clip(s, 0, la)[:, None] * a, axis=1)
        dj = np.linalg.norm(rel, axis=1)
        # distance to the arm segment (from the joint to DQL*length along the arm)
        sc = np.clip(s, -1, E('DQL', 0.6) * la)
        d = np.linalg.norm(rel - sc[:, None] * a, axis=1)
        r0, r1 = E('DQR0', 0.07), E('DQR1', 0.17)
        tt = np.clip((d - r0) / (r1 - r0), 0, 1); f = 1 - tt * tt * (3 - 2 * tt)
        side = np.sign(j[0]); f *= (co[:, 0] * side > 0)
        # armpit / lat attenuation: below the joint and medial to the arm axis
        if E('DQPIT', 1.0) < 1:
            below = np.clip((j[2] - co[:, 2] - E('DQPZ0', 0.02)) / E('DQPZW', 0.08), 0, 1)
            f *= 1 - (1 - E('DQPIT', 1.0)) * below * (s < E('DQPS', 0.10))
        m = np.maximum(m, f)
    m *= np.clip(1 - nh * E('DQNECK', 3.0), 0, 1)
    lower = W[:, 2:].sum(1); m *= np.clip(1 - lower * 4, 0, 1)
    return m

def add_cs(hi, rig, E):
    bb = rig.data.bones
    if E('CSM', 1) > 0 and 'CS' in hi.vertex_groups:
        cs = hi.modifiers.new('CorrectiveSmooth', 'CORRECTIVE_SMOOTH'); cs.vertex_group = 'CS'; cs.iterations = int(E('CSIT', 10)); cs.factor = E('CSF', 0.8)
        cs.smooth_type = 'LENGTH_WEIGHTED'; cs.rest_source = 'ORCO'
    if E('CS2IT', 0) > 0:
        me = hi.data; nv = len(me.vertices); co = rest_co(hi)
        d = np.min([np.linalg.norm(co - np.array(bb['upper_arm.' + L].head_local), axis=1) for L in 'LR'], axis=0)
        t = np.clip((d - E('S2D0', 0.09)) / (E('S2D1', 0.18) - E('S2D0', 0.09)), 0, 1); w = 1 - t * t * (3 - 2 * t)
        nh = read_weights(hi, ['neck', 'head']).sum(1)
        w = w * np.clip(1 - nh * E('S2NECK', 3.0), 0, 1)
        set_group(hi, 'CS2', w, 64)
        c2 = hi.modifiers.new('CorrectiveSmooth2', 'CORRECTIVE_SMOOTH'); c2.vertex_group = 'CS2'; c2.iterations = int(E('CS2IT', 0)); c2.factor = E('CS2F', 1.0)
        c2.smooth_type = 'LENGTH_WEIGHTED'; c2.rest_source = 'ORCO'

def _build_native(hi, rig, md, E):
    mode = os.environ.get('SKIN', 'lbs')
    if mode == 'dqs':
        md.use_deform_preserve_volume = True
    elif mode == 'mix':
        m = dq_mask(hi, rig, E)
        set_group(hi, 'DQ', m)
        md2 = hi.modifiers.new('ArmatureDQ', 'ARMATURE'); md2.object = rig; md2.use_deform_preserve_volume = True
        md2.use_multi_modifier = True; md2.vertex_group = 'DQ'
    add_cs(hi, rig, E)

# ---------------------------------------------------------------- baked skinning (CoR) with bound corrective smooth
import hashlib, time
import corskin as D_cor

def eval_coords(hi):
    dg = bpy.context.evaluated_depsgraph_get(); ev = hi.evaluated_get(dg); me = ev.to_mesh()
    c = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', c); ev.to_mesh_clear(); return c.reshape(-1, 3)

def region_and_mask(hi, rig, names, W, co, E):
    k = {n: i for i, n in enumerate(names)}
    verts = []; mask = np.zeros(len(co))
    for L in 'LR':
        sh = W[:, k['upper_arm.' + L]] + W[:, k['clavicle.' + L]] + (W[:, k['delt.' + L]] if 'delt.' + L in k else 0)
        lower = sum(W[:, k[n]] for n in names if n.endswith('.' + L) and n.split('.')[0] in ('forearm', 'fa_tw1', 'fa_tw2', 'fa_tw3', 'hand'))
        r = (sh > 1e-4) & (lower < 0.25)
        m = np.clip(1 - lower * 4, 0, 1)
        if E('SHW', 0) > 0: m = m * sstep(sh / E('SHW', 0))     # fade to plain LBS where the shoulder weight is small (no step at the region edge)
        mask[r] = np.maximum(mask[r], m[r]); verts.append(np.where(r)[0])
    verts = np.unique(np.concatenate(verts))
    return verts, mask[verts]

def cor_cache(co, tris, W, verts, E, log):
    h = hashlib.md5(W[verts].tobytes() + co[verts].tobytes() + np.int64(verts).tobytes() + str((E('CORSIG', 0.1), E('CORTS', 1))).encode()).hexdigest()[:12]
    fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'corcache_{h}.npz')
    if os.path.exists(fn):
        z = np.load(fn); return z['p'], z['ok']
    p, ok = D_cor.precompute(co, tris, W, verts, sig=E('CORSIG', 0.1), tsub=int(E('CORTS', 1)), log=log)
    np.savez(fn, p=p, ok=ok); return p, ok

def sstep(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

def cor_mask(c, E):
    """share of CoR (vs LBS) per vertex: CoR on the compressed side (deltoid cap, top of the shoulder), LBS in the
    stretched armpit / lat / side of the chest"""
    m = np.zeros(len(c))
    for sd in (1.0, -1.0):
        A = np.array((sd * E('APX', 0.172), E('APY', -0.03), E('APZ', 1.215)))
        dA = np.linalg.norm(c - A, axis=1)
        s1 = sstep((dA - E('MR0', 0.03)) / (E('MR1', 0.12) - E('MR0', 0.03)))
        s2 = sstep((c[:, 2] - (A[2] - E('MZB', 0.0))) / E('MZW', 0.06))
        f = np.maximum(s1 * s2, E('MFLOOR', 0.0))
        m = np.where(c[:, 0] * sd > 0, f, m)
    return m

def add_twist(rig, names, W, M, co, E, log):
    """virtual 'swing + part of the twist' copy of each upper arm: the skin near the shoulder takes only TW0 of the
    humeral twist, rising smoothly to the full twist at TB of the arm length (like game-rig upper-arm twist bones)"""
    from mathutils import Matrix, Quaternion
    pb = rig.pose.bones; bb = rig.data.bones
    names = list(names); Ms = [M]; Wc = [W]
    for L in 'LR':
        ku = names.index('upper_arm.' + L)
        Rua = bb['upper_arm.' + L].matrix_local; Rcl = bb['clavicle.' + L].matrix_local
        Pua = pb['upper_arm.' + L].matrix; Pcl = pb['clavicle.' + L].matrix
        rel = Rcl.to_3x3().inverted() @ Rua.to_3x3()
        Ql = (rel.inverted() @ Pcl.to_3x3().inverted() @ Pua.to_3x3()).to_quaternion()
        if Ql.w < 0: Ql = -Ql
        ang = 2 * math.atan2(Ql.y, Ql.w); tw = Quaternion((0, 1, 0), ang); sw = Ql @ tw.inverted()
        f = E('TW0', 0.5)
        Qf = sw @ Quaternion((0, 1, 0), ang * f)
        Pf = (Pcl.to_3x3() @ rel @ Qf.to_matrix()).to_4x4(); Pf.translation = Pua.translation
        Mf = np.array(Pf @ Rua.inverted())
        a = np.array(bb['upper_arm.' + L].head_local); b = np.array(bb['upper_arm.' + L].tail_local); dv = b - a
        t = (co - a) @ dv / (dv @ dv)
        g = sstep((t - E('TA', 0.0)) / (E('TB', 0.7) - E('TA', 0.0)))
        wu = W[:, ku].copy()
        col = (wu * (1 - g))[:, None].astype(W.dtype)
        W[:, ku] = wu * g
        Wc.append(col); Ms.append(Mf[None]); names.append('ua_tw.' + L)
        log(f'{L} humeral twist {math.degrees(ang):+.1f} deg, shoulder skin takes {f:.2f} of it')
    return names, np.hstack(Wc), np.concatenate(Ms)

def build_cor(hi, rig, md, E):
    t0 = time.time(); log = lambda s: print('D_', s)
    me = hi.data; co = rest_co(hi)
    names = D_cor.bone_list(hi, rig); W = D_cor.weights(hi, names)
    s = W.sum(1, keepdims=True); s[s == 0] = 1; W = W / s
    me.calc_loop_triangles(); tris = np.zeros(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get('vertices', tris); tris = tris.reshape(-1, 3)
    verts, m = region_and_mask(hi, rig, names, W, co, E)
    M = D_cor.bone_mats(rig, names)
    # blender's own LBS for everything (exactly the baseline outside the shoulders)
    for x in hi.modifiers: x.show_viewport = (x == md)
    lb = eval_coords(hi)
    log(f'lbs check max diff {np.abs(D_cor.lbs(co, W, M, verts) - lb[verts]).max() * 1000:.2f} mm')
    if E('TW', 0) > 0: names, W, M = add_twist(rig, names, W, M, co, E, log)
    p, ok = cor_cache(co, tris, W, verts, E, log)
    sph = np.zeros(len(verts))
    if E('SPH', 0) > 0:
        # deltoid cap = skin over the humeral head (a ball): rotate it about the real joint centre, so it stays round
        bb = rig.data.bones
        for L in 'LR':
            sd = 1.0 if L == 'L' else -1.0
            c = np.array(bb['upper_arm.' + L].head_local) + np.array((sd * E('SCX', 0.0), E('SCY', 0.0), E('SCZ', 0.0)))
            dd = np.linalg.norm(co[verts] - c, axis=1)
            sL = 1 - sstep((dd - E('SR0', 0.06)) / (E('SR1', 0.12) - E('SR0', 0.06)))
            sL *= (co[verts, 0] * sd > E('SXMIN', 0.06))
            sph = np.maximum(sph, sL)
            sel = sL > 0
            p[sel] = p[sel] * (1 - sL[sel, None]) + c[None] * sL[sel, None]
            ok = ok | sel
        log(f'sphere cap verts {int((sph > 0.5).sum())}')
    mine = D_cor.lbs(co, W, M, verts)
    cs = D_cor.skin(co, W, M, p, verts)
    if E('CMASK', 1) > 0: m = m * cor_mask(co[verts], E)
    m = m * E('CORK', 1.0)
    m = np.maximum(m, sph * E('SPHK', 1.0))
    m = np.where(ok, m, 0.0)
    new = lb.copy(); new[verts] = mine * (1 - m[:, None]) + cs * m[:, None]
    if os.environ.get('DBGHL'):
        h = np.zeros(len(co)); 
        if os.environ['DBGHL'] == 'mask': h[verts] = m
        else: h[verts] = np.clip(np.linalg.norm(cs - mine, axis=1) / E('DBGS', 0.06), 0, 1)
        me = hi.data
        if 'hl' in me.attributes: me.attributes.remove(me.attributes['hl'])
        a = me.attributes.new('hl', 'FLOAT', 'POINT'); a.data.foreach_set('value', h.astype(np.float32))
    log(f'CoR max move vs LBS {np.linalg.norm(cs - mine, axis=1).max() * 1000:.1f} mm, {time.time() - t0:.1f}s')
    return new

def bake(hi, new, E):
    """remove armature modifiers, bind the corrective smooths to the rest mesh, write the posed coordinates"""
    for x in list(hi.modifiers):
        if x.type == 'ARMATURE': hi.modifiers.remove(x)
    for x in hi.modifiers:
        x.show_viewport = True
        if x.type == 'CORRECTIVE_SMOOTH':
            x.rest_source = 'BIND'
            with bpy.context.temp_override(object=hi, active_object=hi):
                bpy.ops.object.correctivesmooth_bind(modifier=x.name)
    bpy.context.view_layer.update(); bpy.context.evaluated_depsgraph_get()
    hi.data.vertices.foreach_set('co', new.ravel()); hi.data.update()
    for x in hi.modifiers:
        if x.type == 'CORRECTIVE_SMOOTH': print('D_ bound', x.name, x.is_bind)

def build(hi, rig, md, E):
    mode = os.environ.get('SKIN', 'lbs')
    if mode == 'cor':
        new = build_cor(hi, rig, md, E)
        add_cs(hi, rig, E)
        bake(hi, new, E)
        return
    _build_native(hi, rig, md, E)
