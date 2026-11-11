# usage: headviews.sh file.blend out.jpg
S=$(dirname $0); for Y in 0 90 150; do ( GG=0.35 GP=1.0 AOD=0.06 AOP=2.0 LK=0.6 AMB=0.14 PIT=3 YAW=$Y RES=600 SMP=12 VIEWS=cus TX=0 TY=-0.02 TZ=1.45 OSC=0.6 REDIDS=-5 LNK=0.3 SHV=0.04 $S/venv/bin/python -I $S/rendarm.py $1 r/hv_$Y > /dev/null 2>&1 ) & done; wait
$S/venv/bin/python -I -c "
from PIL import Image
im=Image.new('RGB',(1800,600),'white')
for k,Y in enumerate(('0','90','150')):
    x=Image.open(f'r/hv_{Y}_cus.png'); im.paste(x,(k*600,0),x)
im.save('$2',quality=88)"
