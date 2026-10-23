import sys,numpy as np
from PIL import Image
for f in sys.argv[1:]:
    im=np.asarray(Image.open(f).convert('RGB')).astype(float)
    sub=im[20:200,320:470]
    mx=sub.max(-1); mn=sub.min(-1); sat=(mx-mn)/(mx+1e-6); red=(sat>0.3)&(sub[...,0]>sub[...,1]+30)
    R=sub[red]; L=R.sum(1); o=np.argsort(L)
    print(f.split('/')[-1],' '.join('p%d=%s'%(p,R[o[int(len(o)*p/100)-1]].astype(int).tolist()) for p in (3,10,25,50,75,90,99)))
print('ref   p3=[89,55,45] p10=[147,75,53] p25=[173,96,68] p50=[221,114,78] p75=[238,146,109] p90=[238,164,127] p99=[247,196,165]')
