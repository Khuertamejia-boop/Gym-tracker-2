import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F='/usr/share/fonts/opentype/inter/'
def font(w,s): return ImageFont.truetype(F+{'b':'Inter-Bold.otf','sb':'Inter-SemiBold.otf','m':'Inter-Medium.otf','r':'Inter-Regular.otf'}[w],s)
def load(p): return np.asarray(Image.open(p).convert('RGBA')).astype(float)/255
def rounded(size,r):
    m=Image.new('L',size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,size[0]-1,size[1]-1),r,fill=255); return m
def body_layer(kind,part,H,mode):
    g=load(f'card_{part}g_cus.png'); m=load(f'card_{part}m_cus.png')[...,0]; c=load(f'card_{part}_cus.png')
    a=g[...,3]; L=g[...,:3].mean(-1)
    if mode=='white':      # on the red card: faint white body, worked muscles bright white with the lines
        Lw=np.clip(L*1.25,0,1)
        alpha=a*(0.20*(1-m)+0.97*m)
        rgb=np.stack([Lw]*3,-1)*np.where(m[...,None]>0.5,1.0,1.0)
        rgb=np.clip(0.55+0.45*rgb,0,1)*np.where(m[...,None]>0.5,Lw[...,None]**0.35,1)
        out=np.dstack([rgb,alpha])
    else:                  # on a light card: grey body + crimson worked muscles
        out=c
    im=Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8),'RGBA')
    # crop to the body
    bb=im.getchannel('A').getbbox(); im=im.crop(bb)
    s=H/im.height; im=im.resize((int(im.width*s),H),Image.LANCZOS)
    return im
def fade(im,bottom=0.35,left=0.0):
    a=np.asarray(im.getchannel('A')).astype(float); h,w=a.shape
    yy=np.linspace(0,1,h)[:,None]; xx=np.linspace(0,1,w)[None,:]
    f=np.clip((1-yy)/bottom,0,1) if bottom>0 else 1
    if left>0: f=f*np.clip(xx/left,0,1)
    im.putalpha(Image.fromarray((a*f).astype(np.uint8))); return im
RED=(184,44,56); CARD=(250,249,248); BG=(242,241,239)
def card(w,h,color,part,mode,label,title,sub,meta,dark_text,scale,ox,oy):
    cv=Image.new('RGBA',(w,h),color+(255,))
    b=body_layer('x',part,int(h*scale),mode); b=fade(b,0.30 if part=='tor' else 0.12)
    cv.alpha_composite(b,(ox if ox>=0 else w-b.width+ox, oy))
    d=ImageDraw.Draw(cv)
    tc=(255,255,255) if not dark_text else (20,20,20); lc=(255,255,255,215) if not dark_text else (RED[0],RED[1],RED[2],255)
    d.text((54,62),label,font=font('sb',30),fill=lc,spacing=4)
    if title: d.text((54,h-245 if sub else h-130),title,font=font('b',62),fill=tc)
    if sub: d.text((54,h-160),sub,font=font('m',30),fill=tc if not dark_text else (60,60,60))
    if meta: d.text((54,h-108),meta,font=font('r',30),fill=(255,255,255,220) if not dark_text else (110,110,110))
    out=Image.new('RGBA',(w,h),(0,0,0,0)); out.paste(cv,(0,0),rounded((w,h),64)); return out
def screen(variant):
    W,H=1880,900; sc=Image.new('RGBA',(W,H),BG+(255,))
    if variant=='A':
        c1=card(1160,740,RED,'tor','white','MAÑANA · LUN 5','Torso','Hombros · Espalda · Pecho · Tríceps · Bíceps','8 ejercicios · ~80 min',False,1.25,-40,-20)
    else:
        c1=card(1160,740,CARD,'tor','color','MAÑANA · LUN 5','Torso','Hombros · Espalda · Pecho · Tríceps · Bíceps','8 ejercicios · ~80 min',True,1.25,-40,-20)
    c2=card(640,740,CARD,'leg','color','MAR 6','Pierna A',None,None,True,1.05,-10,-40)
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); dd=ImageDraw.Draw(sh)
    for x,c in ((70,c1),(70+1160+40,c2)): dd.rounded_rectangle((x,96,x+c.width,96+c.height),64,fill=(0,0,0,28))
    sh=sh.filter(ImageFilter.GaussianBlur(18)); sc.alpha_composite(sh)
    sc.alpha_composite(c1,(70,80)); sc.alpha_composite(c2,(70+1160+40,80))
    d=ImageDraw.Draw(sc); d.text((70,830),'Opción '+variant+(': tarjeta roja, cuerpo blanco' if variant=='A' else ': tarjeta clara, músculos en carmesí'),font=font('sb',36),fill=(60,60,60))
    return sc.convert('RGB')
a=screen('A'); b=screen('B')
o=Image.new('RGB',(a.width,a.height*2+20),BG); o.paste(a,(0,0)); o.paste(b,(0,a.height+20)); o.save(os.environ.get('GT3D','/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad')+'/out/tarjetas_AB.jpg',quality=90)
