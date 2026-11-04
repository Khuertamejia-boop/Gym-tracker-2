# App background animation from the rendered poses (transparent PNGs, rest -> pose):
#  1) mockup video inside the owner's «Mi plan» screenshot (old figure erased, title / muscles replaced), H.264
#  2) transparent video (ProRes 4444 with alpha, .mov) + the transparent frames cropped to the figure (same box for all)
# usage: python3 app_video.py <frames dir> <out prefix>      env: TITLE, SUB (text on the screen), FPS (25),
#   HOLDB (rest at the start, frames), HOLDT (pose held, frames), HOLDE (rest at the end), W (mockup width, 720),
#   TH (height of the transparent video, 900)
import sys, os, glob, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
E = lambda k, d: int(os.environ.get(k, d))
src, outp = sys.argv[1], sys.argv[2]
fs = sorted(glob.glob(os.path.join(src, 'f[0-9][0-9].png'))); n = len(fs)
seq = [0] * E('HOLDB', 8) + list(range(1, n)) + [n - 1] * E('HOLDT', 30) + list(range(n - 2, 0, -1)) + [0] * E('HOLDE', 12)
FPS = E('FPS', 25)
ims = [Image.open(f).convert('RGBA') for f in fs]
# one crop box for every frame: union of the figure over all frames (+ margin), so nothing jumps
bbs = np.array([im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox() for im in ims])
x0, y0 = bbs[:, 0].min(), bbs[:, 1].min(); x1, y1 = bbs[:, 2].max(), bbs[:, 3].max()
cx = ims[0].width / 2; hw = max(cx - x0, x1 - cx) + 16; x0, x1 = int(cx - hw), int(cx + hw)
y0, y1 = int(y0 - 16), int(y1 + 16)
print('crop', (x0, y0, x1, y1), 'frames', n, 'video frames', len(seq), '%.2f s' % (len(seq) / FPS))
crops = [im.crop((x0, y0, x1, y1)) for im in ims]
tmp = tempfile.mkdtemp()

def encode(frames_dir, pattern, out, args):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames_dir, pattern)] + args + [out], check=True)

# ---------- 2) transparent: frames + ProRes 4444 with alpha
TH = E('TH', 900); sc = TH / crops[0].height; tw = int(round(crops[0].width * sc / 2)) * 2
small = [c.resize((tw, TH), Image.LANCZOS) for c in crops]
fd = outp + '_frames'; os.makedirs(fd, exist_ok=True)
for i, c in enumerate(small): c.save(os.path.join(fd, 'f%02d.png' % i), optimize=True)
d2 = os.path.join(tmp, 't'); os.makedirs(d2)
for k, i in enumerate(seq): os.symlink(os.path.join(os.path.abspath(fd), 'f%02d.png' % i), os.path.join(d2, 'v%05d.png' % k))
encode(d2, 'v%05d.png', outp + '_transparente.mov', ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le',
       '-alpha_bits', '8', '-vendor', 'apl0', '-qscale:v', os.environ.get('PQ', '6')])

# ---------- 1) mockup inside the screenshot
SHOT = os.environ.get('SHOT', '/home/user/Gym-tracker-2/cuerpo3d/referencias/c7eb47ab-app-pull.jpg')
scr = Image.open(SHOT).convert('RGB'); k = scr.width / 944
a = np.asarray(scr).astype(float)
# erase the old figure: the screen has a soft radial glow behind it, modelled as b0 + A*exp(-(r/s)^p) (fit on the clean
# background around and between the old figure), then every pixel of the old figure (and its shadow) takes the model
H_, W_, _ = a.shape; yy, xx = np.mgrid[0:H_, 0:W_]
r = np.hypot((xx - 520) * 0.8, yy - 920)
Lm = a.mean(2)
def boxf(x, R):
    c = np.cumsum(np.cumsum(np.pad(x, ((R + 1, R), (R + 1, R)), mode='edge'), 0), 1)
    return (c[2 * R + 1:, 2 * R + 1:] - c[:-2 * R - 1, 2 * R + 1:] - c[2 * R + 1:, :-2 * R - 1] + c[:-2 * R - 1, :-2 * R - 1]) / (2 * R + 1) ** 2
