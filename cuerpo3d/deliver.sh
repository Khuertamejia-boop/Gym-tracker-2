#!/bin/bash
# deliver.sh TAG : final neutral views + highlight images + light model, from PSM_TAG.blend
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; T=$1; cd $S/w
(HLIDS=60,61,62,63,64,65,66,1,2,3 CLOSE=260 DT=0.10 $S/venv/bin/python -I scripts/hl.py PSM_$T.blend HLF_$T.blend 2>&1 | grep -i "trace" -A3) &
(HLIDS=75,76,77,78,79,80,81,3 CLOSE=260 DT=0.10 $S/venv/bin/python -I scripts/hl.py PSM_$T.blend HLB_$T.blend 2>&1 | grep -i "trace" -A3) &
(cd $S/w && $S/venv/bin/python -I $S/export_light.py PSM_$T.blend $S/out/light cuerpo3d_v20_ligero 2>&1 | grep -i "after\|fbx\|usd\|trace" ) &
wait
BASE="GG=0.4 GP=1.0 AOD=0.06 AOP=2.5 LK=0.6 AMB=0.14 PIT=3 RES=1400 SMP=24 VIEWS=full LNK=0.3 SHV=0.04 REDC=0.82,0.10,0.02"
for spec in "fin_f 0" "fin_s 90" "fin_b 180"; do set -- $spec
  (env $BASE YAW=$2 REDIDS=-5 $S/venv/bin/python -I $S/rendarm.py PSM_$T.blend r/$1 2>&1 | grep Traceback) &
done; wait
(env $BASE YAW=0 HL=1 REDIDS=-5 $S/venv/bin/python -I $S/rendarm.py HLF_$T.blend r/hlf 2>&1 | grep Traceback) &
(env $BASE YAW=180 HL=1 REDIDS=-5 $S/venv/bin/python -I $S/rendarm.py HLB_$T.blend r/hlb 2>&1 | grep Traceback) &
wait
cd r; python3 -I - <<'PY'
from PIL import Image
S="${GT3D:-${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}}/"
for n,f in (('frente','fin_f'),('perfil','fin_s'),('espalda','fin_b'),('resalte_pecho_hombros','hlf'),('resalte_espalda','hlb')):
    rgba=Image.open(f'{f}_full.png').convert('RGBA'); bb=rgba.getchannel('A').getbbox(); pad=40
    box=(max(bb[0]-pad,0),max(bb[1]-pad,0),min(bb[2]+pad,rgba.width),min(bb[3]+pad,rgba.height))
    bg=Image.new('RGBA',rgba.size,'white'); bg.alpha_composite(rgba)
    bg.convert('RGB').crop(box).save(S+f'out/cuerpo3d_{n}.jpg',quality=92); rgba.crop(box).save(S+f'out/cuerpo3d_{n}.png')
def sheet(names,out):
    ims=[Image.open(S+f'out/cuerpo3d_{n}.jpg') for n in names]; H=max(i.height for i in ims)
    c=Image.new('RGB',(sum(i.width for i in ims),H),'white'); x=0
    for i in ims: c.paste(i,(x,0)); x+=i.width
    c.save(S+out,quality=90)
sheet(('frente','perfil','espalda'),'out/cuerpo3d_3vistas.jpg'); sheet(('resalte_pecho_hombros','resalte_espalda'),'out/cuerpo3d_resaltes.jpg')
PY
