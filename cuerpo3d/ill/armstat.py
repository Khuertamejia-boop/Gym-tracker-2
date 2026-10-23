import sys,numpy as np
from PIL import Image
for f in sys.argv[1:]:
    a=np.asarray(Image.open(f).convert('RGBA')).astype(float)
    # arm region of the 700px close-up: columns 230..470, rows 150..650, opaque, not red (low saturation)
    sub=a[150:650,250:470]; rgb=sub[...,:3]; al=sub[...,3]
    mx=rgb.max(-1); mn=rgb.min(-1); sat=(mx-mn)/(mx+1e-6)
    m=(al>250)&(sat<0.12)
    g=rgb.mean(-1)[m]
    print(f.split('/')[-1],'grey percentiles',np.percentile(g,[5,15,30,50,70,85,95]).astype(int),'n',m.sum())
