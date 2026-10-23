# red / grey percentiles of a full-frame render scaled to the reference size vs the reference
import sys,numpy as np
from PIL import Image
def stats(im,name):
    a=np.asarray(im).astype(float); mx=a.max(-1); mn=a.min(-1); sat=(mx-mn)/(mx+1e-6)
    red=(sat>0.3)&(a[...,0]>a[...,1]+30); R=a[red]; L=R.sum(1); o=np.argsort(L)
    g=(sat<0.08)&(mx>60)&(mx<250); G=a[g][:,0]
    print('%-8s red'%name,' '.join('%d:%s'%(p,R[o[int(len(o)*p/100)-1]].astype(int).tolist()) for p in (5,25,50,75,95)),'| grey',np.percentile(G,[5,25,50,75,95]).astype(int).tolist())
ref=Image.open(__import__('os').environ.get('GT3D','.')+'/referencias/8ccf8362-image.jpg').convert('RGB').crop((170,10,480,470))
stats(ref,'ref')
for n in sys.argv[1:]:
    im=Image.open(n); bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); bb=im.getchannel('A').getbbox()
    fr=bg.convert('RGB').crop((bb[0]-15,bb[1]-15,bb[2]+15,bb[3]+15)); fr=fr.resize((int(fr.width*674/fr.height),674),Image.LANCZOS)
    stats(fr.crop((int(fr.width*0.18),10,int(fr.width*0.66),470)),n.split('/')[-1][:-4])
