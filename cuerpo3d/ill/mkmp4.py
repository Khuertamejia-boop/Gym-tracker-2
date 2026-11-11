# MP4 (25 fps, H.264) with the same timing as mkgif2.py: up 1 image per video frame (40 ms), down 2 (80 ms),
# pauses at the top (10 frames) and the bottom (15 frames).   python3 mkmp4.py out.mp4 f00.png ... fNN.png
#   env: UPK (1), DOWNK (2), HOLDT (10), HOLDB (15), W (1920)
import sys, os, subprocess, tempfile
from PIL import Image
out=sys.argv[1]; fs=sys.argv[2:]; E=lambda k,d: int(os.environ.get(k,d)); W=E('W',1920)
n=len(fs); seq=[0]*E('HOLDB',15)
for i in range(1,n): seq+=[i]*E('UPK',1)
seq+=[n-1]*E('HOLDT',10)
for i in range(n-2,0,-1): seq+=[i]*E('DOWNK',2)
d=tempfile.mkdtemp()
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGBA'); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); c=bg.convert('RGB')
    if c.width!=W: c=c.resize((W,int(c.height*W/c.width)//2*2),Image.LANCZOS)
    c.save(os.path.join(d,'s%03d.png'%i))
for k,i in enumerate(seq): os.symlink(os.path.join(d,'s%03d.png'%i),os.path.join(d,'v%05d.png'%k))
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','25','-i',os.path.join(d,'v%05d.png'),'-c:v','libx264','-pix_fmt','yuv420p',
                '-crf','20','-preset','slow','-movflags','+faststart',out],check=True)
print('mp4',out,len(seq),'frames, %.2f s'%(len(seq)/25))
