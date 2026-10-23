#!/bin/bash
# usage: calib.sh NAME [env...]  -> renders the t/mask debug for the arm view, prints matching TSTOPS/TONES, then renders NAME with them
S=${GT3D:-/tmp/claude-0/-home-user-Gym-tracker-2/8036e25a-39fc-507e-8939-935aaa1c5ddc/scratchpad}; cd $S/w
n=$1; shift
VIEW="YAW=135 PIT=20 TX=0.24 TY=-0.09 TZ=0.88 OSC=0.6 RES=700"
env $(cat $S/ill/arm_style2.env) "$@" MDEBUG=tm SMP=4 DENOISE=0 MAPS=${MAPS:-$S/ill/maps_bla3} NPZ=$S/ill/pv/bla_row2.npz $VIEW $S/venv/bin/python -I $S/ill/rendsculpt.py ${FRAME:-BRv00}.blend $S/ill/r/${n}_tm > /dev/null 2>&1
read ST TN RS RC < <(python3 -c "
from PIL import Image; import numpy as np
a=np.asarray(Image.open('$S/ill/r/${n}_tm.png').convert('RGBA')).astype(float)/255
lin=lambda c: np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
t=lin(a[...,0]); m=(lin(a[...,1])>0.9)&(a[...,3]>0.99)&(lin(a[...,2])<0.1)
q=np.percentile(t[m],[5,15,30,50,70,85,95])
ref=[87,125,156,184,206,229,242]
st=[0.0]; tn=[0.28]
for v,rv in zip(q,ref):
    v=max(v,st[-1]+0.004); st.append(min(v,0.995)); tn.append(rv/255)
st.append(1.0); tn.append(1.0)
# red: same equalisation against the reference deltoid/back reds
rm=(lin(a[...,2])>0.5)&(a[...,3]>0.99); cm=np.zeros_like(rm); cm[20:200,320:470]=True; rm&=cm
rq=np.percentile(t[rm],[3,10,25,50,75,90,99])
rc=['89/55/45','147/75/53','173/96','221/114/78','238/146/109','238/164/127','247/196/165']
rc=['89/55/45','147/75/53','173/96/68','221/114/78','238/146/109','238/164/127','247/196/165']
rs=[0.0]; rcs=['70/35/25']
for v,c in zip(rq,rc):
    v=max(v,rs[-1]+0.004); rs.append(min(v,0.995)); rcs.append(c)
rs.append(1.0); rcs.append('250/210/185')
print(','.join('%.4f'%x for x in st),','.join('%.3f'%x for x in tn),','.join('%.4f'%x for x in rs),','.join(rcs))")
echo "TSTOPS=$ST TONES=$TN RSTOPS=$RS RCOLS=$RC" > $S/ill/r/${n}_calib.txt; cat $S/ill/r/${n}_calib.txt
env $(cat $S/ill/arm_style2.env) TSTOPS=$ST TONES=$TN RSTOPS=$RS RCOLS=$RC "$@" MAPS=${MAPS:-$S/ill/maps_bla3} NPZ=$S/ill/pv/bla_row2.npz $VIEW SMP=${SMP:-24} $S/venv/bin/python -I $S/ill/rendsculpt.py ${FRAME:-BRv00}.blend $S/ill/r/$n 2>&1 | grep -i "Trace" -A5
$S/venv/bin/python -I $S/ill/armstat2.py $S/ill/r/${n}_tm.png $S/ill/r/$n.png
