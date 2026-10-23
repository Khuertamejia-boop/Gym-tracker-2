# grey-level percentiles of the visible left arm (white muscles only), using a mask render (MDEBUG=tm) of the same view
import sys,numpy as np
from PIL import Image
mk=np.asarray(Image.open(sys.argv[1]).convert('RGBA')).astype(float)/255
lin=lambda c: np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
m=(lin(mk[...,1])>0.9)&(mk[...,3]>0.99)&(lin(mk[...,2])<0.1)
for f in sys.argv[2:]:
    a=np.asarray(Image.open(f).convert('RGBA')).astype(float)
    g=a[...,:3].mean(-1)[m]
    print(f.split('/')[-1],'arm grey p5..p95',np.percentile(g,[5,15,30,50,70,85,95]).astype(int),'   ref [ 87 125 156 184 206 229 242]')