sd = np.sqrt(np.maximum(boxf(Lm * Lm, 4) - boxf(Lm, 4) ** 2, 0)); sat = a.max(2) - a.min(2)
smooth = (sd < 0.7) & (sat < 5) & (Lm > 236)
clean = np.asarray(Image.fromarray(((~smooth) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) == 0
box = (xx > 265 * k) & (xx < 685 * k) & (yy > 540 * k) & (yy < 1160 * k)
reg = (xx > 30) & (xx < 1005) & (yy > 600) & (yy < 1290) & clean
model = np.zeros_like(a)
for ch in range(3):
    v = a[..., ch][reg]; rr = r[reg]; best = None
    for p in (1.5, 2.0, 2.5):
        for s_ in np.arange(100, 700, 5):
            g = np.exp(-(rr / s_) ** p); X = np.stack([np.ones_like(g), g], 1); c = np.linalg.lstsq(X, v, rcond=None)[0]
            e = ((X @ c - v) ** 2).mean()
            if best is None or e < best[0]: best = (e, s_, p, c)
    e, s_, p, c = best; model[..., ch] = c[0] + c[1] * np.exp(-(r / s_) ** p)
fig = (np.abs(a - model).max(2) > 2) & box
w = np.asarray(Image.fromarray((fig * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(3))).astype(float)[..., None] / 255
w = w * box[..., None]; a = a * (1 - w) + model * w
bgc = tuple(int(v) for v in a[1300, 40])
base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(base)
TITLE = os.environ.get('TITLE', 'Push'); SUB = os.environ.get('SUB', 'Pecho · Hombros · Tríceps')
FD = '/usr/share/fonts/opentype/inter/'
d.rectangle((300, 1340, 740, 1480), fill=bgc); d.rectangle((180, 1505, 860, 1570), fill=bgc)
ft = ImageFont.truetype(FD + 'InterDisplay-ExtraBold.otf', 150); fsb = ImageFont.truetype(FD + 'Inter-Regular.otf', 39)
cxs = 518
bb = d.textbbox((0, 0), TITLE, font=ft); d.text((cxs - (bb[0] + bb[2]) / 2, 1465 - bb[3]), TITLE, font=ft, fill=(12, 12, 12))
bb = d.textbbox((0, 0), SUB, font=fsb); d.text((cxs - (bb[0] + bb[2]) / 2, 1553 - bb[3]), SUB, font=fsb, fill=(98, 98, 98))
# figure: same size and place as the still (rest pose: 535 high, top at 568, centred at 470, in 944-wide units)
b0 = bbs[0]; s = 535 * k / (b0[3] - b0[1])
fw, fh = int(crops[0].width * s), int(crops[0].height * s)
px = int(470 * k - fw / 2); py = int(568 * k - (b0[1] - y0) * s)
sh = Image.new('L', base.size, 0); ImageDraw.Draw(sh).ellipse((470 * k - 130 * k, py + (b0[3] - y0) * s - 10 * k,
                                                               470 * k + 130 * k, py + (b0[3] - y0) * s + 14 * k), fill=70)
sh = sh.filter(ImageFilter.GaussianBlur(12 * k))
base = Image.composite(Image.new('RGB', base.size, (60, 60, 60)), base, sh)
W = E('W', 720); H = int(base.height * W / base.width) // 2 * 2
d1 = os.path.join(tmp, 'm'); os.makedirs(d1)
for i, c in enumerate(crops):
    fr = base.convert('RGBA'); fr.alpha_composite(c.resize((fw, fh), Image.LANCZOS), (px, py))
    fr.convert('RGB').resize((W, H), Image.LANCZOS).save(os.path.join(d1, 's%02d.png' % i))
    if i in (0, n - 1): fr.convert('RGB').save(outp + '_app_%02d.jpg' % i, quality=92)
for kk, i in enumerate(seq): os.symlink(os.path.join(d1, 's%02d.png' % i), os.path.join(d1, 'v%05d.png' % kk))
encode(d1, 'v%05d.png', outp + '_en_la_app.mp4', ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-movflags', '+faststart'])
# plain H.264 on the app's background colour (no transparency) for a quick look
d3 = os.path.join(tmp, 'p'); os.makedirs(d3)
for i, c in enumerate(small):
    bg = Image.new('RGBA', c.size, bgc + (255,)); bg.alpha_composite(c); bg.convert('RGB').save(os.path.join(d3, 's%02d.png' % i))
for kk, i in enumerate(seq): os.symlink(os.path.join(d3, 's%02d.png' % i), os.path.join(d3, 'v%05d.png' % kk))
encode(d3, 'v%05d.png', outp + '.mp4', ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-movflags', '+faststart'])
for f in (outp + '_transparente.mov', outp + '_en_la_app.mp4', outp + '.mp4'):
    print(os.path.basename(f), '%.1f MB' % (os.path.getsize(f) / 1e6))
